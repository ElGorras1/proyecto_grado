"""Auditoría local de lectura: resultados congelados y reproducción sin entrenar."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import text

from app.db.session import SessionLocal
from app.models.auditoria_historica import ModeloHistorico, ResultadoHistorico
from app.services.datos_analitica import huella, leer_corte
from app.services.evaluacion_analitica import diagnosticar, reproducir_artefacto
from app.services.trabajador_analitica import ARTEFACTOS


def informe(db, modelo):
    rs = db.query(ResultadoHistorico).filter_by(modelo_id=modelo.id).all()
    resultado = diagnosticar(modelo, rs)
    resultado["artefacto"] = reproducir_artefacto(modelo, rs, ARTEFACTOS)
    resultado["reproduccion_artefacto"] = resultado["artefacto"]["estado"]
    actual = leer_corte(db, modelo.configuracion["excluir_articulos"])
    excluidos = {i for ids in actual["exclusiones"].values() for i in ids}
    actuales = {f["id"]: f for f in actual["filas"] if f["id"] not in excluidos}
    congelados = {r.movimiento_id: r.snapshot for r in rs}
    resultado["datos_actuales"] = dict(
        historicos_activos=actual["perfil"]["historicos_activos"],
        elegibles=len(actuales),
        exclusiones=actual["perfil"]["exclusiones"],
        datos_cambiaron=huella(actual["filas"]) != modelo.huella,
        elegibles_sin_resultado=len(set(actuales) - set(congelados)),
        resultados_ya_no_elegibles=len(set(congelados) - set(actuales)),
        resultados_con_datos_distintos=sum(
            actuales[i] != congelados[i] for i in set(actuales) & set(congelados)
        ),
    )
    grupos = dict(
        modelo=set((modelo.metricas or {}).get("top_evaluacion", [])),
        regla=set((modelo.metricas or {}).get("top_regla", [])),
        control={r.movimiento_id for r in rs if r.muestra_control},
    )
    resultado["muestra_revision"] = [
        dict(
            resultado_id=r.id,
            movimiento_id=r.movimiento_id,
            articulo=r.snapshot["articulo"],
            fecha=r.snapshot["fecha"],
            selecciones=[g for g, ids in grupos.items() if r.movimiento_id in ids],
            estado_revision=r.estado_revision,
            etiqueta=r.etiqueta,
        )
        for r in sorted(rs, key=lambda r: r.movimiento_id)
        if any(r.movimiento_id in ids for ids in grupos.values())
    ]
    resultado["generado_en"] = datetime.now(UTC).isoformat()
    return resultado


def markdown(r):
    c, a = r["cobertura"], r["datos_actuales"]
    lineas = [
        "# Evaluación independiente de Isolation Forest",
        "",
        f"Modelo: `{r['modelo_id']}`. Fecha UTC: {r['generado_en']}.",
        "",
        f"Integridad de resultados: **{r['estado']}**. "
        f"Reproducción del archivo privado: **{r['reproduccion_artefacto']}**.",
        "",
        "Esta comprobación no entrenó otro modelo ni registró conclusiones humanas.",
        "",
        f"Se verificaron {c['evaluados']} resultados: "
        + ", ".join(f"{n} de {p}" for p, n in c["particiones"].items())
        + ".",
        "",
        f"{c['sin_referencia_propia']}/{c['evaluacion']} de evaluación "
        f"({c['porcentaje_sin_referencia']:.1f}%) carecen de referencia propia "
        "de artículo/dirección.",
        "",
        "## Comprobaciones",
        "",
        "| Comprobación | Estado | Evidencia |",
        "|---|---|---|",
    ]
    for v in r["comprobaciones"] + r["artefacto"]["comprobaciones"]:
        lineas.append(f"| {v['titulo']} | {v['estado']} | {v['detalle'].replace('|', '/')} |")
    lineas += [
        "",
        "## Revisión humana pendiente",
        "",
        "| Selección | Conclusiones | Pendientes | Proporción relevante |",
        "|---|---:|---:|---|",
    ]
    for nombre in ("modelo", "regla", "control"):
        v = r["evaluacion"][nombre]
        valor = "Pendiente" if v["precision_at_k"] is None else f"{100 * v['precision_at_k']:.1f}%"
        lineas.append(
            f"| {nombre} | {v['revisados_concluyentes']}/{v['k']} | {v['pendientes']} | {valor} |"
        )
    lineas += [
        "",
        f"Son {len(r['muestra_revision'])} movimientos distintos entre las tres selecciones.",
        "",
        "Revisarlos en **Analítica y auditoría histórica → Evaluación y límites del modelo**. "
        "Los accesos a cada selección conservan su ranking y muestran sus evidencias.",
        "",
        "Error documental y No concluyente no cuentan como Legítimo. Reabrir un resultado "
        "vuelve a dejar pendiente la métrica. El control mide proporción relevante, no recall.",
        "",
        "## Corte y datos disponibles actualmente",
        "",
        f"Actualmente: {a['historicos_activos']} históricos activos y "
        f"{a['elegibles']} candidatos elegibles.",
        "",
        f"Hay {a['elegibles_sin_resultado']} candidatos actuales sin resultado de esta versión; "
        f"{a['resultados_ya_no_elegibles']} resultados ya no son elegibles y "
        f"{a['resultados_con_datos_distintos']} resultados elegibles tienen "
        "datos actuales distintos.",
        "",
        "La versión conserva su corte anterior. Esta evaluación no incorpora nuevas cargas.",
        "",
        "## Límites y siguiente revisión",
        "",
        "La integridad y estabilidad no demuestran precisión, detección de fraude ni cobertura "
        "completa. Sigue faltando aproximadamente 30–40% del archivo físico según la estimación "
        "del usuario; todavía no existe un porcentaje físico verificado.",
        "",
        "La comparación entre años, la validación de umbrales con auditores y el análisis de "
        "movimientos actuales requieren sus respectivas tareas. No se calculan recall, AUC "
        "ni exactitud porque no hay una población etiquetada independiente.",
        "",
        "## Referencias para la revisión",
        "",
        "| Movimiento | Artículo | Fecha | Selecciones | Estado |",
        "|---:|---|---|---|---|",
    ]
    for v in r["muestra_revision"]:
        nombre = v["articulo"].replace("|", "/").replace("\n", " ")
        lineas.append(
            f"| {v['movimiento_id']} | {nombre} | {v['fecha']} | "
            f"{', '.join(v['selecciones'])} | {v['estado_revision']} |"
        )
    return "\n".join(lineas) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", required=True, type=UUID)
    parser.add_argument("--salida", type=Path, default=Path("backups/evaluacion_analitica"))
    args = parser.parse_args()
    with SessionLocal() as db:
        # El servidor PostgreSQL impide escrituras, incluso accidentales, en toda la auditoría.
        if db.bind.dialect.name == "postgresql":
            db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        modelo = db.get(ModeloHistorico, str(args.modelo))
        if not modelo or modelo.estado != "COMPLETADO":
            raise SystemExit("Selecciona una versión existente y completada.")
        r = informe(db, modelo)
    args.salida.mkdir(parents=True, exist_ok=True)
    nombre = f"evaluacion_{args.modelo}_{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}"
    j, m = args.salida / (nombre + ".json"), args.salida / (nombre + ".md")
    j.write_text(json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    m.write_text(markdown(r), encoding="utf-8")
    print(
        json.dumps(
            dict(
                modelo_id=r["modelo_id"],
                estado=r["estado"],
                artefacto=r["reproduccion_artefacto"],
                resultados=r["cobertura"]["evaluados"],
                revision=r["evaluacion"],
                datos_actuales=r["datos_actuales"],
                informe=str(m.resolve()),
                json=str(j.resolve()),
            ),
            ensure_ascii=False,
        )
    )
    if r["estado"] != "CONSISTENTE" or r["reproduccion_artefacto"] != "CONSISTENTE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
