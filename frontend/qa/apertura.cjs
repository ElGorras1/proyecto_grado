const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const path = require('path');
(async () => {
 const browser = await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const page = await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(()=>sessionStorage.setItem('access_token','qa-ficticio'));
 const art={id:1,codigo:'QA-01',nombre:'Artículo de demostración',stock_actual:null,apertura:null};
 await page.route('**/api/v1/**',async route=>{
  const url=new URL(route.request().url()); let data;
  if(url.pathname.endsWith('/auth/me')) data={id:1,nombre:'Cuenta QA',rol:'Administrador'};
  else if(url.pathname.endsWith('/apertura')) {
   const body=route.request().postDataJSON();
   art.apertura={cantidad_inicial:body.cantidad,cantidad_actual:body.cantidad,ultimo_moderno_id:1,aprobado_por:1,aprobado_en:'2026-10-06T22:00:00Z',referencia_documento:body.referencia_documento,justificacion:body.justificacion};
   art.stock_actual=body.cantidad; data=art.apertura;
  }
  else if(url.pathname.endsWith('/articulos')) data=[art];
  else if(url.pathname.includes('/historial-actual/')) data=[{id:1,fecha_movimiento:'2025-01-01',detalle:'Antecedente',saldo_registrado:900,estado:'ACTIVO'}];
  else if(url.pathname.endsWith('/nodos') || url.pathname.endsWith('/ferias')) data=[];
  else throw Error('Ruta inesperada '+url.pathname);
  await route.fulfill({json:data});
 });
 await page.goto('http://localhost:5173/inventario-vivo');
 await page.getByText('Artículo de demostración',{exact:true}).click();
 await page.getByRole('heading',{name:'Saldo de apertura pendiente'}).waitFor();
 await page.screenshot({path:path.join(__dirname,'apertura-escritorio.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:path.join(__dirname,'apertura-movil.png'),fullPage:true});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth)) throw Error('Desborde horizontal');
 await page.getByLabel('Cantidad física verificada').fill('12');
 await page.getByLabel('Referencia del acta').fill('ACTA-QA');
 await page.getByLabel('Justificación del saldo').fill('Conteo ficticio para probar la interfaz');
 await page.getByRole('checkbox').check();
 await page.getByRole('button',{name:'Aprobar saldo de apertura'}).click();
 await page.getByText('Apertura aprobada: 12 u.',{exact:true}).waitFor();
 if(await page.getByTitle('Anular Transacción').count()) throw Error('Permite anular un antecedente');
 await page.screenshot({path:path.join(__dirname,'apertura-aprobada.png'),fullPage:true});
 if(errors.length) throw Error(errors.join('\n'));
 console.log('QA apertura escritorio/móvil/aprobación: correcto. Datos ficticios.');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
