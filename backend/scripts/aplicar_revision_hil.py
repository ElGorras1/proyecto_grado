"""Aplica cotejos con bloqueo, precondiciones, original inmutable y auditoría atómica."""
import argparse, hashlib, importlib, json
from copy import deepcopy
from pathlib import Path
from datetime import UTC, datetime, date
from collections import Counter
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.kardex import MovimientoKardex
from app.models.activos import Activo
from app.models.auditoria import AuditoriaSistema
from app.services.revision_documental import aplicar_cambio, snapshot_revision, registrar_revision
from app.services.kardex_service import recalcular_saldos_posteriores
from app.services.datos_analitica import leer_corte
from scripts.generar_plan_revision_hil import digest, CAMPOS_BASE
from scripts.preparar_analitica import digest_tablas

BACKEND=Path(__file__).resolve().parents[1]
DEST=BACKEND/"backups/aplicacion_hil_20261014"

def fuente_hash(db, excluir_ids=()):
    excluidos=set(excluir_ids)
    return digest([list(r) for r in db.execute(text("SELECT id, datos_originales, fecha_original, ruta_imagen_respaldo, numero_pagina FROM movimientos_kardex ORDER BY id")) if r[0] not in excluidos])


def recuperar_filas(db,plan,plan_sha):
    """Recupera filas realmente visibles que el OCR omitió, sin suplantar esa extracción."""
    propuestas=plan.get('recuperaciones',[])
    if not propuestas:return []
    claves=[p['clave'] for p in propuestas]
    assert len(set(claves))==len(claves)
    existentes={}
    for m in db.query(MovimientoKardex).filter(MovimientoKardex.articulo_id.in_({p['campos']['articulo_id'] for p in propuestas})):
        clave=(m.revision_documental or {}).get('recuperacion_clave')
        if clave in claves:
            assert clave not in existentes,'Recuperación duplicada; requiere revisión'
            existentes[clave]=m
    assert len(existentes) in (0,len(propuestas)),'Recuperación parcial; no se insertan duplicados'
    for p in propuestas:
        foto=Path(p['fuente']).resolve()
        assert foto.is_relative_to((BACKEND/'storage').resolve())
        assert hashlib.sha256(foto.read_bytes()).hexdigest()==p['sha256_imagen']
    if existentes:return []
    nuevos=[]
    for p in propuestas:
        campos=deepcopy(p['campos'])
        assert campos['lote_id'] is not None and campos['articulo_id']>0
        assert (BACKEND/campos['ruta_imagen_respaldo']).resolve()==Path(p['fuente']).resolve()
        assert db.query(MovimientoKardex).filter_by(articulo_id=campos['articulo_id'],lote_id=campos['lote_id'],
            ruta_imagen_respaldo=campos['ruta_imagen_respaldo'],numero_pagina=campos['numero_pagina']).first() is not None,'La recuperación necesita una foto ya vinculada al artículo'
        assert type(campos['orden_fila']) is int and campos['orden_fila']>0
        assert type(campos['saldo_registrado']) is int
        for campo in ('ingresos','salidas'):
            assert campos.get(campo) is None or type(campos[campo]) is int and campos[campo]>=0
        assert not ((campos.get('ingresos') or 0)>0 and (campos.get('salidas') or 0)>0)
        campos['fecha_movimiento']=date.fromisoformat(campos['fecha_movimiento'])
        assert campos.get('fecha_original') is None
        assert campos['datos_originales']['fuente']=='LECTURA_FOTO_HIL'
        revision={**deepcopy(p['revision']),'version':1,'recuperacion_clave':p['clave'],
            'criterio_sha256':plan['criterio_sha256'],'plan_sha256':plan_sha,'planes_aplicados':[plan_sha],
            'autor_registro':'Codex, por instrucción del usuario de este chat','revisado_en':datetime.now(UTC).isoformat()}
        assert revision['origen_fecha']=='HIPOTESIS' and revision['fecha_documental'] is None and revision['motivo_fecha']
        assert revision.get('criterios') and revision.get('motivo','').strip()
        m=MovimientoKardex(**campos,revision_documental=revision)
        db.add(m);db.flush();nuevos.append(m.id)
        db.add(AuditoriaSistema(accion='recuperar_fila_kardex_hil',recurso='movimientos_kardex',recurso_id=m.id,
            resultado='exito',fecha_hora=datetime.now(UTC),detalle={'previo':None,'nuevo':snapshot_revision(m),
                'motivo':revision['motivo'],'criterio_sha256':plan['criterio_sha256'],'plan_sha256':plan_sha,
                'limite':'Recuperación desde fotografía existente, no una nueva operación digital ni una nueva extracción OCR.'}))
    return nuevos

def migrar(conexion):
    actual=conexion.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    if actual=="p61b20dc8e35":return
    if actual!="o50a19cb7d24":raise RuntimeError("Revisión de esquema inesperada")
    tablas=["movimientos_kardex","activo"]
    columnas={t:[r[0] for r in conexion.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=:t ORDER BY ordinal_position"),{"t":t})] for t in tablas}
    antes={t:digest([list(r) for r in conexion.execute(text("SELECT "+", ".join(conexion.dialect.identifier_preparer.quote(k) for k in cs)+" FROM "+t+" ORDER BY id"))]) for t,cs in columnas.items()}
    with Operations.context(MigrationContext.configure(conexion)):
        importlib.import_module("migrations.versions.p61b20dc8e35_revision_documental_hil").upgrade()
    despues={t:digest([list(r) for r in conexion.execute(text("SELECT "+", ".join(conexion.dialect.identifier_preparer.quote(k) for k in cs)+" FROM "+t+" ORDER BY id"))]) for t,cs in columnas.items()}
    assert antes==despues,"La migración alteró columnas previas"
    conexion.execute(text("UPDATE alembic_version SET version_num='p61b20dc8e35' WHERE version_num='o50a19cb7d24'"))

def aplicar(db,plan,confirmar=False):
    plan_sha=digest(plan)
    policy=json.loads((DEST/"criterios_version_1.json").read_text(encoding="utf-8"))
    assert digest(policy)==plan["criterio_sha256"]
    if db.bind.url.get_backend_name()=="postgresql":
        if not db.execute(text("SELECT pg_try_advisory_xact_lock(20261014, 23)")).scalar_one():
            raise RuntimeError("Otra revisión está aplicándose")
    fuentes={r["fuente"]:r["sha256_imagen"] for r in plan["revisiones"]}
    for path,expected in fuentes.items():
        p=Path(path).resolve()
        assert p.is_relative_to((BACKEND/"storage").resolve())
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,"Cambió una foto fuente"
    original=fuente_hash(db)
    cantidad=db.query(MovimientoKardex).count()
    nuevos_ids=recuperar_filas(db,plan,plan_sha)
    ids=sorted({r["articulo_id"] for r in plan["revisiones"]})
    articulos=db.query(Activo).filter(Activo.id.in_(ids)).order_by(Activo.id).with_for_update().all()
    movimientos=db.query(MovimientoKardex).filter(MovimientoKardex.articulo_id.in_(ids)).order_by(MovimientoKardex.id).with_for_update().all()
    por_id={m.id:m for m in movimientos}
    previos={m.id:snapshot_revision(m) for m in movimientos}
    aplicados=[]
    for entry in plan["revisiones"]:
        m=por_id[entry["id"]]
        previa=m.revision_documental or {}
        if previa.get("plan_sha256")==plan_sha or plan_sha in previa.get("planes_aplicados",[]):continue
        estado=snapshot_revision(m)
        assert {k:estado[k] for k in CAMPOS_BASE}==entry["esperado"],f"La fila{m.id} cambió desde el cotejo"
        assert all(estado[k]==v for k,v in entry.get('esperado_adicional',{}).items()),f"Cambió la clasificación de la fila{m.id} desde el cotejo"
        aplicar_cambio(m,entry["cambios"],entry["revision"],criterio_sha256=plan["criterio_sha256"],plan_sha256=plan_sha)
        aplicados.append(m.id)
    for id in sorted({por_id[k].articulo_id for k in aplicados}):
        recalcular_saldos_posteriores(db,id,confirmar=False)
    aud=len(nuevos_ids);mobs=0
    for m in movimientos:
        aud+=registrar_revision(db,m,previos[m.id],criterio_sha256=plan["criterio_sha256"],
                               motivo="Aplicación asistida de criterios HIL y comprobación de continuidad del artículo.")
    amap={a.id:a for a in articulos}
    for note in plan["observaciones_articulos"]:
        a=amap[note["articulo_id"]]
        previa=a.observacion_hil or {}
        conocidos=set(previa.get("planes_aplicados",[]))
        if previa.get("plan_sha256"):conocidos.add(previa["plan_sha256"])
        # La observación puede tener una revisión posterior. Recuperar también
        # las versiones de las filas ANTES de este lote impide que un reintento
        # de un plan antiguo revierta la nota más reciente del artículo.
        for m in movimientos:
            # Una fila insertada por ESTE plan ya lleva su huella; no prueba
            # que la observación del artículo se haya registrado antes.
            if m.articulo_id!=a.id or m.id in nuevos_ids:continue
            revision_previa=previos[m.id].get("revision_documental") or {}
            conocidos.update(revision_previa.get("planes_aplicados",[]))
            if revision_previa.get("plan_sha256"):conocidos.add(revision_previa["plan_sha256"])
        if plan_sha in conocidos:continue
        before=a.observacion_hil
        a.observacion_hil={**note,"criterio_sha256":plan["criterio_sha256"],"plan_sha256":plan_sha,
                          "planes_aplicados":sorted(conocidos|{plan_sha}),
                          "revisado_en":datetime.now(UTC).isoformat(),"autor_registro":"Codex, según criterios del titular"}
        db.add(AuditoriaSistema(accion="revisar_observacion_hil",recurso="activo",recurso_id=a.id,
            resultado="exito",fecha_hora=datetime.now(UTC),detalle={"previo":before,"nuevo":a.observacion_hil,
                "autor_registro":"Codex, según criterios del titular"}))
        mobs+=1
    db.flush()
    assert db.query(MovimientoKardex).count()==cantidad+len(nuevos_ids)
    assert fuente_hash(db,excluir_ids=nuevos_ids)==original,"Se alteró extracción original, fecha original o fotografía de registros preexistentes"
    # Estos controles descubren una lectura desplazada o un recalculo incorrecto.
    if 9657 in por_id:
        assert por_id[9657].ingresos==40 and por_id[9657].saldo_registrado==41
        assert por_id[9658].saldo_registrado==36
    if 5115 in por_id:
        assert por_id[5115].saldo_registrado==434 and por_id[5115].saldo_calculado==434
    if 1449 in por_id:assert por_id[1449].saldo_registrado==25
    if 8023 in por_id:assert por_id[8023].saldo_calculado==3
    if 7294 in por_id:assert por_id[7294].revision_documental["diferencia_con_cadena_previa"]==-18
    if 9764 in por_id:assert por_id[9764].ingresos==4
    if 6389 in por_id:assert por_id[6389].estado=="ANULADO_DOCUMENTO"
    corte=leer_corte(db)
    summary={"aplicadas":len(aplicados),"auditorias_movimientos":aud,"observaciones_articulos":mobs,
        "articulos_cotejados":len(ids),"movimientos_totales_conservados":cantidad+len(nuevos_ids),
        "filas_recuperadas":nuevos_ids,
        "originales_fotos_y_numeracion_sin_cambios":True,"plan_sha256":plan_sha,
        "estados":dict(Counter(m.estado for m in movimientos)),
        "perfil_analitica":corte["perfil"],"confirmado":confirmar,
        "limite":"Se aplicó el lote de ejemplos ampliados. El resto del histórico sigue en cotejo con los mismos criterios."}
    if confirmar:db.commit()
    else:db.rollback()
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ensayo",action="store_true")
    p.add_argument("--migrar",action="store_true")
    p.add_argument("--ejecutar",action="store_true")
    p.add_argument("--plan",type=Path,default=DEST/"plan_correcciones.json")
    args=p.parse_args()
    plan=json.loads(args.plan.read_text(encoding="utf-8"))
    if args.ensayo:
        from scripts.respaldo_recuperacion import nueva_copia
        backup=sorted((BACKEND/"backups").glob("respaldo_hil_*"))[-1]
        target,nombre,_=nueva_copia(backup,"hil"+datetime.now(UTC).strftime("%Y%m%d%H%M%S"),"activos_continuacion_qa_")
        with target.begin() as c:migrar(c)
        if args.plan.name!="plan_correcciones.json":
            with Session(target) as db:
                aplicar(db,json.loads((DEST/"plan_correcciones.json").read_text(encoding="utf-8")),confirmar=True)
        with Session(target) as db:report=aplicar(db,plan,confirmar=True)
        report["base_ensayo"]=nombre
        (DEST/("ensayo_"+args.plan.stem+".json")).write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    else:
        if args.migrar:
            with engine.begin() as c:
                c.execute(text("SET LOCAL lock_timeout='5s'"))
                c.execute(text("LOCK TABLE movimientos_kardex, activo IN SHARE ROW EXCLUSIVE MODE"))
                migrar(c)
        with Session(engine) as db:report=aplicar(db,plan,confirmar=args.ejecutar)
        if args.ejecutar:
            target=DEST/("resultado_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S")+".json")
            target.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="perfil_analitica"},ensure_ascii=False))

if __name__=="__main__":main()

