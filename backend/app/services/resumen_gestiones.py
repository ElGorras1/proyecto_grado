"""Cobertura de puntuación del corte conservado; no entrena ni confirma anomalías."""

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.auditoria_historica import ModeloHistorico, ResultadoHistorico


def resumir_gestiones(db: Session, modelo: ModeloHistorico):
    cobertura = (modelo.corte.get("perfil") or {}).get("por_gestion") or {}
    filas = (
        db.query(
            ResultadoHistorico.gestion,
            func.count(ResultadoHistorico.id),
            func.sum(case((ResultadoHistorico.alerta.is_(True), 1), else_=0)),
            func.count(func.distinct(ResultadoHistorico.articulo_id)),
            func.sum(case((ResultadoHistorico.particion == "evaluacion", 1), else_=0)),
        )
        .filter(ResultadoHistorico.modelo_id == modelo.id)
        .group_by(ResultadoHistorico.gestion)
        .all()
    )
    puntuadas = {str(g): (n, a, articulos, reservadas) for g, n, a, articulos, reservadas in filas}
    gestiones = []
    claves = set(cobertura) | set(puntuadas)
    for gestion in sorted(
        claves, key=lambda g: (g.isdecimal(), int(g) if g.isdecimal() else 0), reverse=True
    ):
        origen = cobertura.get(gestion, {})
        disponibles = int(origen.get("disponibles", 0))
        elegibles = int(origen.get("elegibles", 0))
        analizados, alertas, articulos, reservadas = puntuadas.get(gestion, (0, 0, 0, 0))
        if analizados > elegibles or elegibles > disponibles:
            estado = "REVISAR_COBERTURA"
        elif elegibles == 0:
            estado = "SIN_ELEGIBLES"
        elif analizados == elegibles:
            estado = "PUNTUACION_COMPLETA"
        elif analizados:
            estado = "PUNTUACION_PARCIAL"
        else:
            estado = "SIN_RESULTADOS"
        gestiones.append(
            dict(
                gestion=gestion,
                documentales=disponibles,
                elegibles=elegibles,
                analizados=int(analizados),
                alertas=int(alertas),
                articulos=int(articulos),
                evaluacion_reservada=int(reservadas),
                no_elegibles=max(0, disponibles - elegibles),
                elegibles_sin_puntuar=max(0, elegibles - analizados),
                estado=estado,
            )
        )
    return dict(
        modelo_id=modelo.id,
        estado_modelo=modelo.estado,
        modo=modelo.configuracion.get("modo", "RETROSPECTIVO"),
        gestiones=gestiones,
        totales={
            campo: sum(f[campo] for f in gestiones)
            for campo in (
                "documentales",
                "elegibles",
                "analizados",
                "alertas",
                "evaluacion_reservada",
                "no_elegibles",
                "elegibles_sin_puntuar",
            )
        },
        alcance=(
            "Puntajes de la versión seleccionada agrupados por fecha documental. "
            "No son modelos independientes por año ni anomalías confirmadas. "
            "Los no elegibles conservan sus exclusiones y no se consideran normales."
        ),
    )
