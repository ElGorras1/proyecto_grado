import io
from PIL import Image
from app.core.config import settings


def limites_carga():
    return {"paginas": settings.KARDEX_MAX_PAGINAS, "mb_imagen": settings.KARDEX_MAX_MB_IMAGEN,
            "mb_lote": settings.KARDEX_MAX_MB_LOTE, "megapixeles": settings.KARDEX_MAX_MEGAPIXELES,
            "formatos": ["JPEG", "PNG", "WEBP"]}


def preparar_imagen(contenido, mime):
    formatos = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}
    if mime not in formatos:
        raise ValueError("Formato no admitido. Utiliza imágenes JPEG, PNG o WebP")
    try:
        with Image.open(io.BytesIO(contenido)) as imagen:
            if imagen.format != formatos[mime]:
                raise ValueError("El contenido de la imagen no coincide con su tipo declarado")
            if imagen.width * imagen.height > settings.KARDEX_MAX_MEGAPIXELES * 1_000_000:
                raise ValueError(f"La imagen supera {settings.KARDEX_MAX_MEGAPIXELES} megapíxeles")
            imagen.verify()
        with Image.open(io.BytesIO(contenido)) as imagen:
            if imagen.mode in ("RGBA", "P"):
                imagen = imagen.convert("RGB")
            salida = io.BytesIO()
            imagen.save(salida, "webp", quality=60)
            return salida.getvalue()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("La imagen no se puede leer o está dañada") from exc
