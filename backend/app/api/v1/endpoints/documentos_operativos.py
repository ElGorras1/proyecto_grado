"""Documentos privados conservados por articulo y referencia, sin alterar stock."""
import hashlib
import io
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.activos import Activo
from app.models.documento_operativo import DocumentoOperativo
from app.services.inventario import auditar

router = APIRouter(prefix='/kardex/articulos', tags=['Documentos operativos'])
RAIZ = Path(__file__).resolve().parents[4] / 'storage' / 'documentos_operativos'
MAX_BYTES = 10 * 1024 * 1024


def publico(d):
    return {k: getattr(d, k) for k in ('id', 'articulo_id', 'referencia', 'nombre', 'tipo',
                                      'bytes', 'sha256', 'registrado_por', 'registrado_en')}


@router.get('/{articulo_id}/documentos')
def listar(articulo_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if db.get(Activo, articulo_id) is None:
        raise HTTPException(404, 'Artículo no encontrado')
    return [publico(d) for d in db.query(DocumentoOperativo).filter_by(
        articulo_id=articulo_id).order_by(DocumentoOperativo.id.desc())]


@router.post('/{articulo_id}/documentos', status_code=201)
async def subir(articulo_id: int, request: Request, referencia: str = Form(min_length=3, max_length=200),
                archivo: UploadFile = File(...), db: Session = Depends(get_db),
                usuario=Depends(require_roles('Administrador', 'Operador'))):
    if db.get(Activo, articulo_id) is None:
        raise HTTPException(404, 'Artículo no encontrado')
    referencia = referencia.strip()
    if len(referencia) < 3:
        raise HTTPException(422, 'Indica la referencia del acta o documento')
    contenido = await archivo.read(MAX_BYTES + 1)
    if not contenido or len(contenido) > MAX_BYTES:
        raise HTTPException(422, 'El documento debe contener entre 1 byte y 10 MB')
    tipo = None
    if contenido.startswith(b'%PDF-') and contenido.rstrip().endswith(b'%%EOF'):
        tipo = 'application/pdf'
    else:
        try:
            with Image.open(io.BytesIO(contenido)) as imagen:
                if imagen.width * imagen.height > 40_000_000:
                    raise ValueError('Imagen demasiado grande')
                tipo = {'PNG': 'image/png', 'JPEG': 'image/jpeg', 'WEBP': 'image/webp'}.get(imagen.format)
                imagen.verify()
        except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError):
            tipo = None
    if tipo is None:
        raise HTTPException(422, 'Selecciona un PDF o una imagen PNG, JPEG o WebP válida')
    nombre = (archivo.filename or 'documento').replace('\\', '/').rsplit('/', 1)[-1]
    nombre = ''.join(c for c in nombre if c.isprintable()).strip()[:180] or 'documento'
    RAIZ.mkdir(parents=True, exist_ok=True)
    clave = uuid4().hex + '.bin'
    ruta = RAIZ / clave
    creado = False
    try:
        with ruta.open('xb') as destino:
            creado = True
            destino.write(contenido)
        d = DocumentoOperativo(articulo_id=articulo_id, referencia=referencia, nombre=nombre,
            archivo=clave, tipo=tipo, bytes=len(contenido), sha256=hashlib.sha256(contenido).hexdigest(),
            registrado_por=usuario.id, registrado_en=datetime.now(UTC))
        db.add(d)
        db.flush()
        auditar(db, usuario, request, 'adjuntar_documento_operativo', 'documento_operativo', d.id,
                {'articulo_id': articulo_id, 'referencia': referencia, 'sha256': d.sha256})
        resultado = publico(d)
        db.commit()
        return resultado
    except Exception:
        db.rollback()
        if creado:
            ruta.unlink(missing_ok=True)
        raise


@router.get('/{articulo_id}/documentos/{id}/archivo')
def descargar(articulo_id: int, id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    d = db.query(DocumentoOperativo).filter_by(id=id, articulo_id=articulo_id).first()
    if d is None:
        raise HTTPException(404, 'Documento no encontrado')
    ruta = (RAIZ / d.archivo).resolve()
    if not ruta.is_relative_to(RAIZ.resolve()) or not ruta.is_file():
        raise HTTPException(409, 'El archivo privado no está disponible')
    if hashlib.sha256(ruta.read_bytes()).hexdigest() != d.sha256:
        raise HTTPException(409, 'La huella del archivo cambió; requiere revisión')
    return FileResponse(ruta, media_type=d.tipo, filename=d.nombre,
                        headers={'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'})
