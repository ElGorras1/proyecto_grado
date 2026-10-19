"""Completa únicamente la observación omitida del artículo 91 en el lote 10."""
import argparse,json
from datetime import datetime,UTC
from pathlib import Path
from sqlalchemy import inspect,text
from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.activos import Activo
from app.models.auditoria import AuditoriaSistema
from scripts.aplicar_revision_hil import BACKEND,DEST,fuente_hash
from scripts.generar_plan_revision_hil import digest
from scripts.preparar_analitica import digest_tablas
from scripts.respaldo_recuperacion import nueva_copia


def completar(db,plan):
    db.execute(text('SELECT pg_advisory_xact_lock(20261014,23)'))
    a=db.query(Activo).filter(Activo.id==91).with_for_update().one()
    sha=digest(plan)
    if a.observacion_hil and a.observacion_hil.get('plan_sha256')==sha:return False
    assert a.observacion_hil is None,'Conservar cualquier revisión posterior; no sobrescribirla'
    nota=next(n for n in plan['observaciones_articulos'] if n['articulo_id']==91)
    a.observacion_hil={**nota,'criterio_sha256':plan['criterio_sha256'],'plan_sha256':sha,
        'planes_aplicados':[sha],'revisado_en':datetime.now(UTC).isoformat(),
        'autor_registro':'Codex, según criterios del titular',
        'motivo_completitud':'Resumen del cotejo 10: las filas ya estaban revisadas; la recuperación de filas hizo omitir esta observación del artículo.'}
    db.add(AuditoriaSistema(accion='completar_observacion_hil',recurso='activo',recurso_id=91,resultado='exito',
        fecha_hora=datetime.now(UTC),detalle={'previo':None,'nuevo':a.observacion_hil,
            'limite':'Completa el resumen ya previsto en el plan 10; no modifica filas ni añade un nuevo cotejo.'}))
    return True


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--respaldo',type=Path,required=True)
    grupo=p.add_mutually_exclusive_group(required=True);grupo.add_argument('--ensayo',action='store_true');grupo.add_argument('--ejecutar',action='store_true')
    args=p.parse_args();respaldo=args.respaldo.resolve();assert respaldo.is_relative_to((BACKEND/'backups').resolve())
    plan=json.loads((DEST/'plan_continuacion_10.json').read_text(encoding='utf-8'));prueba=DEST/'ensayo_completar_observacion_10.json'
    if args.ensayo:target,nombre,_=nueva_copia(respaldo,'nota10'+datetime.now(UTC).strftime('%Y%m%d%H%M%S'),'activos_continuacion_qa_')
    else:
        assert json.loads(prueba.read_text(encoding='utf-8'))['verificado'];target,nombre=engine,'institucional'
    with target.connect() as c:antes=digest_tablas(c,inspect(c).get_table_names())
    with Session(target) as db:
        fuente=fuente_hash(db);cambio=completar(db,plan);db.commit()
        assert fuente_hash(db)==fuente
        assert not completar(db,plan);db.rollback()
        assert db.get(Activo,91).observacion_hil['plan_sha256']==digest(plan)
    with target.connect() as c:despues=digest_tablas(c,inspect(c).get_table_names())
    cambios=[t for t in antes if antes[t]!=despues[t]];assert set(cambios)<= {'activo','auditoria_sistema'}
    r={'verificado':True,'base':nombre,'observacion_completada':cambio,'tablas_modificadas':cambios,'movimientos_modificados':0,'fuente_sha256':fuente,'plan_sha256':digest(plan),'reintento_sin_cambios':True}
    out=prueba if args.ensayo else DEST/'resultado_completar_observacion_10.json'
    out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False))


if __name__=='__main__':main()
