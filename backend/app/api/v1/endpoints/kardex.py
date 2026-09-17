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
        
    # 2. Llamada a Gemini 3.6 Flash (en thread para no bloquear el Event Loop)
    from starlette.concurrency import run_in_threadpool
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
    
    # Contar alertas rojas y amarillas por artículo (solo legacy)
    sum_rojas = func.sum(case((MovimientoKardex.tiene_error_saldo == True, 1), else_=0)).label('rojas')
    sum_amarillas = func.sum(case((MovimientoKardex.requiere_auditoria_nodo == True, 1), else_=0)).label('amarillas')
    
    resultados = db.query(Activo.id, Activo.nombre, Activo.codigo, sum_rojas, sum_amarillas)\
        .outerjoin(MovimientoKardex, Activo.id == MovimientoKardex.articulo_id)\
        .group_by(Activo.id)\
        .all()
    
    # Calcular stock actual por artículo (último saldo_registrado)
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
    Retorna las áreas y operaciones activas del catálogo maestro 
    para poblar el dropdown de nuevas transacciones.
    """
    from sqlalchemy import text
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
def get_ferias(db: Session = Depends(get_db)):
    """Retorna las ferias activas del catálogo."""
    from sqlalchemy import text
    result = db.execute(text("SELECT id, nombre, ciudad FROM catalogo_ferias WHERE activa = TRUE ORDER BY nombre"))
    return [{"id": r[0], "nombre": r[1], "ciudad": r[2]} for r in result]

@router.get("/catalogo-areas")
def get_catalogo_areas(db: Session = Depends(get_db)):
    """Retorna todas las áreas del catálogo (activas e inactivas) para administración."""
    from sqlalchemy import text
    result = db.execute(text(
        "SELECT id, nombre_oficial, abreviatura, descripcion, tipo, activa FROM catalogo_areas ORDER BY activa DESC, nombre_oficial"
    ))
    return [{"id": r[0], "nombre": r[1], "abreviatura": r[2], "descripcion": r[3], "tipo": r[4], "activa": r[5]} for r in result]

from pydantic import BaseModel
from datetime import date
from typing import Optional
from app.api.deps import get_current_user
from app.models.usuario import Usuario

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

@router.post("/movimiento-actual")
def registrar_movimiento_actual(
    payload: MovimientoActualCrear, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registra un movimiento operativo en el presente, sumando/restando al último saldo.
    Valida que haya stock suficiente para salidas. Guarda detalles enriquecidos.
    """
    # 1. Obtener el último saldo (considerando legacy + modernos) con BLOQUEO DE FILA para evitar Race Conditions
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
        detalle=f"Movimiento Actual: {payload.observaciones}",
        ingresos=ing if ing > 0 else None,
        salidas=sal if sal > 0 else None,
        saldo_registrado=nuevo_saldo,
        saldo_calculado=nuevo_saldo,
        tiene_error_saldo=False,
        requiere_auditoria_nodo=False,
        nodo_grafo=payload.nodo_grafo,
        observaciones="Registro digital",
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
    return nuevo_mov

@router.get("/historial/{articulo_id}", response_model=List[MovimientoKardexOut])
def get_historial_kardex(articulo_id: int, db: Session = Depends(get_db)):
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
def get_historial_actual(articulo_id: int, db: Session = Depends(get_db)):
    """Solo retorna movimientos modernos (digitales, sin lote_id)."""
    movimientos = db.query(MovimientoKardex)\
        .filter(
            MovimientoKardex.articulo_id == articulo_id,
            MovimientoKardex.lote_id.is_(None)
        )\
        .order_by(MovimientoKardex.id.asc())\
        .all()
    return movimientos

@router.post("/movimiento-actual/{movimiento_id}/anular", response_model=MovimientoKardexOut)
def anular_movimiento_actual(
    movimiento_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Anula un movimiento moderno y recalcula los saldos de los movimientos posteriores del mismo artículo."""
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
        
    # Obtener el saldo del movimiento anterior para base de cálculo
    anterior = db.query(MovimientoKardex)\
        .filter(MovimientoKardex.articulo_id == mov.articulo_id, MovimientoKardex.id < mov.id)\
        .order_by(MovimientoKardex.id.desc())\
        .first()
        
    saldo_actual = anterior.saldo_registrado if anterior else 0
    
    # El movimiento anulado queda con saldo = saldo_anterior
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
    return mov

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
