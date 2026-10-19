// Revisión real en lectura. Se bloquean todas las escrituras desde la interfaz.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('fs'), path = require('path'), assert = require('node:assert/strict');

(async () => {
  assert(process.env.QA_ACCESS_TOKEN, 'Falta sesión QA local');
  const browser = await chromium.launch({
    executablePath: process.env.BROWSER_EXECUTABLE || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true,
  });
  const salida = process.env.QA_OUTPUT || path.join(__dirname, '../../backend/backups/revision_modulos_20261012');
  fs.mkdirSync(salida, { recursive: true });
  const comprobaciones = [], errores = [], escrituras = [];
  try {
    const api = await browser.newContext({ extraHTTPHeaders: { Authorization: 'Bearer ' + process.env.QA_ACCESS_TOKEN } });
    const leer = async (ruta, params = {}) => {
      const r = await api.request.get('http://localhost:8000/api/v1' + ruta, { params });
      assert.equal(r.status(), 200, ruta + ' no respondió correctamente');
      return r.json();
    };
    const openapi = await (await api.request.get('http://localhost:8000/openapi.json')).json();
    for (const ruta of ['/api/v1/analitica-operativa/resultados', '/api/v1/control-alertas']) {
      assert(openapi.paths[ruta].get.parameters.some(p => p.name === 'gestion'), 'API antigua sin gestión');
    }
    const modelos = await leer('/analitica/modelos');
    const modelo = modelos.filas.find(m => m.estado === 'COMPLETADO');
    assert(modelo, 'Falta un modelo histórico completado');
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    page.setDefaultTimeout(45000);
    page.on('pageerror', e => errores.push(e.message));
    page.on('response', r => { if (r.url().includes('/api/v1/') && r.status() >= 400) errores.push(r.status() + ' ' + new URL(r.url()).pathname); });
    await page.addInitScript(t => sessionStorage.setItem('access_token', t), process.env.QA_ACCESS_TOKEN);
    await page.route('**/api/v1/**', async r => {
      if (!['GET', 'OPTIONS'].includes(r.request().method())) {
        escrituras.push(r.request().method() + ' ' + new URL(r.request().url()).pathname); await r.abort();
      } else await r.continue();
    });
    async function consultar(ruta, accion, params) {
      const respuesta = page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1' + ruta && r.request().method() === 'GET');
      await accion();
      const r = await respuesta;
      assert.equal(r.status(), 200);
      const query = new URL(r.url()).searchParams;
      for (const [k, v] of Object.entries(params)) assert.equal(query.get(k), String(v), 'Filtro no enviado: ' + k);
      const data = await r.json();
      const boton = ruta === '/reportes/institucional' ? 'Consultar' : 'Aplicar filtros';
      await page.waitForFunction(nombre => {
        const b = [...document.querySelectorAll('main button')].find(x => x.textContent.trim() === nombre);
        return b && !b.disabled;
      }, boton);
      return data;
    }
    await page.goto('http://localhost:5173/analitica');
    await page.getByRole('button', { name: 'Ver evidencia', exact: true }).first().waitFor();
    const original = await leer('/analitica/resultados', { modelo_id: modelo.id });
    const gestor = page.getByLabel('Gestión documental', { exact: true });
    await gestor.selectOption('2025');
    await page.getByText('Hay cambios sin aplicar.', { exact: false }).waitFor();
    let datos = await consultar('/analitica/resultados', () => page.getByRole('button', { name: 'Aplicar filtros', exact: true }).click(), { gestion: 2025 });
    assert(datos.total > 0 && datos.total < original.total);
    await page.getByText(datos.total + ' resultados · Página 1 de', { exact: false }).waitFor();
    assert(datos.filas.every(r => r.gestion === 2025 && r.snapshot.fecha.startsWith('2025')));
    const cantidad2025 = datos.total;
    const articulo = datos.filas[0].snapshot.articulo;
    await page.getByLabel('Artículo o código', { exact: true }).fill('  ' + articulo + '  ');
    datos = await consultar('/analitica/resultados', () => page.getByRole('button', { name: 'Aplicar filtros', exact: true }).click(), { gestion: 2025, articulo });
    assert(datos.total > 0 && datos.filas.every(r => r.snapshot.articulo.toLowerCase().includes(articulo.toLowerCase())));
    await page.getByLabel('Artículo o código', { exact: true }).fill('QA_NO_EXISTE_20261012');
    datos = await consultar('/analitica/resultados', () => page.getByRole('button', { name: 'Aplicar filtros', exact: true }).click(), { articulo: 'QA_NO_EXISTE_20261012' });
    assert.equal(datos.total, 0);
    await page.getByText('No hay resultados para estos filtros.', { exact: true }).waitFor();
    datos = await consultar('/analitica/resultados', () => page.getByRole('button', { name: 'Limpiar filtros', exact: true }).click(), { seleccion: 'todos' });
    assert.equal(datos.total, original.total);
    const siguiente = await consultar('/analitica/resultados', () => page.getByRole('button', { name: 'Siguiente', exact: true }).click(), { pagina: 2 });
    assert.equal(siguiente.total, original.total);
    assert(siguiente.filas.every(r => !original.filas.some(p => p.id === r.id)));
    const nodo = original.filas.find(r => r.nodo)?.nodo;
    if (nodo) {
      await page.getByLabel('Nodo exacto', { exact: true }).fill(nodo);
      datos = await consultar('/analitica/resultados', () => page.getByRole('button', { name: 'Aplicar filtros', exact: true }).click(), { nodo, pagina: 1 });
      assert(datos.total > 0 && datos.filas.every(r => r.nodo === nodo));
      await page.getByLabel('Nodo exacto', { exact: true }).fill('');
    }
    for (const estado of ['PENDIENTE', 'EN_REVISION', 'JUSTIFICADO', 'REQUIERE_SEGUIMIENTO', 'CERRADO']) {
      await page.getByLabel('Revisión histórica', { exact: true }).selectOption(estado);
      datos = await consultar('/analitica/resultados', () => page.getByRole('button', { name: 'Aplicar filtros', exact: true }).click(), { estado });
      const esperado = await leer('/analitica/resultados', { modelo_id: modelo.id, estado });
      assert.equal(datos.total, esperado.total);
      assert(datos.filas.every(r => r.estado_revision === estado));
    }
    await page.getByLabel('Revisión histórica', { exact: true }).selectOption('');
    for (const seleccion of ['alertas', 'control', 'top_modelo', 'top_regla']) {
      await page.getByLabel('Selección', { exact: true }).selectOption(seleccion);
      datos = await consultar('/analitica/resultados', () => page.getByRole('button', { name: 'Aplicar filtros', exact: true }).click(), { seleccion });
      const esperado = await leer('/analitica/resultados', { modelo_id: modelo.id, seleccion });
      assert.equal(datos.total, esperado.total);
      if (seleccion === 'alertas') assert(datos.filas.every(r => r.alerta));
      if (seleccion === 'control') assert(datos.filas.every(r => r.muestra_control && !r.alerta));
    }
    await page.getByRole('button', { name: 'Limpiar filtros', exact: true }).click();
    await page.getByRole('button', { name: 'Ver evidencia', exact: true }).first().click();
    const foto = page.getByAltText('Fotografía original del Kárdex');
    await foto.waitFor(); await foto.evaluate(img => img.decode());
    assert(await foto.evaluate(img => img.naturalWidth > 0));
    await page.getByRole('button', { name: 'Cerrar detalle', exact: true }).click();
    await page.screenshot({ path: path.join(salida, 'historica.png'), fullPage: true });
    comprobaciones.push({ apartado: 'Histórico', evaluados: original.total, gestion2025: cantidad2025, filtros: 'gestión, artículo, selección, vacío, limpiar; evidencia visible' });

    await page.goto('http://localhost:5173/analitica-operativa');
    await page.getByText('Actualmente no hay un modelo operativo activo.', { exact: true }).waitFor();
    assert(await page.getByRole('button', { name: 'Preparar nueva versión', exact: true }).isDisabled());
    await page.getByLabel('Gestión de registro', { exact: true }).fill('2026');
    await page.getByLabel('Solo casos con alerta', { exact: true }).uncheck();
    const articuloDigital = await page.getByLabel('Artículo', { exact: true }).locator('option').nth(1).getAttribute('value');
    assert(articuloDigital);
    await page.getByLabel('Artículo', { exact: true }).selectOption(articuloDigital);
    datos = await consultar('/analitica-operativa/resultados', () => page.getByRole('button', { name: 'Aplicar filtros', exact: true }).click(), { gestion: 2026, alertas: false, articulo_id: articuloDigital });
    assert.equal(datos.total, 0);
    await page.getByText('No hay puntuaciones para esta selección.', { exact: false }).waitFor();
    await page.getByRole('button', { name: 'Limpiar filtros', exact: true }).click();
    await page.screenshot({ path: path.join(salida, 'operativa.png'), fullPage: true });
    comprobaciones.push({ apartado: 'Operativa', puntuaciones: 0, filtros: 'gestión, alerta, limpiar; entrenamiento bloqueado por falta de datos' });

    await page.goto('http://localhost:5173/alertas-inventario');
    await page.getByText('No hay casos para estos filtros.', { exact: false }).waitFor();
    await page.getByLabel('Estado del caso', { exact: true }).selectOption('TODOS');
    await page.getByLabel('Prioridad del caso', { exact: true }).selectOption('ALTA');
    await page.getByLabel('Revisor asignado', { exact: true }).selectOption('sin');
    await page.getByLabel('Gestión de registro', { exact: true }).fill('2026');
    await page.getByLabel('Desde', { exact: true }).fill('2026-01-01');
    await page.getByLabel('Hasta', { exact: true }).fill('2026-12-31');
    await page.getByLabel('Artículo', { exact: true }).selectOption(articuloDigital);
    datos = await consultar('/control-alertas', () => page.getByRole('button', { name: 'Aplicar filtros', exact: true }).click(), { estado: 'TODOS', prioridad: 'ALTA', sin_asignar: true, gestion: 2026, desde: '2026-01-01', hasta: '2026-12-31', articulo_id: articuloDigital });
    assert.equal(datos.total, 0);
    await page.getByLabel('Desde', { exact: true }).fill('2026-12-31');
    await page.getByLabel('Hasta', { exact: true }).fill('2026-01-01');
    await page.getByRole('button', { name: 'Aplicar filtros', exact: true }).click();
    await page.getByText('El inicio no puede ser posterior al fin', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Limpiar filtros', exact: true }).click();
    await page.screenshot({ path: path.join(salida, 'alertas.png'), fullPage: true });
    comprobaciones.push({ apartado: 'Alertas', casos: 0, filtros: 'estado, prioridad, revisor, gestión, fechas, limpiar' });

    await page.goto('http://localhost:5173/gestion-institucional');
    await page.getByRole('heading', { name: 'Documentos históricos de 2026', exact: true }).waitFor();
    assert(await page.getByRole('button', { name: 'Guardar cierre anual', exact: true }).isDisabled());
    await page.getByLabel('Gestión de registro', { exact: true }).fill('2025');
    await page.getByText('La gestión cambió sin consultar.', { exact: false }).waitFor();
    const informe = await consultar('/reportes/institucional', () => page.getByRole('button', { name: 'Consultar', exact: true }).click(), { gestion: 2025 });
    await page.getByRole('heading', { name: 'Documentos históricos de 2025', exact: true }).waitFor();
    await page.getByText('90 movimientos escaneados activos', { exact: false }).waitFor();
    assert.equal(informe.cobertura_historica.por_gestion['2025'].disponibles, 90);
    assert.equal(informe.resumen_periodo.eventos, 0);
    assert(await page.getByRole('button', { name: 'Guardar cierre anual', exact: true }).isDisabled());
    await page.screenshot({ path: path.join(salida, 'informe2025.png'), fullPage: true });
    await page.getByRole('link', { name: 'Ver todos los movimientos escaneados de 2025', exact: true }).click();
    await page.getByRole('heading', { name: 'Movimiento mensual · 2025', exact: true }).waitFor();
    const historico = await leer('/reportes/inventario', { gestion: 2025, origen: 'historico' });
    assert.equal(historico.resumen.movimientos, 90);
    assert.equal(await page.getByLabel('Gestión', { exact: true }).inputValue(), '2025');
    assert.equal(await page.getByLabel('Origen', { exact: true }).inputValue(), 'historico');
    await page.screenshot({ path: path.join(salida, 'movimientos2025.png'), fullPage: true });
    comprobaciones.push({ apartado: 'Informe y cierre', gestion: 2025, escaneados: 90, digitales: 0, cierre: 'bloqueado sin base; filtro y enlace conservan gestión' });
    await page.setViewportSize({ width: 390, height: 844 });
    for (const ruta of ['/analitica-operativa', '/alertas-inventario', '/gestion-institucional']) {
      await page.goto('http://localhost:5173' + ruta);
      await page.getByRole('button', { name: ruta === '/gestion-institucional' ? 'Consultar' : 'Aplicar filtros', exact: true }).waitFor();
      await page.waitForFunction(() => !document.querySelector('main button[type="submit"]')?.disabled);
      assert(!(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)), 'Desborde móvil: ' + ruta);
    }
    assert.deepEqual(errores, []); assert.deepEqual(escrituras, []);
    fs.writeFileSync(path.join(salida, 'navegador.json'), JSON.stringify({ comprobaciones, errores, escrituras }, null, 2));
    console.log(JSON.stringify({ comprobaciones, errores, escrituras }));
    await api.close();
  } finally { await browser.close(); }
})().catch(e => { console.error(e.stack); process.exitCode = 1; });
