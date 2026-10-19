"""Carga secuencial y reanudable de Kárdex ya fotografiados en la tanda 2.

El modo predeterminado sólo verifica el plan. Para escribir en el sistema hay
que indicar --ejecutar. Nunca confirma automáticamente encabezados distintos.
"""

from __future__ import annotations

import argparse
import ast
import csv
import getpass
import hashlib
import json
import os
import sys
import time
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

import httpx
from PIL import Image


DEFAULT_API = "http://127.0.0.1:8000/api/v1"


def leer_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def preparar_plan(root: Path) -> list[dict]:
    manifest = leer_csv(root / "manifest.csv")
    plan = leer_csv(root / "plan_carga.csv")
    assert len(manifest) == 166 and len(plan) == 96
    by_index = {int(row["orden_captura"]): row for row in manifest}
    assert len(by_index) == 166
    used = set()
    prepared = []
    for row in plan:
        start, end = int(row["orden_inicial"]), int(row["orden_final"])
        assert 1 <= start <= end <= 166
        names = row["fotos_originales"].split("|")
        assert len(names) == end - start + 1
        images = []
        for index, name in zip(range(start, end + 1), names):
            entry = by_index[index]
            assert index not in used and entry["clasificacion"] != "separador"
            assert entry["archivo_original"] == name
            if index != start:
                assert entry["clasificacion"] == "articulo_varias_fotos"
            used.add(index)
            path = root / "originales" / name
            assert path.is_file(), path
            assert path.stat().st_size == int(entry["bytes"]), path
            assert sha256(path) == entry["sha256"], path
            with Image.open(path) as image:
                assert image.format == "JPEG", path
                image.verify()
            images.append(path)
        assert row["estado_titulo"] in {"LISTO", "REVISAR"}
        assert row["titulo"].strip()
        prepared.append({"numero": int(row["numero"]), "inicio": start,
                         "fin": end, "titulo": row["titulo"].strip(),
                         "estado_titulo": row["estado_titulo"], "images": images})
    assert len(used) == 127
    assert len({item["inicio"] for item in prepared}) == 96
    assert all(prepared[i]["inicio"] < prepared[i + 1]["inicio"]
               for i in range(len(prepared) - 1))
    return prepared


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "articulos": {}}
    state = json.loads(path.read_text(encoding="utf-8"))
    assert state["version"] == 1
    return state


def dev_credentials() -> tuple[str, str]:
    """Lee las credenciales de semilla sólo para este servidor de desarrollo."""
    seed = Path(__file__).with_name("seed_admin.py")
    module = ast.parse(seed.read_text(encoding="utf-8"))
    email = password = None
    for node in ast.walk(module):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if any(isinstance(t, ast.Name) and t.id == "email" for t in node.targets):
                email = node.value.value
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "hash_password" and node.args
                and isinstance(node.args[0], ast.Constant)):
            password = node.args[0].value
    assert isinstance(email, str) and isinstance(password, str)
    return email, password


class API:
    def __init__(self, base: str, email: str, password: str) -> None:
        self.client = httpx.Client(base_url=base,
                                   timeout=httpx.Timeout(connect=10, read=900, write=120, pool=10))
        self.email, self.password = email, password
        self.login_time = 0.0

    def close(self) -> None:
        self.client.close()

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        if time.monotonic() - self.login_time > 20 * 60:
            self.login()
        response = self.client.request(method, path, **kwargs)
        if response.status_code == 401 and "files" not in kwargs:
            self.login()
            response = self.client.request(method, path, **kwargs)
        response.raise_for_status()
        return response

    def login(self) -> None:
        response = self.client.post("/auth/login", json={"email": self.email,
                                                          "password": self.password}, timeout=15)
        response.raise_for_status()
        token = response.json()["access_token"]
        self.client.headers["Authorization"] = f"Bearer {token}"
        self.login_time = time.monotonic()
        role = self.client.get("/auth/me", timeout=15).json().get("rol")
        if role not in {"Administrador", "Operador"}:
            raise RuntimeError(f"La cuenta tiene rol {role}; se requiere Administrador u Operador")


def log(root: Path, message: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {message}"
    print(line, flush=True)
    with (root / "_revision" / "importacion.log").open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")


def create_or_resume(api: API, item: dict, record: dict, state: dict,
                     state_path: Path) -> int:
    if record.get("articulo_id"):
        return int(record["articulo_id"])
    catalog = api.request("GET", "/kardex/articulos").json()
    matches = [article for article in catalog
               if article["nombre"].strip().casefold() == item["titulo"].casefold()]
    if matches:
        raise RuntimeError(f"Ya existe un artículo con ese título: {item['titulo']}. "
                           "Revisar antes de asociar imágenes.")
    created = api.request("POST", "/kardex/articulos",
                          json={"nombre": item["titulo"]}).json()
    record.update(articulo_id=created["id"], estado="articulo_creado",
                  titulo=item["titulo"],
                  fotos=[path.name for path in item["images"]])
    save_state(state_path, state)
    return int(created["id"])


def upload(api: API, item: dict, article_id: int) -> dict:
    with ExitStack() as stack:
        files = [("archivos", (path.name, stack.enter_context(path.open("rb")), "image/jpeg"))
                 for path in item["images"]]
        return api.request("POST", "/kardex/upload-lote",
                           data={"articulo_id": str(article_id), "tanda": "2"}, files=files).json()


def verify_lot(api: API, article_id: int, lot_id: int, page_count: int) -> int:
    rows = api.request("GET", f"/kardex/historial/{article_id}",
                       params={"tanda": 2}).json()
    in_lot = [row for row in rows if row["lote_id"] == lot_id]
    pages = {row["numero_pagina"] for row in in_lot}
    if not in_lot or pages != set(range(1, page_count + 1)):
        raise RuntimeError(f"El lote {lot_id} no muestra todas sus páginas en el historial")
    return len(in_lot)


def run(args: argparse.Namespace) -> int:
    root = args.carpeta.resolve()
    items = preparar_plan(root)
    ready = [item for item in items if item["estado_titulo"] == "LISTO"]
    review = [item for item in items if item["estado_titulo"] == "REVISAR"]
    print(f"Plan verificado: {len(items)} artículos, {len(ready)} listos, "
          f"{len(review)} con título para revisar; 127 fotos útiles.")
    print("Por revisar:", ", ".join(str(item["inicio"]) for item in review))
    if not args.ejecutar:
        print("Simulación terminada. No se escribió en el sistema.")
        return 0

    if args.credenciales_desarrollo:
        if args.api.rstrip("/") != DEFAULT_API:
            raise RuntimeError("Credenciales de desarrollo sólo admitidas para la API local")
        email, password = dev_credentials()
    else:
        email = args.usuario or input("Correo del Operador/Administrador: ").strip()
        password = getpass.getpass("Contraseña (no se guarda): ")
    state_path = root / "_revision" / "estado_importacion.json"
    state = load_state(state_path)
    api = API(args.api, email, password)
    attempted = 0
    try:
        tandas = api.request("GET", "/kardex/tandas").json()
        if 2 not in {t["id"] for t in tandas["tandas"]}:
            raise RuntimeError("La API no permite consultar/cargar tanda 2")
        for item in items:
            if args.solo and item["inicio"] not in args.solo:
                continue
            key = str(item["inicio"])
            record = state["articulos"].setdefault(key, {})
            if record.get("estado") == "cargado":
                continue
            if item["estado_titulo"] == "REVISAR":
                log(root, f"PENDIENTE_TITULO foto {key}: {item['titulo']}")
                continue
            if record.get("estado") == "revision_titulos":
                log(root, f"PENDIENTE_CONFIRMACION foto {key}, artículo {record['articulo_id']}")
                continue
            if record.get("titulo") and record["titulo"] != item["titulo"]:
                raise RuntimeError(f"Cambió el título de un artículo ya creado: foto {key}")
            if record.get("fotos") and record["fotos"] != [p.name for p in item["images"]]:
                raise RuntimeError(f"Cambió la agrupación de un artículo ya creado: foto {key}")
            if args.max_articulos and attempted >= args.max_articulos:
                break
            attempted += 1
            log(root, f"INICIO {item['numero']}/{len(items)} foto {key}: "
                f"{item['titulo']} ({len(item['images'])} página/s)")
            article_id = create_or_resume(api, item, record, state, state_path)
            log(root, f"ARTICULO_CREADO_O_REANUDADO foto {key}: id {article_id}")
            try:
                for intento in range(1, 4):
                    try:
                        result = upload(api, item, article_id)
                        break
                    except httpx.HTTPStatusError as exc:
                        # El backend devuelve HTTP 500 si Gemini está saturado o
                        # se corta su conexión TLS. La solicitud fallida queda
                        # reintentable; la huella evita duplicar un lote guardado.
                        detalle = exc.response.text
                        temporal = (exc.response.status_code == 500
                                    and ("503 unavailable" in detalle.lower()
                                         or "ssleoferror" in detalle.lower()
                                         or "timed out" in detalle.lower()
                                         or "timeout" in detalle.lower()))
                        if not temporal or intento == 3:
                            raise
                        espera = max(args.pausa_segundos, 90) * intento
                        log(root, f"FALLO_IA_TRANSITORIO foto {key}: reintento {intento}/2 "
                            f"en {espera} segundos")
                        time.sleep(espera)
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                detail = exc.response.text[:1000]
                record.update(estado="error_extraccion" if status == 422 else "error_http",
                              error=f"HTTP {status}: {detail}")
                save_state(state_path, state)
                log(root, f"ERROR foto {key}: HTTP {status}; artículo {article_id}")
                if status == 422:
                    time.sleep(args.pausa_segundos)
                    continue
                return 2
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                record.update(estado="resultado_incierto", error=str(exc))
                save_state(state_path, state)
                log(root, f"RESULTADO_INCIERTO foto {key}: reanudar con las mismas fotos")
                return 3
            if result.get("requiere_confirmacion"):
                record.update(estado="revision_titulos",
                              pendiente_id=result["pendiente_id"],
                              diferencias=result.get("diferencias", []))
                save_state(state_path, state)
                log(root, f"REVISION_TITULOS foto {key}: id {result['pendiente_id']}")
            else:
                lot_id = int(result["lote_id"])
                if result.get("tanda") != 2:
                    raise RuntimeError(f"El lote {lot_id} no quedó en tanda 2")
                movements = verify_lot(api, article_id, lot_id, len(item["images"]))
                record.update(estado="cargado", lote_id=lot_id,
                              movimientos=movements, error=None)
                save_state(state_path, state)
                log(root, f"CARGADO foto {key}: lote {lot_id}, "
                    f"{movements} movimientos, tanda 2")
            if args.pausa_segundos and not (args.max_articulos and attempted >= args.max_articulos):
                time.sleep(args.pausa_segundos)
    finally:
        api.close()
    print(f"Terminó esta ejecución. Intentados: {attempted}. "
          f"Estado: {state_path}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("carpeta", type=Path, help="Carpeta tanda_2_2026-10-07")
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("--ejecutar", action="store_true")
    parser.add_argument("--usuario")
    parser.add_argument("--credenciales-desarrollo", action="store_true")
    parser.add_argument("--pausa-segundos", type=int, default=90)
    parser.add_argument("--max-articulos", type=int, default=0)
    parser.add_argument("--solo", type=int, nargs="*", default=[])
    args = parser.parse_args()
    if args.pausa_segundos < 0 or args.max_articulos < 0:
        parser.error("La pausa y el máximo no pueden ser negativos")
    try:
        raise SystemExit(run(args))
    except (AssertionError, OSError, ValueError, RuntimeError, httpx.HTTPError) as exc:
        print(f"Detenido: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
