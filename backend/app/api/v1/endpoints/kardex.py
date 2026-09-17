import os
import shutil
import uuid
import io
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, case, text
from starlette.concurrency import run_in_threadpool
from PIL import Image

from app.db.session import get_db
from app.models.kardex import MovimientoKardex
from app.models.activos import Activo, CategoriaActivo
from app.models.usuario import Usuario
from app.schemas.kardex import MovimientoKardexOut, MovimientoKardexEdit
from app.services.gemini_service import procesar_lote_imagenes
from app.services.kardex_service import procesar_y_guardar_lote, recalcular_saldos_posteriores
from app.api.deps import get_current_user, require_roles
from app.crud.auditoria import registrar_evento_auditoria

router = APIRouter()

STORAGE_DIR = "storage/kardex_images"

# ============================================================
# Schemas Locales
# ============================================================

class NuevoArticulo(BaseModel):
    nombre: str

class MovimientoActualCrear(BaseModel):
    articulo_id: int
    tipo: str  # "ingreso" o "salida"
    cantidad: int
    nodo_grafo: str
    observaciones: str = ""
    # Campos enriquecidos
    tipo_operacion: Optional[str] = None
    receptor: Optional[str] = None
    feria_id: Optional[int] = None
    ciudad_feria: Optional[str] = None
    canal_venta: Optional[str] = None
    motivo_baja: Optional[str] = None
    referencia_documento: Optional[str] = None


# ============================================================
# 1. Digitalización de Kárdex Histórico (Legacy)
# ============================================================

@router.post("/upload-lote")
async def upload_lote(
    request: Request,
    articulo_id: int = Form(...),
    archivos: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador"))
):
    """Procesa un lote de fotografías de Kárdex físico con Gemini Multimodal."""
    activo = db.query(Activo).filter(Activo.id == articulo_id).first()
    if not activo:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
        
    os.makedirs(STORAGE_DIR, exist_ok=True)
    
    # 1. Guardar archivos localmente (Comprimidos a WebP)
    imagenes_paths = []
    lote_uuid = str(uuid.uuid4())[:8]
    
    for idx, archivo in enumerate(archivos):
        nuevo_nombre = f"lote_{lote_uuid}_pag_{idx+1}.webp"
        ruta_completa = os.path.join(STORAGE_DIR, nuevo_nombre)
        
        img_bytes = await archivo.read()
        try:
            img = Image.open(io.BytesIO(img_bytes))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(ruta_completa, "webp", quality=60)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error procesando imagen: {e}")
            
        imagenes_paths.append(ruta_completa)
        
    # 2. Llamada a Gemini Flash en Threadpool para no bloquear el Event Loop
    try:
        paginas_extraidas = await run_in_threadpool(procesar_lote_imagenes, imagenes_paths)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Gemini LLM: {str(e)}")
        
    # 3. Validar aritméticamente e insertar en BD
    lote = procesar_y_guardar_lote(
        db=db,
        articulo_id=articulo_id,
        paginas=paginas_extraidas,
        imagenes_paths=imagenes_paths
    )
    
    # Auditoría institucional
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="subir_lote_kardex",
        recurso="lotes_carga",
        recurso_id=lote.id,
        resultado="exito",
        ip_origen=request.client.host if request.client else None,
        detalle={"articulo_id": articulo_id, "total_imagenes": len(archivos)}
    )
    
    return {"mensaje": "Lote procesado exitosamente", "lote_id": lote.id}


@router.put("/movimiento/{movimiento_id}", response_model=MovimientoKardexOut)
def update_movimiento_kardex(
    request: Request,
    movimiento_id: int, 
    payload: MovimientoKardexEdit, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador"))
):
    """Permite corregir un movimiento legacy en Human-In-The-Loop y recalcula saldos en cascada."""
    movimiento = db.query(MovimientoKardex).filter(MovimientoKardex.id == movimiento_id).first()
    if not movimiento:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
        
    valores_previos = {
        "ingresos": movimiento.ingresos,
        "salidas": movimiento.salidas,
        "saldo": movimiento.saldo_registrado,
        "nodo": movimiento.nodo_grafo
    }
    
    movimiento.ingresos = payload.ingresos
    movimiento.salidas = payload.salidas
    movimiento.saldo_registrado = payload.saldo_registrado
    
    if payload.nodo_grafo is not None:
        movimiento.nodo_grafo = payload.nodo_grafo
        movimiento.requiere_auditoria_nodo = False
        
    db.commit()
    
    # Recalcular balance posterior
    recalcular_saldos_posteriores(db, movimiento.articulo_id)
    db.refresh(movimiento)
    
    # Auditoría institucional
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="corregir_kardex_hil",
        recurso="movimientos_kardex",
        recurso_id=movimiento_id,
        resultado="exito",
        ip_origen=request.client.host if request.client else None,
        detalle={"previo": valores_previos, "nuevo": payload.model_dump()}
    )
    
    return movimiento


# ============================================================
# 2. Artículos y Consultas (Protegidos con get_current_user)
# ============================================================

@router.post("/articulos")
def crear_articulo(
    request: Request,
    payload: NuevoArticulo, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador"))
):
    """Alta de nuevo producto en el catálogo general."""
    if not payload.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre del artículo no puede estar vacío")

    cat = db.query(CategoriaActivo).filter(CategoriaActivo.nombre == "Digitalizados").first()
    if not cat:
        cat = CategoriaActivo(nombre="Digitalizados", descripcion="Artículos creados desde Kárdex Digital")
        db.add(cat)
        db.commit()
        db.refresh(cat)
    
    import time
    codigo_gen = f"KDX-{int(time.time())}"
    
    nuevo_activo = Activo(
        categoria_id=cat.id,
        codigo=codigo_gen,
        nombre=payload.nombre.strip().upper(),
        unidad_medida="unidad"
    )
    db.add(nuevo_activo)
    db.commit()
    db.refresh(nuevo_activo)
    
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="crear_articulo",
        recurso="activo",
        recurso_id=nuevo_activo.id,
        resultado="exito",
        ip_origen=request.client.host if request.client else None,
        detalle={"codigo": nuevo_activo.codigo, "nombre": nuevo_activo.nombre}
    )
    
    return {"id": nuevo_activo.id, "nombre": nuevo_activo.nombre, "codigo": nuevo_activo.codigo}


@router.get("/articulos")
def get_articulos_typeahead(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listado de artículos con conteo de alertas y stock actual calculado."""
    sum_rojas = func.sum(case((MovimientoKardex.tiene_error_saldo == True, 1), else_=0)).label('rojas')
    sum_amarillas = func.sum(case((MovimientoKardex.requiere_auditoria_nodo == True, 1), else_=0)).label('amarillas')
    
    resultados = db.query(Activo.id, Activo.nombre, Activo.codigo, sum_rojas, sum_amarillas)\
        .outerjoin(MovimientoKardex, Activo.id == MovimientoKardex.articulo_id)\
        .group_by(Activo.id)\
        .all()
    
    lista = []
    for a in resultados:
        ultimo = db.query(MovimientoKardex.saldo_registrado)\
            .filter(MovimientoKardex.articulo_id == a.id)\
            .order_by(MovimientoKardex.id.desc())\
            .first()
        stock = ultimo[0] if ultimo else 0
        lista.append({
            "id": a.id, 
            "nombre": a.nombre, 
            "codigo": a.codigo,
            "alertas_rojas": a.rojas or 0,
            "alertas_amarillas": a.amarillas or 0,
            "stock_actual": stock
        })
    return lista


@router.get("/errores")
def get_errores_human_in_the_loop(
    articulo_id: Optional[int] = None, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Retorna movimientos con error de saldo o nodo dudoso para revisión HIL."""
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


@router.get("/grafo/{articulo_id}")
def get_grafo_articulo(
    articulo_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Genera nodos y enlaces de Teoría de Grafos para el diagrama Sankey."""
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
        
        if tot_out > 0:
            links.append({"source": "Almacén Central", "target": nodo, "value": tot_out})
        if tot_in > 0:
            links.append({"source": nodo, "target": "Almacén Central", "value": tot_in})
            
    nodos = [{"name": n} for n in nodos_vistos]
    return {"nodes": nodos, "links": links}


@router.get("/nodos")
def get_nodos_disponibles(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Áreas y operaciones activas para selects."""
    result = db.execute(text(
        "SELECT nombre_oficial, tipo FROM catalogo_areas WHERE activa = TRUE ORDER BY tipo, nombre_oficial"
    ))
    nodos = []
    for nombre, tipo in result:
        if tipo == 'departamento':
            nodos.append({"valor": f"Área: {nombre}", "etiqueta": f"📍 {nombre}", "grupo": "Departamentos"})
        else:
            nodos.append({"valor": nombre, "etiqueta": f"📦 {nombre}", "grupo": "Tipo de Operación"})
    return nodos


@router.get("/ferias")
def get_ferias(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Catálogo de ferias del libro."""
    result = db.execute(text("SELECT id, nombre, ciudad FROM catalogo_ferias WHERE activa = TRUE ORDER BY nombre"))
    return [{"id": r[0], "nombre": r[1], "ciudad": r[2]} for r in result]


@router.get("/catalogo-areas")
def get_catalogo_areas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listado completo de áreas del catálogo."""
    result = db.execute(text(
        "SELECT id, nombre_oficial, abreviatura, descripcion, tipo, activa FROM catalogo_areas ORDER BY activa DESC, nombre_oficial"
    ))
    return [{"id": r[0], "nombre": r[1], "abreviatura": r[2], "descripcion": r[3], "tipo": r[4], "activa": r[5]} for r in result]


@router.get("/historial/{articulo_id}", response_model=List[MovimientoKardexOut])
def get_historial_kardex(
    articulo_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Solo retorna movimientos legacy (escaneados del papel, con lote_id)."""
    movimientos = db.query(MovimientoKardex)\
        .filter(
            MovimientoKardex.articulo_id == articulo_id,
            MovimientoKardex.lote_id.isnot(None)
        )\
        .order_by(MovimientoKardex.fecha_movimiento.asc(), MovimientoKardex.numero_pagina.asc(), MovimientoKardex.orden_fila.asc())\
        .all()
    return movimientos


@router.get("/historial-actual/{articulo_id}", response_model=List[MovimientoKardexOut])
def get_historial_actual(
    articulo_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Solo retorna movimientos modernos (digitales, sin lote_id)."""
    movimientos = db.query(MovimientoKardex)\
        .filter(
            MovimientoKardex.articulo_id == articulo_id,
            MovimientoKardex.lote_id.is_(None)
        )\
        .order_by(MovimientoKardex.id.asc())\
        .all()
    return movimientos


# ============================================================
# 3. Operaciones Modernas (Inventario Vivo)
# ============================================================

@router.post("/movimiento-actual", response_model=MovimientoKardexOut)
def registrar_movimiento_actual(
    request: Request,
    payload: MovimientoActualCrear, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador"))
):
    """
    Registra un movimiento operativo en el presente con bloqueo de fila anti-race conditions.
    Valida stock disponible y guarda auditoría.
    """
    if payload.cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a 0.")

    # 1. Obtener el último saldo con BLOQUEO DE FILA para evitar Race Conditions
    ultimo_mov = db.query(MovimientoKardex)\
        .filter(MovimientoKardex.articulo_id == payload.articulo_id)\
        .order_by(MovimientoKardex.id.desc())\
        .with_for_update()\
        .first()
        
    saldo_anterior = ultimo_mov.saldo_registrado if ultimo_mov else 0
    ing = payload.cantidad if payload.tipo == "ingreso" else 0
    sal = payload.cantidad if payload.tipo == "salida" else 0
    nuevo_saldo = saldo_anterior + ing - sal
    
    # 2. Validar stock suficiente
    if nuevo_saldo < 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Stock insuficiente. Saldo actual: {saldo_anterior} unidades. "
                   f"No se pueden retirar {sal} unidades."
        )
    
    nuevo_mov = MovimientoKardex(
        articulo_id=payload.articulo_id,
        fecha_movimiento=date.today(),
        detalle=f"Movimiento Actual: {payload.observaciones or payload.tipo_operacion or ''}",
        ingresos=ing if ing > 0 else None,
        salidas=sal if sal > 0 else None,
        saldo_registrado=nuevo_saldo,
        saldo_calculado=nuevo_saldo,
        tiene_error_saldo=False,
        requiere_auditoria_nodo=False,
        nodo_grafo=payload.nodo_grafo,
        observaciones=payload.observaciones or "Registro digital",
        estado="ACTIVO",
        # Campos enriquecidos
        usuario_operador=current_user.nombre,
        tipo_operacion=payload.tipo_operacion,
        receptor=payload.receptor,
        feria_id=payload.feria_id,
        ciudad_feria=payload.ciudad_feria,
        canal_venta=payload.canal_venta,
        motivo_baja=payload.motivo_baja,
        referencia_documento=payload.referencia_documento
    )
    db.add(nuevo_mov)
    db.commit()
    db.refresh(nuevo_mov)
    
    # Auditoría institucional
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="crear_movimiento_inventario",
        recurso="movimientos_kardex",
        recurso_id=nuevo_mov.id,
        resultado="exito",
        ip_origen=request.client.host if request.client else None,
        detalle={
            "articulo_id": payload.articulo_id,
            "tipo": payload.tipo,
            "cantidad": payload.cantidad,
            "nuevo_saldo": nuevo_saldo,
            "operacion": payload.tipo_operacion
        }
    )
    
    return nuevo_mov


@router.post("/movimiento-actual/{movimiento_id}/anular", response_model=MovimientoKardexOut)
def anular_movimiento_actual(
    request: Request,
    movimiento_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador"))
):
    """Anula un movimiento moderno y recalcula los saldos de los movimientos posteriores."""
    mov = db.query(MovimientoKardex).filter(MovimientoKardex.id == movimiento_id).first()
    if not mov:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
        
    if mov.lote_id is not None:
        raise HTTPException(status_code=400, detail="No se pueden anular registros legacy por este medio")
        
    if mov.estado == 'ANULADO':
        raise HTTPException(status_code=400, detail="El movimiento ya está anulado")
        
    mov.estado = 'ANULADO'
    
    # Recalcular saldos posteriores (modernos)
    posteriores = db.query(MovimientoKardex)\
        .filter(MovimientoKardex.articulo_id == mov.articulo_id, MovimientoKardex.id > mov.id, MovimientoKardex.lote_id.is_(None))\
        .order_by(MovimientoKardex.id.asc())\
        .all()
        
    anterior = db.query(MovimientoKardex)\
        .filter(MovimientoKardex.articulo_id == mov.articulo_id, MovimientoKardex.id < mov.id)\
        .order_by(MovimientoKardex.id.desc())\
        .first()
        
    saldo_actual = anterior.saldo_registrado if anterior else 0
    mov.saldo_registrado = saldo_actual
    
    for m in posteriores:
        if m.estado == 'ANULADO':
            m.saldo_registrado = saldo_actual
            continue
            
        ing = m.ingresos or 0
        sal = m.salidas or 0
        saldo_actual = saldo_actual + ing - sal
        m.saldo_registrado = saldo_actual

    db.commit()
    db.refresh(mov)
    
    # Auditoría institucional
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="anular_movimiento_inventario",
        recurso="movimientos_kardex",
        recurso_id=movimiento_id,
        resultado="exito",
        ip_origen=request.client.host if request.client else None,
        detalle={"articulo_id": mov.articulo_id, "saldo_recalculado": saldo_actual}
    )
    
    return mov
