"""Identidad del contenido de una carga de Kárdex (artículo se agrega en la BD)."""
import hashlib


def huella_de_paginas(paginas: list[bytes]) -> str:
    if not paginas:
        raise ValueError("El lote debe contener al menos una página")
    huella = hashlib.sha256(b"kardex-webp-v1\0")
    huella.update(len(paginas).to_bytes(4, "big"))
    for pagina in paginas:
        huella.update(hashlib.sha256(pagina).digest())
    return huella.hexdigest()
