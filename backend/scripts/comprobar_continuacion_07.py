"""Ensaya o aplica el cotejo 07, verificando fuente, efectos y reintentos."""
import argparse
import json
from datetime import datetime, UTC
from pathlib import Path
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.activos import Activo
from app.models.kardex import MovimientoKardex as M
from app.models.inventario import AperturaInventario
from app.services.calidad_kardex import tipos_alerta
from app.services.revision_documental import pagina_sql, snapshot_revision
from scripts.aplicar_revision_hil import aplicar, fuente_hash, DEST
from scripts.generar_plan_revision_hil import digest
from scripts.preparar_analitica import digest_tablas
from scripts.respaldo_recuperacion import nueva_copia

PLAN = DEST/'plan_continuacion_07.json'
RESPALDO = Path(__file__).resolve().parents[1]/'backups/respaldo_hil_20261015T015616_07'


def verificar(db):
    rows = db.query(M).filter(M.articulo_id==88).order_by(M.lote_id,pagina_sql(),M.orden_fila,M.id).all()
    assert len(rows)==241 and rows[0].id==5798 and rows[-1].id==5935
    assert rows[-1].saldo_registrado==rows[-1].saldo_calculado==1
    assert len({m.ruta_imagen_respaldo for m in rows})==10
    assert sum(m.estado!='ACTIVO' for m in rows)==1
    by_id={m.id:m for m in rows}
    assert by_id[5742].estado=='ANULADO_DOCUMENTO'
    assert by_id[5810].salidas==70
    assert by_id[5755].salidas==by_id[5756].salidas==1
    for id in (5833,5934):assert by_id[id].ingresos==1 and by_id[id].salidas is None
    assert by_id[5932].ingresos==2 and by_id[5932].salidas is None
    assert by_id[5796].revision_documental['saldo_documental']==175
    assert by_id[5796].revision_documental['saldo_documental_rectificado']==183
    assert by_id[5796].saldo_registrado==183
    assert by_id[5828].saldo_registrado==173
    errores_saldo=[m.id for m in rows if m.estado=='ACTIVO' and m.tiene_error_saldo]
    errores_fecha=[m.id for m in rows if m.estado=='ACTIVO' and m.tiene_error_fecha]
    assert not errores_saldo, errores_saldo
    assert not errores_fecha, errores_fecha
    assert all(m.revision_documental for m in rows)
    assert not db.get(Activo,88).observacion_hil['excluir_entrenamiento']
    assert db.get(AperturaInventario,88) is None
    reintentos={}
    for archivo in ('plan_correcciones.json','plan_continuacion_03.json','plan_continuacion_04.json',
                    'plan_continuacion_05.json','plan_continuacion_06.json','plan_continuacion_07.json'):
        r=aplicar(db,json.loads((DEST/archivo).read_text(encoding='utf-8')),confirmar=False)
        reintentos[archivo]={k:r[k] for k in ('aplicadas','auditorias_movimientos','observaciones_articulos')}
        assert all(v==0 for v in reintentos[archivo].values()),archivo
    return reintentos


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modo=parser.add_mutually_exclusive_group(required=True)
    modo.add_argument('--ensayo',action='store_true')
    modo.add_argument('--ejecutar',action='store_true')
    args=parser.parse_args()
    if args.ejecutar and (DEST/'resultado_continuacion_07.json').exists():
        raise RuntimeError('El resultado institucional ya existe; conservarlo.')
    plan=json.loads(PLAN.read_text(encoding='utf-8'))
    if args.ensayo:
        target,nombre,_=nueva_copia(RESPALDO,'hil07'+datetime.now(UTC).strftime('%Y%m%d%H%M%S'),'activos_continuacion_qa_')
    else:
        prueba=json.loads((DEST/'ensayo_plan_continuacion_07.json').read_text(encoding='utf-8'))
        assert prueba['plan_sha256']==digest(plan) and prueba['verificado'] is True
        target,nombre=engine,'institucional'
    with target.connect() as conn:antes=digest_tablas(conn,inspect(conn).get_table_names())
    with Session(target) as db:
        original=fuente_hash(db)
        previos={m.id:snapshot_revision(m) for m in db.query(M).filter(M.articulo_id==88)}
        resultado=aplicar(db,plan,confirmar=True)
    with Session(target) as db:
        reintentos=verificar(db)
        assert fuente_hash(db)==original
        actuales={m.id:snapshot_revision(m) for m in db.query(M).filter(M.articulo_id==88)}
        total=db.query(M).count()
        revisados=db.query(M).filter(M.revision_documental.isnot(None)).count()
        pendientes=sum(bool(tipos_alerta(m)) for m in db.query(M).filter(M.lote_id.isnot(None),M.estado=='ACTIVO'))
    with target.connect() as conn:despues=digest_tablas(conn,inspect(conn).get_table_names())
    modificadas=[t for t in antes if antes[t]!=despues[t]]
    assert set(modificadas)<= {'movimientos_kardex','activo','auditoria_sistema'},modificadas
    campos=('fecha_movimiento','detalle','referencia','area','ingresos','salidas','saldo_registrado','estado','orden_pagina_validado')
    modificados={k:sum(previos[id][k]!=r[k] for id,r in actuales.items()) for k in campos}
    filas_cambiadas=sum(any(previos[id][k]!=r[k] for k in campos if k!='orden_pagina_validado') for id,r in actuales.items())
    resultado.update(base_ensayo=nombre,verificado=True,tablas_modificadas=modificadas,
        fuente_sha256=original,reintentos=reintentos,cotejo=plan['cotejo'],
        registros=total,revisados_acumulados=revisados,pendientes_hil=pendientes,
        campos_modificados=modificados,movimientos_con_cambios_de_lectura_o_estado=filas_cambiadas)
    archivo=DEST/('ensayo_plan_continuacion_07.json' if args.ensayo else 'resultado_continuacion_07.json')
    if archivo.exists() and args.ejecutar:raise RuntimeError('El resultado institucional ya existe; conservarlo.')
    archivo.write_text(json.dumps(resultado,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps({k:v for k,v in resultado.items() if k!='perfil_analitica'},ensure_ascii=False))


if __name__=='__main__':main()
