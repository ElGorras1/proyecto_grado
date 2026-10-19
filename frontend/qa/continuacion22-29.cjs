// Lectura real: no registra stock, modelos, cierres ni revisiones humanas.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('fs'),path=require('path');
(async()=>{
  if(!process.env.QA_ACCESS_TOKEN) throw Error('Falta la sesión QA local');
  const browser=await chromium.launch({executablePath:process.env.BROWSER_EXECUTABLE || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1440,height:1050}}),errores=[],escrituras=[];
    page.on('pageerror',e=>errores.push(e.message));
    page.on('response',r=>{if(r.url().includes('/api/v1/') && r.status()>=400) errores.push(r.status()+' '+new URL(r.url()).pathname)});
    await page.addInitScript(t=>sessionStorage.setItem('access_token',t),process.env.QA_ACCESS_TOKEN);
    await page.route('**/api/v1/**',async r=>{
      if(!['GET','OPTIONS'].includes(r.request().method())) {escrituras.push(r.request().method());await r.abort()}
      else await r.continue();
    });
    const salida=process.env.QA_OUTPUT || path.join(__dirname,'../../backend/backups/continuacion22_29_qa');
    fs.mkdirSync(salida,{recursive:true});
    await page.goto('http://localhost:5173/gestion-institucional');
    await page.getByText('Unidades de inventario activado',{exact:true}).waitFor();
    if(!(await page.locator('main').innerText()).includes('sin porcentaje verificado')) throw Error('Cobertura física incorrecta');
    if(!(await page.locator('main').innerText()).includes('La gestión todavía no terminó.')) throw Error('Cierre anual indebido');
    if(!await page.getByRole('button',{name:'Guardar cierre anual',exact:true}).isDisabled()) throw Error('Cierre habilitado sin condiciones');
    await page.screenshot({path:path.join(salida,'informe-escritorio.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw Error('Desborde móvil del informe');
    await page.screenshot({path:path.join(salida,'informe-movil.png'),fullPage:true});
    await page.goto('http://localhost:5173/analitica-operativa');
    await page.getByText('Actualmente no hay un modelo operativo activo.',{exact:true}).waitFor();
    if(!await page.getByRole('button',{name:'Preparar nueva versión',exact:true}).isDisabled()) throw Error('Entrenamiento habilitado sin datos');
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw Error('Desborde móvil de analítica');
    await page.screenshot({path:path.join(salida,'operativa-movil.png'),fullPage:true});
    await page.setViewportSize({width:1440,height:1050});
    await page.goto('http://localhost:5173/analitica');
    await page.getByRole('button',{name:'Ver evidencia',exact:true}).first().waitFor();
    await page.getByRole('button',{name:'Ver evidencia',exact:true}).first().click();
    const detalle=page.getByRole('region',{name:'Evidencia del hallazgo'});
    await detalle.getByRole('heading').first().waitFor();
    const foto=page.getByAltText('Fotografía original del Kárdex');
    await foto.waitFor({state:'attached'});await foto.evaluate(img=>img.decode());
    if(!(await foto.evaluate(img=>img.naturalWidth>0 && img.getBoundingClientRect().width>0))) throw Error('Imagen cargada sin visualización');
    const url=await foto.getAttribute('src');
    if((await page.request.get(url)).status()!==200) throw Error('Foto inaccesible con sesión');
    const anonimo=await browser.newContext();
    if((await anonimo.request.get(url)).status()!==401) throw Error('Foto expuesta sin sesión');
    await anonimo.close();
    await page.getByRole('button',{name:'Cerrar detalle',exact:true}).click();
    const modo=page.locator('select').filter({has:page.locator('option[value="TEMPORAL"]')});
    await modo.selectOption('TEMPORAL');
    await page.getByText('La muestra temporal es insuficiente.',{exact:false}).waitFor();
    if(!await page.getByRole('button',{name:'Entrenar nueva versión',exact:true}).isDisabled()) throw Error('Corte anual insuficiente habilitado');
    await page.screenshot({path:path.join(salida,'temporal-escritorio.png'),fullPage:true});
    if(errores.length || escrituras.length) throw Error([...errores,...escrituras].join('\n'));
    console.log('QA real: informe, cierre bloqueado, analítica operativa sin datos, corte temporal insuficiente, fotos privadas y móvil; sin escrituras.');
  }finally{await browser.close()}
})().catch(e=>{console.error(e.message);process.exit(1)});
