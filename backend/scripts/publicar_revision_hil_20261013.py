"""Publica un expediente local; solo consulta la BD y copia fuentes sin alterarlas."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import text
from app.db.session import engine
from scripts.catalogo_revision_hil_20261013 import CASOS
from scripts.recopilar_revision_hil import digest

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

def verify_database(meta):
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as db:
        with db.begin():
            db.execute(text("SET TRANSACTION READ ONLY"))
            rows = [dict(r) for r in db.execute(text("""
                SELECT m.*, a.nombre AS articulo_nombre, l.tanda
                FROM movimientos_kardex m JOIN activo a ON a.id=m.articulo_id
                LEFT JOIN lotes_carga l ON l.id=m.lote_id
                ORDER BY m.articulo_id,m.lote_id NULLS LAST,m.numero_pagina NULLS LAST,
                         m.orden_fila NULLS LAST,m.id
            """)).mappings()]
            tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name")).scalars().all()
            quote = db.dialect.identifier_preparer.quote
            counts = {t: db.execute(text("SELECT count(*) FROM " + quote(t))).scalar_one() for t in tables}
            schema = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    raw = json.loads(json.dumps(rows, ensure_ascii=False, default=str))
    return {
        "comprobado_en": datetime.now(ZoneInfo("America/La_Paz")).isoformat(),
        "modo": "REPEATABLE READ / READ ONLY",
        "filas": len(raw),
        "huella_inicial": meta["huella_filas"],
        "huella_final": digest(raw),
        "movimientos_sin_cambios": digest(raw) == meta["huella_filas"],
        "conteos_44_tablas_sin_cambios": counts == meta["conteos_tablas"],
        "schema_sin_cambios": schema == meta["schema"],
        "alcance": "Comparación de contenido de todos los movimientos (incluidos títulos y tandas) y de conteos de las tablas; no se afirma comparación de contenido de todas las demás tablas.",
        "conteos_finales": counts,
    }

def prepare_notes(audit, pages):
    initial = json.loads((audit / "cotejo_visual.json").read_text(encoding="utf-8"))
    notes = {n["pagina"]: dict(n) for n in initial}
    extra = dict(json.loads((audit / "observaciones_sin_avisos.json").read_text(encoding="utf-8")))
    for p in pages:
        if p["id"] not in notes:
            notes[p["id"]] = {
                "pagina": p["id"], "nivel": "INSPECCION_HOJA_COMPLETA_ATLAS",
                "tipos_observados": [],
                "observacion": extra.get(p["id"], "Inspección general de la hoja completa sin un hallazgo adicional destacado en esta pasada. No equivale a validación de cada campo; todas sus filas y la fotografía están incluidas para el cotejo posterior."),
                "datos_institucionales_modificados": False,
            }
    rectifications = {
        "L0027-P02": "El cotejo ampliado distingue dos casos: FIL 1026 muestra 1-08-11 y guarda 2011-08-11 (día OCR incorrecto); COMPRA TRONO 1034 muestra 7-2-11, no 7-2-12. Su retroceso frente a diciembre de 2011 está escrito en el papel y no se debe corregir automáticamente a 2012.",
        "L0094-P03": "Cotejo ampliado: el desplazamiento afecta cantidades y saldos. 5101 Lib. Amigos guarda salida3/saldo495, pero la foto muestra salida10/saldo573; 5102 Chuymampi guarda salida75/saldo490 y la foto muestra salida3/saldo570. También hay inconsistencias y rectificaciones manuscritas propias. Revisar bloque completo; último saldo visible434 frente a digital573.",
    }
    for key, value in rectifications.items():
        notes[key]["observacion_atlas_inicial"] = notes[key]["observacion"]
        notes[key]["observacion"] = value
        notes[key]["rectificacion_por_cotejo_ampliado"] = True
    for p in pages:
        p["cotejo"] = notes[p["id"]]
        p["estado_cotejo_visual"] = "PRIMERA_INSPECCION_COMPLETA_PENDIENTE_CRITERIO"
    assert len(notes) == len(pages) == 693
    return list(notes.values())

def markdown(data, output, audit, check):
    s = data["resumen"]
    lines = [
        "# Revisión documental de movimientos y criterios HIL · 13/10/2026", "",
        "Estado: recopilación de ejemplos terminada; criterios humanos pendientes; ninguna corrección institucional aplicada.", "",
        "El usuario pidió revisar las filas con errores y también las anteriores y posteriores de la misma hoja, agrupar tipos con ejemplos, y esperar sus instrucciones para corregir casos equivalentes. Este documento registra esa fase.", "",
        f"Expediente navegable sin conexión: [Abrir expediente]({(output / 'index.html').as_posix()}). Conserva junta la carpeta completa, incluido el subdirectorio fotos.", "",
        "## Corte y alcance", "",
        f"- Corte de Bolivia: {s['corte_bolivia']}.",
        "- 11.896 registros congelados en el respaldo, de los cuales 11.887 son movimientos históricos activos incluidos en el visor.",
        "- 693 fotografías referenciadas inspeccionadas como hojas completas en atlas. Se ampliaron ejemplos representativos para distinguir lectura OCR e inconsistencia de la fuente.",
        "- 1.378 filas distintas tienen avisos existentes en 470 hojas; no son 1.378 errores confirmados.",
        "- Revisión inicial ampliada: 482 hojas, 9.822 filas y 8.444 filas vecinas sin avisos. Se añadieron las otras 211 hojas para buscar problemas que no dispararon alarmas.",
        "- Avisos por campo: saldo 395, fecha 516, área 554 y referencia 15. Hay solapamientos; su suma no es el total de filas distintas.",
        "- 23 familias de ejemplos, 23 criterios pendientes, 0 cambios aplicados y 0 criterios aprobados.",
        "- La inspección de hoja completa no certifica cada carácter ni garantiza que no queden errores de lectura. La aplicación posterior requiere cotejar cada fila candidata contra su fuente.", "",
        "## Evidencia conservada", "",
        "La carpeta del expediente conserva copias byte a byte de las 693 imágenes. El manifiesto permite comparar sus hashes SHA-256 con los archivos fuente. El respaldo comprimido congela todas las columnas de los 11.896 registros; todos tienen datos_originales disponible. Este campo documenta la extracción conservada por el sistema; su presencia por sí sola no prueba que nunca haya sido alterado antes de este corte.", "",
        "La extracción conservada, el dato vigente del corte y las observaciones de esta revisión se presentan por separado. Ninguna conclusión del catálogo sustituye esos valores. Las notas preliminares se conservan en el respaldo; dos interpretaciones de atlas se rectificaron tras ampliar los ejemplos, sin cambiar los datos institucionales.", "",
        f"Respaldo de trabajo: {audit}.", "",
        f"Huella de registros: {s['huella_filas']}.", "",
        f"Verificación final: contenido de movimientos sin cambios = {check['movimientos_sin_cambios']}; conteos de 44 tablas sin cambios = {check['conteos_44_tablas_sin_cambios']}; schema sin cambios = {check['schema_sin_cambios']}; fotos fuente y copias verificadas = {check['fotos_verificadas']}.",
        "No se afirma una comparación de contenido de todas las demás tablas. No se invocó el clasificador de áreas ni se generaron sinónimos. No se reimportó, entrenó ni corrigió el histórico.", "",
        "## Cómo revisar", "",
        "1. Abrir index.html en la carpeta de Descargas.",
        "2. Elegir un tipo T01–T23. Leer el hallazgo, el contexto y la decisión pendiente.",
        "3. Ampliar la fotografía y revisar todas las filas, no solamente las verdes o las alarmadas. Abrir las otras hojas del artículo si el problema afecta continuidad.",
        "4. Hacer clic en el ID de una fila para comparar datos_originales con todos sus campos vigentes.",
        "5. Comunicar el criterio por código: qué se corrige, qué queda documentado y qué excepción debe permanecer pendiente. La caja del visor solo exporta un borrador; no aprueba ni aplica nada.", "",
        "## Catálogo de tipos", "",
        "Las siguientes familias se solapan: una hoja puede tener varios problemas y una fila con aviso puede ser correcta. Los IDs son ejemplos, no una lista exhaustiva de filas que deban cambiarse.", "",
    ]
    for c in CASOS:
        lines += [
            f"### {c['codigo']} · {c['titulo']}", "",
            f"Clase: {c['clase']}. Estado del criterio: PENDIENTE.", "",
            c["hallazgo"], "", "**Contexto de la misma hoja:** " + c["contexto"], "",
            "**Criterio que debe definir el usuario:** " + c["criterio_por_definir"], "",
            "**Límite de aplicación:** " + c["limite"], "",
            "Hojas: " + ", ".join(c["paginas"]) + ". Movimientos de ejemplo: " + (", ".join(map(str, c["movimientos"])) or "revisión visual de toda la hoja") + ".", "",
            f"[Ver el ejemplo con fotos]({(output / 'index.html').as_posix()}#tipo={c['codigo']}&hoja={c['paginas'][0]})", "",
        ]
    lines += [
        "## Protocolo para la siguiente fase", "",
        "Todavía no se ha ejecutado esta fase. El criterio humano debe quedar asociado a su mensaje de aprobación, versión, ejemplos aceptados, excepciones y alcance. Un criterio aprobado autoriza aplicar el mismo tratamiento a casos realmente equivalentes después de comprobar la fuente, sin inventar una regla más amplia.", "",
        "Antes de aplicar cada lote, preparar una propuesta revisable con los IDs, valores anteriores/nuevos y fotos; identificar lectura literal, dato desconocido, interpretación institucional y valor derivado. Conservar un respaldo y el historial de cada modificación, incluido autor, fecha, motivo, versión del criterio y huella de evidencia. Mantener la extracción inicial y las fotografías separadas del dato vigente.", "",
        "Los errores del documento no deben borrarse para conseguir una tabla que cuadre. Pueden tener una conclusión como inconsistencia documental confirmada o dato no recuperable y dejar de figurar como tarea pendiente, conservando el hallazgo para auditoría. El saldo documental y el reconstruido requieren procedencia explícita; no afirmar que un saldo inferido estuvo escrito.", "",
        "Fechas ausentes, precisión parcial y saldos documentales vacíos requieren comprobar que el modelo y las exportaciones admitan esa representación antes de actualizar registros. No reemplazar desconocidos por cero o por el 1 de enero. Los criterios para áreas/receptores, anulaciones, recuentos, daño y reasociación de páginas también necesitan representación y trazabilidad adecuadas.", "",
        "Después de cada lote, revisar nuevamente todas las filas de la hoja y la continuidad del artículo. Recalcular métricas y avisos con la política aprobada; comprobar que las vistas y exportaciones distingan dato vigente, evidencia e incertidumbre. Reentrenar el modelo únicamente sobre un conjunto versionado apropiado, una vez validado su uso. La limpieza documental no equivale a confirmar el inventario físico actual.", "",
        "## Archivos generados y reproducibilidad", "",
        "- snapshot_movimientos_sin_modificar.json.gz: corte completo y metadatos de solo lectura.",
        "- expediente.json: todas las hojas y sus filas/contexto.",
        "- catalogo_tipos.json: las 23 familias con ejemplos.",
        "- criterios_pendientes.json: criterios sin aprobar; no es un plan automático de cambios.",
        "- cotejo_visual.json: 693 notas de primera revisión y rectificaciones documentadas.",
        "- fuentes_manifest.json: correspondencia y hashes de cada fuente/copia.",
        "- verificacion_sin_cambios.json: comprobación final de movimientos, conteos, esquema e imágenes.",
        "- fotos/: las 693 fotografías sin modificación.",
        "- catalogos_snapshot.json: catálogo documental del corte.",
        "- scripts/recopilar_revision_hil.py: exportador de solo lectura; usar otra carpeta si se necesita un nuevo corte.",
        "- scripts/catalogo_revision_hil_20261013.py: catálogo editorial de casos.",
        "- scripts/publicar_revision_hil_20261013.py y scripts/plantilla_revision_hil.html: generador local del expediente; no aplican correcciones.", "",
    ]
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--auditoria", type=Path, required=True)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    audit, output = args.auditoria.resolve(), args.salida.resolve()
    data = json.loads((audit / "expediente.json").read_text(encoding="utf-8"))
    pages = data["paginas"]
    by_page = {p["id"]: p for p in pages}
    by_row = {r["id"]: p["id"] for p in pages for r in p["filas"]}
    for c in CASOS:
        assert all(k in by_page for k in c["paginas"]), c["codigo"]
        assert all(by_row.get(i) in c["paginas"] for i in c["movimientos"]), c["codigo"]
        assert c["estado_criterio"] == "PENDIENTE" and c["cambios_aplicados"] == 0
    output.mkdir(parents=True, exist_ok=True)
    (output / "fotos").mkdir(exist_ok=True)
    manifest = []
    for p in pages:
        source = Path(p["imagen"])
        assert source.is_relative_to((BACKEND / "storage").resolve()) and source.is_file()
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        assert source_hash == p["sha256_imagen"], f"Fuente cambió: {p['id']}"
        local = f"fotos/{p['id']}{source.suffix.lower()}"
        target = output / local
        if not target.exists():
            shutil.copy2(source, target)
        assert hashlib.sha256(target.read_bytes()).hexdigest() == source_hash, p["id"]
        p["foto_local"] = local
        manifest.append({"pagina": p["id"], "articulo_id": p["articulo_id"],
                         "fuente": str(source), "copia": local, "bytes": source.stat().st_size,
                         "sha256_fuente": source_hash, "sha256_copia": source_hash, "iguales": True})
    notes = prepare_notes(audit, pages)
    check = verify_database(data["resumen"])
    check.update(fotos_verificadas=len(manifest), fotos_fuente_sin_cambios=True, copias_exactas=True, criterios_aprobados=0, cambios_aplicados=0)
    write_json(audit / "verificacion_sin_cambios.json", check)
    assert check["movimientos_sin_cambios"] and check["conteos_44_tablas_sin_cambios"] and check["schema_sin_cambios"], "Cambió el corte durante la revisión; conserva archivos y revisa el resultado."
    data["casos"] = CASOS
    data["resumen"]["hojas_inspeccionadas_primera_pasada"] = len(notes)
    data["resumen"]["criterios_pendientes"] = len(CASOS)
    write_json(output / "expediente.json", data)
    write_json(output / "catalogo_tipos.json", CASOS)
    write_json(output / "cotejo_visual.json", notes)
    write_json(output / "fuentes_manifest.json", manifest)
    write_json(output / "verificacion_sin_cambios.json", check)
    write_json(output / "criterios_pendientes.json", {
        "corte": data["resumen"]["corte_bolivia"], "estado": "PENDIENTE_CRITERIOS_DEL_USUARIO",
        "cambios_aplicados": 0,
        "criterios": [{"codigo": c["codigo"], "titulo": c["titulo"], "estado": "PENDIENTE",
                      "pregunta": c["criterio_por_definir"], "criterio_aprobado": None,
                      "aprobador": None, "aprobado_en": None, "excepciones": [], "version": None}
                     for c in CASOS],
    })
    for filename in ["snapshot_movimientos_sin_modificar.json.gz", "catalogos_snapshot.json"]:
        target = output / filename
        if not target.exists():
            shutil.copy2(audit / filename, target)
        assert hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256((audit / filename).read_bytes()).digest()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    template = (BACKEND / "scripts/plantilla_revision_hil.html").read_text(encoding="utf-8")
    assert template.count("__DATOS_REVISION__") == 1
    (output / "index.html").write_text(template.replace("__DATOS_REVISION__", payload), encoding="utf-8")
    document = markdown(data, output, audit, check)
    for target in [ROOT / "docs/revision-hil-tipos-2026-10-13.md", output / "LEEME.md", audit / "informe_revision.md"]:
        target.write_text(document, encoding="utf-8")
    print(json.dumps({"expediente": str(output / "index.html"), "hojas": len(pages),
                      "historicos": sum(len(p["filas"]) for p in pages), "tipos": len(CASOS),
                      "fotos_bytes": sum(m["bytes"] for m in manifest),
                      "verificacion": {k:v for k,v in check.items() if k != "conteos_finales"}}, ensure_ascii=False))

if __name__ == "__main__":
    main()

