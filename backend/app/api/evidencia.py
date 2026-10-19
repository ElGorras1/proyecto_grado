"""Fotografías privadas: cookie HttpOnly o Bearer, nunca un token en la URL."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db

router = APIRouter()
RAIZ = Path(__file__).resolve().parents[2] / "storage"
EXTENSIONES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".pdf"}
TIPOS = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".pdf": "application/pdf",
}


@router.get("/storage/{ruta:path}", include_in_schema=False)
def ver(ruta: str, request: Request, db: Session = Depends(get_db)):
    cabecera = request.headers.get("authorization", "")
    token = (
        cabecera.split(" ", 1)[1]
        if cabecera.lower().startswith("bearer ")
        else request.cookies.get("evidencia_sesion")
    )
    get_current_user(token, db)
    raiz = RAIZ.resolve()
    try:
        archivo = (raiz / ruta).resolve()
        disponible = (
            archivo.is_relative_to(raiz)
            and archivo.suffix.lower() in EXTENSIONES
            and archivo.is_file()
        )
    except (ValueError, OSError, RuntimeError):
        # Una ruta inválida o un enlace circular tampoco es evidencia accesible.
        disponible = False
    if not disponible:
        raise HTTPException(404, "Imagen de respaldo no encontrada")
    return FileResponse(
        archivo,
        media_type=TIPOS[archivo.suffix.lower()],
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )
