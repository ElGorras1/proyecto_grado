"""Modelo provisional para registros digitales reales; el OCR nunca se incorpora."""

import hashlib
import io
import logging
import math
import pickle
import re
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from uuid import UUID
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest

from app.models.activos import Activo
from app.models.analitica_operativa import ModeloOperativo, ResultadoOperativo
from app.models.inventario import AperturaInventario
from app.models.kardex import MovimientoKardex
from app.services.control_alertas import ORIGENES, operacion
from app.services.datos_analitica import huella

ARTEFACTOS = Path(__file__).resolve().parents[2] / ".analytics_operativa"
MINIMO = 125
MIN_DIAS = 14
log = logging.getLogger(__name__)
_cache = {}
ERRORES_MODELO = (
    ValueError,
    OSError,
    KeyError,
    EOFError,
    TypeError,
    AttributeError,
    IndexError,
    OverflowError,
    pickle.UnpicklingError,
)


def fecha(valor):
    d = datetime.fromisoformat(valor) if isinstance(valor, str) else valor
    return d if d.tzinfo else d.replace(tzinfo=UTC)


def capturar(db):
    from app.models.rectificacion_logistica import RectificacionLogistica
    rectificadas = set()
    for r in db.query(RectificacionLogistica):
        rectificadas.add(("CUSTODIA" if r.clase == "ENTREGA" else r.clase,
                         r.transferencia_id if r.clase == "TRANSFERENCIA" else r.custodia_id if r.clase == "ENTREGA" else r.evento_custodia_id))
    filas, omitidos = [], defaultdict(int)
    nombres = {a.id: a.nombre for a in db.query(Activo)}
    corregidos = {
        i
        for (i,) in db.query(MovimientoKardex.corrige_movimiento_id).filter(
            MovimientoKardex.corrige_movimiento_id.isnot(None)
        )
    }
    for clase, (modelo, _) in ORIGENES.items():
        q = db.query(modelo)
        if clase == "MOVIMIENTO":
            q = q.join(
                AperturaInventario, AperturaInventario.articulo_id == modelo.articulo_id
            ).filter(
                modelo.lote_id.is_(None),
                modelo.id > AperturaInventario.ultimo_moderno_id,
                modelo.estado == "ACTIVO",
                modelo.corrige_movimiento_id.is_(None),
            )
        for f in q:
            if (clase, f.id) in rectificadas:
                omitidos["rectificados_logisticos"] += 1
                continue
            if clase == "MOVIMIENTO" and f.id in corregidos:
                omitidos["rectificados"] += 1
                continue
            if re.search(r"\b(prueba|test|dummy|demo)\b", nombres.get(f.articulo_id, ""), re.I):
                omitidos["articulos_de_prueba"] += 1
                continue
            if not f.registrado_en or not f.ocurrido_en or not f.encargado_id:
                omitidos["procedencia_incompleta"] += 1
                continue
            dato = operacion(f, clase)
            if dato["cantidad"] <= 0 or fecha(dato["ocurrido_en"]) > fecha(dato["registrado_en"]):
                omitidos["cantidad_o_fecha_invalida"] += 1
                continue
            dato["articulo"] = nombres[f.articulo_id]
            filas.append(dato)
    filas.sort(key=lambda f: (fecha(f["registrado_en"]), f["clase"], f["id"]))
    return filas, dict(omitidos)


def dividir(filas):
    n = int(len(filas) * 0.8)
    if n < 100 or len(filas) - n < 25:
        raise ValueError(
            "Se necesitan 125 operaciones reales: al menos 100 anteriores y 25 de calibración."
        )
    if (fecha(filas[-1]["registrado_en"]) - fecha(filas[0]["registrado_en"])).days < MIN_DIAS:
        raise ValueError(
            "Se necesitan registros de al menos catorce días para modelar hora y día semanal."
        )
    frontera = fecha(filas[n]["registrado_en"])
    train = [f for f in filas if fecha(f["registrado_en"]) < frontera]
    cal = [f for f in filas if fecha(f["registrado_en"]) >= frontera]
    if len(train) < 100 or len(cal) < 25:
        raise ValueError(
            "No hay suficientes registros con fechas separadas para entrenamiento y calibración."
        )
    return train, cal


def referencias(filas):
    valores = defaultdict(list)
    for f in filas:
        valores[(f["clase"], f["tipo"], f["direccion"])].append(f["cantidad"])
    return {
        k: (float(median(v)), max(1.0, float(median(abs(x - median(v)) for x in v))), len(v))
        for k, v in valores.items()
    }


def transformar(filas, refs):
    matriz, contextos = [], []
    for f in filas:
        cantidad = f["cantidad"]
        m, mad, n = refs.get((f["clase"], f["tipo"], f["direccion"]), (1.0, 1.0, 0))
        ocurrido = fecha(f["ocurrido_en"]).astimezone(ZoneInfo("America/La_Paz"))
        registrado = fecha(f["registrado_en"])
        hora = ocurrido.hour + ocurrido.minute / 60
        demora = max(0.0, (registrado - ocurrido).total_seconds() / 3600)
        saldo = f["saldo_registrado"]
        if f["clase"] == "MOVIMIENTO":
            previo = saldo + cantidad if f["direccion"] == "SALIDA" else saldo - cantidad
        elif f["clase"] == "EVENTO_CUSTODIA" and f["tipo"] == "VENTA":
            previo = saldo + cantidad
        else:
            previo = saldo
        matriz.append(
            [
                math.log1p(cantidad),
                math.log((cantidad + 1) / (m + 1)),
                math.log1p(abs(cantidad - m) / mad),
                cantidad / (max(previo, 0) + 1),
                math.sin(2 * math.pi * hora / 24),
                math.cos(2 * math.pi * hora / 24),
                ocurrido.weekday() / 6,
                math.log1p(demora),
                int(n == 0),
                *[int(f["clase"] == clase) for clase in ORIGENES],
            ]
        )
        contextos.append(
            dict(
                cantidad=cantidad,
                mediana=m,
                referencias=n,
                saldo_institucional_previo=previo,
                hora_local=hora,
                demora_horas=demora,
                sin_referencia=n == 0,
            )
        )
    return np.asarray(matriz), contextos


def calcular(filas, config):
    train, cal = dividir(filas)
    refs = referencias(train)
    x, _ = transformar(train, refs)
    if np.unique(x, axis=0).shape[0] < 2:
        raise ValueError("Las operaciones de entrenamiento no tienen variación suficiente.")
    forest = IsolationForest(
        n_estimators=config["arboles"],
        max_samples=min(256, len(train)),
        random_state=config["semilla"],
        contamination="auto",
        n_jobs=1,
    ).fit(x)
    xc, _ = transformar(cal, refs)
    scores = -forest.score_samples(xc)
    umbral = float(np.quantile(scores, 1 - config["porcentaje_revision"] / 100))
    deps = dict(
        python=sys.version.split()[0], scikit_learn=sklearn.__version__, numpy=np.__version__
    )
    metricas = dict(
        entrenamiento=len(train),
        calibracion=len(cal),
        version_variables=1,
        corte_registro=train[-1]["registrado_en"],
        primer_registro_calibracion=cal[0]["registrado_en"],
        dependencias=deps,
        precision=None,
        estado_validacion="PROVISIONAL_SIN_EVALUACION_HUMANA",
        advertencia="Calibración cronológica; aún no hay una evaluación humana independiente. "
        "La puntuación representa rareza. Los controles de stock siguen aplicándose.",
    )
    return (
        dict(
            modelo=forest,
            referencias=refs,
            umbral=umbral,
            configuracion=config,
            metricas=metricas,
            huella=huella(filas),
        ),
        metricas,
    )


def cargar(m, directorio=None):
    if str(UUID(m.id)) != m.id or not re.fullmatch(r"[0-9a-f]{64}", m.artefacto_sha256 or ""):
        raise ValueError("Identidad del archivo operativo inválida")
    carpeta = Path(directorio or ARTEFACTOS).resolve()
    ruta = carpeta / (m.id + ".joblib")
    if ruta.is_symlink() or ruta.resolve().parent != carpeta or not ruta.is_file():
        raise ValueError("Archivo operativo privado no disponible")
    contenido = ruta.read_bytes()
    if hashlib.sha256(contenido).hexdigest() != m.artefacto_sha256:
        raise ValueError("Hash del modelo operativo incorrecto")
    deps = dict(
        python=sys.version.split()[0], scikit_learn=sklearn.__version__, numpy=np.__version__
    )
    if deps != (m.metricas or {}).get("dependencias"):
        raise ValueError("Versiones incompatibles para el modelo operativo")
    key = (m.id, m.artefacto_sha256)
    if key not in _cache:
        _cache.clear()
        _cache[key] = joblib.load(io.BytesIO(contenido))
    a = _cache[key]
    if (
        a["huella"] != m.huella
        or huella(m.corte) != m.huella
        or a["umbral"] != m.umbral
        or a["configuracion"] != m.configuracion
        or a["metricas"] != m.metricas
        or a["modelo"].n_features_in_ != 13
    ):
        raise ValueError("Metadatos operativos inconsistentes")
    return a


def puntuar_nueva(db, fila, clase):
    """Dentro de la transacción: una puntuación por modelo/origen. Sin alterar stock."""
    if clase == "MOVIMIENTO" and (
        fila.lote_id is not None or fila.corrige_movimiento_id is not None
    ):
        return None
    if not fila.registrado_en or not fila.ocurrido_en or not fila.encargado_id:
        return None
    m = db.query(ModeloOperativo).filter_by(activo=1, estado="COMPLETADO").first()
    if not m:
        return None
    dato = operacion(fila, clase)
    try:
        if fecha(dato["registrado_en"]) <= max(fecha(d["registrado_en"]) for d in m.corte):
            return None
        # La inferencia prospectiva nunca reevalúa registros que formaron parte del corte.
        if any(d["clase"] == clase and d["id"] == fila.id for d in m.corte):
            return None
    except ERRORES_MODELO:
        log.exception("Corte operativo inválido; controles determinísticos permanecen activos")
        return None
    if fila.id is None:
        db.flush()
        dato = operacion(fila, clase)
    recurso = clase + ":" + str(fila.id)
    previo = db.query(ResultadoOperativo).filter_by(modelo_id=m.id, recurso=recurso).first()
    if previo:
        return previo
    try:
        a = cargar(m)
        x, contexto = transformar([dato], a["referencias"])
        score = float(-a["modelo"].score_samples(x)[0])
        if not math.isfinite(score):
            raise ValueError("Puntuación operativa inválida")
    except ERRORES_MODELO:
        log.exception(
            "Modelo operativo no disponible; controles determinísticos permanecen activos"
        )
        return None
    resultado = ResultadoOperativo(
        modelo_id=m.id,
        recurso=recurso,
        articulo_id=fila.articulo_id,
        **{ORIGENES[clase][1]: fila.id},
        snapshot=dato,
        contexto=contexto[0],
        score=score,
        alerta=score > m.umbral,
    )
    db.add(resultado)
    if resultado.alerta:
        fila.alertas_control = [
            *(fila.alertas_control or []),
            dict(
                codigo="ISOLATION_OPERATIVO",
                nivel="medio",
                mensaje="La operación es inusual respecto del modelo digital activo. "
                "Requiere revisión documental.",
                datos=dict(
                    modelo_id=m.id,
                    score=score,
                    umbral=m.umbral,
                    contexto=contexto[0],
                    estado_validacion="PROVISIONAL",
                ),
            ),
        ]
    db.flush()
    return resultado
