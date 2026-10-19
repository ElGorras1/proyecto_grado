"""Informe de consulta del cotejo 03/04; no modifica la base de datos."""
import argparse
import hashlib
import html
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import text
from app.db.session import SessionLocal
from app.models.activos import Activo
from app.models.kardex import MovimientoKardex
from app.services.revision_documental import snapshot_revision
from scripts.aplicar_revision_hil import BACKEND, DEST, fuente_hash
from scripts.generar_plan_revision_hil import digest


def esc(valor):
    return html.escape('—' if valor is None else str(valor), quote=True)


def preparar():
    planes = [json.loads((DEST / n).read_text(encoding='utf-8')) for n in
              ('plan_continuacion_03.json', 'plan_continuacion_04.json')]
    entradas = {e['id']: e for p in planes for e in p['revisiones']}
    cierre = json.loads((DEST / 'cierre_continuacion_03_06.json').read_text(encoding='utf-8'))
    with SessionLocal() as db:
        db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
        assert fuente_hash(db) == cierre['fuente_sha256'], 'La fuente cambió desde la verificación'
        movimientos = db.query(MovimientoKardex).filter(MovimientoKardex.id.in_(entradas)).order_by(
            MovimientoKardex.articulo_id, MovimientoKardex.id).all()
        assert len(movimientos) == 341
        articulos = {a.id: a for a in db.query(Activo).filter(
            Activo.id.in_({m.articulo_id for m in movimientos})).all()}
        grupos = []
        for aid, articulo in articulos.items():
            filas = []
            for m in movimientos:
                if m.articulo_id != aid:
                    continue
                entrada = entradas[m.id]
                assert hashlib.sha256(Path(entrada['fuente']).read_bytes()).hexdigest() == entrada['sha256_imagen']
                actual = snapshot_revision(m)
                assert digest(next(p for p in planes if entrada in p['revisiones'])) in actual['revision_documental']['planes_aplicados']
                filas.append({'antes': entrada['esperado'], 'actual': actual, 'pagina': entrada['pagina'],
                              'foto': (BACKEND / m.ruta_imagen_respaldo).resolve().as_uri()})
            grupos.append({'id': aid, 'nombre': articulo.nombre, 'observacion': articulo.observacion_hil, 'filas': filas})
        db.rollback()
    return {'generado_en': datetime.now(ZoneInfo('America/La_Paz')).isoformat(),
            'cierre_verificado': cierre, 'articulos': sorted(grupos, key=lambda a: a['id'])}


def renderizar(datos):
    partes = ['''<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Continuación de la revisión HIL · 14/10/2026</title>
<style>
body{font:15px/1.5 system-ui,sans-serif;margin:0;background:#f3f6fa;color:#183047}
main{max-width:1280px;margin:auto;padding:28px}h1{font-size:28px;margin:0 0 10px}
h2{font-size:20px}p{max-width:1000px}.aviso{border-left:4px solid #ba7c19;background:#fff6df;padding:16px}
table{width:100%;border-collapse:collapse;background:white;margin:14px 0 24px}
th,td{padding:10px;border:1px solid #d6dfe8;text-align:left;vertical-align:top}th{background:#e8eef6}
td.num{white-space:nowrap;text-align:right}a{color:#075bb2}summary{cursor:pointer;font-weight:600}
details.articulo{background:white;margin:20px 0;padding:18px;border:1px solid #d6dfe8;border-radius:8px}
details.articulo>summary{font-size:18px}details.fila{font-size:13px;margin-top:8px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4f8;padding:10px;font-size:12px}
.tabla{overflow-x:auto}.muted{color:#4e6276;font-size:13px}.estimada{color:#78500d;font-weight:600}
@media print{body{background:white}main{padding:0}details.articulo{break-before:page}a{color:inherit}}
</style><main><h1>Continuación de la revisión HIL</h1>
<p>Aplicación de los criterios del titular · 14 de octubre de 2026 · Bolivia</p>
<p><strong>341 movimientos cotejados en cinco artículos y 16 fotos; 175 con cambios de campos.</strong>
Acumulado: 486 movimientos distintos con revisión. Este informe contiene este bloque; no es todo el dataset.</p>
<p class="aviso">La fotografía y la extracción original permanecen intactas. Los saldos reconstruidos
no acreditan existencias físicas. Las fechas técnicas y los saldos hipotéticos siguen identificados.
RIMSA y JULIO conservan diferencias con el papel. El histórico completo todavía requiere revisión.</p>
<div class="tabla"><table><thead><tr><th>Artículo</th><th>Filas</th><th>Reconstruido</th><th>Escrito</th></tr></thead><tbody>''']
    if datos.get('presentacion'):
        fecha_informe=datetime.fromisoformat(datos['generado_en'])
        partes[0]=partes[0].replace('14/10/2026',fecha_informe.strftime('%d/%m/%Y'))
        partes[0]=partes[0].replace('14 de octubre de 2026',fecha_informe.strftime('%d/%m/%Y'))
        # Permite otro bloque sin cambiar las cifras del informe congelado 03/04.
        texto_antiguo = '<p><strong>341 movimientos cotejados en cinco artículos y 16 fotos; 175 con cambios de campos.</strong>\nAcumulado: 486 movimientos distintos con revisión. Este informe contiene este bloque; no es todo el dataset.</p>'
        assert texto_antiguo in partes[0]
        partes[0] = partes[0].replace(texto_antiguo, '<p><strong>'+esc(datos['presentacion']['resumen'])+'</strong><br>'+esc(datos['presentacion']['acumulado'])+'</p>')
        aviso_antiguo = '<p class="aviso">La fotografía y la extracción original permanecen intactas. Los saldos reconstruidos\nno acreditan existencias físicas. Las fechas técnicas y los saldos hipotéticos siguen identificados.\nRIMSA y JULIO conservan diferencias con el papel. El histórico completo todavía requiere revisión.</p>'
        assert aviso_antiguo in partes[0]
        partes[0] = partes[0].replace(aviso_antiguo, '<p class="aviso">'+esc(datos['presentacion']['aviso'])+'</p>')
    por_id = {a['id']: a for a in datos['articulos']}
    if any(c.get('pendiente') for c in datos['cierre_verificado']['cierres']):
        partes[0]=partes[0].replace('<th>Reconstruido</th>','<th>Saldo conservado / condición</th>')
    for c in datos['cierre_verificado']['cierres']:
        condicion=''
        if c.get('pendiente'):
            condicion=f'<br><strong>Pendiente de conciliación · no operable</strong><br>Acumulado condicional: {esc(c["saldo_calculado"])}<br>{esc(c.get("limite_cierre"))}'
        elif c.get('limite_cierre'):
            condicion=f'<br><strong>Límite documental</strong><br>{esc(c["limite_cierre"])}'
        partes.append(f'<tr><td><a href="#articulo-{c["id"]}">{esc(c["articulo"])}</a></td>'
                      f'<td>{len(por_id[c["id"]]["filas"])}</td><td>{esc(c["saldo_vigente"])}{condicion}</td><td>{esc(c["saldo_documental"])}</td></tr>')
    partes.append('</tbody></table></div>')
    campos = ('fecha_movimiento', 'detalle', 'referencia', 'area', 'ingresos', 'salidas', 'saldo_registrado')
    for a in datos['articulos']:
        partes.append(f'<details class="articulo" id="articulo-{a["id"]}" open><summary>{esc(a["nombre"])} · {len(a["filas"])} movimientos</summary>')
        if a['observacion']:
            partes.append(f'<details><summary>Observación conservada del artículo</summary><pre>{esc(json.dumps(a["observacion"],ensure_ascii=False,indent=2))}</pre></details>')
        partes.append('<div class="tabla"><table><thead><tr><th>Fila / evidencia</th><th>Fecha de consulta</th><th>Detalle y revisión</th><th>I</th><th>S</th><th>Saldo vigente</th><th>Saldo escrito</th></tr></thead><tbody>')
        for f in a['filas']:
            m, antes = f['actual'], f['antes']
            rev = m['revision_documental']
            estimada = rev.get('origen_fecha') in ('HIPOTESIS', 'SECUENCIA_AJUSTADA')
            cambios = {k: {'antes': antes[k], 'vigente': m[k]} for k in campos if antes[k] != m[k]}
            evidencia = {'cambios_de_campos_en_esta_continuacion': cambios, 'estado_vigente': m['estado'], 'revision_vigente': rev,
                         'extraccion_original': m['datos_originales'], 'fecha_original': m['fecha_original']}
            etiquetas=''
            if rev.get('tipo_fila')=='BASE_DOCUMENTAL':
                etiquetas+='<br><strong>Base documental · sin ingreso añadido</strong>'
            if rev.get('operacion_mixta')=='DONACION_Y_VENTA' and rev.get('sin_desglose_documental'):
                etiquetas+='<br><strong>Donación y venta · sin desglose documental</strong>'
            partes.append(f'<tr><td>#{m["id"]}<br>{esc(f["pagina"])} · fila {esc(m["orden_fila"])}<br><a href="{esc(f["foto"])}">Abrir fotografía</a></td>'
                          f'<td>{esc(m["fecha_movimiento"])}'+('<br><span class="estimada">Fecha técnica / estimada</span>' if estimada else '')+'</td>'
                          f'<td>{esc(m["detalle"])}'+etiquetas+('<br><strong>Fila recuperada desde la foto · omitida por OCR</strong>' if rev.get('recuperacion_clave') else '')+('<br><strong>'+('Nota documental' if m['estado']=='NOTA_DOCUMENTAL' else 'Anulado en el documento')+' · sin efecto en el saldo</strong>' if m['estado']!='ACTIVO' else '')+('<br><strong>Cantidad hipotética</strong>' if rev.get('origen_cantidades')=='HIPOTESIS' else '')+'<br><span class="muted">'+('No existía un registro OCR de esta fila' if rev.get('recuperacion_clave') else ('Campos corregidos' if cambios else 'Cotejado; sin cambios en estos campos'))+'</span>'
                          f'<details class="fila"><summary>Comparación, originales y criterio</summary><pre>{esc(json.dumps(evidencia,ensure_ascii=False,indent=2))}</pre></details></td>'
                          f'<td class="num">{esc(m["ingresos"])}</td><td class="num">{esc(m["salidas"])}</td>'
                          f'<td class="num">{esc(m["saldo_registrado"])}'+('<br><span class="estimada">Saldo hipotético</span>' if rev.get('origen_saldo')=='HIPOTESIS' else '')+f'</td><td class="num">{esc(rev.get("saldo_documental"))}</td></tr>')
        partes.append('</tbody></table></div></details>')
    partes.append(f'<p class="muted">Instantánea generada: {esc(datos["generado_en"])}. Las fotos enlazadas requieren conservar la carpeta del proyecto en esta computadora.</p></main></html>')
    return ''.join(partes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args()
    copia = DEST / 'instantanea_informe_continuacion_03_06.json'
    # La instantánea del primer informe es inmutable; una ejecución posterior
    # conserva ese corte en lugar de presentarlo como dato vivo.
    if copia.exists():
        datos = json.loads(copia.read_text(encoding='utf-8'))
    else:
        datos = preparar()
        copia.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding='utf-8')
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(renderizar(datos), encoding='utf-8')
    print(json.dumps({'informe': str(args.salida.resolve()), 'movimientos': sum(len(a['filas']) for a in datos['articulos'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
