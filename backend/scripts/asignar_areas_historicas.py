"""Ensaya un plan congelado en una restauración y aplica clasificaciones inferidas.

No corrige el texto de AREA ni confirma equivalencias del catálogo.
Requiere el respaldo coherente y restaurado de la misma base.
"""
import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.kardex import MovimientoKardex
from app.models.auditoria import AuditoriaSistema
from app.services.areas_historicas import aplicar_asignacion, VERSION
from app.services.datos_analitica import leer_corte, seleccionar
from app.services.revision_documental import snapshot_revision
from app.services.tratamiento_hil import resumen_tratamiento
from scripts.respaldo_recuperacion import verificar_paquete, estado
from scripts.preparar_analitica import digest_tablas

BACKEND=Path(__file__).resolve().parents[1]


def auditar_preexistentes(c, maximo):
    filas=c.scalars(text("SELECT to_jsonb(t)::text FROM auditoria_sistema t WHERE id<=:m ORDER BY id"),{"m":maximo}).all()
    return hashlib.sha256("\n".join(filas).encode()).hexdigest()


def ejecutar(c, plan, sha):
    c.execute(text("SET LOCAL lock_timeout='5s'"))
    c.execute(text("SET LOCAL statement_timeout='60s'"))
    tablas=inspect(c).get_table_names()
    c.execute(text("LOCK TABLE "+", ".join(c.dialect.identifier_preparer.quote(t) for t in sorted(tablas))+
                   " IN SHARE ROW EXCLUSIVE MODE"))
    resto=[t for t in tablas if t not in {"movimientos_kardex","auditoria_sistema"}]
    otras=digest_tablas(c,resto)
    maximo=c.scalar(text("SELECT coalesce(max(id),0) FROM auditoria_sistema"))
    aud_prev=auditar_preexistentes(c,maximo)
    acciones={f["id"]:f for f in plan["acciones"] if f["propuesta"]["area"]}
    if not acciones:
        raise ValueError("Plan sin asignaciones")
    with Session(bind=c) as db:
        filas=db.query(MovimientoKardex).order_by(MovimientoKardex.id).all()
        antes={m.id:snapshot_revision(m) for m in filas}
        indice={m.id:m for m in filas}
        corte=leer_corte(db)
        ids_eligibles={f["id"] for f in seleccionar(corte["filas"])[0]}
        tratamientos={m.id:resumen_tratamiento(m) for m in filas if m.lote_id is not None and m.estado=="ACTIVO"}
        for f in plan["acciones"]:
            if snapshot_revision(indice[f["id"]])!=f["snapshot_antes"]:
                raise ValueError("La fila cambió desde el plan: "+str(f["id"]))
        cambios=[]
        now=datetime.now(UTC).isoformat()
        for mid,f in acciones.items():
            m=indice[mid]
            assert aplicar_asignacion(m,f["propuesta"],plan_sha256=sha,autor=plan["autor"],registrado_en=now)
            posterior=snapshot_revision(m)
            permitidos={"nodo_grafo","area_estado","requiere_auditoria_nodo","revision_documental"}
            assert {k:v for k,v in antes[mid].items() if k not in permitidos}=={k:v for k,v in posterior.items() if k not in permitidos}
            assert resumen_tratamiento(m)["estado"]=="CATEGORIZADO_CON_MARCA"
            db.add(AuditoriaSistema(accion="corregir_kardex_hil",recurso="movimientos_kardex",recurso_id=mid,
                resultado="exito",fecha_hora=datetime.now(UTC),usuario_id=None,
                detalle={"previo":antes[mid],"nuevo":posterior,"motivo":f["propuesta"]["motivo"],
                         "plan_sha256":sha,"autor_registro":plan["autor"],"tarea":"AREAS_HISTORICAS_CORRELACION"}))
            cambios.append({"id":mid,"literal":m.area,"area":f["propuesta"]["area"],"soporte":f["propuesta"]["soporte"]})
        db.flush()
        for m in filas:
            if m.id not in acciones:
                assert snapshot_revision(m)==antes[m.id]
                if m.id in tratamientos:
                    assert resumen_tratamiento(m)==tratamientos[m.id]
        despues=leer_corte(db)
        assert {f["id"] for f in seleccionar(despues["filas"])[0]}==ids_eligibles
        assert despues["perfil"]==corte["perfil"]
        assert digest_tablas(c,resto)==otras
        assert auditar_preexistentes(c,maximo)==aud_prev
        assert c.scalar(text("SELECT count(*) FROM auditoria_sistema WHERE id>:m"),{"m":maximo})==len(acciones)
        assert sum(t["estado"]=="REQUIERE_RECATEGORIZAR" for t in tratamientos.values() if t)==0
        return {"cambios":cambios,"auditorias_nuevas":len(cambios),"elegibles":len(ids_eligibles),
                "perfil_y_elegibilidad_conservados":True,"otras_tablas_inalteradas":True,
                "filas_ajenas_inalteradas":True,"lecturas_cantidades_fechas_saldos_conservados":True}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--plan",type=Path,required=True)
    p.add_argument("--respaldo",type=Path,required=True)
    p.add_argument("--aplicar",action="store_true")
    args=p.parse_args()
    planpath=args.plan.resolve(strict=True)
    respaldo=args.respaldo.resolve(strict=True)
    if not planpath.is_relative_to((BACKEND/"backups").resolve()) or not respaldo.is_relative_to((BACKEND/"backups").resolve()):
        raise ValueError("Plan o respaldo fuera de la carpeta técnica")
    raw=planpath.read_bytes();sha=hashlib.sha256(raw).hexdigest();plan=json.loads(raw)
    assert plan["version"]==VERSION
    manifiesto=verificar_paquete(respaldo)
    ver=json.loads((respaldo/"verificacion.json").read_text(encoding="utf-8"))
    nombre=ver["base_restaurada"]
    assert ver["resultado"]=="VERIFICADO" and re.fullmatch(r"activos_recuperacion_qa_[a-z0-9]+",nombre)
    qa=create_engine(engine.url.set(database=nombre))
    with qa.connect() as c:
        assert estado(c)==manifiesto["base"],"La copia QA cambió desde su restauración"
        c.rollback()
        with c.begin():
            ensayo=ejecutar(c,plan,sha)
    qa.dispose()
    resultado={"version":VERSION,"plan_sha256":sha,"respaldo":str(respaldo),"base_ensayo":nombre,
               "ensayo":"APROBADO","aplicado":False,"resultado":ensayo}
    (planpath.parent/"ensayo_asignacion.json").write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding="utf-8")
    if args.aplicar:
        with engine.begin() as c:
            # Se bloquean antes de comprobar el respaldo para impedir cambios concurrentes.
            nombres=inspect(c).get_table_names()
            c.execute(text("SET LOCAL lock_timeout='5s'"))
            c.execute(text("LOCK TABLE "+", ".join(c.dialect.identifier_preparer.quote(t) for t in sorted(nombres))+
                           " IN SHARE ROW EXCLUSIVE MODE"))
            assert estado(c)==manifiesto["base"],"La base cambió desde el respaldo"
            aplicado=ejecutar(c,plan,sha)
        resultado.update(aplicado=True,resultado=aplicado)
        (planpath.parent/"resultado_asignacion.json").write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(resultado,ensure_ascii=False))


if __name__=="__main__":
    main()
