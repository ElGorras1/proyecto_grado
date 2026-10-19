"""Expediente de revisión documental de solo lectura; nunca corrige el libro.

Congela todas las filas, analiza secuencia completa por artículo y genera una cola
por hoja con su contexto anterior/posterior. Las categorías son hipótesis hasta
cotejar fotografías; ninguna decide fechas, áreas ni cantidades automáticamente.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont, ImageOps
from sqlalchemy import text

from app.db.session import engine


BACKEND = Path(__file__).resolve().parents[1]
AREA_PENDIENTE = {"AREA_NO_CATALOGADA", "PENDIENTE_HIL"}


def digest(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                    default=str, separators=(",", ":")).encode()).hexdigest()


def alerts(r):
    out = []
    if r["tiene_error_saldo"]:
        out.append("saldo")
    if r["fecha_estado"] == "PENDIENTE_HIL":
        out.append("fecha")
    if r["requiere_auditoria_nodo"] or r["area_estado"] in AREA_PENDIENTE:
        out.append("area")
    if r["requiere_auditoria_referencia"] or r["referencia_estado"] in {"ILEGIBLE", "INCIERTA"}:
        out.append("referencia")
    return out


def snapshot(out):
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
            catalogs = {"areas": [dict(r) for r in db.execute(text("SELECT * FROM catalogo_areas ORDER BY id")).mappings()],
                        "sinonimos": [dict(r) for r in db.execute(text("SELECT * FROM sinonimos_area ORDER BY id")).mappings()]}
            tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name")).scalars().all()
            quote = db.dialect.identifier_preparer.quote
            counts = {t: db.execute(text("SELECT count(*) FROM " + quote(t))).scalar_one() for t in tables}
            schema = db.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    raw = json.loads(json.dumps(rows, ensure_ascii=False, default=str))
    meta = {"corte_bolivia": datetime.now(ZoneInfo("America/La_Paz")).isoformat(),
            "modo": "REPEATABLE READ / READ ONLY", "schema": schema,
            "filas_originales": len(raw), "huella_filas": digest(raw), "conteos_tablas": counts}
    with gzip.open(out / "snapshot_movimientos_sin_modificar.json.gz", "wt", encoding="utf-8") as f:
        json.dump({"meta": meta, "movimientos": raw}, f, ensure_ascii=False)
    return raw, catalogs, meta


def collect(rows, catalogs, meta):
    historical = [r for r in rows if r["lote_id"] is not None and r["estado"] == "ACTIVO"]
    pages, last = {}, {}
    official = {str(v).strip().upper(): a["nombre_oficial"] for a in catalogs["areas"]
                for v in (a["nombre_oficial"], a.get("abreviatura")) if v}
    aliases = {a["texto_sucio"].strip().upper(): a for a in catalogs["sinonimos"]}
    causes = Counter()
    for r in historical:
        previous = last.get(r["articulo_id"])
        r["avisos"] = alerts(r)
        r["hipotesis"] = []
        r["movimiento_anterior_id"] = previous["id"] if previous else None
        r["saldo_anterior_documental"] = previous["saldo_registrado"] if previous else None
        i, s = r["ingresos"] or 0, r["salidas"] or 0
        expected = previous["saldo_registrado"] + i - s if previous else None
        r["saldo_esperado_con_anterior"] = expected
        r["diferencia_con_anterior"] = r["saldo_registrado"] - expected if expected is not None else None
        if r["tiene_error_saldo"]:
            if previous is None:
                r["hipotesis"].append("S_INICIO_SIN_BASE")
            elif previous["lote_id"] != r["lote_id"]:
                r["hipotesis"].append("S_SALTO_ENTRE_LOTES")
            elif previous["numero_pagina"] != r["numero_pagina"]:
                r["hipotesis"].append("S_CONTINUIDAD_ENTRE_HOJAS")
            else:
                r["hipotesis"].append("S_DIFERENCIA_EN_HOJA")
        elif expected is not None and expected != r["saldo_registrado"]:
            r["hipotesis"].append("S_DIFERENCIA_SIN_AVISO")
        if (i > 0) == (s > 0):
            r["hipotesis"].append("Q_SIN_MOVIMIENTO" if i == s == 0 else "Q_DOBLE_DIRECCION")
        if i < 0 or s < 0:
            r["hipotesis"].append("Q_NEGATIVA")
        if "fecha" in r["avisos"]:
            if previous:
                current_date = date.fromisoformat(r["fecha_movimiento"])
                prev_date = date.fromisoformat(previous["fecha_movimiento"])
                r["retroceso_dias"] = (prev_date - current_date).days
                if current_date.year != prev_date.year:
                    r["hipotesis"].append("F_RETROCESO_CAMBIO_ANO")
                else:
                    r["hipotesis"].append("F_RETROCESO_MISMO_ANO")
            else:
                r["hipotesis"].append("F_AVISO_SIN_ANTERIOR")
        if r["fecha_movimiento"].endswith("-01-01"):
            r["hipotesis"].append("F_1_ENERO_POR_COTEJAR")
        if "area" in r["avisos"]:
            area = (r["area"] or "").strip().upper()
            if not area:
                r["hipotesis"].append("A_AUSENTE_O_SIN_DIRECCION")
            elif re.fullmatch(r'[\s\"\'´`“”‘’.,:;\-]+', area):
                r["hipotesis"].append("A_COMILLAS_O_SIGNOS")
            elif area in official:
                r["hipotesis"].append("A_CATALOGADA_CON_AVISO")
            elif area in aliases:
                r["hipotesis"].append("A_ALIAS_NO_CONFIRMADO" if not aliases[area]["confirmado"] else "A_ALIAS_CONFIRMADO_CON_AVISO")
            else:
                r["hipotesis"].append("A_TEXTO_NO_RECONOCIDO")
        if "referencia" in r["avisos"]:
            r["hipotesis"].append("R_ILEGIBLE_O_SIGNOS")
        if r["id"] == 12272:
            r["hipotesis"].append("F_AUSENTE_FOTO_CONFIRMADA")
        causes.update(r["hipotesis"])
        key = f"L{r['lote_id']:04d}-P{r['numero_pagina']:02d}"
        if key not in pages:
            path = (BACKEND / r["ruta_imagen_respaldo"].replace("\\", "/")).resolve()
            assert path.is_relative_to((BACKEND / "storage").resolve()) and path.is_file(), str(path)
            pages[key] = {"id": key, "articulo_id": r["articulo_id"], "articulo": r["articulo_nombre"],
                          "lote_id": r["lote_id"], "pagina": r["numero_pagina"], "tanda": r["tanda"],
                          "imagen": str(path), "sha256_imagen": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "filas": [], "avisos": [], "hipotesis": [],
                          "estado_cotejo_visual": "PENDIENTE", "notas_visual": []}
        pages[key]["filas"].append(r)
        last[r["articulo_id"]] = r
    by_id = {r["id"]: r for r in historical}
    for page in pages.values():
        for n, r in enumerate(page["filas"]):
            r["fila_anterior_en_hoja_id"] = page["filas"][n-1]["id"] if n else None
            r["fila_siguiente_en_hoja_id"] = page["filas"][n+1]["id"] if n + 1 < len(page["filas"]) else None
        first, final = page["filas"][0], page["filas"][-1]
        page["anterior_fuera_hoja"] = by_id.get(first["movimiento_anterior_id"])
        page["avisos"] = sorted({a for r in page["filas"] for a in r["avisos"]})
        page["hipotesis"] = sorted({a for r in page["filas"] for a in r["hipotesis"]})
        page["movimientos_con_avisos"] = [r["id"] for r in page["filas"] if r["avisos"]]
        page["filas_contexto_sin_avisos"] = [r["id"] for r in page["filas"] if not r["avisos"]]
        page["requiere_revision"] = bool(page["hipotesis"] or page["avisos"])
    reviewed_scope = [p for p in pages.values() if p["requiere_revision"]]
    summary = {**meta, "historicos": len(historical), "paginas_totales": len(pages),
               "movimientos_con_avisos": sum(bool(r["avisos"]) for r in historical),
               "paginas_con_avisos": sum(bool(p["avisos"]) for p in pages.values()),
               "paginas_de_revision_ampliada": len(reviewed_scope),
               "filas_en_hojas_de_revision": sum(len(p["filas"]) for p in reviewed_scope),
               "filas_contexto_sin_avisos": sum(len(p["filas_contexto_sin_avisos"]) for p in reviewed_scope),
               "avisos_por_tipo": dict(Counter(a for r in historical for a in r["avisos"])),
               "hipotesis_por_tipo": dict(causes),
               "advertencia": "Hipótesis automáticas no equivalen a errores confirmados; cada cambio necesita cotejo visual y criterio humano aprobado."}
    return {"resumen": summary, "paginas": list(pages.values()), "criterios_aprobados": [], "ejemplos": []}


def contacts(data, out):
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
    small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
    pending = [p for p in data["paginas"] if p["requiere_revision"]]
    destination = out / "contactos"
    destination.mkdir(exist_ok=True)
    indexes = []
    for start in range(0, len(pending), 6):
        group = pending[start:start+6]
        tile_w, tile_h = 1040, 1530
        sheet = Image.new("RGB", (tile_w*2, tile_h*3), "white")
        draw = ImageDraw.Draw(sheet)
        for n, p in enumerate(group):
            x, y = (n % 2) * tile_w, (n // 2) * tile_h
            label = f"{start+n+1}/{len(pending)} {p['id']} A{p['articulo_id']} T{p['tanda']}"
            draw.text((x+10, y+5), label, fill="black", font=font)
            draw.text((x+10, y+38), p["articulo"][:70], fill="black", font=small)
            draw.text((x+10, y+67), ", ".join(p["avisos"]) or "Candidatos sin aviso HIL", fill="#a00000", font=small)
            with Image.open(p["imagen"]) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                # Copia de presentación: conserva la foto fuente completa. No OCR,
                # no relleno, no cambio de cifras; solo ajuste de tamaño en el atlas.
                im.thumbnail((tile_w-12, tile_h-108), Image.Resampling.LANCZOS)
                sheet.paste(im, (x+(tile_w-im.width)//2, y+100))
        target = destination / f"hojas_{start//6+1:03d}.jpg"
        sheet.save(target, quality=95)
        indexes.append({"indice": start//6+1, "archivo": str(target), "paginas": [p["id"] for p in group]})
    (out/"indice_contactos.json").write_text(json.dumps(indexes, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    out = args.salida.resolve()
    if out.exists():
        raise RuntimeError("Usa una carpeta nueva para conservar el corte anterior")
    out.mkdir(parents=True)
    rows, catalogs, meta = snapshot(out)
    data = collect(rows, catalogs, meta)
    (out/"expediente.json").write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (out/"catalogos_snapshot.json").write_text(json.dumps(catalogs, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    contacts(data, out)
    print(json.dumps({"carpeta": str(out), "resumen": data["resumen"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
