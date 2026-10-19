"""Importación secuencial de un plan revisado, reanudable y sin confirmar títulos.

Predeterminado: verifica archivos, sin escribir. Ejecutar con --ejecutar.
La sesión local de desarrollo usa una cuenta administrativa existente y activa;
no crea cuentas, no cambia contraseñas y nunca guarda ni imprime su token.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import time
from contextlib import ExitStack, contextmanager
from datetime import UTC, datetime
from pathlib import Path

if os.name == "nt":
    import msvcrt
else:
    import fcntl

import httpx
from PIL import Image

from scripts.importar_tanda2 import DEFAULT_API, leer_csv, log, save_state, sha256

BACKEND = Path(__file__).resolve().parents[1]
ESTADOS_PENDIENTES = {"revision_titulos", "revision_manual", "revision_catalogo"}
ESTADOS_RESUELTOS = {"descartado", "dividido"}


def preparar_plan(root: Path, tanda: int) -> list[dict]:
    manifest = leer_csv(root / "manifest.csv")
    plan = leer_csv(root / "plan_carga.csv")
    if not manifest or not plan:
        raise ValueError("El manifiesto y el plan no pueden estar vacíos")
    por_indice = {int(f["orden_captura"]): f for f in manifest}
    assert set(por_indice) == set(range(1, len(manifest) + 1))
    assert len(por_indice) == len(manifest)
    usados = set()
    titulos = {}
    resultado = []
    for fila in plan:
        inicio, fin = int(fila["orden_inicial"]), int(fila["orden_final"])
        assert int(fila["tanda"]) == tanda
        assert 1 <= inicio <= fin <= len(manifest)
        nombres = fila["fotos_originales"].split("|")
        assert len(nombres) == fin - inicio + 1
        assert fila["estado_titulo"] in {"LISTO", "REVISAR"} and fila["titulo"].strip()
        fotos = []
        for indice, nombre in zip(range(inicio, fin + 1), nombres):
            registro = por_indice[indice]
            assert indice not in usados and registro["clasificacion"] != "separador"
            assert registro["archivo_original"] == nombre
            assert int(registro["articulo"]) == int(fila["numero"])
            p = (root / "originales" / nombre).resolve(strict=True)
            assert p.is_relative_to((root / "originales").resolve())
            assert p.stat().st_size == int(registro["bytes"]) and sha256(p) == registro["sha256"]
            with Image.open(p) as img:
                assert img.format == "JPEG"
                img.verify()
            usados.add(indice)
            fotos.append(p)
        titulo = fila["titulo"].strip()
        if fila["estado_titulo"] == "LISTO":
            assert titulo.casefold() not in titulos, "Títulos listos repetidos: " + titulo
            titulos[titulo.casefold()] = inicio
        resultado.append(
            dict(
                numero=int(fila["numero"]),
                inicio=inicio,
                fin=fin,
                titulo=titulo,
                estado_titulo=fila["estado_titulo"],
                motivo_revision=fila.get("motivo_revision", ""),
                images=fotos,
            )
        )
    assert usados == {i for i, f in por_indice.items() if f["clasificacion"] != "separador"}
    assert len({i["numero"] for i in resultado}) == len(resultado)
    assert all(a["fin"] < b["inicio"] for a, b in zip(resultado, resultado[1:]))
    return resultado


@contextmanager
def importador_unico():
    """Bloqueo exclusivo del sistema operativo, también en contenedores Linux."""
    ruta = BACKEND / "logs" / "importacion_kardex.lock"
    ruta.parent.mkdir(exist_ok=True)
    with ruta.open("a+b") as f:
        if f.tell() == 0:
            f.write(b"0")
            f.flush()
        f.seek(0)
        try:
            if os.name == "nt":
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            raise RuntimeError("Otro importador tiene el bloqueo; no iniciar en paralelo") from e
        try:
            yield
        finally:
            f.seek(0)
            if os.name == "nt":
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


class API:
    def __init__(self, args):
        self.local = args.sesion_local_desarrollo
        if self.local and args.api.rstrip("/") != DEFAULT_API:
            raise RuntimeError("Sesión de desarrollo sólo permitida contra la API local")
        self.email = args.usuario
        self.password = None if self.local else getpass.getpass("Contraseña: ")
        if not self.local and not self.email:
            raise ValueError("Indica --usuario")
        self.client = httpx.Client(
            base_url=args.api, timeout=httpx.Timeout(connect=10, read=900, write=120, pool=10)
        )
        self.login_time = 0.0

    def login(self):
        if self.local:
            from app.core.config import settings
            from app.core.security import create_access_token
            from app.db.session import SessionLocal
            from app.models.rol import Rol
            from app.models.usuario import Usuario

            if settings.ENVIRONMENT != "development":
                raise RuntimeError("Sesión local no permitida fuera de desarrollo")
            with SessionLocal() as db:
                consulta = (
                    db.query(Usuario)
                    .join(Rol)
                    .filter(
                        Usuario.estado == "activo",
                        Rol.nombre == "Administrador",
                        Rol.estado == "activo",
                    )
                )
                if self.email:
                    consulta = consulta.filter(Usuario.email == self.email)
                usuario = consulta.order_by(Usuario.id).first()
                if usuario is None:
                    raise RuntimeError("No hay una cuenta administrativa activa")
                token = create_access_token(usuario.id)
                self.usuario_id = usuario.id
        else:
            r = self.client.post(
                "/auth/login", json={"email": self.email, "password": self.password}
            )
            r.raise_for_status()
            token = r.json()["access_token"]
        self.client.headers["Authorization"] = "Bearer " + token
        r = self.client.get("/auth/me")
        r.raise_for_status()
        if r.json().get("rol") not in {"Administrador", "Operador"}:
            raise RuntimeError("Se requiere una cuenta habilitada para escanear")
        self.login_time = time.monotonic()

    def request(self, method, path, **kwargs):
        if time.monotonic() - self.login_time > 20 * 60:
            self.login()
        r = self.client.request(method, path, **kwargs)
        if r.status_code == 401 and "files" not in kwargs:
            self.login()
            r = self.client.request(method, path, **kwargs)
        r.raise_for_status()
        return r

    def close(self):
        self.client.close()


def huella_item(item):
    from app.services.huella_lote import huella_de_paginas
    from app.services.validacion_carga import preparar_imagen

    return huella_de_paginas(
        [preparar_imagen(p.read_bytes(), "image/jpeg") for p in item["images"]]
    )


def verificar_lote(api, item, record, tanda, lote_id):
    filas = api.request(
        "GET", f"/kardex/historial/{record['articulo_id']}", params={"tanda": tanda}
    ).json()
    filas = [f for f in filas if f["lote_id"] == lote_id]
    if not filas or {f["numero_pagina"] for f in filas} != set(range(1, len(item["images"]) + 1)):
        raise RuntimeError(f"El lote {lote_id} no muestra todas las páginas esperadas")
    record.update(estado="cargado", lote_id=lote_id, movimientos=len(filas), tanda=tanda)


def reconciliar(api, item, record, tanda):
    solicitudes = api.request(
        "GET", "/kardex/solicitudes", params={"articulo_id": record["articulo_id"]}
    ).json()
    iguales = [s for s in solicitudes if s.get("huella") == record["huella"]]
    if len(iguales) > 1:
        raise RuntimeError("Más de una solicitud para la misma huella")
    if not iguales:
        return False
    s = iguales[0]
    record["solicitud_id"] = s["id"]
    if s["tanda"] != tanda:
        raise RuntimeError("La solicitud pertenece a otra tanda; revisar asociación")
    if s["estado"] == "COMPLETADO":
        verificar_lote(api, item, record, tanda, s["lote_id"])
        return True
    if s["estado"] == "PENDIENTE":
        record.update(estado="revision_titulos", pendiente_id=s["pendiente_id"])
        return True
    if s["estado"] == "PROCESANDO":
        record["estado"] = "resultado_incierto"
        raise RuntimeError("La solicitud sigue PROCESANDO; espera y comprueba antes de reintentar")
    if s["estado"] not in {"FALLIDO", "CANCELADO"}:
        raise RuntimeError("Estado de solicitud inesperado: " + s["estado"])
    return False


def esperar(root, state, state_path, segundos):
    if segundos <= 0:
        return
    limite = time.time() + segundos
    state.update(
        fase="DESCANSO", siguiente_carga_no_antes=datetime.fromtimestamp(limite, UTC).isoformat()
    )
    save_state(state_path, state)
    while time.time() < limite:
        if (root / "_revision/detener_despues_actual.flag").exists():
            raise InterruptedError("Pausa solicitada después del artículo actual")
        time.sleep(min(2, max(0, limite - time.time())))


def ejecutar(args):
    root = args.carpeta.resolve(strict=True)
    items = preparar_plan(root, args.tanda)
    print(
        f"Plan verificado: tanda {args.tanda}, {len(items)} artículos, "
        f"{sum(i['estado_titulo']=='LISTO' for i in items)} listos; "
        f"{sum(len(i['images']) for i in items)} fotos de Kárdex.",
        flush=True,
    )
    if not args.ejecutar:
        return 0
    if args.pausa_segundos < 120:
        raise ValueError("Mantén al menos 120 segundos entre artículos")
    state_path = root / "_revision/estado_importacion.json"
    state = (
        json.loads(state_path.read_text(encoding="utf-8"))
        if state_path.exists()
        else dict(version=2, tanda=args.tanda, articulos={})
    )
    if state["version"] != 2 or state["tanda"] != args.tanda:
        raise ValueError("Estado de otra tanda/versión")
    plan_hash = sha256(root / "plan_carga.csv")
    if state.get("plan_sha256", plan_hash) != plan_hash:
        raise ValueError("Cambió el plan de una ejecución anterior; revisar antes de reanudar")
    state.update(
        plan_sha256=plan_hash, total_articulos=len(items), pid=os.getpid(), fase="PREPARANDO"
    )
    api = API(args)
    intentados = 0
    try:
        limite = api.request("GET", "/kardex/limites-carga").json()
        for item in items:
            if len(item["images"]) > limite["paginas"]:
                raise ValueError("Un artículo supera el límite de páginas")
        tandas = api.request("GET", "/kardex/tandas").json()
        if args.tanda not in {t["id"] for t in tandas["tandas"]}:
            raise RuntimeError("La tanda solicitada no aparece en el sistema")
        for item in items:
            key = str(item["inicio"])
            record = state["articulos"].setdefault(key, {"estado": "pendiente"})
            nombres = [p.name for p in item["images"]]
            if (
                record.get("titulo", item["titulo"]) != item["titulo"]
                or record.get("fotos", nombres) != nombres
            ):
                raise ValueError("El estado del artículo no corresponde a las fotos del plan")
            record.update(titulo=item["titulo"], fotos=nombres, numero=item["numero"])
            if record.get("estado") == "cargado" or record.get("estado") in ESTADOS_PENDIENTES | ESTADOS_RESUELTOS:
                continue
            if item["estado_titulo"] == "REVISAR":
                record.update(estado="revision_manual", motivo=item["motivo_revision"])
                save_state(state_path, state)
                continue
            if args.solo and item["inicio"] not in args.solo:
                continue
            if args.max_articulos and intentados >= args.max_articulos:
                break
            if (root / "_revision/detener_despues_actual.flag").exists():
                raise InterruptedError("Pausa solicitada")
            if state.get("ultima_respuesta_en"):
                anterior = datetime.fromisoformat(state["ultima_respuesta_en"]).timestamp()
                esperar(
                    root, state, state_path, max(0, args.pausa_segundos - (time.time() - anterior))
                )
            state.update(fase="PROCESANDO", articulo_actual=key)
            save_state(state_path, state)
            log(
                root,
                f"INICIO {item['numero']}/{len(items)} foto {key}: "
                f"{item['titulo']} ({len(nombres)} página/s)",
            )
            if not record.get("articulo_id"):
                catalogo = api.request("GET", "/kardex/articulos").json()
                coincidencias = [
                    a
                    for a in catalogo
                    if a["nombre"].strip().casefold() == item["titulo"].casefold()
                ]
                if coincidencias:
                    record.update(
                        estado="revision_catalogo",
                        posibles_articulos=[a["id"] for a in coincidencias],
                        motivo="Título existente; no asociar sin revisar la evidencia",
                    )
                    save_state(state_path, state)
                    log(root, f"PENDIENTE_CATALOGO foto {key}")
                    continue
                # Guardar intención antes del POST: si su resultado es incierto,
                # una reanudación detecta el nombre existente y no crea un duplicado.
                record["estado"] = "creando_articulo"
                save_state(state_path, state)
                nuevo = api.request(
                    "POST", "/kardex/articulos", json={"nombre": item["titulo"]}
                ).json()
                record.update(articulo_id=nuevo["id"], estado="articulo_creado")
                save_state(state_path, state)
            if not record.get("huella"):
                record["huella"] = huella_item(item)
                save_state(state_path, state)
            if reconciliar(api, item, record, args.tanda):
                save_state(state_path, state)
                log(root, f"RECUPERADO foto {key}: {record['estado']}")
                continue
            intentados += 1
            for intento in range(1, args.reintentos + 1):
                record.update(estado="procesando", intento_local=intento)
                save_state(state_path, state)
                try:
                    with ExitStack() as stack:
                        files = [
                            ("archivos", (p.name, stack.enter_context(p.open("rb")), "image/jpeg"))
                            for p in item["images"]
                        ]
                        respuesta = api.request(
                            "POST",
                            "/kardex/upload-lote",
                            data={
                                "articulo_id": str(record["articulo_id"]),
                                "tanda": str(args.tanda),
                            },
                            files=files,
                        ).json()
                    state["ultima_respuesta_en"] = datetime.now(UTC).isoformat()
                    if respuesta["tanda"] != args.tanda:
                        raise RuntimeError("Respuesta de otra tanda")
                    if respuesta.get("requiere_confirmacion"):
                        record.update(
                            estado="revision_titulos",
                            pendiente_id=respuesta["pendiente_id"],
                            diferencias=respuesta.get("diferencias", []),
                        )
                        log(root, f"PENDIENTE_CONFIRMACION foto {key}")
                    else:
                        verificar_lote(api, item, record, args.tanda, respuesta["lote_id"])
                        log(
                            root,
                            f"CARGADO foto {key}: lote {record['lote_id']}, "
                            f"{record['movimientos']} movimientos",
                        )
                    save_state(state_path, state)
                    break
                except (httpx.HTTPError, RuntimeError) as error:
                    state["ultima_respuesta_en"] = datetime.now(UTC).isoformat()
                    record.update(estado="resultado_incierto", error=str(error)[:2000])
                    save_state(state_path, state)
                    # Nunca interpretar una desconexión como prueba de fallo del OCR.
                    if reconciliar(api, item, record, args.tanda):
                        save_state(state_path, state)
                        log(root, f"RECUPERADO foto {key}: {record['estado']}")
                        break
                    codigo = (
                        error.response.status_code
                        if isinstance(error, httpx.HTTPStatusError)
                        else None
                    )
                    if codigo == 422:
                        record["estado"] = "error_extraccion"
                        save_state(state_path, state)
                        log(root, f"ERROR_EXTRACCION foto {key}; continuar con el siguiente")
                        break
                    if codigo in {429, 500, 502, 503, 504} and intento < args.reintentos:
                        record["estado"] = "reintento_pendiente"
                        save_state(state_path, state)
                        log(root, f"REINTENTO foto {key} después del descanso, intento {intento+1}")
                        esperar(root, state, state_path, args.pausa_segundos * intento)
                        continue
                    record["estado"] = "error"
                    save_state(state_path, state)
                    raise
        completo = all(
            state["articulos"].get(str(i["inicio"]), {}).get("estado")
            in {"cargado", "error_extraccion"} | ESTADOS_PENDIENTES | ESTADOS_RESUELTOS
            for i in items
        )
        state.update(
            fase="FINALIZADO" if completo else "PARCIAL", terminado_en=datetime.now(UTC).isoformat()
        )
        save_state(state_path, state)
        conteos = {}
        for r in state["articulos"].values():
            conteos[r["estado"]] = conteos.get(r["estado"], 0) + 1
        log(root, "FIN " + json.dumps(conteos, ensure_ascii=False))
        return 0
    except InterruptedError as e:
        state.update(fase="PAUSADO", motivo=str(e))
        save_state(state_path, state)
        log(root, "PAUSADO: " + str(e))
        return 0
    except Exception as e:
        state.update(fase="DETENIDO_POR_INCIDENTE", error=str(e)[:2000])
        save_state(state_path, state)
        log(root, "DETENIDO: " + str(e))
        raise
    finally:
        api.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--carpeta", type=Path, required=True)
    p.add_argument("--tanda", type=int, required=True, choices=range(1, 10000))
    p.add_argument("--ejecutar", action="store_true")
    p.add_argument("--sesion-local-desarrollo", action="store_true")
    p.add_argument("--usuario")
    p.add_argument("--api", default=DEFAULT_API)
    p.add_argument("--pausa-segundos", type=int, default=120)
    p.add_argument("--reintentos", type=int, default=3)
    p.add_argument("--solo", type=int, nargs="+")
    p.add_argument("--max-articulos", type=int)
    args = p.parse_args()
    if args.ejecutar:
        with importador_unico():
            return ejecutar(args)
    return ejecutar(args)


if __name__ == "__main__":
    raise SystemExit(main())
