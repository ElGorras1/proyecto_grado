import argparse
import csv
import hashlib
import json

import httpx
import pytest
from PIL import Image

from scripts import importar_tanda as imp


def plan(tmp_path):
    (tmp_path / "originales").mkdir()
    (tmp_path / "_revision").mkdir()
    manifest = []
    items = []
    for i in (1, 2):
        p = tmp_path / "originales" / f"{i}.jpg"
        Image.new("RGB", (10, 10), color=(i, 0, 0)).save(p)
        manifest.append(
            dict(
                orden_captura=i,
                archivo_original=p.name,
                clasificacion="articulo_una_foto",
                articulo=i,
                bytes=p.stat().st_size,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            )
        )
        items.append(
            dict(
                numero=i,
                tanda=3,
                orden_inicial=i,
                orden_final=i,
                titulo=f"Titulo {i}",
                estado_titulo="LISTO",
                motivo_revision="",
                fotos_originales=p.name,
            )
        )
    for nombre, filas in [("manifest.csv", manifest), ("plan_carga.csv", items)]:
        with (tmp_path / nombre).open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=filas[0].keys())
            w.writeheader()
            w.writerows(filas)
    return argparse.Namespace(
        carpeta=tmp_path,
        tanda=3,
        ejecutar=True,
        sesion_local_desarrollo=True,
        usuario=None,
        api=imp.DEFAULT_API,
        pausa_segundos=120,
        reintentos=3,
        solo=None,
        max_articulos=None,
    )


class APIPrueba:
    def __init__(self, args):
        self.llamadas = []
        self.respuestas = []
        self.solicitudes = []
        self.siguiente = 30

    def close(self):
        pass

    def request(self, method, path, **kw):
        self.llamadas.append((method, path, kw))
        data = None
        if path == "/kardex/limites-carga":
            data = {"paginas": 20}
        elif path == "/kardex/tandas":
            data = {"tandas": [{"id": 3}]}
        elif path == "/kardex/articulos" and method == "GET":
            data = []
        elif path == "/kardex/articulos":
            self.siguiente += 1
            data = {"id": self.siguiente}
        elif path == "/kardex/solicitudes":
            data = self.solicitudes.pop(0) if self.solicitudes else []
        elif path.startswith("/kardex/historial/"):
            data = [{"lote_id": 90, "numero_pagina": 1}]
        elif path == "/kardex/upload-lote":
            data = self.respuestas.pop(0)
            if isinstance(data, Exception):
                raise data
        else:
            raise AssertionError("Operación inesperada: " + method + " " + path)
        return httpx.Response(
            200, json=data, request=httpx.Request(method, "http://localhost" + path)
        )


def instalar(monkeypatch, args):
    api = APIPrueba(args)
    monkeypatch.setattr(imp, "API", lambda _: api)
    monkeypatch.setattr(imp, "huella_item", lambda _: "a" * 64)
    pausas = []
    monkeypatch.setattr(imp, "esperar", lambda root, state, path, seg: pausas.append(seg))
    return api, pausas


def test_no_confirma_titulos_y_descansa_antes_del_siguiente(tmp_path, monkeypatch):
    args = plan(tmp_path)
    api, pausas = instalar(monkeypatch, args)
    api.respuestas = [
        dict(tanda=3, requiere_confirmacion=True, pendiente_id=8, diferencias=[{"pagina": 1}]),
        dict(tanda=3, lote_id=90),
    ]
    assert imp.ejecutar(args) == 0
    state = json.loads((tmp_path / "_revision/estado_importacion.json").read_text())
    assert state["articulos"]["1"]["estado"] == "revision_titulos"
    assert state["articulos"]["2"]["estado"] == "cargado"
    assert state["fase"] == "FINALIZADO"
    assert any(119 < p <= 120 for p in pausas)
    uploads = [kw for method, path, kw in api.llamadas if path.endswith("upload-lote")]
    assert all(kw["data"]["tanda"] == "3" for kw in uploads)
    assert not any("decision" in path for _, path, _ in api.llamadas)


def test_desconexion_recupera_solicitud_completada_sin_repetir_ocr(tmp_path, monkeypatch):
    args = plan(tmp_path)
    args.max_articulos = 1
    api, _ = instalar(monkeypatch, args)
    api.respuestas = [httpx.ReadTimeout("Conexión cerrada")]
    api.solicitudes = [[], [dict(id=7, huella="a" * 64, estado="COMPLETADO", tanda=3, lote_id=90)]]
    assert imp.ejecutar(args) == 0
    state = json.loads((tmp_path / "_revision/estado_importacion.json").read_text())
    assert state["articulos"]["1"]["estado"] == "cargado"
    assert len([c for c in api.llamadas if c[1].endswith("upload-lote")]) == 1
    assert state["fase"] == "PARCIAL"


def test_solicitud_procesando_detiene_sin_nuevo_post(tmp_path, monkeypatch):
    args = plan(tmp_path)
    api, _ = instalar(monkeypatch, args)
    api.solicitudes = [[dict(id=7, huella="a" * 64, estado="PROCESANDO", tanda=3, lote_id=None)]]
    with pytest.raises(RuntimeError, match="PROCESANDO"):
        imp.ejecutar(args)
    assert not any(c[1].endswith("upload-lote") for c in api.llamadas)
    state = json.loads((tmp_path / "_revision/estado_importacion.json").read_text())
    assert state["articulos"]["1"]["estado"] == "resultado_incierto"
    assert state["fase"] == "DETENIDO_POR_INCIDENTE"


def test_archivo_cambiado_rechazado_antes_de_crear_articulos(tmp_path, monkeypatch):
    plan(tmp_path)
    (tmp_path / "originales/1.jpg").write_bytes(b"alterado")
    with pytest.raises(AssertionError):
        imp.preparar_plan(tmp_path, 3)


def test_otro_importador_no_puede_tomar_el_bloqueo(tmp_path, monkeypatch):
    monkeypatch.setattr(imp, "BACKEND", tmp_path)
    with imp.importador_unico():
        with pytest.raises(RuntimeError, match="Otro importador"):
            with imp.importador_unico():
                pass


def test_descartados_y_divididos_no_se_vuelven_a_cargar(tmp_path, monkeypatch):
    args = plan(tmp_path)
    state = dict(version=2, tanda=3, articulos={
        "1": {"estado": "descartado", "motivo": "Decisión del usuario"},
        "2": {"estado": "dividido", "motivo": "Cargado como dos artículos"},
    })
    imp.save_state(args.carpeta / "_revision/estado_importacion.json", state)
    api, _ = instalar(monkeypatch, args)
    assert imp.ejecutar(args) == 0
    assert not any(method == "POST" for method, _, _ in api.llamadas)
    saved = json.loads((args.carpeta / "_revision/estado_importacion.json").read_text())
    assert saved["fase"] == "FINALIZADO"
    assert saved["articulos"]["1"]["estado"] == "descartado"
    assert saved["articulos"]["2"]["estado"] == "dividido"
