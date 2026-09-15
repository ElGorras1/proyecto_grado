import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.kardex import MovimientoKardex
from app.models.activos import Activo
from app.schemas.kardex import MovimientoKardexOut, MovimientoKardexEdit
from app.services.gemini_service import procesar_lote_imagenes
from app.services.kardex_service import procesar_y_guardar_lote, recalcular_saldos_posteriores

router = APIRouter()

STORAGE_DIR = "storage/kardex_images"

@router.post("/upload-lote")
async def upload_lote(
    articulo_id: int = Form(...),
    archivos: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    # Validar activo_id directo en DB (Requerimiento 3)
    activo = db.query(Activo).filter(Activo.id == articulo_id).first()
    if not activo:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
        
    os.makedirs(STORAGE_DIR, exist_ok=True)
    
    # 1. Guardar archivos localmente (Comprimidos)
    imagenes_paths = []
    # Usamos timestamp para el prefijo de carpeta temporal antes de tener lote_id
    import uuid
    from PIL import Image
    import io
    
    lote_uuid = str(uuid.uuid4())[:8]
    
    for idx, archivo in enumerate(archivos):
        nuevo_nombre = f"lote_{lote_uuid}_pag_{idx+1}.webp"
        ruta_completa = os.path.join(STORAGE_DIR, nuevo_nombre)
        
        # Leemos en memoria, procesamos con Pillow para comprimir y guardamos
        img_bytes = await archivo.read()
        try:
            img = Image.open(io.BytesIO(img_bytes))
            # Convertir a RGB por si es un formato con transparencia (como PNG)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            # Guardamos como WebP con calidad 60 (comprime ~80% sin perder legibilidad)
            img.save(ruta_completa, "webp", quality=60)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error procesando imagen: {e}")
            
        imagenes_paths.append(ruta_completa)
        
    # 2. Llamada a Gemini 3.6 Flash
    try:
        paginas_extraidas = procesar_lote_imagenes(imagenes_paths)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Gemini LLM: {str(e)}")
        
    # 3. Validar aritméticamente e insertar en BD
    lote = procesar_y_guardar_lote(
        db=db,
        articulo_id=articulo_id,
        paginas=paginas_extraidas,
        imagenes_paths=imagenes_paths
    )
    
    return {"mensaje": "Lote procesado exitosamente", "lote_id": lote.id}

from pydantic import BaseModel
from app.models.activos import Activo, CategoriaActivo

class NuevoArticulo(BaseModel):
    nombre: str

@router.post("/articulos")
def crear_articulo(payload: NuevoArticulo, db: Session = Depends(get_db)):
    # Buscar o crear categoría genérica
    cat = db.query(CategoriaActivo).filter(CategoriaActivo.nombre == "Digitalizados").first()
    if not cat:
        cat = CategoriaActivo(nombre="Digitalizados", descripcion="Artículos creados desde Kárdex Digital")
        db.add(cat)
        db.commit()
        db.refresh(cat)
    
    # Generar código auto-incremental simple basado en el id máximo
    import time
    codigo_gen = f"KDX-{int(time.time())}"
    
    nuevo_activo = Activo(
        categoria_id=cat.id,
        codigo=codigo_gen,
        nombre=payload.nombre.upper(),
        unidad_medida="unidad"
    )
    db.add(nuevo_activo)
    db.commit()
    db.refresh(nuevo_activo)
    
    return {"id": nuevo_activo.id, "nombre": nuevo_activo.nombre, "codigo": nuevo_activo.codigo}

from typing import Optional
@router.get("/errores")
def get_errores_human_in_the_loop(articulo_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Retorna movimientos con error matemático O con nodo de grafo dudoso.
    Filtra por articulo_id si es provisto.
    """
    from sqlalchemy import or_
    query = db.query(MovimientoKardex, Activo.nombre.label("articulo_nombre"))\
        .join(Activo, MovimientoKardex.articulo_id == Activo.id)\
        .filter(or_(
            MovimientoKardex.tiene_error_saldo == True,
            MovimientoKardex.requiere_auditoria_nodo == True
        ))
        
    if articulo_id:
        query = query.filter(MovimientoKardex.articulo_id == articulo_id)
        
    errores = query.order_by(Activo.nombre.asc(), MovimientoKardex.fecha_movimiento.asc()).all()
        
    resultado = []
    for mov, articulo_nombre in errores:
        dto = MovimientoKardexOut.model_validate(mov).model_dump()
        dto["articulo_nombre"] = articulo_nombre
        if dto.get("ruta_imagen_respaldo"):
            path = dto["ruta_imagen_respaldo"].replace("\\", "/")
            dto["url_imagen"] = f"/{path}" 
        resultado.append(dto)
        
    return resultado

@router.get("/articulos")
def get_articulos_typeahead(db: Session = Depends(get_db)):
    from sqlalchemy import func, case
    
    # Contar alertas rojas y amarillas por artículo
    sum_rojas = func.sum(case((MovimientoKardex.tiene_error_saldo == True, 1), else_=0)).label('rojas')
    sum_amarillas = func.sum(case((MovimientoKardex.requiere_auditoria_nodo == True, 1), else_=0)).label('amarillas')
    
    resultados = db.query(Activo.id, Activo.nombre, Activo.codigo, sum_rojas, sum_amarillas)\
        .outerjoin(MovimientoKardex, Activo.id == MovimientoKardex.articulo_id)\
        .group_by(Activo.id)\
        .all()
        
    return [{
        "id": a.id, 
        "nombre": a.nombre, 
        "codigo": a.codigo,
        "alertas_rojas": a.rojas or 0,
        "alertas_amarillas": a.amarillas or 0
    } for a in resultados]

@router.get("/grafo/{articulo_id}")
def get_grafo_articulo(articulo_id: int, db: Session = Depends(get_db)):
    """
    Formatea la data para el Diagrama de Sankey (Apache ECharts).
    """
    from sqlalchemy import func
    movimientos = db.query(
        MovimientoKardex.nodo_grafo, 
        func.sum(MovimientoKardex.ingresos).label("total_ingresos"),
        func.sum(MovimientoKardex.salidas).label("total_salidas")
    ).filter(
        MovimientoKardex.articulo_id == articulo_id,
        MovimientoKardex.nodo_grafo.isnot(None)
    ).group_by(MovimientoKardex.nodo_grafo).all()
    
    nodos_vistos = set(["Almacén Central"])
    links = []
    
    for mov in movimientos:
        nodo = mov.nodo_grafo
        nodos_vistos.add(nodo)
        
        tot_in = int(mov.total_ingresos or 0)
        tot_out = int(mov.total_salidas or 0)
        
        # Sankey links (source, target, value)
        if tot_out > 0:
            links.append({"source": "Almacén Central", "target": nodo, "value": tot_out})
        if tot_in > 0:
            links.append({"source": nodo, "target": "Almacén Central", "value": tot_in})
            
    nodos = [{"name": n} for n in nodos_vistos]
        
    return {"nodes": nodos, "links": links}

@router.get("/nodos")
def get_nodos_disponibles(db: Session = Depends(get_db)):
    """
    Retorna la lista de todos los nodos/áreas distintos usados en la historia 
    para poblar el dropdown de nuevos movimientos.
    """
    nodos_historicos = db.query(MovimientoKardex.nodo_grafo)\
        .filter(MovimientoKardex.nodo_grafo.isnot(None))\
        .distinct().all()
    lista = [n[0] for n in nodos_historicos]
    # Nodos base por si la base está vacía
    base = ["Salida: Ventas", "Salida: Obsequios", "Salida: Baja/Pérdida", "Feria", "Donación"]
    for b in base:
        if b not in lista:
            lista.append(b)
    return sorted(lista)

from pydantic import BaseModel
from datetime import date
class MovimientoActualCrear(BaseModel):
    articulo_id: int
    tipo: str  # "ingreso" o "salida"
    cantidad: int
    nodo_grafo: str
    observaciones: str = ""

@router.post("/movimiento-actual")
def registrar_movimiento_actual(payload: MovimientoActualCrear, db: Session = Depends(get_db)):
    """
    Registra un movimiento operativo en el presente, sumando/restando al último saldo.
    """
    # 1. Obtener el último saldo
    ultimo_mov = db.query(MovimientoKardex)\
        .filter(MovimientoKardex.articulo_id == payload.articulo_id)\
        .order_by(MovimientoKardex.fecha_movimiento.desc(), MovimientoKardex.numero_pagina.desc(), MovimientoKardex.orden_fila.desc())\
        .first()
        
    saldo_anterior = ultimo_mov.saldo_registrado if ultimo_mov else 0
    ing = payload.cantidad if payload.tipo == "ingreso" else 0
    sal = payload.cantidad if payload.tipo == "salida" else 0
    nuevo_saldo = saldo_anterior + ing - sal
    
    nuevo_mov = MovimientoKardex(
        articulo_id=payload.articulo_id,
        fecha_movimiento=date.today(),
        detalle=f"Movimiento Actual: {payload.observaciones}",
        ingresos=ing if ing > 0 else None,
        salidas=sal if sal > 0 else None,
        saldo_registrado=nuevo_saldo,
        saldo_calculado=nuevo_saldo,
        tiene_error_saldo=False,
        requiere_auditoria_nodo=False,
        nodo_grafo=payload.nodo_grafo,
        observaciones="Registro digital"
    )
    db.add(nuevo_mov)
    db.commit()
    db.refresh(nuevo_mov)
    return nuevo_mov

@router.get("/historial/{articulo_id}", response_model=List[MovimientoKardexOut])
def get_historial_kardex(articulo_id: int, db: Session = Depends(get_db)):
    movimientos = db.query(MovimientoKardex)\
        .filter(MovimientoKardex.articulo_id == articulo_id)\
        .order_by(MovimientoKardex.fecha_movimiento.asc(), MovimientoKardex.numero_pagina.asc(), MovimientoKardex.orden_fila.asc())\
        .all()
    return movimientos

@router.put("/movimiento/{movimiento_id}", response_model=MovimientoKardexOut)
def update_movimiento_kardex(movimiento_id: int, payload: MovimientoKardexEdit, db: Session = Depends(get_db)):
    movimiento = db.query(MovimientoKardex).filter(MovimientoKardex.id == movimiento_id).first()
    if not movimiento:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
        
    movimiento.ingresos = payload.ingresos
    movimiento.salidas = payload.salidas
    movimiento.saldo_registrado = payload.saldo_registrado
    
    if payload.nodo_grafo is not None:
        movimiento.nodo_grafo = payload.nodo_grafo
        # Si un humano lo actualizó, ya no requiere auditoría
        movimiento.requiere_auditoria_nodo = False
        
    db.commit()
    
    # REQUERIMIENTO 4: Recalcular balance
    recalcular_saldos_posteriores(db, movimiento.articulo_id)
    
    db.refresh(movimiento)
    return movimiento
