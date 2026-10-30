"""C01: corrige solo nodos históricos cuyo catálogo declara una operación.

Uso: --preparar; después --respaldo RUTA --aplicar.
Ensaya en la restauración verificada y reconcilia antes de aplicar.
No reescribe la columna AREA ni reentrena modelos.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import UTC,datetime
import hashlib,json,re
from pathlib import Path
from sqlalchemy import create_engine,inspect,text
from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.kardex import MovimientoKardex as M
from app.models.auditoria import AuditoriaSistema
from app.services.clasificador_nodos import clasificar_movimiento,AREA_NO_APLICA
from app.services.calidad_kardex import tipos_alerta
from app.services.datos_analitica import leer_corte,seleccionar
from app.services.revision_documental import snapshot_revision
from app.services.tratamiento_hil import huella_datos,resumen_tratamiento
from scripts.preparar_analitica import digest_tablas
from scripts.respaldo_recuperacion import verificar_paquete,estado

BACKEND=Path(__file__).resolve().parents[1]
OUT=BACKEND/"backups/c01_operaciones_catalogo_20261029"
IDS={432,4272,4398,4721,5050,5540,7313}
AUTOR="Codex, por instrucción del titular de completar C01, una tarea por vez"

def guardar(nombre,obj):
 OUT.mkdir(exist_ok=True,parents=True)
 (OUT/nombre).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")


def preparar():
 with engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
  c.execute(text("SET TRANSACTION READ ONLY"))
  with Session(bind=c) as db:
   nombres=set(c.scalars(text("SELECT nombre_oficial FROM catalogo_areas WHERE tipo='operacion'")))
   filas=db.query(M).filter(M.lote_id.isnot(None),M.estado=="ACTIVO",M.nodo_grafo.in_(["Área: "+n for n in nombres])).order_by(M.id).all()
   if {m.id for m in filas}!=IDS:
    raise ValueError("El conjunto observado cambió; revisar antes de regenerar el plan")
   acciones=[]
   for m in filas:
    clas=clasificar_movimiento(m.detalle,m.referencia,m.area,m.ingresos,m.salidas,db)
    assert clas.nodo_grafo=="Salida: Ventas" and clas.area_estado==AREA_NO_APLICA and not clas.requiere_auditoria_nodo
    acciones.append({"id":m.id,"antes":snapshot_revision(m),"tratamiento_antes":resumen_tratamiento(m),
      "cambios":{"nodo_grafo":clas.nodo_grafo,"area_estado":clas.area_estado,"requiere_auditoria_nodo":False},
      "foto_sha256":hashlib.sha256((BACKEND/m.ruta_imagen_respaldo.replace("\\","/")).read_bytes()).hexdigest()})
   plan={"tarea":"C01","version":1,"fecha":"2026-10-29","autor":AUTOR,
    "motivo":"El catálogo define Ventas como operación. La columna AREA del papel se conserva; el nodo se corrige a Salida: Ventas y su estado a NO_APLICA.",
    "acciones":acciones}
   guardar("plan.json",plan)
   print(json.dumps({"objetivos":len(acciones),"tratamientos_previos":dict(Counter(a["tratamiento_antes"]["estado"] for a in acciones))},ensure_ascii=False))


def aud_antigua(c,maximo):
 filas=c.scalars(text("SELECT to_jsonb(t)::text FROM auditoria_sistema t WHERE id<=:m ORDER BY id"),{"m":maximo}).all()
 return hashlib.sha256("\n".join(filas).encode()).hexdigest()


def aplicar_filas(c,plan,sha):
 c.execute(text("SET LOCAL lock_timeout='5s'"));c.execute(text("SET LOCAL statement_timeout='60s'"))
 tablas=inspect(c).get_table_names()
 c.execute(text("LOCK TABLE "+", ".join(c.dialect.identifier_preparer.quote(t) for t in sorted(tablas))+" IN SHARE ROW EXCLUSIVE MODE"))
 otras=[t for t in tablas if t not in {"movimientos_kardex","auditoria_sistema"}]
 hashes=digest_tablas(c,otras)
 maximo=c.scalar(text("SELECT coalesce(max(id),0) FROM auditoria_sistema"))
 previa_aud=aud_antigua(c,maximo)
 with Session(bind=c) as db:
  movimientos=db.query(M).order_by(M.id).all()
  antes={m.id:snapshot_revision(m) for m in movimientos};indice={m.id:m for m in movimientos}
  tratamientos={m.id:resumen_tratamiento(m) for m in movimientos if m.lote_id is not None}
  corte=leer_corte(db);elegibles={f["id"] for f in seleccionar(corte["filas"])[0]}
  cambios=[]
  assert {a["id"] for a in plan["acciones"]}==IDS
  for a in plan["acciones"]:
   m=indice[a["id"]]
   assert snapshot_revision(m)==a["antes"],f"Cambió la fila {m.id}"
   assert resumen_tratamiento(m)==a["tratamiento_antes"]
   foto=BACKEND/m.ruta_imagen_respaldo.replace("\\","/")
   assert hashlib.sha256(foto.read_bytes()).hexdigest()==a["foto_sha256"]
   clas=clasificar_movimiento(m.detalle,m.referencia,m.area,m.ingresos,m.salidas,db)
   assert a["cambios"]=={"nodo_grafo":clas.nodo_grafo,"area_estado":clas.area_estado,"requiere_auditoria_nodo":clas.requiere_auditoria_nodo}
   avisos=tipos_alerta(m)
   for k,v in a["cambios"].items():setattr(m,k,v)
   assert tipos_alerta(m)==avisos
   if tratamientos[m.id]["estado"]=="CATEGORIZADO_CON_MARCA":
    revision=deepcopy(m.revision_documental)
    registro=revision["tratamiento_hil"]
    registro["huella_datos"]=huella_datos(m)
    m.revision_documental=revision
   assert resumen_tratamiento(m)==tratamientos[m.id]
   despues=snapshot_revision(m)
   permitidos={"nodo_grafo","area_estado","requiere_auditoria_nodo"}
   if tratamientos[m.id]["estado"]=="CATEGORIZADO_CON_MARCA":permitidos.add("revision_documental")
   assert {k:v for k,v in antes[m.id].items() if k not in permitidos}=={k:v for k,v in despues.items() if k not in permitidos}
   db.add(AuditoriaSistema(accion="corregir_kardex_hil",recurso="movimientos_kardex",recurso_id=m.id,
    resultado="exito",fecha_hora=datetime.now(UTC),usuario_id=None,
    detalle={"tarea":"C01","autor_registro":AUTOR,"motivo":plan["motivo"],"plan_sha256":sha,
             "previo":antes[m.id],"nuevo":despues,"foto_sha256":a["foto_sha256"]}))
   cambios.append({"id":m.id,"articulo_id":m.articulo_id,"area_literal":m.area,"antes":antes[m.id]["nodo_grafo"],
                   "despues":m.nodo_grafo,"afecta_proximo_corte_elegible":m.id in elegibles})
  db.flush()
  for m in movimientos:
   if m.id not in IDS:assert snapshot_revision(m)==antes[m.id]
   if m.id in tratamientos:assert resumen_tratamiento(m)==tratamientos[m.id]
  actual=leer_corte(db)
  assert actual["perfil"]==corte["perfil"]
  assert {f["id"] for f in seleccionar(actual["filas"])[0]}==elegibles
  assert digest_tablas(c,otras)==hashes and aud_antigua(c,maximo)==previa_aud
  assert c.scalar(text("SELECT count(*) FROM auditoria_sistema WHERE id>:m"),{"m":maximo})==len(IDS)
  assert db.query(M).filter(M.nodo_grafo=="Área: Ventas",M.estado=="ACTIVO",M.lote_id.isnot(None)).count()==0
  return {"cambios":cambios,"auditorias":len(cambios),"elegibles":len(elegibles),
   "otras_filas_y_tablas_inalteradas":True,"tratamientos_conservados":True,"cantidades_fechas_lecturas_saldos_conservados":True,
   "modelos_resultados_y_cortes_congelados_inalterados":True}


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--preparar",action="store_true")
 p.add_argument("--respaldo",type=Path)
 p.add_argument("--aplicar",action="store_true")
 args=p.parse_args()
 if args.preparar:
  if args.aplicar:raise ValueError("Preparar y aplicar son etapas separadas")
  preparar();return
 if not args.respaldo:raise ValueError("Indica el respaldo restaurado")
 raw=(OUT/"plan.json").read_bytes();plan=json.loads(raw);sha=hashlib.sha256(raw).hexdigest()
 assert plan["tarea"]=="C01" and plan["version"]==1
 respaldo=args.respaldo.resolve(strict=True)
 assert respaldo.is_relative_to((BACKEND/"backups").resolve())
 manifiesto=verificar_paquete(respaldo)
 cfg=json.loads((respaldo/"verificacion.json").read_text(encoding="utf-8"));nombre=cfg["base_restaurada"]
 assert cfg["resultado"]=="VERIFICADO" and re.fullmatch(r"activos_recuperacion_qa_[a-z0-9]+",nombre)
 copia=create_engine(engine.url.set(database=nombre))
 with copia.begin() as c:
  assert estado(c)==manifiesto["base"],"La copia cambió desde el respaldo"
  ensayo=aplicar_filas(c,plan,sha)
 copia.dispose()
 reporte={"tarea":"C01","plan_sha256":sha,"respaldo":str(respaldo),"base_ensayo":nombre,"ensayo":"APROBADO","aplicado":False,"resultado":ensayo}
 guardar("ensayo.json",reporte)
 if args.aplicar:
  with engine.begin() as c:
   c.execute(text("SET LOCAL lock_timeout='5s'"))
   tablas=inspect(c).get_table_names()
   c.execute(text("LOCK TABLE "+", ".join(c.dialect.identifier_preparer.quote(t) for t in sorted(tablas))+" IN SHARE ROW EXCLUSIVE MODE"))
   assert estado(c)==manifiesto["base"],"La instalación cambió desde el respaldo"
   aplicado=aplicar_filas(c,plan,sha)
  reporte.update(aplicado=True,resultado=aplicado)
  guardar("resultado.json",reporte)
 print(json.dumps(reporte,ensure_ascii=False))


if __name__=="__main__":main()
