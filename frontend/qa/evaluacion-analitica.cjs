// QA de lectura contra la instalación local. El token se recibe por entorno y no se imprime.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  if (!process.env.QA_ACCESS_TOKEN) throw Error('Falta QA_ACCESS_TOKEN de una cuenta local autorizada');
  const browser = await chromium.launch({
    executablePath: process.env.BROWSER_EXECUTABLE || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true,
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
    const errores = [], escrituras = [];
    page.on('pageerror', e => errores.push(e.message));
    page.on('response', r => {
      if (r.url().includes('/api/v1/') && r.status() >= 400) errores.push('HTTP ' + r.status() + ' ' + new URL(r.url()).pathname);
    });
    await page.addInitScript(token => sessionStorage.setItem('access_token', token), process.env.QA_ACCESS_TOKEN);
    await page.route('**/api/v1/**', async route => {
      if (!['GET', 'OPTIONS'].includes(route.request().method())) {
        escrituras.push(route.request().method() + ' ' + new URL(route.request().url()).pathname);
        await route.abort();
      } else await route.continue();
    });
    const salida = process.env.QA_OUTPUT || path.join(__dirname, '../../backend/backups/evaluacion_analitica/qa');
    fs.mkdirSync(salida, { recursive: true });
    await page.goto('http://localhost:5173/analitica?gestion=2025');
    await page.getByText('Evaluación y límites del modelo', { exact: true }).click();
    const panel = page.getByRole('region', { name: 'Evaluación independiente' });
    await panel.getByText('Comprobación técnica', { exact: true }).waitFor();
    if (!(await panel.innerText()).includes('0/20')) throw Error('No aparece revisión humana pendiente');
    if (!(await panel.innerText()).includes('779/1112')) throw Error('No aparece cobertura real');
    await panel.getByText('Ver comprobaciones del corte y resultados', { exact: true }).click();
    await panel.screenshot({ path: path.join(salida, 'evaluacion-escritorio.png') });
    const consulta = page.waitForResponse(r => r.url().includes('/analitica/resultados?') && new URL(r.url()).searchParams.get('seleccion') === 'top_modelo');
    await panel.getByRole('button', { name: 'Revisar selección', exact: true }).nth(0).click();
    await page.waitForFunction(() => document.querySelector('form.filtros select')?.value === '');
    await consulta;
    await page.getByRole('button', { name: 'Ver evidencia', exact: true }).first().click();
    await page.getByRole('heading', { name: 'Documentar revisión' }).waitFor();
    await page.getByRole('button', { name: 'Cerrar detalle', exact: true }).click();
    await page.setViewportSize({ width: 390, height: 844 });
    await panel.screenshot({ path: path.join(salida, 'evaluacion-movil.png') });
    if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) throw Error('Desborde horizontal de la página');
    if (errores.length || escrituras.length) throw Error([...errores, ...escrituras].join('\n'));
    console.log('QA con datos reales: evaluación, selección completa, evidencia, escritorio y móvil. Sin errores JS, desborde ni solicitudes de escritura.');
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e.message); process.exit(1); });
