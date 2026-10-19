// Consulta el sistema local real. Bloquea cualquier escritura de la interfaz.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
(async()=>{
  assert(process.env.QA_ACCESS_TOKEN && process.env.QA_OUTPUT);
  const api='http://localhost:8000/api/v1',web='http://localhost:5173';
  const checks=[],errors=[],writes=[],output=process.env.QA_OUTPUT;
  fs.mkdirSync(output,{recursive:true});
  const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  try {
    const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
    await context.addInitScript(t=>sessionStorage.setItem('access_token',t),process.env.QA_ACCESS_TOKEN);
    const page=await context.newPage();page.setDefaultTimeout(45000);
    page.on('pageerror',e=>errors.push(e.message));
    page.on('response',r=>{if(r.url().includes('/api/v1/') && r.status()>=400)errors.push(r.status()+' '+new URL(r.url()).pathname)});
    await page.route('**/api/v1/**',async r=>{
      if(!['GET','OPTIONS'].includes(r.request().method())) {writes.push(r.request().method());await r.abort()}
      else await r.continue();
    });
    const headers={Authorization:'Bearer '+process.env.QA_ACCESS_TOKEN};
    async function leer(params){const r=await context.request.get(api+'/analitica/reglas-historicas',{headers,params});assert.equal(r.status(),200);return r.json()}
    async function consultar(params,accion){
      const pending=page.waitForResponse(r=>{
        const u=new URL(r.url());return u.pathname==='/api/v1/analitica/reglas-historicas' && Object.entries(params).every(([k,v])=>u.searchParams.get(k)===String(v));
      });await accion();const response=await pending;assert.equal(response.status(),200);const data=await response.json();
      await page.waitForFunction(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Consultar reglas');return b && !b.disabled});return data;
    }
    await page.goto(web+'/analitica');
    const section=page.getByRole('region',{name:'Reglas sobre gestiones antiguas'});
    await section.getByText(/movimientos en la consulta/).waitFor();
    await section.getByLabel('Gestión de reglas históricas').selectOption('2025');
    await section.getByLabel('Selección de reglas históricas').selectOption('todos');
    let data=await consultar({gestion:2025,seleccion:'todos'},()=>section.getByRole('button',{name:'Consultar reglas',exact:true}).click());
    assert.equal(data.total,216);assert(data.filas.every(f=>f.gestion===2025));checks.push('2025: 216 filas históricas; filtro y paginación correctos.');
    await section.getByLabel('Selección de reglas históricas').selectOption('avisos');
    await section.getByLabel('Regla histórica').selectOption('AGOTA_STOCK');
    data=await consultar({gestion:2025,seleccion:'avisos',regla:'AGOTA_STOCK'},()=>section.getByRole('button',{name:'Consultar reglas',exact:true}).click());
    const expected=await leer({gestion:2025,seleccion:'avisos',regla:'AGOTA_STOCK'});
    assert.equal(data.total,expected.total);assert(data.total>0);
    const row=data.filas[0];assert(row.base_utilizable);assert.equal(row.salidas,row.saldo_previo);
    await section.getByRole('button',{name:'Ver detalle de reglas',exact:true}).first().click();
    const detail=section.getByRole('region',{name:'Evidencia de reglas históricas'});
    const photo=detail.getByAltText('Fotografía de la regla histórica');await photo.waitFor();await photo.evaluate(img=>img.decode());
    assert(await photo.evaluate(img=>img.naturalWidth>0));
    assert((await detail.innerText()).includes('Salida de todas las unidades'));
    assert((await detail.innerText()).includes('Filas anteriores y siguientes'));
    const link=detail.getByRole('link',{name:'Abrir revisión humana del artículo'});assert((await link.getAttribute('href')).includes('articulo_id='+row.articulo_id));
    checks.push({caso_real:row.id,articulo:row.articulo,gestion:2025,salida:row.salidas,saldo_previo:row.saldo_previo,total_retiros:data.total});
    await page.screenshot({path:path.join(output,'reglas-2025-evidencia.png'),fullPage:true});
    const pending=page.waitForEvent('download');await section.getByRole('button',{name:'Descargar reglas históricas (CSV)',exact:true}).click();
    const download=await pending;assert.equal(await download.failure(),null);await download.saveAs(path.join(output,'reglas_historicas_2025.csv'));
    checks.push('CSV de las reglas aplicadas descargado desde la interfaz.');
    await section.getByLabel('Artículo de reglas históricas').fill('QA_ARTICULO_INEXISTENTE');
    data=await consultar({articulo:'QA_ARTICULO_INEXISTENTE'},()=>section.getByRole('button',{name:'Consultar reglas',exact:true}).click());
    assert.equal(data.total,0);await section.getByText('No hay movimientos para los filtros de reglas seleccionados.').waitFor();
    checks.push('Búsqueda sin coincidencias: cero resultados.');
    await section.getByRole('button',{name:'Limpiar filtros de reglas',exact:true}).click();
    await section.getByText(/movimientos en la consulta/).waitFor();
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await page.screenshot({path:path.join(output,'reglas-movil.png'),fullPage:true});
    checks.push('Consulta visible en móvil sin desbordamiento de la página.');
    assert.deepEqual(errors,[]);assert.deepEqual(writes,[]);
    fs.writeFileSync(path.join(output,'navegador.json'),JSON.stringify({resultado:'CORRECTO',checks,errors,writes},null,2));
    console.log(JSON.stringify({resultado:'CORRECTO',checks}));
  }finally{await browser.close()}
})().catch(e=>{console.error(e.message);process.exit(1)});
