// Recorrido de presentación: exclusivamente contra la copia PostgreSQL en 8018.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('fs'), path = require('path'), assert = require('node:assert/strict');
const API = 'http://127.0.0.1:8018/api/v1', WEB = 'http://127.0.0.1:5188';

function csv(text) {
  const rows = []; let row = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') {
      if (quoted && text[i + 1] === '"') { field += '"'; i++; } else quoted = !quoted;
    } else if (c === ';' && !quoted) { row.push(field); field = ''; }
    else if ((c === '\n' || c === '\r') && !quoted) {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(field); rows.push(row); row = []; field = '';
    } else field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows;
}

(async () => {
  assert(process.env.QA_ACCESS_TOKEN && process.env.QA_OUTPUT, 'Falta la sesión de ensayo.');
  const output = process.env.QA_OUTPUT; fs.mkdirSync(output, { recursive: true });
  const checks = [], errors = [], forbiddenWrites = [];
  const browser = await chromium.launch({headless: true,
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}, acceptDownloads: true});
  await context.addInitScript(t => sessionStorage.setItem('access_token', t), process.env.QA_ACCESS_TOKEN);
  const page = await context.newPage(); page.setDefaultTimeout(20000);
  page.on('pageerror', e => errors.push(e.message));
  await page.route('**/api/v1/**', async route => {
    if (!route.request().url().startsWith(API)) {
      forbiddenWrites.push(route.request().url()); await route.abort();
    } else await route.continue();
  });
  const headers = {Authorization: 'Bearer ' + process.env.QA_ACCESS_TOKEN};
  async function get(route, params = {}) {
    const r = await context.request.get(API + route, {headers, params});
    assert.equal(r.status(), 200, route + ': ' + await r.text()); return r.json();
  }
  function pass(name, details) { checks.push({name, details}); console.log('PROBADO: ' + name); }
  async function screenshot(name) { await page.screenshot({path: path.join(output, name + '.png'), fullPage: true}); }
  async function download(button, filename) {
    const pending = page.waitForEvent('download'); await button.click();
    const d = await pending; assert.equal(await d.failure(), null);
    await d.saveAs(path.join(output, filename));
    return csv(fs.readFileSync(path.join(output, filename), 'utf8').replace(/^\uFEFF/, ''));
  }
  async function applyReport(params) {
    const pending = page.waitForResponse(r => {
      const url = new URL(r.url());
      return url.pathname === '/api/v1/reportes/inventario' &&
        Object.entries(params).every(([key, value]) => url.searchParams.get(key) === String(value));
    });
    await page.getByRole('button', {name: 'Aplicar filtros', exact: true}).click();
    const r = await pending; assert.equal(r.status(), 200);
    const q = new URL(r.url()).searchParams;
    for (const [key, value] of Object.entries(params)) assert.equal(q.get(key), String(value));
    const data = await r.json();
    await page.getByRole('button', {name: 'Aplicar filtros', exact: true}).waitFor();
    await page.waitForFunction(() => ![...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Aplicar filtros')?.disabled);
    return data;
  }
  try {
    const tandas = await get('/kardex/tandas');
    assert.deepEqual(tandas.tandas.map(t => t.id), [1, 2, 3]);
    const arts = await get('/kardex/articulos');
    const art = arts.find(a => a.id === 4);
    assert.equal(art.stock_actual, 126); assert.equal(art.apertura, null);
    assert.equal(art.base_kardex.operable, true);
    const historicalBefore = await get('/kardex/historial/4');
    await page.goto(WEB + '/kardex-digital');
    await page.getByRole('button', {name: /Tanda 3 ·/}).waitFor();
    for (const t of tandas.tandas) {
      assert((await page.getByRole('button', {name: new RegExp('Tanda ' + t.id + ' ·')}).innerText()).includes(String(t.movimientos)));
    }
    const music = arts.find(a => a.nombre.toUpperCase().includes('MUSICREAR'));
    assert(music, 'Falta el artículo CD MUSICREAR de la tanda 3.');
    await page.getByLabel('Buscar artículos por nombre o código').fill('MUSICREAR');
    await page.locator('.articulo-card').filter({hasText: music.nombre}).click();
    await page.getByRole('button', {name: /Tanda 3 ·/}).click();
    await page.getByTitle('Ver Foto', {exact: true}).first().waitFor();
    await page.getByTitle('Ver Foto', {exact: true}).first().click();
    const image = page.getByAltText('Hoja de Kárdex');
    await image.waitFor(); await image.evaluate(img => img.decode());
    assert(await image.evaluate(img => img.naturalWidth > 0));
    await screenshot('16-tanda3-evidencia');
    pass('16: tandas, historial y fotografía real', tandas);

    await page.goto(WEB + '/reportes/inventario');
    await page.getByRole('region', {name: 'Resumen del reporte'}).waitFor();
    await page.getByLabel('Gestión', {exact: true}).selectOption('2025');
    await page.getByLabel('Origen', {exact: true}).selectOption('historico');
    const report = await applyReport({gestion: 2025, origen: 'historico'});
    assert.equal(report.resumen.movimientos, 216); assert.equal(report.resumen.articulos, 142);
    const reportCsv = await download(page.getByRole('button', {name: '↓ Descargar CSV', exact: true}), '17-reporte-historico-2025.csv');
    assert.equal(reportCsv.length - 1, 216);
    await screenshot('17-reporte-2025');
    await page.getByLabel('Artículo o código', {exact: true}).fill('NO_EXISTE_DEMO_16_18');
    const none = await applyReport({articulo: 'NO_EXISTE_DEMO_16_18'});
    assert.equal(none.resumen.movimientos, 0);
    pass('17: filtro por gestión, exportación idéntica y búsqueda sin resultados', report.resumen);

    await page.goto(WEB + '/inventario-vivo');
    await page.getByLabel('Buscar artículos por nombre o código').fill('DAVID CRESPO');
    await page.locator('.articulo-card').filter({hasText: art.nombre}).click();
    await page.getByRole('region', {name: 'Kárdex digital por artículo'}).waitFor();
    await page.getByText('Base de trabajo del Kárdex histórico: 126 u.', {exact: true}).waitFor();
    await screenshot('18-base-historica-126');
    // Los campos sin asociación label/id se ubican por su grupo visible.
    async function transaction(type, quantity, document) {
      await page.getByRole('button', {name: '+ Nueva Transacción', exact: true}).click();
      await page.getByRole('heading', {name: 'Registrar Transacción', exact: true}).waitFor();
      const form = page.locator('.form-container').filter({has: page.getByRole('heading', {name: 'Registrar Transacción', exact: true})});
      await form.locator('.form-group').filter({has: page.locator('label', {hasText: 'Tipo de Operación:'})}).locator('select').selectOption(type);
      await form.locator('.form-group').filter({has: page.locator('label', {hasText: /^Cantidad:$/})}).locator('input').fill(String(quantity));
      const options = await page.locator('#movimiento-encargado option:not([disabled])').all();
      assert(options.length > 0); await page.locator('#movimiento-encargado').selectOption(await options[0].getAttribute('value'));
      await page.locator('#movimiento-referencia').fill(document);
      if (type === 'Ventas') {
        await page.locator('#receptor-operacion').fill('Destinatario ficticio del ensayo');
        await page.locator('#tipo-receptor-operacion').selectOption('INSTITUCION');
        const channel = form.locator('.form-group').filter({has: page.locator('label', {hasText: 'Canal de Venta:'})}).locator('select');
        if (await channel.count()) await channel.selectOption({index: 1});
      }
      const pending = page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1/kardex/movimiento-actual' && r.request().method() === 'POST');
      await page.getByRole('button', {name: 'Registrar transacción', exact: true}).click();
      let response = await pending;
      if (response.status() === 409 && (await response.json()).detail?.codigo === 'ALERTAS_CONTROL') {
        await page.locator('#motivo-alertas').fill('Operación ficticia autorizada para verificar la presentación en la copia de ensayo.');
        const again = page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1/kardex/movimiento-actual' && r.request().method() === 'POST');
        await page.getByRole('button', {name: 'Confirmar operación alertada', exact: true}).click();
        response = await again;
      }
      assert.equal(response.status(), 200, await response.text());
      await page.getByRole('button', {name: '+ Nueva Transacción', exact: true}).waitFor();
      return response.json();
    }
    const income = await transaction('Inventario / Compra', 2, 'DEMO-INGRESO-01');
    assert.equal(income.saldo_registrado, 128);
    const sale = await transaction('Ventas', 1, 'DEMO-SALIDA-01');
    assert.equal(sale.saldo_registrado, 127);
    const book = await get('/kardex/articulos/4/kardex-digital');
    assert.equal(book.base.cantidad, 126); assert.equal(book.saldo_final, 127);
    assert.equal(book.integridad, true); assert.equal(book.eventos.length, 2);
    assert.deepEqual(book.eventos.map(e => e.saldo_institucional), [128, 127]);
    assert.deepEqual(await get('/kardex/historial/4'), historicalBefore);
    const digitalCsv = await download(page.getByRole('button', {name: 'Descargar Kárdex digital (CSV)', exact: true}), '17-18-kardex-digital-demo.csv');
    assert.deepEqual(digitalCsv.slice(1).map(r => r[9]), ['126', '128', '127']);
    await screenshot('18-consolidacion-126-128-127');
    pass('18: base histórica, entrada +2, salida -1, libro íntegro y fuente intacta', book);

    await page.goto(WEB + '/reportes/inventario');
    await page.getByRole('region', {name: 'Resumen del reporte'}).waitFor();
    await page.getByLabel('Gestión', {exact: true}).selectOption('2026');
    await page.getByLabel('Origen', {exact: true}).selectOption('moderno');
    await page.getByLabel('Artículo o código', {exact: true}).fill('DAVID CRESPO');
    const modern = await applyReport({gestion: 2026, origen: 'moderno', articulo: 'DAVID CRESPO'});
    assert.equal(modern.resumen.movimientos, 2); assert.equal(modern.resumen.ingresos, 2); assert.equal(modern.resumen.salidas, 1);
    const modernCsv = await download(page.getByRole('button', {name: '↓ Descargar CSV', exact: true}), '18-reporte-moderno-demo-2026.csv');
    assert.equal(modernCsv.length - 1, 2);
    await screenshot('18-reporte-moderno-2026');
    pass('17-18: operaciones del ensayo en el reporte de 2026 y su CSV', modern.resumen);
    assert.deepEqual(errors, []); assert.deepEqual(forbiddenWrites, []);
    fs.writeFileSync(path.join(output, 'recorrido.json'), JSON.stringify({resultado: 'CORRECTO', checks, errors, forbiddenWrites}, null, 2));
  } catch (e) {
    await screenshot('error-recorrido');
    fs.writeFileSync(path.join(output, 'recorrido.json'), JSON.stringify({resultado: 'FALLO', checks, error: e.message, errors, forbiddenWrites}, null, 2));
    throw e;
  } finally { await browser.close(); }
})().catch(e => {console.error(e.message); process.exit(1);});
