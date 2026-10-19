import json

import pytest

from scripts.respaldo_recuperacion import verificar_paquete
from scripts.verificar_respaldo_actual import crear_zip, sha256_archivo


def paquete(tmp_path, ruta="storage/kardex_images/hoja.webp"):
    origen = tmp_path / "hoja.webp"
    origen.write_bytes(b"fotografia-local-ficticia")
    carpeta = tmp_path / "respaldo"
    carpeta.mkdir()
    (carpeta / "base.dump").write_bytes(b"dump-ficticio")
    entradas = crear_zip(carpeta / "archivos.zip", [(origen, ruta)])
    manifiesto = {
        "archivos": entradas,
        "paquete": {
            p.name: {"bytes": p.stat().st_size, "sha256": sha256_archivo(p)}
            for p in (carpeta / "base.dump", carpeta / "archivos.zip")
        },
    }
    (carpeta / "manifiesto.json").write_text(json.dumps(manifiesto), encoding="utf-8")
    return carpeta


def test_rechaza_dump_alterado_antes_de_restaurar(tmp_path):
    carpeta = paquete(tmp_path)
    assert verificar_paquete(carpeta)["archivos"][0]["bytes"] > 0
    (carpeta / "base.dump").write_bytes(b"archivo-alterado")
    with pytest.raises(RuntimeError, match="alterado"):
        verificar_paquete(carpeta)


@pytest.mark.parametrize(
    "ruta", ["../.env", "C:/secreto.env", "storage/../../.env", ".env", "storage\\hoja.webp"]
)
def test_rechaza_rutas_fuera_del_respaldo(tmp_path, ruta):
    with pytest.raises(RuntimeError, match="ruta no permitida"):
        verificar_paquete(paquete(tmp_path, ruta))
