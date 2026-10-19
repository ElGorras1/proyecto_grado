const {chromium}=require('C:/Users/LENOVO/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {pathToFileURL,fileURLToPath}=require('url');const fs=require('fs');const path=require('path');
(async()=>{
 const numeros=process.argv.slice(2).map(Number);if(!numeros.length||numeros.some(n=>!Number.isInteger(n)||n<13||n>99))throw Error('Indicar números de lotes 13–99');
 const dir=path.resolve(__dirname,'../backups/aplicacion_hil_20261014');const resultados=[],errores=[];
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try{
  const page=await browser.newPage();page.on('pageerror',e=>errores.push(String(e)));
  for(const n of numeros){
   const sufijo=String(n).padStart(2,'0');const datos=JSON.parse(fs.readFileSync(path.join(dir,`instantanea_informe_continuacion_${sufijo}.json`),'utf8'));
   const resultado=JSON.parse(fs.readFileSync(path.join(dir,`resultado_continuacion_${sufijo}.json`),'utf8'));
   const cantidad=datos.articulos.reduce((s,a)=>s+a.filas.length,0);
   await page.setViewportSize({width:1440,height:1000});await page.goto(pathToFileURL(`C:/Users/LENOVO/Downloads/Continuacion_HIL_Lote_${sufijo}_2026-10-15.html`).href);
   if(await page.locator('details.articulo tbody tr').count()!==cantidad||await page.locator('details.articulo').count()!==datos.articulos.length)throw Error('Conteos '+n);
   const texto=await page.locator('main').innerText();if(!texto.includes(`${resultado.revisados_acumulados} movimientos distintos`))throw Error('Acumulado '+n);
   const fotos=await page.locator('a[href^="file:"]').evaluateAll(a=>Array.from(new Set(a.map(x=>x.href))));
   if(fotos.length!==resultado.cotejo.fotografias||!fotos.every(f=>fs.existsSync(fileURLToPath(f))))throw Error('Evidencias '+n);
   if(n===14){
    const fila=page.locator('#articulo-78 tbody tr').filter({hasText:'#4421'});await fila.locator('summary').click();
    if(!(await fila.innerText()).includes('tachada'))throw Error('No conserva la marca anulada de la celda');
   }
   if(n===15){
    const fila=page.locator('#articulo-77 tbody tr').filter({hasText:'#4256'});await fila.locator('summary').click();
    if(!(await fila.innerText()).includes('salida 40 y saldo 49'))throw Error('Falta criterio de la salida anterior');
   }
   if(n===17){
    if(!texto.includes('Pendiente de conciliación · no operable')||!texto.includes('Acumulado condicional: 309')||!texto.includes('Saldo hipotético'))throw Error('El informe oculta la incertidumbre de Campero');
    const cierre=page.locator('main > .tabla tbody tr').first();
    if(!(await cierre.innerText()).includes('300'))throw Error('Falta el cierre escrito conservado');
   }
   if(n===18){
    const base=page.locator('#articulo-84 tbody tr').filter({hasText:'#5214'});
    if(!(await base.innerText()).includes('Base documental · sin ingreso añadido')||await base.locator('td').nth(3).innerText()!=='—')throw Error('La base inicial parece un ingreso añadido');
    const dudosa=page.locator('#articulo-84 tbody tr').filter({hasText:'#5271'});
    if(!(await dudosa.innerText()).includes('Cantidad hipotética'))throw Error('Se oculta la cantidad dudosa de Expo');
   }
   if(n===19){
    const mixta=page.locator('#articulo-99 tbody tr').filter({hasText:'#6886'});
    if(!(await mixta.innerText()).includes('Donación y venta · sin desglose documental')||await mixta.locator('td').nth(3).innerText()!=='—'||await mixta.locator('td').nth(4).innerText()!=='360')throw Error('Salida mixta incorrecta');
   }
   if(n===20){
    for(const [id,ingreso] of [[2382,4],[2399,1],[2400,8]]){
     const fila=page.locator('#articulo-53 tbody tr').filter({hasText:'#'+id});
     if(await fila.locator('td').nth(3).innerText()!==String(ingreso)||await fila.locator('td').nth(4).innerText()!=='—')throw Error('Ingreso desplazado no recuperado '+id);
    }
   }
   if(n===21){
    const cero=page.locator('#articulo-86 tbody tr').filter({hasText:'#5438'});
    if(!(await cero.locator('td').nth(5).innerText()).includes('Saldo hipotético')||await cero.locator('td').nth(6).innerText()!=='—')throw Error('El guion documental aparece como cero confirmado');
    const final=page.locator('#articulo-86 tbody tr').filter({hasText:'#5527'});
    if(!(await final.innerText()).includes('Fecha técnica / estimada'))throw Error('La devolución sin fecha parece fechada en el papel');
   }
   if(n===22){
    if(!texto.includes('Discontinuidad de 56 unidades entre fotos')||!texto.includes('cierre escrito 251 y cálculo 250'))throw Error('No se distinguen los límites de ambos cierres pendientes');
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const resta=fila(85,5352);
    if(await resta.locator('td').nth(4).innerText()!=='6'||await resta.locator('td').nth(5).innerText()!=='357'||await resta.locator('td').nth(6).innerText()!=='358')throw Error('Se alteró la salida 6 para cuadrar el papel');
    const compensada=fila(97,6862);
    if(await compensada.locator('td').nth(3).innerText()!=='1'||await compensada.locator('td').nth(5).innerText()!=='222'||await compensada.locator('td').nth(6).innerText()!=='220')throw Error('No conserva el error compensado de Cambio climático');
    if(await fila(85,5323).locator('td').nth(3).innerText()!=='0')throw Error('Se perdió el cero escrito');
    const salto=fila(90,6018);
    if(!(await salto.locator('td').nth(5).innerText()).includes('Saldo hipotético')||await salto.locator('td').nth(6).innerText()!=='96')throw Error('Se oculta la discontinuidad entre hojas');
   }
   if(n===23){
    if(!texto.includes('Cierre 67 frente a acumulado condicional 57')||!texto.includes('Pendiente de conciliación · no operable'))throw Error('El informe oculta la diferencia persistente de Tía Dorita');
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const instituciones=fila(67,3651);
    if(await instituciones.locator('td').nth(4).innerText()!=='20'||!(await instituciones.locator('td').nth(5).innerText()).startsWith('281')||await instituciones.locator('td').nth(6).innerText()!=='291')throw Error('Se redujo la salida 20 para cuadrar el saldo');
    const csip=fila(66,3617);
    if(await csip.locator('td').nth(3).innerText()!=='11'||await csip.locator('td').nth(5).innerText()!=='231')throw Error('No se recuperó el ingreso 11 de CSIP');
    const taiwan=fila(66,3587);
    if(await taiwan.locator('td').nth(4).innerText()!=='1')throw Error('La salida de Taiwan no coincide con la foto');
    if(!(await fila(67,3759).innerText()).includes('Fecha técnica / estimada'))throw Error('FIL sin fecha se presenta como fechado en el papel');
   }
   if(n===24){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const base=fila(120,7289);
    if(!(await base.innerText()).includes('Base documental · sin ingreso añadido')||await base.locator('td').nth(3).innerText()!=='—')throw Error('La base 23 parece un nuevo ingreso');
    const recuento=fila(120,7294);await recuento.locator('summary').click();
    if(!(await recuento.innerText()).includes('revision_previa_cotejo_completo')||!(await recuento.innerText()).includes('-18'))throw Error('Se perdió la decisión previa del recuento');
    if(!(await fila(120,7296).innerText()).includes('Fecha técnica / estimada')||await fila(120,7296).locator('td').nth(6).innerText()!=='—')throw Error('El saldo o fecha ausentes del anclaje parecen escritos');
    if(await fila(120,7333).locator('td').nth(3).innerText()!=='0')throw Error('Se perdió el cero escrito');
    if(await fila(72,4025).locator('td').nth(3).innerText()!=='2')throw Error('Se alteró el ingreso ya cotejado');
   }
   if(n===25){
    const ultima=page.locator('#articulo-49 tbody tr').filter({hasText:'#1980'});await ultima.locator('summary').click();
    if(await ultima.locator('td').nth(3).innerText()!=='4'||await ultima.locator('td').nth(4).innerText()!=='—'||!(await ultima.innerText()).includes('columna_documental_cantidad'))throw Error('No distingue columna escrita e interpretación de la devolución');
    const base=page.locator('#articulo-49 tbody tr').filter({hasText:'#1888'});
    if(await base.locator('td').nth(3).innerText()!=='—'||await base.locator('td').nth(4).innerText()!=='5')throw Error('Se inventó un ingreso de apertura');
   }
   if(n===26){
    if(!texto.includes('Acumulado condicional: -1')||!texto.includes('apertura bloqueada'))throw Error('Se oculta la insuficiencia de Las estaciones');
    if(await page.locator('main > .tabla tbody tr').first().locator('td').last().innerText()!=='—')throw Error('El saldo documental ausente no aparece como ausencia');
    const nota=page.locator('#articulo-80 tbody tr').filter({hasText:'#4710'});await nota.locator('summary').click();
    if(await nota.locator('td').nth(4).innerText()!=='2'||await nota.locator('td').nth(6).innerText()!=='—'||!(await nota.innerText()).includes('FALTA SALIDA'))throw Error('No se distingue la nota adherida del saldo en blanco');
    const anulada=page.locator('#articulo-169 tbody tr').filter({hasText:'#8262'});await anulada.locator('summary').click();
    if(await anulada.locator('td').nth(4).innerText()!=='4'||!(await anulada.innerText()).includes('ANULADO_DOCUMENTO'))throw Error('Se perdió la fila tachada o se ocultó su cantidad original');
    const recuperada=page.locator('#articulo-169 tbody tr').filter({hasText:'fila completamente tachada'});
    if(await recuperada.count()!==1||!(await recuperada.innerText()).includes('Fila recuperada desde la foto'))throw Error('La recuperación tachada no aparece una sola vez');
    const final=page.locator('#articulo-169 tbody tr').filter({hasText:'#8293'});await final.locator('summary').click();
    if(await final.locator('td').nth(4).innerText()!=='2'||!(await final.innerText()).includes('columna_documental_cantidad'))throw Error('No conserva la interpretación de columna de FIL-2016');
   }
   if(n===27){
    if(!texto.includes('Acumulado condicional: 20')||!texto.includes('pendiente, sin apertura automática'))throw Error('Se oculta la diferencia persistente de Compositores');
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const base=fila(50,1981);
    if(await base.locator('td').nth(3).innerText()!=='—'||!(await base.innerText()).includes('Base documental · sin ingreso añadido'))throw Error('Se inventó un ingreso 85');
    const ingreso=fila(50,1984);await ingreso.locator('summary').click();
    if(await ingreso.locator('td').nth(3).innerText()!=='5'||!(await ingreso.innerText()).includes('columna_documental_cantidad'))throw Error('No se conserva el 5 escrito en ÁREA');
    const parcial=fila(50,1990);
    if(await parcial.locator('td').nth(6).innerText()!=='—'||!(await parcial.innerText()).includes('Saldo hipotético'))throw Error('Se certifica una lectura dudosa de saldo');
    if(await fila(56,2466).locator('td').nth(4).innerText()!=='10'||await fila(60,2720).locator('td').nth(4).innerText()!=='1')throw Error('No se recuperaron las salidas mal leídas');
    if(!(await fila(56,2551).innerText()).includes('Fecha técnica / estimada'))throw Error('Se confirma FIL sin fecha propia');
    const recuperadas=page.locator('#articulo-60 tbody tr').filter({hasText:'de ingreso/donación completamente tachado'});
    if(await recuperadas.count()!==2)throw Error('Las dos filas tachadas no aparecen una sola vez');
    for(const f of await recuperadas.all())if(!(await f.innerText()).includes('Anulado en el documento')||!(await f.innerText()).includes('Fila recuperada desde la foto'))throw Error('La recuperación tachada parece operativa');
   }
   if(n===28){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const limite=page.locator('main > .tabla tbody tr').filter({hasText:'TALLER'});
    if(!(await limite.innerText()).includes('Límite documental')||!(await limite.innerText()).includes('ingreso hipotético 6')||(await limite.innerText()).includes('no operable'))throw Error('El cierre condicionado de Taller no se explica correctamente');
    const base=fila(185,8458);
    if(await base.locator('td').nth(3).innerText()!=='—'||!(await base.innerText()).includes('Base documental · sin ingreso añadido'))throw Error('Se inventó un ingreso inicial 10');
    const dudosa=fila(185,8469);
    if(await dudosa.locator('td').nth(3).innerText()!=='6'||await dudosa.locator('td').nth(6).innerText()!=='—'||!(await dudosa.innerText()).includes('Cantidad hipotética'))throw Error('Se certifica la devolución repasada');
    const recuento=page.locator('#articulo-185 tbody tr').filter({hasText:'SEGUN RECUENTO FISICO'});await recuento.locator('summary').click();
    if(await recuento.count()!==1||!(await recuento.innerText()).includes('diferencia_con_cadena_previa')||!(await recuento.innerText()).includes('-4')||await recuento.locator('td').nth(3).innerText()!=='—'||await recuento.locator('td').nth(4).innerText()!=='—'||await recuento.locator('td').nth(6).innerText()!=='3')throw Error('El recuento recuperado perdió su diferencia o parece una operación añadida');
    for(const id of [2843,2846])if(await fila(62,id).locator('td').nth(3).innerText()!=='4')throw Error('No se recupera ingreso 4 desplazado');
    if(await fila(98,6755).locator('td').nth(4).innerText()!=='100')throw Error('Se alteró la salida 100 para reducirla');
    if(await page.locator('#articulo-62 tbody tr').filter({hasText:'renglón completamente tachado'}).count()!==1)throw Error('Falta la recuperación anulada de Iporre');
    for(const id of [2863,2864])if(!(await fila(62,id).innerText()).includes('Fecha técnica / estimada'))throw Error('Se atribuyó fecha documental a FIL');
   }
   if(n===29){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    if(!(await page.locator('#articulo-27 tbody tr').first().innerText()).includes('#1125'))throw Error('No se respeta el orden documental 3-2-1');
    if(await fila(27,1124).locator('td').nth(5).innerText()!=='90'||await fila(27,1124).locator('td').nth(6).innerText()!=='98')throw Error('Se borró la discrepancia intermedia de Betshabé');
    for(const [id,valor] of [[3884,1],[3888,90]])if(await fila(69,id).locator('td').nth(3).innerText()!==String(valor))throw Error('Ingreso desplazado no recuperado '+id);
    if(await fila(69,3885).locator('td').nth(4).innerText()!=='130')throw Error('Se redujo la entrega a autoras');
    if(await fila(290,10169).locator('td').nth(3).innerText()!=='6'||await fila(290,10169).locator('td').nth(6).innerText()!=='22')throw Error('Se cambió el ingreso 6 para cuadrar el papel');
    if(await fila(290,10180).locator('td').nth(4).innerText()!=='5')throw Error('Se convirtió automáticamente una devolución en ingreso');
    if(!texto.includes('Acumulado condicional: 10')||!texto.includes('Cierre escrito 9 frente a cálculo 10'))throw Error('Se oculta el cierre pendiente de Ecológica 33');
    const anulada=page.locator('#articulo-290 tbody tr').filter({hasText:'renglón completamente tachado'});
    if(await anulada.count()!==1||!(await anulada.innerText()).includes('Anulado en el documento')||!(await anulada.innerText()).includes('Fila recuperada desde la foto'))throw Error('La recuperación anulada falta o parece operativa');
   }
   if(n===30){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const cantidad=fila(68,3850);
    if(await cantidad.locator('td').nth(4).innerText()!=='364'||!(await cantidad.locator('td').nth(5).innerText()).startsWith('279')||await cantidad.locator('td').nth(6).innerText()!=='273')throw Error('Se cambió la salida 364 o se ocultó el saldo erróneo de Pienso');
    if(!texto.includes('Acumulado condicional: 234')||!texto.includes('Cierre escrito 228 frente a cálculo 234'))throw Error('Se oculta el cierre pendiente de Pienso');
    const recuento=fila(147,7930);await recuento.locator('summary').click();
    if(await recuento.locator('td').nth(3).innerText()!=='—'||await recuento.locator('td').nth(4).innerText()!=='—'||await recuento.locator('td').nth(5).innerText()!=='260'||!(await recuento.innerText()).includes('diferencia_con_cadena_previa')||!(await recuento.innerText()).includes('-1'))throw Error('El recuento 260 perdió la diferencia -1 o parece salida añadida');
    if(!(await fila(68,3831).innerText()).includes('Fecha técnica / estimada')||!(await fila(147,7910).innerText()).includes('Fecha técnica / estimada'))throw Error('Se certifican fechas incompletas o con año erróneo');
    if(await fila(147,7981).locator('td').nth(3).innerText()!=='3'||await fila(147,7978).locator('td').nth(3).innerText()!=='—')throw Error('Se perdió el ingreso 3 o el tachón se volvió ingreso');
   }
   if(n===31){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const galeria=fila(48,1847);
    if(await galeria.locator('td').nth(3).innerText()!=='1'||await galeria.locator('td').nth(4).innerText()!=='—'||await galeria.locator('td').nth(6).innerText()!=='528')throw Error('La devolución y venta de Teatro siguen unidas');
    const venta=page.locator('#articulo-48 tbody tr').filter({hasText:'VENTA (detalle documental en blanco)'});
    if(await venta.count()!==1||await venta.locator('td').nth(4).innerText()!=='1'||await venta.locator('td').nth(6).innerText()!=='527'||!(await venta.innerText()).includes('Fila recuperada desde la foto')||!(await venta.innerText()).includes('Fecha técnica / estimada'))throw Error('La salida fotografiada no se recuperó correctamente');
    for(const id of [2088,2089])if(await fila(51,id).locator('td').nth(4).innerText()!=='10'||await fila(51,id).locator('td').nth(3).innerText()!=='—')throw Error('Las salidas 10 siguen como ingresos');
    if(await fila(51,2160).locator('td').nth(3).innerText()!=='5')throw Error('No se recuperó ingreso 5 desplazado');
    for(const [id,valor] of [[2238,6],[2239,25]])if(await fila(52,id).locator('td').nth(3).innerText()!==String(valor))throw Error('Se deduplicaron devoluciones distintas');
    if(!(await fila(52,2265).innerText()).includes('Fecha técnica / estimada')||await fila(52,2265).locator('td').nth(4).innerText()!=='2')throw Error('Una fecha tachada anuló la operación o se certifica');
    if(!(await fila(52,2274).innerText()).includes('2021-10-01'))throw Error('Fecha 1-10-21 incorrecta');
   }
   if(n===32){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const base=fila(25,970);
    if(await base.locator('td').nth(3).innerText()!=='—'||!(await base.innerText()).includes('Base documental · sin ingreso añadido'))throw Error('Se inventó ingreso 232');
    if(await fila(25,979).locator('td').nth(6).innerText()!=='—'||await fila(25,980).locator('td').nth(6).innerText()!=='—')throw Error('Los saldos vacíos parecen cifras escritas');
    if(await fila(176,8325).locator('td').nth(3).innerText()!=='10'||await fila(176,8331).locator('td').nth(4).innerText()!=='—')throw Error('El ingreso 10 o la marca tachada siguen incorrectos');
    if(await fila(176,8317).locator('td').nth(6).innerText()!=='0')throw Error('Se perdió el cero escrito');
    if(!(await fila(176,8330).innerText()).includes('Fecha técnica / estimada')||!(await fila(193,8785).innerText()).includes('Fecha técnica / estimada'))throw Error('FIL 17 aparece con fecha confirmada');
    if(!(await fila(193,8786).innerText()).includes('2019-07-05'))throw Error('Fecha 5-7-19 incorrecta');
   }
   if(n===33){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const recuento=fila(128,7384);await recuento.locator('summary').click();
    if(await recuento.locator('td').nth(3).innerText()!=='—'||await recuento.locator('td').nth(4).innerText()!=='—'||await recuento.locator('td').nth(6).innerText()!=='28'||!(await recuento.innerText()).includes('diferencia_con_cadena_previa')||!(await recuento.innerText()).includes('-3'))throw Error('El recuento 28 no conserva su diferencia -3');
    const imposible=fila(128,7390);await imposible.locator('summary').click();
    if(!(await imposible.innerText()).includes('29-02-02')||!(await imposible.innerText()).includes('Fecha técnica / estimada')||!(await imposible.innerText()).includes('fecha_documental_imposible'))throw Error('La fecha imposible se certifica como válida');
    if(!(await fila(318,10835).innerText()).includes('Anulado en el documento'))throw Error('La fila completamente tachada sigue operativa');
    if(await fila(318,10831).locator('td').nth(4).innerText()!=='5'||await fila(368,11589).locator('td').nth(3).innerText()!=='5')throw Error('Lecturas finales 5 incorrectas');
    if(await fila(368,11596).locator('td').nth(4).innerText()!=='21')throw Error('Se invirtió la devolución con salida 21');
   }
   if(n===34){
    const fila=id=>page.locator('#articulo-25 tbody tr').filter({hasText:'#'+id});
    const primera=fila(971);await primera.locator('summary').click();
    if(await primera.locator('td').nth(3).innerText()!=='2'||await primera.locator('td').nth(5).innerText()!=='234'||await primera.locator('td').nth(6).innerText()!=='224'||!(await primera.innerText()).includes('revision_previa_rectificacion_documental'))throw Error('La rectificación perdió la lectura escrita o su antecedente');
    const siguiente=fila(972);await siguiente.locator('summary').click();
    if(await siguiente.locator('td').nth(3).innerText()!=='5'||await siguiente.locator('td').nth(6).innerText()!=='239'||!(await siguiente.innerText()).includes('diferencia_local_papel'))throw Error('No se conserva la compensación documental +10');
   }
   if(n===35){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    if(await fila(132,7451).locator('td').nth(6).innerText()!=='0'||await fila(132,7452).locator('td').nth(6).innerText()!=='-1'||await fila(132,7453).locator('td').nth(6).innerText()!=='1')throw Error('Se borró el cero o el negativo histórico de Chapaca');
    const vacia=fila(132,7455);await vacia.locator('summary').click();
    if(await vacia.locator('td').nth(3).innerText()!=='—'||await vacia.locator('td').nth(4).innerText()!=='—'||await vacia.locator('td').nth(6).innerText()!=='—'||!(await vacia.innerText()).includes('efecto_cuantitativo_no_acreditado'))throw Error('Se inventó cantidad para la devolución incompleta');
    const parcial=fila(198,8860);await parcial.locator('summary').click();
    if(await parcial.locator('td').nth(4).innerText()!=='6'||await parcial.locator('td').nth(6).innerText()!=='—'||!(await parcial.innerText()).includes('Cantidad hipotética')||!(await parcial.innerText()).includes('candidatos_cantidad_documental'))throw Error('Se certifica la cifra repasada del Festival');
    for(const [id,valor] of [[8882,4],[8883,3]])if(await fila(198,id).locator('td').nth(4).innerText()!==String(valor)||await fila(198,id).locator('td').nth(3).innerText()!=='—')throw Error('Las salidas del Festival siguen invertidas');
    const cierres=await page.locator('main > .tabla').innerText();
    if(!cierres.includes('Límite documental')||!cierres.includes('devolución no consigna cantidad')||!cierres.includes('salida hipotética 6')||cierres.includes('no operable'))throw Error('No se explican los límites sin declarar bloqueos inexistentes');
   }
   if(n===36){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const incierta=fila(42,1680);await incierta.locator('summary').click();
    if(!(await incierta.innerText()).includes('Cantidad hipotética')||!(await incierta.innerText()).includes('candidatos_cantidad_documental'))throw Error('El ingreso repasado de Moraima aparece certificado');
    if(await fila(92,6212).locator('td').nth(4).innerText()!=='10'||await fila(92,6212).locator('td').nth(3).innerText()!=='—')throw Error('La salida FIL sigue como ingreso');
    if(await fila(92,6217).locator('td').nth(6).innerText()!=='189'||!(await fila(92,6217).locator('td').nth(5).innerText()).startsWith('188'))throw Error('El error escrito de APAC se ocultó');
    if(!texto.includes('Cierre escrito 142 frente a cálculo 141')||!texto.includes('Pendiente de conciliación · no operable'))throw Error('El cierre discrepante de Quipus parece operable');
   }
   if(n===37){
    const fila=id=>page.locator('#articulo-35 tbody tr').filter({hasText:'#'+id});
    const ancla=fila(1449);await ancla.locator('summary').click();
    if(await ancla.locator('td').nth(6).innerText()!=='25'||!(await ancla.innerText()).includes('revision_previa_cotejo_completo')||!(await ancla.innerText()).includes('CONFIRMACION_USUARIO'))throw Error('Se perdió la confirmación T06 o su antecedente');
    if(!(await fila(1455).innerText()).includes('2012-10-04')||!(await fila(1487).innerText()).includes('2017-10-05'))throw Error('Las fechas cotejadas no se muestran correctamente');
    if(!(await fila(1410).innerText()).includes('Fecha técnica / estimada'))throw Error('La recepción sin fecha parece fechada en el papel');
   }
   if(n===38){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    if(!(await fila(11,592).innerText()).includes('Nota documental')||await fila(11,593).locator('td').nth(3).innerText()!=='59')throw Error('La nota parece un segundo ingreso');
    for(const [id,q] of [[11800,20],[11804,20],[11805,9],[11811,2]])if(await fila(379,id).locator('td').nth(3).innerText()!==String(q))throw Error('Ingreso desplazado no recuperado '+id);
    if(await fila(379,11808).locator('td').nth(4).innerText()!=='25'||await fila(379,11808).locator('td').nth(3).innerText()!=='—')throw Error('La salida 25 sigue invertida');
    const incompleta=fila(142,7805);await incompleta.locator('summary').click();
    if(await incompleta.locator('td').nth(3).innerText()!=='—'||await incompleta.locator('td').nth(4).innerText()!=='—'||!(await incompleta.innerText()).includes('efecto_cuantitativo_no_acreditado'))throw Error('Se inventó una salida para FIL-2019');
    if(await fila(142,7804).locator('td').nth(6).innerText()!=='—'||await fila(142,7809).locator('td').nth(6).innerText()!=='0')throw Error('Se confundió guion con cero documental');
    if(!texto.includes('Cierre escrito 0 frente a cálculo condicional 1')||!texto.includes('Pendiente de conciliación · no operable'))throw Error('El cierre de Música no conserva su límite');
   }
   if(n===39){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    if(await fila(243,9623).locator('td').nth(3).innerText()!=='5'||await fila(243,9623).locator('td').nth(4).innerText()!=='—')throw Error('El tachón de ingreso 5 sigue como salida adicional');
    if(await fila(397,12140).locator('td').nth(3).innerText()!=='—'||await fila(397,12140).locator('td').nth(4).innerText()!=='10')throw Error('La anotación (10) se cuenta como segundo movimiento');
    const anulada=page.locator('#articulo-397 tbody tr').filter({hasText:'Renglón final completamente tachado'});
    if(await anulada.count()!==1||!(await anulada.innerText()).includes('Fila recuperada desde la foto')||!(await anulada.innerText()).includes('Anulado en el documento'))throw Error('No se conserva la fila tachada omitida');
    if(await fila(397,12154).locator('td').nth(6).innerText()!=='26'||await fila(397,12155).locator('td').nth(6).innerText()!=='22')throw Error('Se borró la discrepancia compensada del papel');
   }
   if(n===40){
    const fila=id=>page.locator('#articulo-245 tbody tr').filter({hasText:'#'+id});
    const ancla=fila(9657);await ancla.locator('summary').click();
    if(await ancla.locator('td').nth(3).innerText()!=='40'||await ancla.locator('td').nth(6).innerText()!=='41'||!(await ancla.innerText()).includes('revision_previa_cotejo_completo'))throw Error('El anclaje de Murciélagos se perdió');
    const cubierta=fila(9677);await cubierta.locator('summary').click();
    if(await cubierta.locator('td').nth(6).innerText()!=='—'||!(await cubierta.locator('td').nth(5).innerText()).startsWith('26')||!(await cubierta.innerText()).includes('saldo_documental_cubierto')||!(await cubierta.innerText()).includes('Saldo hipotético'))throw Error('Se simula lectura debajo de la nota adherida');
    if(await fila(9690).locator('td').nth(6).innerText()!=='0'||!(await fila(9691).innerText()).includes('Fecha técnica / estimada'))throw Error('Se borró el cero o se certifica el año fuera de orden');
   }
   if(n===41){
    const fila=id=>page.locator('#articulo-11 tbody tr').filter({hasText:'#'+id});
    const incierta=fila(608);await incierta.locator('summary').click();
    if(await incierta.locator('td').nth(3).innerText()!=='3'||!(await incierta.innerText()).includes('Cantidad hipotética')||!(await incierta.innerText()).includes('revision_previa_rectificacion_documental')||!(await incierta.innerText()).includes('candidatos_cantidad_documental'))throw Error('La ampliación certificó la cantidad o perdió su revisión previa');
    if(!(await fila(592).innerText()).includes('Nota documental')||await fila(593).locator('td').nth(3).innerText()!=='59')throw Error('La ampliación cambió la nota o el ingreso 59');
    const cierre=await page.locator('main > .tabla').innerText();
    if(!cierre.includes('Límite documental')||!cierre.includes('ingreso hipotético 3')||cierre.includes('no operable'))throw Error('El cierre condicional se oculta o se declara bloqueado sin evidencia');
   }
   if(n===42){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    if(await fila(65,3473).locator('td').nth(3).innerText()!=='4'||await fila(65,3471).locator('td').nth(4).innerText()!=='364')throw Error('Se perdió el ingreso 4 o la salida grande legible');
    const base=fila(89,5936);
    if(await base.locator('td').nth(3).innerText()!=='—'||!(await base.innerText()).includes('Base documental · sin ingreso añadido'))throw Error('Se inventó ingreso 223');
    const doble=fila(233,9462);await doble.locator('summary').click();
    if(await doble.locator('td').nth(3).innerText()!=='1'||await doble.locator('td').nth(4).innerText()!=='1'||!(await doble.innerText()).includes('Cantidad hipotética')||!(await doble.innerText()).includes('efecto_cuantitativo_no_acreditado'))throw Error('Se eliminó una cifra para cuadrar');
    const imposible=fila(233,9502);await imposible.locator('summary').click();
    if(!(await imposible.innerText()).includes('15-15-24')||!(await imposible.innerText()).includes('Fecha técnica / estimada'))throw Error('La fecha imposible parece confirmada');
    if(!texto.includes('Cierre escrito 3 frente a cálculo condicional 4')||!texto.includes('Pendiente de conciliación · no operable'))throw Error('El cierre de Algas oculta la diferencia');
   }
   if(n===43){
    const fila=id=>page.locator('#articulo-186 tbody tr').filter({hasText:'#'+id});
    const recuento=fila(8534);await recuento.locator('summary').click();
    if(await recuento.locator('td').nth(3).innerText()!=='—'||await recuento.locator('td').nth(4).innerText()!=='—'||await recuento.locator('td').nth(6).innerText()!=='3'||!(await recuento.innerText()).includes('diferencia_con_cadena_previa')||!(await recuento.innerText()).includes('-4'))throw Error('El recuento 3 se convirtió en operación compensatoria');
    if(await fila(8533).locator('td').nth(4).innerText()!=='1'||await fila(8533).locator('td').nth(6).innerText()!=='4'||await fila(8533).locator('td').nth(5).innerText()!=='7')throw Error('Se corrigió el papel cambiando la salida 1');
   }
   if(n===44){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const error=fila(8,412);
    if(await error.locator('td').nth(4).innerText()!=='2'||await error.locator('td').nth(6).innerText()!=='488'||!(await error.locator('td').nth(5).innerText()).startsWith('498'))throw Error('Se cambió la salida 2 para cuadrar');
    if(await fila(8,408).locator('td').nth(3).innerText()!=='—'||!(await fila(8,408).innerText()).includes('Base documental · sin ingreso añadido'))throw Error('Se inventó ingreso 525');
    const anulada=page.locator('#articulo-8 tbody tr').filter({hasText:'Renglón completamente tachado antes de FIL 2021'});
    if(await anulada.count()!==1||!(await anulada.innerText()).includes('Anulado en el documento')||!(await anulada.innerText()).includes('Fila recuperada desde la foto'))throw Error('La cancelación recuperada falta o se duplicó');
    if(await fila(3,105).locator('td').nth(4).innerText()!=='1'||!texto.includes('Cierre escrito 332 frente a cálculo 342'))throw Error('Se contó la anotación (3) o se ocultó el cierre discrepante');
   }
   if(n===45){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    for(const [id,q] of [[7530,10],[7543,15]])if(await fila(134,id).locator('td').nth(4).innerText()!==String(q)||await fila(134,id).locator('td').nth(3).innerText()!=='—')throw Error('Las salidas Guaraní siguen invertidas');
    const nota=page.locator('#articulo-177 tbody tr').filter({hasText:'Cifra 6 sin leyenda, fecha ni cantidades'});
    if(await nota.count()!==1||!(await nota.innerText()).includes('Nota documental')||await nota.locator('td').nth(3).innerText()!=='—'||await nota.locator('td').nth(4).innerText()!=='—'||await nota.locator('td').nth(6).innerText()!=='6')throw Error('La cifra aislada se convirtió en ajuste o fue borrada');
    for(const id of [9788,9789,9790,9791]){
     const resumen=fila(256,id);await resumen.locator('summary').click();
     if(!(await resumen.innerText()).includes('Nota documental')||!(await resumen.innerText()).includes('interpretacion_cuadro_pendiente')||await resumen.locator('td').nth(3).innerText()!=='—'||await resumen.locator('td').nth(4).innerText()!=='—')throw Error('Se inventaron ingresos para otro cuadro');
    }
    if(!texto.includes('Cierre escrito 11 frente a cálculo 26')||!texto.includes('Interpretación pendiente'))throw Error('No se explican los límites de Festival y Ecología 5');
   }
   if(n===46){
    const fila=id=>page.locator('#articulo-186 tbody tr').filter({hasText:'#'+id});
    if(!(await fila(8530).innerText()).includes('Cedoal Oruro')||!(await fila(8536).innerText()).includes('Edgar Arandia'))throw Error('Las lecturas de texto ampliadas no aparecen');
    const recuento=fila(8534);await recuento.locator('summary').click();
    if(await recuento.locator('td').nth(6).innerText()!=='3'||await recuento.locator('td').nth(3).innerText()!=='—'||await recuento.locator('td').nth(4).innerText()!=='—'||!(await recuento.innerText()).includes('revision_previa_cotejo_completo')||!(await recuento.innerText()).includes('diferencia_con_cadena_previa'))throw Error('La ampliación perdió el recuento o su revisión anterior');
   }
   if(n===47){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const nueva=page.locator('#articulo-385 tbody tr').filter({hasText:'Ingreso 5 sin fecha ni detalle documental'});
    if(await nueva.count()!==1||await nueva.locator('td').nth(3).innerText()!=='5'||await nueva.locator('td').nth(6).innerText()!=='5'||!(await nueva.innerText()).includes('Fila recuperada desde la foto')||!(await nueva.innerText()).includes('Fecha técnica / estimada'))throw Error('La recepción omitida falta, se duplicó o tiene fecha certificada');
    if(await fila(385,11907).locator('td').nth(6).innerText()!=='—'||!(await fila(385,11907).locator('td').nth(5).innerText()).startsWith('9')||await fila(388,11972).locator('td').nth(6).innerText()!=='—')throw Error('Se llenaron saldos vacíos del papel');
    const guiones=fila(385,11923);await guiones.locator('summary').click();
    if(await guiones.locator('td').nth(3).innerText()!=='—'||await guiones.locator('td').nth(4).innerText()!=='—'||!(await guiones.innerText()).includes('efecto_cuantitativo_no_acreditado'))throw Error('Se inventó una devolución para los guiones');
    const base=fila(388,11970);
    if(await base.locator('td').nth(3).innerText()!=='—'||!(await base.innerText()).includes('Base documental · sin ingreso añadido'))throw Error('Se inventó un ingreso para la base 5');
    if(await fila(385,11934).locator('td').nth(4).innerText()!=='24'||await fila(388,12006).locator('td').nth(4).innerText()!=='26')throw Error('Se invirtieron las devoluciones legibles');
    if(!texto.includes('Cierre escrito 15 coincide condicionalmente')||(await page.locator('main > .tabla').innerText()).includes('no operable'))throw Error('El cierre condicional no muestra su límite o se presenta bloqueado sin evidencia');
   }
   if(n===49){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const base=page.locator('#articulo-30 tbody tr').filter({hasText:'Saldo inicial 11 sin fecha ni detalle documental'});
    if(await base.count()!==1||await base.locator('td').nth(3).innerText()!=='—'||await base.locator('td').nth(6).innerText()!=='11'||!(await base.innerText()).includes('Fila recuperada desde la foto'))throw Error('La base 11 omitida se perdió o parece ingreso');
    if(await fila(30,1269).locator('td').nth(6).innerText()!=='—'||await fila(30,1291).locator('td').nth(4).innerText()!=='1'||await fila(30,1291).locator('td').nth(6).innerText()!=='19')throw Error('Se llenó un saldo vacío o se corrigió el papel inventando operaciones');
    const nota=fila(137,7618);
    if(!(await nota.innerText()).includes('Nota documental')||await nota.locator('td').nth(6).innerText()!=='15'||await nota.locator('td').nth(3).innerText()!=='—')throw Error('La cifra 15 se convirtió en recuento o ingreso');
    if(await fila(137,7619).locator('td').nth(3).innerText()!=='22'||await fila(137,7662).locator('td').nth(4).innerText()!=='6'||await fila(137,7662).locator('td').nth(3).innerText()!=='—')throw Error('Se cambiaron las cifras para conciliar entre hojas');
    const referencia=fila(93,6294);await referencia.locator('summary').click();
    const datoReferencia=datos.articulos.find(a=>a.id===93).filas.find(f=>f.actual.id===6294).actual;
    if(!(await referencia.innerText()).includes('referencia_documental_ambigua')||!(await referencia.innerText()).includes('CBA/CDA')||datoReferencia.referencia_estado!=='INCIERTA'||!datoReferencia.requiere_auditoria_referencia)throw Error('Se certificó la referencia ambigua por semejanza');
    if(!texto.includes('Cierre escrito 12 frente a cálculo 11')||!texto.includes('Cierre escrito 0 frente a cálculo condicional 2'))throw Error('No se muestran los cierres discrepantes');
   }
   if(n===50){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    if(await fila(15,815).locator('td').nth(4).innerText()!=='5'||await fila(15,814).locator('td').nth(6).innerText()!=='—'||!(await fila(15,814).locator('td').nth(5).innerText()).startsWith('16'))throw Error('Se perdió la salida 5 o se certificó el saldo repasado');
    const incierto=fila(15,814);await incierto.locator('summary').click();
    if(!(await incierto.innerText()).includes('candidatos_saldo_documental'))throw Error('Falta la incertidumbre 12/16');
    if(await fila(115,7162).locator('td').nth(3).innerText()!=='—'||!(await fila(115,7162).innerText()).includes('Base documental · sin ingreso añadido'))throw Error('Se inventó ingreso 26');
    if(!(await fila(115,7222).innerText()).includes('Fecha técnica / estimada'))throw Error('FIL 17 parece tener fecha escrita');
    if(await fila(395,12240).locator('td').nth(3).innerText()!=='0')throw Error('El cero escrito se confundió con vacío');
    const ancla=fila(395,12272);await ancla.locator('summary').click();
    if(await ancla.locator('td').nth(3).innerText()!=='5'||await ancla.locator('td').nth(6).innerText()!=='6'||!(await ancla.innerText()).includes('revision_previa_cotejo_completo')||!(await ancla.innerText()).includes('Fecha técnica / estimada'))throw Error('El anclaje anterior se perdió o se certificó su fecha');
    const adhesivo=fila(395,12274);await adhesivo.locator('summary').click();
    if(await adhesivo.locator('td').nth(4).innerText()!=='2'||!(await adhesivo.innerText()).includes('Adhesivo'))throw Error('Se perdió la corrección visible sobre adhesivo');
   }
   if(n===51){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const columna=fila(7,403);await columna.locator('summary').click();
    if(await columna.locator('td').nth(3).innerText()!=='1'||await columna.locator('td').nth(4).innerText()!=='—'||!(await columna.innerText()).includes('columna_reinterpretada'))throw Error('No se conserva la interpretación y columna original de INGRESO 1');
    const dudosa=fila(7,372);await dudosa.locator('summary').click();
    if(!(await dudosa.innerText()).includes('Cantidad hipotética')||!(await dudosa.innerText()).includes('candidatos_salidas_documentales')||await fila(7,405).locator('td').nth(6).innerText()!=='—')throw Error('Se certificó la marca ennegrecida o el guion como cero');
    const nota=page.locator('#articulo-184 tbody tr').filter({hasText:'Cifra 2 en INGRESOS sin fecha, detalle ni saldo'});
    if(await nota.count()!==1||!(await nota.innerText()).includes('Nota documental')||!(await nota.innerText()).includes('Fila recuperada desde la foto')||await nota.locator('td').nth(3).innerText()!=='—')throw Error('La cifra aislada se inventó como recepción confirmada');
    if(await fila(184,8457).locator('td').nth(3).innerText()!=='—'||await fila(184,8457).locator('td').nth(4).innerText()!=='1')throw Error('La nota sigue unida a FIL-2015');
    if(await fila(247,9716).locator('td').nth(6).innerText()!=='—'||await fila(247,9723).locator('td').nth(4).innerText()!=='1'||await fila(247,9723).locator('td').nth(6).innerText()!=='4')throw Error('Se rellenó el saldo vacío o se cambió la salida 1 para cuadrar');
    const ingreso=page.locator('#articulo-386 tbody tr').filter({hasText:'Ingreso 5 sin fecha ni detalle documental'});
    if(await ingreso.count()!==1||await ingreso.locator('td').nth(3).innerText()!=='5'||!(await ingreso.innerText()).includes('Fecha técnica / estimada')||await fila(386,11942).locator('td').nth(6).innerText()!=='—')throw Error('La recepción omitida falta, se duplicó o se certificó su fecha');
    if(!texto.includes('Cierre escrito 0 frente a cálculo condicional -1')||!texto.includes('Cierre escrito 26 coincide condicionalmente'))throw Error('Se ocultaron los límites documentales');
   }
   if(n===52){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const base=fila(9,510);await base.locator('summary').click();
    if(await base.locator('td').nth(3).innerText()!=='—'||await base.locator('td').nth(6).innerText()!=='5'||!(await base.innerText()).includes('recuento_documental_inicial'))throw Error('La base inicial se convirtió en recepción o perdió el recuento escrito');
    for(const [aid,id] of [[9,513],[9,515],[118,7248],[394,12117]])if(await fila(aid,id).locator('td').nth(6).innerText()!=='—')throw Error('Se certificó un guion o saldo vacío como cifra escrita');
    if(await fila(9,531).locator('td').nth(3).innerText()!=='1'||await fila(374,11703).locator('td').nth(4).innerText()!=='34'||await fila(374,11703).locator('td').nth(3).innerText()!=='—'||await fila(394,12117).locator('td').nth(4).innerText()!=='2')throw Error('Las correcciones de cantidad o columna no aparecen');
    if(!(await fila(9,512).innerText()).includes('Fecha técnica / estimada')||!(await fila(154,8052).innerText()).includes('Fecha técnica / estimada')||await fila(394,12104).locator('td').nth(6).innerText()!=='0')throw Error('Se certificó una fecha reconstruida o se perdió el cero numérico');
   }
   if(n===53){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const cubierta=fila(70,3934);await cubierta.locator('summary').click();
    if(await cubierta.locator('td').nth(3).innerText()!=='732'||await cubierta.locator('td').nth(6).innerText()!=='—'||!(await cubierta.innerText()).includes('saldo_documental_cubierto'))throw Error('Se afirma leer debajo del adhesivo o se alteró ingreso 732');
    const incierta=fila(70,3948);await incierta.locator('summary').click();
    if(!(await incierta.innerText()).includes('Cantidad hipotética')||!(await incierta.innerText()).includes('candidatos_salidas_documentales'))throw Error('La cantidad repasada parece confirmada');
    if(await fila(70,3958).locator('td').nth(4).innerText()!=='40'||await fila(70,3966).locator('td').nth(6).innerText()!=='597'||!texto.includes('Cierre escrito 597 frente a cálculo condicional 606'))throw Error('La salida 40 o la diferencia persistente se perdieron');
    if(await fila(384,11872).locator('td').nth(3).innerText()!=='1'||await fila(384,11872).locator('td').nth(6).innerText()!=='1'||await fila(384,11874).locator('td').nth(6).innerText()!=='—'||!texto.includes('Cierre escrito 11 frente a cálculo 12'))throw Error('Se corrigió la diferencia del papel inventando operaciones');
    if(!(await fila(54,2440).innerText()).includes('Fecha técnica / estimada')||!(await fila(310,10602).innerText()).includes('Fecha técnica / estimada'))throw Error('Las fechas fuera de orden parecen certificadas');
   }
   if(n===54){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    if(await fila(13,681).locator('td').nth(4).innerText()!=='8'||await fila(13,681).locator('td').nth(6).innerText()!=='6'||await fila(13,681).locator('td').nth(5).innerText()!=='5'||!texto.includes('Cierre escrito 6 frente a cálculo 5'))throw Error('Se alteró salida 8 para cuadrar el papel');
    if(!(await fila(13,677).innerText()).includes('2011-05-18')||!(await fila(190,8699).innerText()).includes('2013-10-02')||!(await fila(190,8700).innerText()).includes('2013-11-04'))throw Error('Las fechas OCR corregidas no se muestran');
    for(const [aid,id] of [[141,7770],[155,8068],[155,8074],[155,8075],[155,8076],[190,8697]])if(!(await fila(aid,id).innerText()).includes('Fecha técnica / estimada'))throw Error('Una fecha ausente o incierta parece confirmada');
    const anulada=page.locator('#articulo-141 tbody tr').filter({hasText:'Ingreso completamente tachado antes de FIL 2021'});
    if(await anulada.count()!==1||!(await anulada.innerText()).includes('Anulado en el documento')||!(await anulada.innerText()).includes('Fila recuperada desde la foto')||await anulada.locator('td').nth(3).innerText()!=='—')throw Error('El ingreso tachado omitido falta, se duplicó o se contabiliza');
    const atributo=fila(155,8078);await atributo.locator('summary').click();
    if(await atributo.locator('td').nth(3).innerText()!=='6'||!(await atributo.innerText()).includes('atribucion_documental_ambigua'))throw Error('Se perdió el ingreso 6 o se certificó el área ambigua');
   }
   if(n===55){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    if(await fila(240,9557).locator('td').nth(6).innerText()!=='—'||await fila(240,9559).locator('td').nth(6).innerText()!=='0'||await fila(348,11290).locator('td').nth(4).innerText()!=='11')throw Error('Se confundió guion y cero o se cambió la salida 11 por otra hoja');
    if(!(await fila(223,9292).innerText()).includes('2011-08-17')||!(await fila(223,9293).innerText()).includes('2011-08-22'))throw Error('Las fechas recuperadas por foto no aparecen');
    for(const [aid,id] of [[223,9313],[240,9561],[240,9564],[348,11284],[348,11321]])if(!(await fila(aid,id).innerText()).includes('Fecha técnica / estimada'))throw Error('Una fecha reconstruida parece escrita');
    const marca=fila(240,9562);await marca.locator('summary').click();
    if(await marca.locator('td').nth(3).innerText()!=='10'||await marca.locator('td').nth(4).innerText()!=='—'||!(await marca.innerText()).includes('Trazo angular'))throw Error('La marca angular se convirtió en otra operación');
    const referencia=fila(191,8703);await referencia.locator('summary').click();
    if(!(await referencia.innerText()).includes('referencia_documental_ambigua'))throw Error('Se perdió la referencia incierta');
   }
   if(n===56){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const cruces=fila(36,1536);await cruces.locator('summary').click();
    if(await cruces.locator('td').nth(3).innerText()!=='—'||await cruces.locator('td').nth(4).innerText()!=='—'||!(await cruces.innerText()).includes('Cantidad hipotética')||!(await cruces.innerText()).includes('efecto_cuantitativo_no_acreditado'))throw Error('Las cruces X se convirtieron en cantidades confirmadas');
    const anulada=page.locator('#articulo-36 tbody tr').filter({hasText:'Donación completamente tachada antes de Eric Altorfer'});
    if(await anulada.count()!==1||!(await anulada.innerText()).includes('Anulado en el documento')||!(await anulada.innerText()).includes('Fila recuperada desde la foto'))throw Error('La donación tachada omitida se perdió o se duplicó');
    if(await fila(36,1493).locator('td').nth(3).innerText()!=='27'||await fila(373,11678).locator('td').nth(4).innerText()!=='30'||await fila(373,11678).locator('td').nth(3).innerText()!=='—')throw Error('El ingreso inicial o la salida 30 se interpretaron por su nombre');
    if(!(await fila(31,1317).innerText()).includes('2010-09-08')||!(await fila(31,1318).innerText()).includes('2010-09-29')||!(await fila(36,1508).innerText()).includes('2008-11-14')||!(await fila(36,1554).innerText()).includes('2014-07-25'))throw Error('No aparecen las fechas recuperadas del OCR');
    for(const [aid,id] of [[31,1374],[136,7552],[136,7608],[373,11656],[373,11666],[373,11679]])if(!(await fila(aid,id).innerText()).includes('Fecha técnica / estimada'))throw Error('Una fecha parcial, ausente o fuera de orden parece confirmada');
    const base=fila(136,7552);
    if(await base.locator('td').nth(3).innerText()!=='—'||!(await base.innerText()).includes('Base documental · sin ingreso añadido'))throw Error('Se inventó un ingreso para la base 15');
    if(!texto.includes('Cierre escrito 15 coincide condicionalmente'))throw Error('Se ocultó el límite documental de Norma');
   }
   if(n===57){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const ancla=fila(14,733);await ancla.locator('summary').click();
    const actual=datos.articulos.find(a=>a.id===14).filas.find(f=>f.actual.id===733).actual;
    if(await ancla.locator('td').nth(3).innerText()!=='3'||await ancla.locator('td').nth(5).innerText()!=='80'||actual.saldo_calculado!==79||!(await ancla.innerText()).includes('revision_previa_rectificacion_documental'))throw Error('Se perdió la decisión T03 o el cálculo independiente');
    const recuperadas=datos.articulos.find(a=>a.id===14).filas.filter(f=>f.actual.revision_documental?.recuperacion_clave==='art14-upea-separada-despues710-v1');
    if(recuperadas.length!==1)throw Error('La donación UPEA falta o está duplicada');
    const upea=fila(14,recuperadas[0].actual.id);
    if(await upea.locator('td').nth(4).innerText()!=='1'||await upea.locator('td').nth(6).innerText()!=='118'||!(await upea.innerText()).includes('Fila recuperada desde la foto'))throw Error('La donación UPEA sigue fusionada');
    if(await fila(14,710).locator('td').nth(6).innerText()!=='—'||await fila(209,9048).locator('td').nth(4).innerText()!=='2'||await fila(209,9048).locator('td').nth(3).innerText()!=='—')throw Error('Se llenó el saldo de CONAMAQ o se invirtió la salida 2');
    for(const id of [9778,9779,9780,9781,9782])if(!(await fila(255,id).innerText()).includes('Nota documental')||await fila(255,id).locator('td').nth(3).innerText()!=='—')throw Error('Se inventaron ingresos o recuentos para notas');
    if(!texto.includes('Cierre escrito 1 frente a cálculo 0'))throw Error('Se ocultó el cierre discrepante de Poetas');
   }
   if(n===59){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const nota=fila(140,7718);await nota.locator('summary').click();
    if(!(await nota.innerText()).includes('Nota documental')||!(await nota.innerText()).includes('detalle_documental')||await nota.locator('td').nth(6).innerText()!=='—')throw Error('Se inventó la devolución o el saldo de la nota fechada');
    const ancla=fila(140,7712);await ancla.locator('summary').click();
    if(!(await ancla.innerText()).includes('revision_previa_cotejo_completo')||!(await ancla.innerText()).includes('Fecha técnica / estimada'))throw Error('Se perdió un anclaje de Historias impulsivas');
    const anulada=page.locator('#articulo-231 tbody tr').filter({hasText:'Ingreso completamente tachado antes de 10-9-21'});
    if(await anulada.count()!==1||!(await anulada.innerText()).includes('Anulado en el documento')||!(await anulada.innerText()).includes('Fila recuperada desde la foto')||await anulada.locator('td').nth(3).innerText()!=='—')throw Error('Se perdió o contabilizó el ingreso tachado');
    if(await fila(357,11450).locator('td').nth(4).innerText()!=='41'||await fila(357,11450).locator('td').nth(3).innerText()!=='—'||await fila(357,11450).locator('td').nth(6).innerText()!=='15')throw Error('La salida 41 sigue invertida');
    const incierto=fila(231,9433);await incierto.locator('summary').click();
    if(await incierto.locator('td').nth(6).innerText()!=='—'||!(await incierto.innerText()).includes('candidatos_saldo_documental')||!texto.includes('Cierre escrito 3 coincide solo condicionalmente'))throw Error('Se certificó el saldo parcial incierto');
    for(const [aid,id] of [[157,8117],[157,8119],[201,8956]])if(await fila(aid,id).locator('td').nth(6).innerText()!=='—')throw Error('Un guion se convirtió en cero escrito');
   }
   if(n===60){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const dano=fila(138,7670);await dano.locator('summary').click();
    if(await dano.locator('td').nth(6).innerText()!=='11'||!(await dano.innerText()).includes('6 en mal estado')||!(await dano.innerText()).includes('ambito_anotacion_pendiente'))throw Error('Se perdió la anotación de ejemplares dañados');
    const invertida=fila(138,7687);await invertida.locator('summary').click();
    if(await invertida.locator('td').nth(4).innerText()!=='1'||await invertida.locator('td').nth(3).innerText()!=='—'||!(await invertida.innerText()).includes('columnas_documentales')||!(await invertida.innerText()).includes('Fecha técnica / estimada'))throw Error('FIL-24 perdió su interpretación o tiene fecha certificada');
    for(const [aid,id,q] of [[244,9631,15],[383,11850,4]])if(await fila(aid,id).locator('td').nth(3).innerText()!=='—'||await fila(aid,id).locator('td').nth(6).innerText()!==String(q)||!(await fila(aid,id).innerText()).includes('Base documental · sin ingreso añadido'))throw Error('Se inventaron ingresos para bases escritas');
    if(await fila(304,10417).locator('td').nth(6).innerText()!=='—'||!(await fila(304,10417).locator('td').nth(5).innerText()).startsWith('-1')||await fila(304,10419).locator('td').nth(6).innerText()!=='—')throw Error('Se ocultó el saldo negativo condicional o se certificó un guion');
    const nota=fila(383,11864);await nota.locator('summary').click();
    if(!(await nota.innerText()).includes('Nota documental')||!(await nota.innerText()).includes('2008-12-16')||await nota.locator('td').nth(3).innerText()!=='—')throw Error('La nota Saldo se convirtió en transacción o perdió su fecha literal');
    if(await fila(244,9649).locator('td').nth(4).innerText()!=='34'||await fila(244,9649).locator('td').nth(3).innerText()!=='—')throw Error('Se invirtió salida 34 por el nombre');
   }
   if(n===61){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    if(await fila(58,2634).locator('td').nth(4).innerText()!=='4'||await fila(58,2634).locator('td').nth(6).innerText()!=='231'||!texto.includes('Cierre escrito 200 frente a cálculo condicional 198'))throw Error('Se cambió salida 4 para cuadrar o se ocultó el cierre');
    const incierta=fila(58,2636);await incierta.locator('summary').click();
    if(!(await incierta.innerText()).includes('Cantidad hipotética')||!(await incierta.innerText()).includes('candidatos_salidas_documentales'))throw Error('Se certificó la cantidad 10/40');
    const anulada=fila(325,11011);await anulada.locator('summary').click();
    if(!(await anulada.innerText()).includes('Anulado en el documento')||await anulada.locator('td').nth(3).innerText()!=='—'||await anulada.locator('td').nth(6).innerText()!=='—')throw Error('Se sigue sumando el ingreso tachado');
    if(await fila(325,11013).locator('td').nth(3).innerText()!=='2'||await fila(325,11013).locator('td').nth(6).innerText()!=='9')throw Error('Se anuló toda la fila por corrección de una celda');
    if(!(await fila(325,10992).innerText()).includes('2010-07-20')||!(await fila(156,8110).innerText()).includes('Fecha técnica / estimada')||!(await fila(144,7837).innerText()).includes('Fecha técnica / estimada'))throw Error('Falta fecha OCR corregida o se certificó una fecha vacía');
   }
   if(n===62){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const parentesis=fila(101,6996);await parentesis.locator('summary').click();
    if(await parentesis.locator('td').nth(3).innerText()!=='10'||await parentesis.locator('td').nth(4).innerText()!=='—'||!(await parentesis.innerText()).includes('(1)'))throw Error('Se contó el paréntesis como otro egreso');
    const base=fila(102,7016);await base.locator('summary').click();
    const rbase=datos.articulos.find(a=>a.id===102).filas.find(f=>f.actual.id===7016).actual;
    if(await base.locator('td').nth(3).innerText()!=='—'||await base.locator('td').nth(4).innerText()!=='10'||rbase.revision_documental.saldo_base!==211||rbase.revision_documental.origen_saldo_base!=='HIPOTESIS'||!(await base.innerText()).includes('Saldo previo 211 inferido'))throw Error('Se inventó un ingreso para POLIGENESIS');
    const separacion=datos.articulos.find(a=>a.id===102).observacion.motivo;
    if(!separacion.includes('separado de REV DE HISTORIA POLIGENESIS 1')||!separacion.includes('56 filas quedan protegidos')||await page.locator('#articulo-98').count()!==0)throw Error('Se perdió la separación de artículos');
    for(const [aid,id] of [[101,7014],[218,9185]])if(!(await fila(aid,id).innerText()).includes('Fecha técnica / estimada'))throw Error('Una fecha vacía parece certificada');
    if(await fila(218,9184).locator('td').nth(4).innerText()!=='41'||await fila(218,9184).locator('td').nth(3).innerText()!=='—')throw Error('Se invirtió la devolución por el nombre');
   }
   if(n===63){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    for(const id of [8891,8892])if(await fila(199,id).locator('td').nth(3).innerText()!=='20')throw Error('Se eliminó un ingreso por similitud');
    if(await fila(199,8905).locator('td').nth(3).innerText()!=='0'||await fila(100,6943).locator('td').nth(6).innerText()!=='—')throw Error('Se perdió el cero o se simuló leer bajo el adhesivo');
    for(const [id,q,correccion] of [[8925,10,12],[8926,4,6]]){
     const r=fila(199,id);await r.locator('summary').click();
     const actual=datos.articulos.find(a=>a.id===199).filas.find(f=>f.actual.id===id).actual;
     if(await r.locator('td').nth(6).innerText()!==String(q)||actual.revision_documental.saldo_corregido_margen!==correccion)throw Error('Se perdió la cifra principal o su corrección marginal');
    }
    const parentesis=fila(356,11396);await parentesis.locator('summary').click();
    if(await parentesis.locator('td').nth(4).innerText()!=='5'||await parentesis.locator('td').nth(6).innerText()!=='15'||!(await parentesis.innerText()).includes('Cantidad hipotética')||!(await parentesis.innerText()).includes('ambito_parentesis_pendiente'))throw Error('El paréntesis se certificó, eliminó o leyó como negativo');
    const recuperadas=datos.articulos.find(a=>a.id===199).filas.filter(f=>f.actual.revision_documental?.recuperacion_clave==='art199-fila-tachada-despues8932-v1');
    if(recuperadas.length!==1||recuperadas[0].actual.estado!=='ANULADO_DOCUMENTO'||recuperadas[0].actual.numero_pagina!==2)throw Error('La cancelación omitida falta, se duplicó o perdió su página');
    if(!texto.includes('Cierre escrito 1 frente a cálculo condicional 21')||!texto.includes('Cierre escrito 7 frente a cálculo condicional 2'))throw Error('Se ocultaron los cierres condicionales discrepantes');
   }
   if(n===64){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const ancla=fila(221,9240);await ancla.locator('summary').click();
    if(await ancla.locator('td').nth(6).innerText()!=='—'||!(await ancla.innerText()).includes('revision_previa_cotejo_completo')||!(await ancla.locator('td').nth(5).innerText()).includes('Saldo hipotético'))throw Error('Se perdió la hipótesis de un saldo bajo el pliegue');
    for(const [aid,id] of [[221,9231],[228,9384]])if(await fila(aid,id).locator('td').nth(3).innerText()!=='0')throw Error('Un cero numérico se convirtió en blanco');
    if(await fila(228,9413).locator('td').nth(3).innerText()!=='1'||await fila(228,9413).locator('td').nth(4).innerText()!=='—')throw Error('Se invirtió ingreso 1 por el nombre FIL');
    for(const [aid,id] of [[221,9211],[221,9212],[221,9214],[221,9261],[228,9392],[228,9413]])if(!(await fila(aid,id).innerText()).includes('Fecha técnica / estimada'))throw Error('Fecha vacía, repasada o ajustada certificada');
    if(!(await fila(221,9226).innerText()).includes('2010-06-11')||!(await fila(221,9257).innerText()).includes('2015-08-03'))throw Error('Las fechas OCR corregidas no aparecen');
   }
   if(n===66){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    const ancla=fila(10,560);await ancla.locator('summary').click();
    const actual=datos.articulos.find(a=>a.id===10).filas.find(f=>f.actual.id===560).actual;
    if(await ancla.locator('td').nth(3).innerText()!=='1'||await ancla.locator('td').nth(5).innerText()!=='1'||actual.saldo_calculado!==51||!actual.revision_documental.criterios.includes('T20')||!(await ancla.innerText()).includes('revision_previa_rectificacion_documental'))throw Error('Se perdió la agrupación aprobada o se alteró su recepción/saldo');
    const nota=fila(74,4132);await nota.locator('summary').click();
    if(!(await nota.innerText()).includes('Nota documental')||await nota.locator('td').nth(3).innerText()!=='—'||await nota.locator('td').nth(4).innerText()!=='—'||await nota.locator('td').nth(6).innerText()!=='—'||!(await nota.innerText()).includes('NO a ambos lados'))throw Error('Las cruces se convirtieron en cantidades o saldo escrito');
    const marca=fila(74,4154);await marca.locator('summary').click();
    if(await marca.locator('td').nth(3).innerText()!=='2'||!(await marca.innerText()).includes('Cantidad hipotética')||!(await marca.innerText()).includes('ambito_marca_salidas_pendiente'))throw Error('Se certificó la marca ennegrecida por aritmética');
    for(const id of [561,562,563,564,565,566,567,568,569])if(!(await fila(10,id).innerText()).includes('Fecha técnica / estimada'))throw Error('Una fecha retrocedida entre hojas parece confirmada');
    if(!texto.includes('Cierre escrito 40 frente a cálculo condicional 41'))throw Error('Se ocultó el ámbito pendiente entre hojas');
   }
   if(n===67){
    const fila=(aid,id)=>page.locator(`#articulo-${aid} tbody tr`).filter({hasText:'#'+id});
    for(const [id,q] of [[4213,1],[4220,3]]){
     const r=fila(75,id);await r.locator('summary').click();
     const actual=datos.articulos.find(a=>a.id===75).filas.find(f=>f.actual.id===id).actual;
     if(await r.locator('td').nth(3).innerText()!==String(q)||actual.area!==null||!(await r.innerText()).includes('desplazamiento_columna_ocr'))throw Error('La recepción sigue desplazada a área numérica');
    }
    for(const id of [1025,1026,1033,1034]){
     const r=fila(26,id);await r.locator('summary').click();
     if(!(await r.innerText()).includes('revision_previa_cotejo_completo')||!(await r.innerText()).includes('Fecha técnica / estimada'))throw Error('Se perdió la decisión previa de fecha técnica');
    }
    for(const [id,fecha] of [[4158,'2010-06-11'],[4161,'2010-09-03'],[4192,'2012-12-05'],[4204,'2013-07-01']])if(!(await fila(75,id).innerText()).includes(fecha))throw Error('Una corrección de fecha desde la foto falta');
    if(await fila(26,996).locator('td').nth(3).innerText()!=='5'||await fila(26,1077).locator('td').nth(6).innerText()!=='130'||await fila(75,4230).locator('td').nth(6).innerText()!=='205')throw Error('Las cantidades o cierres no coinciden con la evidencia');
   }
   await page.screenshot({path:path.join(dir,`informe_continuacion_${sufijo}_escritorio.png`)});
   await page.setViewportSize({width:390,height:844});await page.evaluate(()=>scrollTo(0,0));
   const ancho=await page.evaluate(()=>({pantalla:innerWidth,contenido:document.documentElement.scrollWidth}));
   if(ancho.contenido>ancho.pantalla)throw Error('Desbordamiento móvil '+n);
   await page.screenshot({path:path.join(dir,`informe_continuacion_${sufijo}_movil.png`)});
   resultados.push({lote:n,filas:cantidad,articulos:datos.articulos.length,fotos:fotos.length,ancho_movil:ancho});
  }
  if(errores.length)throw Error(errores.join('\n'));
  fs.writeFileSync(path.join(dir,`verificacion_informes_${numeros.join('_')}.json`),JSON.stringify({resultados,errores},null,2));
  console.log(JSON.stringify({resultados,errores}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.stack);process.exit(1)});
