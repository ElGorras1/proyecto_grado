"""Exporta una instantánea verificable de un lote de cotejo HIL."""
import argparse,hashlib,json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from sqlalchemy import text
from app.db.session import SessionLocal
from app.models.activos import Activo
from app.models.kardex import MovimientoKardex as M
from app.services.revision_documental import pagina_sql,snapshot_revision
from scripts.aplicar_revision_hil import BACKEND,DEST,fuente_hash
from scripts.exportar_continuacion_hil_20261014 import renderizar


def preparar(numero):
    sufijo=f'{numero:02d}';plan=json.loads((DEST/f'plan_continuacion_{sufijo}.json').read_text(encoding='utf-8'))
    resultado=json.loads((DEST/f'resultado_continuacion_{sufijo}.json').read_text(encoding='utf-8'))
    assert resultado['verificado']
    entries={e['id']:e for e in plan['revisiones']};grupos=[];cierres=[]
    with SessionLocal() as db:
        db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
        assert fuente_hash(db)==resultado['fuente_sha256']
        for aid in sorted({e['articulo_id'] for e in entries.values()}):
            a=db.get(Activo,aid);filas=[]
            rows=db.query(M).filter(M.articulo_id==aid).order_by(M.lote_id,pagina_sql(),M.orden_fila,M.id).all()
            for m in rows:
                if m.id not in entries:
                    if not (m.revision_documental or {}).get('recuperacion_clave'):continue
                    actual=snapshot_revision(m);antes={k:actual[k] for k in ('fecha_movimiento','detalle','referencia','area','ingresos','salidas','saldo_registrado')}
                    pagina=f'L{m.lote_id:04d}-P{m.numero_pagina:02d}'
                else:
                    e=entries[m.id];antes=e['esperado'];pagina=e['pagina']
                foto=(BACKEND/m.ruta_imagen_respaldo).resolve()
                if m.id in entries:assert hashlib.sha256(foto.read_bytes()).hexdigest()==entries[m.id]['sha256_imagen']
                filas.append({'antes':antes,'actual':snapshot_revision(m),'pagina':pagina,'foto':foto.as_uri()})
            grupos.append({'id':aid,'nombre':a.nombre,'observacion':a.observacion_hil,'filas':filas})
            ultima=next(m for m in reversed(rows) if m.estado=='ACTIVO')
            cierres.append({'id':aid,'articulo':a.nombre,'saldo_vigente':ultima.saldo_registrado,'saldo_documental':ultima.revision_documental.get('saldo_documental'),
                'saldo_calculado':ultima.saldo_calculado,'pendiente':bool(ultima.tiene_error_saldo) or aid in plan['cotejo'].get('cierres_no_operables',[]),
                'limite_cierre':plan['cotejo'].get('limites_cierre',{}).get(str(aid),plan['cotejo'].get('limite_cierre'))})
        db.rollback()
    return {'generado_en':datetime.now(ZoneInfo('America/La_Paz')).isoformat(),'articulos':grupos,'cierre_verificado':{'cierres':cierres},
        'presentacion':{'resumen':f"{sum(len(a['filas']) for a in grupos)} filas cotejadas en {plan['cotejo']['fotografias']} fotos; {resultado['movimientos_con_cambios']} con cambios de campos.",
            'acumulado':f"Acumulado: {resultado['revisados_acumulados']} movimientos distintos revisados. Informe del lote {numero:02d}; no es todo el dataset.",
            'aviso':'Las cantidades, saldos hipotéticos y fechas técnicas están identificados y excluidos del entrenamiento. Se conservan notas, anulaciones, fotos y discrepancias del papel. Los saldos reconstruidos no acreditan existencias físicas actuales. El resto del histórico continúa en revisión.'}}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--numero',type=int,choices=range(9,100),required=True)
    parser.add_argument('--salida',type=Path,required=True);args=parser.parse_args()
    copia=DEST/f'instantanea_informe_continuacion_{args.numero:02d}.json'
    if copia.exists():datos=json.loads(copia.read_text(encoding='utf-8'))
    else:
        datos=preparar(args.numero);copia.write_text(json.dumps(datos,ensure_ascii=False,indent=2),encoding='utf-8')
    args.salida.parent.mkdir(parents=True,exist_ok=True)
    args.salida.write_text(renderizar(datos),encoding='utf-8')
    print(json.dumps({'informe':str(args.salida.resolve()),'filas':sum(len(a['filas']) for a in datos['articulos'])},ensure_ascii=False))


if __name__=='__main__':main()
