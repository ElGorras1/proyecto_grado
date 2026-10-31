"""Localiza el cliente PostgreSQL sin suponer Windows ni una versión instalada."""

import os
import shutil
from pathlib import Path


def postgres_tool(nombre: str) -> Path:
    if nombre not in {"pg_dump", "pg_restore"}:
        raise ValueError("Herramienta PostgreSQL no admitida")
    ejecutable = nombre + (".exe" if os.name == "nt" else "")
    configurado = os.environ.get("POSTGRES_BIN")
    if configurado:
        candidato = Path(configurado).expanduser() / ejecutable
        if not candidato.is_file():
            raise RuntimeError(f"POSTGRES_BIN no contiene {ejecutable}")
        return candidato.resolve()
    encontrado = shutil.which(ejecutable)
    if encontrado:
        return Path(encontrado).resolve()
    if os.name == "nt":
        raiz = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "PostgreSQL"
        versiones = sorted((p for p in raiz.glob("*") if p.name.isdigit()),
                           key=lambda p: int(p.name), reverse=True)
        for version in versiones:
            candidato = version / "bin" / ejecutable
            if candidato.is_file():
                return candidato.resolve()
    raise RuntimeError(f"No se encontró {ejecutable}; instala el cliente o configura POSTGRES_BIN")
