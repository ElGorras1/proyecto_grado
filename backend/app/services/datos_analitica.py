"""Cortes reproducibles y elegibilidad conservadora, sin escrituras al Kárdex."""

import hashlib
import json
import re
from collections import Counter, defaultdict

from app.models.activos import Activo
from app.models.kardex import MovimientoKardex
from app.services.calidad_kardex import tipos_alerta

CAMPOS = (
    "id",
    "articulo_id",
    "lote_id",
    "numero_pagina",
    "orden_fila",
    "detalle",
    "referencia",
    "area",
    "nodo_grafo",
    "ingresos",
    "salidas",
    "saldo_registrado",
    "estado",
    "fecha_estado",
    "tiene_error_saldo",
    "tiene_error_fecha",
    "area_estado",
    "referencia_estado",
    "requiere_auditoria_nodo",
    "requiere_auditoria_referencia",
    "ruta_imagen_respaldo",
    "revision_documental",
    "orden_pagina_validado",
)


def huella(valor):
    return hashlib.sha256(
        json.dumps(
            valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def snapshot(m, a):
    dato = {k: getattr(m, k) for k in CAMPOS}
    dato.update(
        fecha=m.fecha_movimiento.isoformat() if m.fecha_movimiento else None,
        fecha_original=m.fecha_original.isoformat() if m.fecha_original else None,
        articulo=a.nombre,
        codigo=a.codigo,
        observacion_articulo_hil=a.observacion_hil,
        alertas_hil=tipos_alerta(m),
    )
    for campo in ("fecha_documental_texto", "fecha_precision"):
        if getattr(m, campo, None) is not None:
            dato[campo] = getattr(m, campo)
    return dato


def leer_corte(db, excluir_articulos=()):
    # Una única sentencia proporciona una fotografía MVCC coherente en PostgreSQL.
    filas = [
        snapshot(m, a)
        for m, a in db.query(MovimientoKardex, Activo)
        .join(Activo, Activo.id == MovimientoKardex.articulo_id)
        .order_by(MovimientoKardex.id)
        .all()
    ]
    elegibles, exclusiones = seleccionar(filas, excluir_articulos)
    cobertura = defaultdict(lambda: {"disponibles": 0, "elegibles": 0})
    articulos = defaultdict(lambda: {"disponibles": 0, "elegibles": 0})
    ids = {f["id"] for f in elegibles}
    for f in filas:
        if f["lote_id"] is not None and f["estado"] == "ACTIVO":
            rev = f.get("revision_documental") or {}
            gestion = f["fecha"][:4] if f["fecha"] and f["fecha_estado"] != "ESTIMADA_HIL" and rev.get("origen_fecha") not in {"HIPOTESIS", "SECUENCIA_AJUSTADA"} else "SIN_GESTION_CONFIRMADA"
            cobertura[gestion]["disponibles"] += 1
            cobertura[gestion]["elegibles"] += int(f["id"] in ids)
            articulos[f["articulo_id"]]["disponibles"] += 1
            articulos[f["articulo_id"]]["elegibles"] += int(f["id"] in ids)
            articulos[f["articulo_id"]]["nombre"] = f["articulo"]
    perfil = {
        "total": len(filas),
        "historicos_activos": sum(v["disponibles"] for v in cobertura.values()),
        "elegibles": len(elegibles),
        "exclusiones": {k: len(v) for k, v in exclusiones.items()},
        "por_gestion": dict(sorted(cobertura.items())),
        "por_articulo": dict(articulos),
        "advertencia": (
            "Cobertura del archivo físico desconocida. Sin alertas HIL no "
            "significa validación humana integral."
        ),
    }
    return {"filas": filas, "perfil": perfil, "exclusiones": exclusiones}


def seleccionar(filas, excluir_articulos=()):
    posiciones = Counter(
        (f["articulo_id"], f["lote_id"], f["numero_pagina"], f["orden_fila"])
        for f in filas
        if f["lote_id"] is not None
        and f["estado"] == "ACTIVO"
        and f["numero_pagina"] is not None
        and f["orden_fila"] is not None
    )
    excluidas = defaultdict(list)
    elegibles = []
    for f in filas:
        i, s = f["ingresos"] or 0, f["salidas"] or 0
        posicion = (f["articulo_id"], f["lote_id"], f["numero_pagina"], f["orden_fila"])
        if f["estado"] != "ACTIVO":
            razon = "anulados"
        elif f["lote_id"] is None:
            razon = "modernos"
        elif not f.get("fecha"):
            razon = "fecha_no_documentada"
        elif (f.get("observacion_articulo_hil") or {}).get("excluir_entrenamiento"):
            razon = "articulos_observados_hil"
        elif (f.get("revision_documental") or {}).get("origen_cantidades") == "HIPOTESIS":
            razon = "cantidad_hipotetica_hil"
        elif (f.get("revision_documental") or {}).get("origen_fecha") in ("HIPOTESIS", "SECUENCIA_AJUSTADA"):
            razon = "fecha_inferida_hil"
        elif (f.get("revision_documental") or {}).get("origen_saldo") == "HIPOTESIS":
            razon = "saldo_hipotetico_hil"
        elif (f.get("revision_documental") or {}).get("origen_saldo_base") == "HIPOTESIS":
            razon = "base_hipotetica_hil"
        elif f["articulo_id"] in excluir_articulos or re.search(
            r"\b(prueba|test|dummy|demo)\b", f["articulo"] + " " + f["codigo"], re.I
        ):
            razon = "articulos_excluidos_o_prueba"
        elif f["alertas_hil"]:
            razon = "pendientes_hil"
        elif i < 0 or s < 0 or (i > 0) == (s > 0):
            razon = "cantidades_sin_direccion_unica"
        elif posiciones[posicion] > 1:
            razon = "posicion_fisica_duplicada"
        elif not f["ruta_imagen_respaldo"] or f["numero_pagina"] is None or f["orden_fila"] is None:
            razon = "sin_procedencia_completa"
        else:
            elegibles.append(f)
            continue
        excluidas[razon].append(f["id"])
    return elegibles, dict(excluidas)
