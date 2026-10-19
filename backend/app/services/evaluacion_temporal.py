"""Cortes anuales sin entrenamiento con años futuros ni documentos compartidos."""

from collections import Counter, defaultdict
from copy import deepcopy

from app.services.datos_analitica import huella

CAMPOS_CONTENIDO = (
    "articulo_id",
    "fecha",
    "detalle",
    "referencia",
    "area",
    "ingresos",
    "salidas",
    "saldo_registrado",
)


def grupos_documentales(filas):
    padres = {f["lote_id"]: f["lote_id"] for f in filas}

    def raiz(x):
        while padres[x] != x:
            padres[x] = padres[padres[x]]
            x = padres[x]
        return x

    firmas = {}
    for f in filas:
        firma = huella({k: f[k] for k in CAMPOS_CONTENIDO})
        anterior = firmas.setdefault(firma, f["lote_id"])
        padres[raiz(f["lote_id"])] = raiz(anterior)
    grupos = defaultdict(list)
    for f in filas:
        grupos[raiz(f["lote_id"])].append(f)
    return list(grupos.values())


def preparar_corte_temporal(corte, gestion_evaluacion):
    corte = deepcopy(corte)
    descartados = {i for ids in corte["exclusiones"].values() for i in ids}
    filas = [f for f in corte["filas"] if f["id"] not in descartados]
    calibracion = gestion_evaluacion - 1
    partes, purga, grupos_por_parte = {}, defaultdict(list), Counter()
    for grupo in grupos_documentales(filas):
        gestiones = {int(f["fecha"][:4]) for f in grupo}
        if max(gestiones) < calibracion:
            parte = "entrenamiento"
        elif gestiones == {calibracion}:
            parte = "calibracion"
        elif gestiones == {gestion_evaluacion}:
            parte = "evaluacion"
        else:
            razon = (
                "posteriores_al_ano_evaluado"
                if min(gestiones) > gestion_evaluacion
                else "grupos_que_cruzan_fronteras_temporales"
            )
            purga[razon].extend(f["id"] for f in grupo)
            continue
        grupos_por_parte[parte] += 1
        partes.update({str(f["id"]): parte for f in grupo})
    conteos = Counter(partes.values())
    faltantes = {
        p: max(0, minimo - conteos[p])
        for p, minimo in (("entrenamiento", 50), ("calibracion", 20), ("evaluacion", 20))
    }
    suficiente = not any(faltantes.values()) and sum(grupos_por_parte.values()) >= 5
    resumen = dict(
        gestion_evaluacion=gestion_evaluacion,
        gestion_calibracion=calibracion,
        entrenamiento_hasta=calibracion - 1,
        particiones={p: conteos[p] for p in ("entrenamiento", "calibracion", "evaluacion")},
        grupos=dict(grupos_por_parte),
        purga={k: len(v) for k, v in purga.items()},
        faltantes=faltantes,
        suficiente=suficiente,
        advertencia="Comparación cronológica por grupos documentales completos. Los lotes "
        "que mezclan períodos y sus duplicados se excluyen íntegramente. "
        "La elegibilidad no equivale a revisión humana ni cobertura física completa.",
    )
    corte["exclusiones"].update(dict(purga))
    corte["particiones_temporales"] = partes
    corte["temporal"] = resumen
    perfil = corte["perfil"]
    perfil["elegibles"] = len(partes)
    perfil["temporal"] = resumen
    perfil["exclusiones"] = {k: len(v) for k, v in corte["exclusiones"].items()}
    for cobertura in perfil["por_gestion"].values():
        cobertura["elegibles"] = 0
    for cobertura in perfil["por_articulo"].values():
        cobertura["elegibles"] = 0
    for f in filas:
        if str(f["id"]) in partes:
            perfil["por_gestion"][f["fecha"][:4]]["elegibles"] += 1
            clave = (
                f["articulo_id"]
                if f["articulo_id"] in perfil["por_articulo"]
                else str(f["articulo_id"])
            )
            perfil["por_articulo"][clave]["elegibles"] += 1
    return corte
