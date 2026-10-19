"""Aplica los tres títulos de tanda 2 confirmados por el usuario el 07/10/2026.

Respalda PostgreSQL, plan y estado; no confirma los lotes OCR pendientes.
"""

import csv
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func

from app.db.session import SessionLocal, engine
from app.models.activos import Activo
from app.models.auditoria import AuditoriaSistema
from app.models.kardex import LotePendiente, MovimientoKardex
from scripts.importar_tanda2 import preparar_plan, load_state, save_state


ROOT = Path(r"C:\Users\LENOVO\OneDrive - Universidad Privada del Valle\Imágenes\Digitalizaciones\tanda_2_2026-10-07")
TITULOS = {
    1: 'ERASMO ZORZUELA',
    4: 'RAUL PRADA "DOGI"',
    101: 'FESTIVAL LUZ MILA PATIÑO 30 AÑOS "CD"',
}
PENDIENTE_1 = "5a3479a8-698b-48d5-a011-f83e21b6fe80"


def respaldo():
    marca = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    carpeta = Path("backups") / f"titulos_tanda2_{marca}"
    carpeta.mkdir(parents=True)
    shutil.copy2(ROOT / "plan_carga.csv", carpeta / "plan_carga.csv")
    shutil.copy2(ROOT / "_revision" / "estado_importacion.json",
                 carpeta / "estado_importacion.json")
    url = engine.url
    env = os.environ.copy()
    env["PGPASSWORD"] = url.password or ""
    pg = Path(os.environ.get("POSTGRES_BIN", r"C:\Program Files\PostgreSQL\18\bin"))
    subprocess.run([
        str(pg / "pg_dump.exe"), "-h", url.host or "localhost", "-p",
        str(url.port or 5432), "-U", url.username or "postgres",
        "-Fc", "-f", str(carpeta / "base.dump"), url.database,
    ], env=env, check=True)
    return carpeta


def main():
    plan_path = ROOT / "plan_carga.csv"
    with plan_path.open("r", encoding="utf-8-sig", newline="") as stream:
        lector = csv.DictReader(stream)
        campos = lector.fieldnames
        filas = list(lector)
    assert campos and len(filas) == 96
    elegidas = {int(f["orden_inicial"]): f for f in filas if int(f["orden_inicial"]) in TITULOS}
    assert set(elegidas) == set(TITULOS)
    for inicio, titulo in TITULOS.items():
        fila = elegidas[inicio]
        if fila["estado_titulo"] not in {"REVISAR", "LISTO"}:
            raise RuntimeError(f"Estado inesperado de foto {inicio}")
        if fila["estado_titulo"] == "LISTO" and fila["titulo"] != titulo:
            raise RuntimeError(f"Cambió un título ya aprobado: foto {inicio}")

    estado_path = ROOT / "_revision" / "estado_importacion.json"
    estado = load_state(estado_path)
    foto1 = estado["articulos"]["1"]
    if (foto1["articulo_id"] != 103 or foto1["estado"] != "revision_titulos"
            or foto1["pendiente_id"] != PENDIENTE_1):
        raise RuntimeError("La foto 1 ya no coincide con la revisión esperada")
    for inicio in (4, 101):
        if estado["articulos"].get(str(inicio), {}).get("articulo_id"):
            raise RuntimeError(f"La foto {inicio} ya tiene artículo asignado")

    with SessionLocal() as db:
        articulo = db.query(Activo).filter(Activo.id == 103).with_for_update().one()
        pendiente = db.get(LotePendiente, PENDIENTE_1)
        if not pendiente or pendiente.articulo_id != 103 or pendiente.estado != "PENDIENTE":
            raise RuntimeError("La revisión de título de la foto 1 cambió")
        if db.query(MovimientoKardex.id).filter_by(articulo_id=103).first():
            raise RuntimeError("El artículo 103 ya tiene movimientos")
        if db.query(Activo.id).filter(
            func.lower(Activo.nombre) == TITULOS[1].lower(), Activo.id != 103,
        ).first():
            raise RuntimeError("Ya existe otro artículo con el título confirmado")
        if articulo.nombre not in {"ERASMO ZORRILLA", TITULOS[1]}:
            raise RuntimeError("El nombre actual del artículo 103 cambió")

        carpeta = respaldo()
        anterior = articulo.nombre
        if anterior != TITULOS[1]:
            articulo.nombre = TITULOS[1]
            pendiente.extraccion = {
                **pendiente.extraccion,
                "articulo_nombre": TITULOS[1],
                "titulo_plan_previo": anterior,
                "titulo_confirmado_por_usuario": True,
            }
            db.add(AuditoriaSistema(
                usuario_id=None, accion="corregir_titulo_articulo",
                recurso="activo", recurso_id=103, resultado="exito",
                fecha_hora=datetime.now(UTC), ip_origen=None,
                detalle={"anterior": anterior, "confirmado": TITULOS[1],
                         "origen": "confirmación del usuario en este chat",
                         "pendiente_id": PENDIENTE_1},
            ))
            db.commit()

    for inicio, titulo in TITULOS.items():
        elegidas[inicio]["titulo"] = titulo
        elegidas[inicio]["estado_titulo"] = "LISTO"
    temporal = plan_path.with_suffix(".tmp")
    with temporal.open("w", encoding="utf-8-sig", newline="") as stream:
        escritor = csv.DictWriter(stream, fieldnames=campos, lineterminator="\r\n")
        escritor.writeheader()
        escritor.writerows(filas)
    os.replace(temporal, plan_path)
    foto1["titulo"] = TITULOS[1]
    save_state(estado_path, estado)
    revisados = {item["inicio"]: item for item in preparar_plan(ROOT)}
    assert all(revisados[inicio]["estado_titulo"] == "LISTO"
               for inicio in TITULOS)
    print(f"Respaldo: {carpeta.resolve()}")
    print("Títulos preparados. La foto 1 aún requiere decisión del lote; "
          "las fotos 4 y 101 requieren carga y revisión de extracción.")


if __name__ == "__main__":
    main()
