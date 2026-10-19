"""Ensayo aislado y aplicación controlada del cotejo de revistas 08."""
import argparse
import json
from collections import Counter
from datetime import datetime, UTC
from pathlib import Path
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.activos import Activo
from app.models.inventario import AperturaInventario
from app.models.kardex import MovimientoKardex as M
from app.services.calidad_kardex import tipos_alerta
from app.services.datos_analitica import leer_corte, seleccionar
from app.services.revision_documental import pagina_sql, snapshot_revision
from scripts.aplicar_revision_hil import aplicar, fuente_hash, DEST
from scripts.generar_plan_revision_hil import digest
from scripts.preparar_analitica import digest_tablas
from scripts.respaldo_recuperacion import nueva_copia

PLAN=DEST/'plan_continuacion_08.json'
RESPALDO=Path(__file__).resolve().parents[1]/'backups/respaldo_hil_20261015T031647_08'
ARTICULOS=(187,302,306)


def verificar(db,plan):
    filas=db.query(M).filter(M.articulo_id.in_(ARTICULOS)).order_by(M.lote_id,pagina_sql(),M.orden_fila,M.id).all()
    por_id={m.id:m for m in filas}
    assert len(filas)==180 and len({m.ruta_imagen_respaldo for m in filas})==8
    for e in plan['revisiones']:
        actual=snapshot_revision(por_id[e['id']])
        assert all(actual[k]==v for k,v in e['cambios'].items()),e['id']
    assert all(m.estado=='ACTIVO' and not m.tiene_error_saldo and not m.tiene_error_fecha for m in filas),[(m.id,m.tiene_error_saldo,m.tiene_error_fecha) for m in filas if m.tiene_error_saldo or m.tiene_error_fecha]
    for aid,esperado in ((187,10),(302,8),(306,9)):
        ultima=next(m for m in reversed(filas) if m.articulo_id==aid)
        assert ultima.saldo_registrado==ultima.saldo_calculado==esperado
        assert db.get(AperturaInventario,aid) is None
        assert db.get(Activo,aid).observacion_hil['observado'] is True
    assert por_id[10321].ingresos==1 and por_id[10321].area=='Cedoal'
    assert por_id[10319].referencia is None and por_id[10319].area=='Cedoal'
    assert por_id[10367].ingresos==2 and por_id[10367].salidas is None
    assert por_id[10503].area=='CEDOAL'
    assert por_id[10372].salidas==9 and por_id[10508].salidas==16
    assert por_id[8592].ingresos is None and por_id[8592].revision_documental['saldo_base']==7
    corte=leer_corte(db);elegibles,_=seleccionar(corte['filas']);ids_elegibles={f['id'] for f in elegibles}
    inferidos=[]
    for m in filas:
        r=m.revision_documental
        if r.get('origen_fecha') in ('HIPOTESIS','SECUENCIA_AJUSTADA') or r.get('origen_saldo')=='HIPOTESIS' or r.get('origen_saldo_base')=='HIPOTESIS':
            assert m.id not in ids_elegibles,m.id
            inferidos.append(m.id)
    reintentos={}
    for nombre in ('plan_correcciones.json',*(f'plan_continuacion_{n:02d}.json' for n in range(3,9))):
        r=aplicar(db,json.loads((DEST/nombre).read_text(encoding='utf-8')),confirmar=False)
        reintentos[nombre]={k:r[k] for k in ('aplicadas','auditorias_movimientos','observaciones_articulos')}
        assert all(v==0 for v in reintentos[nombre].values()),nombre
    return inferidos,reintentos


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modo=parser.add_mutually_exclusive_group(required=True)
    modo.add_argument('--ensayo',action='store_true');modo.add_argument('--ejecutar',action='store_true')
    args=parser.parse_args()
    resultado_path=DEST/'resultado_continuacion_08.json'
    if args.ejecutar and resultado_path.exists():raise RuntimeError('Conservar el resultado ya existente.')
    plan=json.loads(PLAN.read_text(encoding='utf-8'))
    if args.ensayo:
        target,nombre,_=nueva_copia(RESPALDO,'hil08'+datetime.now(UTC).strftime('%Y%m%d%H%M%S'),'activos_continuacion_qa_')
    else:
        ensayo=json.loads((DEST/'ensayo_plan_continuacion_08.json').read_text(encoding='utf-8'))
        assert ensayo['verificado'] and ensayo['plan_sha256']==digest(plan)
        target,nombre=engine,'institucional'
    with target.connect() as conn:antes=digest_tablas(conn,inspect(conn).get_table_names())
    with Session(target) as db:
        original=fuente_hash(db)
        previos={m.id:snapshot_revision(m) for m in db.query(M).filter(M.articulo_id.in_(ARTICULOS))}
        resultado=aplicar(db,plan,confirmar=True)
    with Session(target) as db:
        inferidos,reintentos=verificar(db,plan)
        assert fuente_hash(db)==original
        actuales={m.id:snapshot_revision(m) for m in db.query(M).filter(M.articulo_id.in_(ARTICULOS))}
        revisados=db.query(M).filter(M.revision_documental.isnot(None)).count()
        pendientes=sum(bool(tipos_alerta(m)) for m in db.query(M).filter(M.lote_id.isnot(None),M.estado=='ACTIVO'))
    with target.connect() as conn:despues=digest_tablas(conn,inspect(conn).get_table_names())
    modificadas=[t for t in antes if antes[t]!=despues[t]]
    assert set(modificadas)<={'movimientos_kardex','activo','auditoria_sistema'},modificadas
    campos=('fecha_movimiento','detalle','referencia','area','ingresos','salidas','saldo_registrado','estado')
    cambios={k:sum(previos[id][k]!=r[k] for id,r in actuales.items()) for k in campos}
    cambiados=sum(any(previos[id][k]!=r[k] for k in campos) for id,r in actuales.items())
    resultado.update(base_ensayo=nombre,verificado=True,tablas_modificadas=modificadas,
        fuente_sha256=original,reintentos=reintentos,cotejo=plan['cotejo'],inferidos_excluidos_entrenamiento=inferidos,
        revisados_acumulados=revisados,pendientes_hil=pendientes,campos_modificados=cambios,
        movimientos_con_cambios_de_lectura_o_estado=cambiados)
    path=DEST/'ensayo_plan_continuacion_08.json' if args.ensayo else resultado_path
    path.write_text(json.dumps(resultado,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps({k:v for k,v in resultado.items() if k not in ('perfil_analitica','reintentos','inferidos_excluidos_entrenamiento')},ensure_ascii=False))


if __name__=='__main__':main()
