"""Review samples with labels independent of operational alert decisions."""

from collections import Counter
from random import Random

from sqlalchemy import or_, select

from app.models.analitica_operativa import ResultadoOperativo
from app.services.control_alertas import ORIGENES
from app.services.periodos import limites_gestion


def en_gestion(consulta, gestion):
    inicio, fin = limites_gestion(gestion)
    return consulta.filter(or_(*(
        getattr(ResultadoOperativo, fk).in_(
            select(tabla.id).where(tabla.registrado_en >= inicio, tabla.registrado_en < fin)
        )
        for tabla, fk in ORIGENES.values()
    )))


def muestrear(resultados, limite, semilla):
    con_alerta, sin_alerta = [], []
    for resultado in resultados:
        (con_alerta if resultado.alerta else sin_alerta).append(resultado)
    if not con_alerta or not sin_alerta:
        return []
    n = min(limite, len(resultados))
    cantidad_alertas = round(n * len(con_alerta) / len(resultados))
    cantidad_alertas = max(1, n - len(sin_alerta), min(cantidad_alertas, len(con_alerta), n - 1))
    rng = Random(semilla)
    muestra = rng.sample(con_alerta, cantidad_alertas) + rng.sample(sin_alerta, n - cantidad_alertas)
    rng.shuffle(muestra)
    return muestra


def resumen(casos):
    conteos = Counter(c.etiqueta for c in casos)
    pendientes = conteos[None]
    datos = dict(total=len(casos), pendientes=pendientes, indeterminados=conteos["INDETERMINADO"])
    if pendientes:
        return datos | {"metricas": None}
    matriz = Counter((c.etiqueta, c.prediccion) for c in casos)
    tp, fp = matriz["ANOMALO", True], matriz["NORMAL", True]
    fn, tn = matriz["ANOMALO", False], matriz["NORMAL", False]
    return datos | {"metricas": dict(
        verdaderos_positivos=tp, falsos_positivos=fp, falsos_negativos=fn, verdaderos_negativos=tn,
        clasificados=tp + fp + fn + tn,
        precision=tp / (tp + fp) if tp + fp else None,
        sensibilidad=tp / (tp + fn) if tp + fn else None,
        f1=2 * tp / (2 * tp + fp + fn) if tp + fn else None,
    )}
