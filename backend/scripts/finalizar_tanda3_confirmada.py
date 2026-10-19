"""Carga el plan complementario aprobado y sincroniza la resolución de tanda 3.

Las decisiones humanas y la correspondencia de fotos están en el archivo local
decisiones_usuario_2026-10-13.json. No confirma nuevas diferencias del OCR.
"""

import argparse
import copy
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from app.db.session import engine
from scripts import importar_tanda as imp
from scripts.importar_tanda2 import save_state, sha256


def sincronizar(batch, decisions, follow):
    parent_path = batch / "_revision/estado_importacion.json"
    state = json.loads(parent_path.read_text(encoding="utf-8"))
    child = json.loads((follow / "_revision/estado_importacion.json").read_text(encoding="utf-8"))
    assert state["plan_sha256"] == decisions["plan_original_sha256"] == sha256(batch / "plan_carga.csv")
    assert child["plan_sha256"] == sha256(follow / "plan_carga.csv")
    for mapping in decisions["cargas_aprobadas"]:
        r = child["articulos"].get(mapping["inicio_complementario"])
        if r:
            assert r["titulo"] == mapping["titulo_confirmado"] and r["fotos"] == mapping["archivos"]
    groups = {}
    for mapping in decisions["cargas_aprobadas"]:
        groups.setdefault(mapping["foto_principal"], []).append(mapping)
    fields = {"estado", "articulo_id", "huella", "lote_id", "movimientos", "tanda", "solicitud_id", "pendiente_id", "diferencias"}
    for key, mappings in groups.items():
        parent = state["articulos"][key]
        parent["confirmacion_usuario_en"] = "2026-10-13"
        parent["plan_complementario"] = str(follow)
        if len(mappings) == 1:
            mapping = mappings[0]
            parent["titulo_confirmado"] = mapping["titulo_confirmado"]
            r = child["articulos"].get(mapping["inicio_complementario"])
            if r and r.get("estado") in {"cargado", "revision_titulos", "revision_catalogo"}:
                assert r["fotos"] == parent["fotos"]
                parent.update({f: copy.deepcopy(r[f]) for f in fields if f in r})
        else:
            parent["estado"] = "dividido"
            parent["motivo"] = "Dos artículos distintos confirmados por el usuario"
            parent["articulos_finales"] = [
                {**copy.deepcopy(child["articulos"].get(m["inicio_complementario"], {"estado": "sin_procesar"})),
                 "titulo_confirmado": m["titulo_confirmado"], "fotos": m["archivos"]}
                for m in mappings
            ]
    approved = [child["articulos"].get(m["inicio_complementario"], {}) for m in decisions["cargas_aprobadas"]]
    complete = all(r.get("estado") == "cargado" for r in approved)
    state.update(fase="FINALIZADO" if complete else "CONFIRMADOS_PENDIENTES",
                 resoluciones_sincronizadas_en=datetime.now(UTC).isoformat(),
                 carpeta_importacion_confirmados=str(follow))
    save_state(parent_path, state)
    if not complete:
        print("Confirmados pendientes: " + json.dumps(dict(Counter(r.get("estado", "sin_procesar") for r in approved)), ensure_ascii=False), flush=True)
        return False
    loaded = []
    for r in state["articulos"].values():
        if r["estado"] == "cargado":
            loaded.append(r)
        elif r["estado"] == "dividido":
            assert all(c["estado"] == "cargado" for c in r["articulos_finales"])
            loaded.extend(r["articulos_finales"])
        else:
            assert r["estado"] == "descartado"
    assert len(loaded) == 200 and len({r["lote_id"] for r in loaded}) == 200
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as db:
        with db.begin():
            db.execute(text("SET TRANSACTION READ ONLY"))
            for r in loaded:
                q = db.execute(text("SELECT estado,lote_id,tanda FROM solicitudes_carga_kardex WHERE articulo_id=:a AND huella=:h"),
                               {"a": r["articulo_id"], "h": r["huella"]}).mappings().one()
                assert q["estado"] == "COMPLETADO" and q["lote_id"] == r["lote_id"] and q["tanda"] == 3
                lot = db.execute(text("SELECT tanda,total_imagenes FROM lotes_carga WHERE id=:l"), {"l": r["lote_id"]}).mappings().one()
                assert lot["tanda"] == 3 and lot["total_imagenes"] == len(r["fotos"])
                rows = db.execute(text("SELECT articulo_id,numero_pagina FROM movimientos_kardex WHERE lote_id=:l"), {"l": r["lote_id"]}).mappings().all()
                assert len(rows) == r["movimientos"] and all(m["articulo_id"] == r["articulo_id"] for m in rows)
                assert {m["numero_pagina"] for m in rows} == set(range(1, len(r["fotos"]) + 1))
            canceled = db.execute(text("SELECT estado,lote_id FROM lotes_pendientes WHERE id=:id"), {"id": decisions["descartados"][1]["pendiente_id"]}).mappings().one()
            assert canceled["estado"] == "CANCELADO" and canceled["lote_id"] is None
            assert db.execute(text("SELECT count(*) FROM movimientos_kardex WHERE articulo_id=316")).scalar_one() == 0
            assert db.execute(text("SELECT estado FROM activo WHERE id=316")).scalar_one() == "baja"
            assert db.execute(text("SELECT count(*) FROM solicitudes_carga_kardex WHERE tanda=3 AND estado='PROCESANDO'")).scalar_one() == 0
            total = db.execute(text("SELECT count(*) FROM movimientos_kardex")).scalar_one()
    result = {"resultado": "VERIFICADO", "verificado_en": datetime.now(UTC).isoformat(),
              "articulos_tanda3": len(loaded), "paginas_tanda3": sum(len(r["fotos"]) for r in loaded),
              "movimientos_tanda3": sum(r["movimientos"] for r in loaded), "movimientos_totales": total,
              "nuevos_articulos_confirmados": len(approved) + 1, "casos_descartados": 2,
              "pendientes": 0, "errores_pendientes": 0,
              "aprobados": [{"caso": m["caso"], "titulo": m["titulo_confirmado"],
                             "articulo_id": r["articulo_id"], "lote_id": r["lote_id"], "movimientos": r["movimientos"]}
                            for m, r in zip(decisions["cargas_aprobadas"], approved)]}
    save_state(batch / "_revision/verificacion_decisiones_2026-10-13.json", result)
    print("RESOLUCIONES VERIFICADAS: " + json.dumps(result, ensure_ascii=False), flush=True)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--carpeta", type=Path, required=True)
    parser.add_argument("--solo-sincronizar", action="store_true")
    args = parser.parse_args()
    batch = args.carpeta.resolve(strict=True)
    decisions = json.loads((batch / "_revision/decisiones_usuario_2026-10-13.json").read_text(encoding="utf-8"))
    follow = Path(decisions["carpeta_complementaria"]).resolve(strict=True)
    assert follow.is_relative_to(batch / "_revision")
    assert len(decisions["cargas_aprobadas"]) == 8
    with imp.importador_unico():
        if args.solo_sincronizar:
            return 0 if sincronizar(batch, decisions, follow) else 2
        job = argparse.Namespace(carpeta=follow, tanda=3, ejecutar=True, sesion_local_desarrollo=True,
                                 usuario=None, api=imp.DEFAULT_API, pausa_segundos=120,
                                 reintentos=3, solo=None, max_articulos=None)
        parent_path = batch / "_revision/estado_importacion.json"
        state = json.loads(parent_path.read_text(encoding="utf-8"))
        state.update(fase="CONFIRMADOS_EN_PROCESO", pid_confirmados=os.getpid())
        save_state(parent_path, state)
        exit_code = imp.ejecutar(job)
        child = json.loads((follow / "_revision/estado_importacion.json").read_text(encoding="utf-8"))
        if child["fase"] == "PAUSADO":
            return exit_code
        return 0 if sincronizar(batch, decisions, follow) else 2


if __name__ == "__main__":
    raise SystemExit(main())
