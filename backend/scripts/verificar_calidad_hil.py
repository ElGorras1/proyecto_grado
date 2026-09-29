"""Reconcilia la migración contra su respaldo sin modificar la base."""
import gzip
import json
import sys
from sqlalchemy import text
from app.db.session import engine


def main():
    with gzip.open(sys.argv[1], "rt", encoding="utf-8") as archivo:
        anteriores = json.load(archivo)["movimientos_kardex"]
    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        actuales = {r["id"]: dict(r) for r in conn.execute(text("SELECT * FROM movimientos_kardex")).mappings()}
    assert len(anteriores) == len(actuales), "Cambió el conteo de movimientos"
    diferencias = []
    for previo in anteriores:
        actual = actuales[previo["id"]]
        for campo, valor in previo.items():
            if campo in ("saldo_calculado", "tiene_error_saldo"):
                continue
            presente = actual[campo]
            if str(valor) != str(presente):
                diferencias.append((previo["id"], campo))
        assert str(actual["fecha_original"]) == previo["fecha_movimiento"]
        assert actual["datos_originales"]["fuente"] == "BASELINE_MIGRACION"
    assert not diferencias, f"Campos de evidencia alterados: {diferencias[:10]}"
    historicos = [r for r in actuales.values() if r["lote_id"] is not None and r["estado"] == "ACTIVO"]
    print(json.dumps({"movimientos_preservados": len(actuales), "diferencias_evidencia": len(diferencias),
        "alertas_saldo": sum(r["tiene_error_saldo"] for r in historicos),
        "alertas_fecha": sum(r["fecha_estado"] == "PENDIENTE_HIL" for r in historicos)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
