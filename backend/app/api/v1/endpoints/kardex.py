import os
import shutil
import uuid
import io
import hashlib
from datetime import date, datetime
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, case, text
from starlette.concurrency import run_in_threadpool
from PIL import Image
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.kardex import MovimientoKardex, LotePendiente, SolicitudCargaKardex
from app.models.activos import Activo, CategoriaActivo
from app.models.usuario import Usuario
from app.models.auditoria import AuditoriaSistema
from app.schemas.kardex import MovimientoKardexOut, MovimientoKardexEdit, ExtraccionKardexHoja
from app.services.gemini_service import procesar_lote_imagenes
from app.services.kardex_service import (
    procesar_y_guardar_lote,
    recalcular_saldos_posteriores,
    validar_paginas_lote,
    diferencias_titulos,
)
from app.services.clasificador_nodos import (
    AREA_NO_APLICA,
    AREA_RESUELTA_AUTOMATICAMENTE,
    ESTADOS_AREA_PENDIENTES,
    NODO_AREA_NO_CATALOGADA,
    NODO_DESTINO_NO_ESPECIFICADO,
    NODO_ORIGEN_NO_ESPECIFICADO,
    NODO_PENDIENTE_CLASIFICACION,
    REFERENCIA_AUSENTE,
    REFERENCIA_PRESENTE,
    estado_area_para_nodo_manual,
    normalizar_nodo_grafo,
)
from app.api.deps import get_current_user, require_roles
from app.crud.auditoria import registrar_evento_auditoria
from app.services.huella_lote import huella_de_paginas
from app.services.calidad_kardex import pendiente_hil_sql, tipos_alerta, snapshot_original
from app.services.validacion_carga import preparar_imagen, limites_carga
from app.core.config import settings

router = APIRouter()

STORAGE_DIR = "storage/kardex_images"


@router.get("/limites-carga")
def limites_upload(current_user: Usuario = Depends(get_current_user)):
    return limites_carga()

# ============================================================
# Schemas Locales
# ============================================================

class NuevoArticulo(BaseModel):
    nombre: str


class DecisionLote(BaseModel):
    confirmar: bool

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
        
    # La identidad se calcula ANTES del OCR y antes de escribir nuevas fotos.
    # Así un reintento tras una desconexión recibe el lote original.
    paginas_webp = []
    if not archivos or len(archivos) > settings.KARDEX_MAX_PAGINAS:
        raise HTTPException(400, f"Selecciona de 1 a {settings.KARDEX_MAX_PAGINAS} páginas por lote")
    total_bytes = 0
    huellas_paginas = set()
    for numero, archivo in enumerate(archivos, 1):
        try:
            contenido = await archivo.read(settings.KARDEX_MAX_MB_IMAGEN * 1024 * 1024 + 1)
            if len(contenido) > settings.KARDEX_MAX_MB_IMAGEN * 1024 * 1024:
                raise ValueError(f"Supera el límite de {settings.KARDEX_MAX_MB_IMAGEN} MB por imagen")
            total_bytes += len(contenido)
            if total_bytes > settings.KARDEX_MAX_MB_LOTE * 1024 * 1024:
                raise ValueError(f"El lote supera {settings.KARDEX_MAX_MB_LOTE} MB")
            pagina = preparar_imagen(contenido, archivo.content_type)
            huella_pagina = hashlib.sha256(pagina).digest()
            if huella_pagina in huellas_paginas:
                raise ValueError("Esta página está repetida dentro del mismo lote; retira la copia")
            huellas_paginas.add(huella_pagina)
            paginas_webp.append(pagina)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Página {numero}: {e}") from e
    if not paginas_webp:
        raise HTTPException(400, "Selecciona al menos una página")
    huella = huella_de_paginas(paginas_webp)
    solicitud = SolicitudCargaKardex(
        articulo_id=articulo_id, huella=huella, estado="PROCESANDO",
        usuario_id=current_user.id,
    )
    db.add(solicitud)
    try:
        db.commit()  # La restricción única arbitra solicitudes concurrentes.
    except IntegrityError:
        db.rollback()
        solicitud = db.query(SolicitudCargaKardex).filter_by(
            articulo_id=articulo_id, huella=huella,
        ).first()
        if not solicitud:
            raise
        if solicitud.estado == "COMPLETADO":
            return {"mensaje": "Este lote ya estaba guardado", "lote_id": solicitud.lote_id,
                    "duplicado": True}
        if solicitud.estado == "PENDIENTE":
            if solicitud.usuario_id != current_user.id:
                raise HTTPException(409, "El lote espera confirmación de otro operador")
            pendiente = db.get(LotePendiente, solicitud.pendiente_id)
            if pendiente and pendiente.estado == "PENDIENTE":
                datos = pendiente.extraccion
                return {"requiere_confirmacion": True, "pendiente_id": pendiente.id,
                        "articulo_nombre": datos["articulo_nombre"],
                        "diferencias": datos["diferencias"], "duplicado": True}
        if solicitud.estado in ("FALLIDO", "CANCELADO"):
            # UPDATE condicional: dos reintentos simultáneos no pueden reclamar
            # el mismo intento fallido para producir dos nuevos lotes.
            reclamadas = db.query(SolicitudCargaKardex).filter(
                SolicitudCargaKardex.id == solicitud.id,
                SolicitudCargaKardex.estado.in_(("FALLIDO", "CANCELADO")),
            ).update({"estado": "PROCESANDO", "pendiente_id": None,
                      "usuario_id": current_user.id}, synchronize_session=False)
            if reclamadas != 1:
                db.rollback()
                raise HTTPException(409, "Estas mismas páginas ya se están procesando. Espera antes de reintentar.")
            db.commit()
            solicitud = db.query(SolicitudCargaKardex).filter_by(
                articulo_id=articulo_id, huella=huella,
            ).one()
        else:
            raise HTTPException(409, "Estas mismas páginas ya se están procesando. Espera antes de reintentar.")

    imagenes_paths = []
    try:
        os.makedirs(STORAGE_DIR, exist_ok=True)
        lote_uuid = str(uuid.uuid4())[:8]
        for idx, contenido in enumerate(paginas_webp, 1):
            ruta = os.path.join(STORAGE_DIR, f"lote_{lote_uuid}_pag_{idx}.webp")
            with open(ruta, "wb") as destino:
                destino.write(contenido)
            imagenes_paths.append(ruta)

        try:
            paginas_extraidas = await run_in_threadpool(procesar_lote_imagenes, imagenes_paths)
        except Exception as e:
            raise HTTPException(500, f"Error en Gemini LLM: {e}") from e
        problemas_lote = validar_paginas_lote(paginas_extraidas)
        if problemas_lote:
            raise HTTPException(422, "Lote detenido antes de guardar: " + " ".join(problemas_lote))

        diferencias = diferencias_titulos(activo.nombre, paginas_extraidas)
        if diferencias:
            pendiente = LotePendiente(
                id=str(uuid.uuid4()), articulo_id=articulo_id, usuario_id=current_user.id,
                extraccion={
                    "paginas": [p.model_dump(mode="json") for p in paginas_extraidas],
                    "imagenes_paths": imagenes_paths,
                    "diferencias": diferencias,
                    "articulo_nombre": activo.nombre,
                },
            )
            db.add(pendiente)
            solicitud.estado = "PENDIENTE"
            solicitud.pendiente_id = pendiente.id
            db.commit()
            return {"requiere_confirmacion": True, "pendiente_id": pendiente.id,
                    "articulo_nombre": activo.nombre, "diferencias": diferencias}

        lote = procesar_y_guardar_lote(
            db=db, articulo_id=articulo_id, paginas=paginas_extraidas,
            imagenes_paths=imagenes_paths, confirmar=False,
        )
        solicitud.estado = "COMPLETADO"
        solicitud.lote_id = lote.id
        registrar_evento_auditoria(
            db, usuario_id=current_user.id, accion="subir_lote_kardex",
            recurso="lotes_carga", recurso_id=lote.id, resultado="exito",
            ip_origen=request.client.host if request.client else None,
            detalle={"articulo_id": articulo_id, "total_imagenes": len(archivos)},
        )
        return {"mensaje": "Lote procesado exitosamente", "lote_id": lote.id}
    except Exception:
        db.rollback()
        # El cliente puede reintentar el mismo lote si OCR/almacenamiento falló.
        solicitud = db.query(SolicitudCargaKardex).filter_by(
            articulo_id=articulo_id, huella=huella,
        ).first()
        if solicitud and solicitud.estado == "PROCESANDO":
            solicitud.estado = "FALLIDO"
            db.commit()
        raise


@router.post("/lotes-pendientes/{pendiente_id}/decision")
def decidir_lote(
    pendiente_id: str,
    payload: DecisionLote,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    pendiente = db.query(LotePendiente).filter(
        LotePendiente.id == pendiente_id,
        LotePendiente.usuario_id == current_user.id,
    ).with_for_update().first()
    if not pendiente:
        raise HTTPException(404, "Extracción pendiente no encontrada")
    if pendiente.estado == "CONFIRMADO" and payload.confirmar:
        return {"lote_id": pendiente.lote_id, "mensaje": "Lote ya guardado"}
    if pendiente.estado != "PENDIENTE":
        if pendiente.estado == "CANCELADO" and not payload.confirmar:
            return {"mensaje": "Lote cancelado"}
        raise HTTPException(409, "La extracción ya tiene una decisión registrada")

    datos = pendiente.extraccion
    solicitud = db.query(SolicitudCargaKardex).filter_by(pendiente_id=pendiente.id).first()
    if payload.confirmar:
        lote = procesar_y_guardar_lote(
            db, pendiente.articulo_id,
            [ExtraccionKardexHoja.model_validate(p) for p in datos["paginas"]],
            datos["imagenes_paths"], confirmar=False,
        )
        pendiente.lote_id = lote.id
        pendiente.estado = "CONFIRMADO"
        if solicitud:
            solicitud.estado = "COMPLETADO"
            solicitud.lote_id = lote.id
    else:
        pendiente.estado = "CANCELADO"
        if solicitud:
            solicitud.estado = "CANCELADO"
    # Auditoría, decisión y movimientos se confirman juntos.
    registrar_evento_auditoria(
        db, usuario_id=current_user.id,
        accion="confirmar_titulos_lote" if payload.confirmar else "cancelar_titulos_lote",
        recurso="lotes_carga", recurso_id=pendiente.lote_id, resultado="exito",
        ip_origen=request.client.host if request.client else None,
        detalle={"pendiente_id": pendiente.id, "articulo_id": pendiente.articulo_id,
                 "articulo_nombre": datos["articulo_nombre"],
                 "diferencias": datos["diferencias"]},
    )
    return {"lote_id": pendiente.lote_id, "mensaje": "Lote guardado" if payload.confirmar else "Lote cancelado"}


@router.put("/movimiento/{movimiento_id}", response_model=MovimientoKardexOut)
def update_movimiento_kardex(
    request: Request,
    movimiento_id: int, 
    payload: MovimientoKardexEdit, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador"))
):
    """Permite corregir un movimiento legacy en Human-In-The-Loop y recalcula saldos en cascada."""
    movimiento = db.query(MovimientoKardex).filter(MovimientoKardex.id == movimiento_id).with_for_update().first()
    if not movimiento:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    if movimiento.lote_id is None:
        raise HTTPException(400, "El HIL solo corrige Kárdex histórico; no modifica operaciones modernas")
    if not payload.motivo.strip():
        raise HTTPException(400, "Indica el motivo y la evidencia de la revisión")
    referencia_final = payload.referencia if "referencia" in payload.model_fields_set else movimiento.referencia
    if payload.referencia_estado == "PRESENTE" and not (referencia_final or "").strip():
        raise HTTPException(400, "Una referencia presente debe tener texto legible")
        
    campos_revision = ("ingresos", "salidas", "saldo_registrado", "nodo_grafo", "fecha_movimiento",
                       "fecha_estado", "area_estado", "referencia", "referencia_estado")
    def valores():
        return {campo: (getattr(movimiento, campo).isoformat() if campo == "fecha_movimiento"
                         else getattr(movimiento, campo)) for campo in campos_revision}
    valores_previos = valores()
    if movimiento.datos_originales is None:
        movimiento.datos_originales = snapshot_original(movimiento)
    if movimiento.fecha_original is None:
        movimiento.fecha_original = movimiento.fecha_movimiento
    if payload.decision_fecha == "corregir":
        movimiento.fecha_movimiento = payload.fecha_movimiento
        movimiento.fecha_estado = "CORREGIDA"
    elif payload.decision_fecha == "confirmar_documento":
        movimiento.fecha_estado = "CONFIRMADA_DOCUMENTO"
    
    if "ingresos" in payload.model_fields_set:
        movimiento.ingresos = payload.ingresos
    if "salidas" in payload.model_fields_set:
        movimiento.salidas = payload.salidas
    movimiento.saldo_registrado = payload.saldo_registrado
    if "referencia" in payload.model_fields_set:
        movimiento.referencia = payload.referencia.strip() if payload.referencia else None
    
    if payload.nodo_grafo is not None:
        nodo_grafo, _ = normalizar_nodo_grafo(
            payload.nodo_grafo,
            movimiento.ingresos or 0,
            movimiento.salidas or 0,
        )
        area_estado, requiere_auditoria = estado_area_para_nodo_manual(nodo_grafo)
        movimiento.nodo_grafo = nodo_grafo
        movimiento.area_estado = area_estado
        movimiento.requiere_auditoria_nodo = requiere_auditoria

    if payload.area_estado is not None:
        movimiento.area_estado = payload.area_estado
        movimiento.requiere_auditoria_nodo = (
            payload.area_estado in ESTADOS_AREA_PENDIENTES
        )

    if payload.referencia_estado is not None:
        movimiento.referencia_estado = payload.referencia_estado
        movimiento.requiere_auditoria_referencia = (
            payload.referencia_estado in {"ILEGIBLE", "INCIERTA"}
        )
        
    # Corrección, recalculo y auditoría se confirman juntos; no quedan cambios sin autoría.
    try:
        recalcular_saldos_posteriores(db, movimiento.articulo_id, confirmar=False)
        registrar_evento_auditoria(
            db, usuario_id=current_user.id, accion="corregir_kardex_hil",
            recurso="movimientos_kardex", recurso_id=movimiento_id, resultado="exito",
            ip_origen=request.client.host if request.client else None,
            detalle={"previo": valores_previos, "nuevo": valores(), "motivo": payload.motivo.strip(),
                     "decision_fecha": payload.decision_fecha}
        )
    except Exception:
        db.rollback()
        raise
    
    return movimiento


@router.get("/movimiento/{movimiento_id}/revisiones")
def revisiones_movimiento(
    movimiento_id: int, db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if not db.get(MovimientoKardex, movimiento_id):
        raise HTTPException(404, "Movimiento no encontrado")
    registros = db.query(AuditoriaSistema, Usuario.nombre).outerjoin(
        Usuario, Usuario.id == AuditoriaSistema.usuario_id
    ).filter(AuditoriaSistema.accion == "corregir_kardex_hil",
             AuditoriaSistema.recurso == "movimientos_kardex",
             AuditoriaSistema.recurso_id == movimiento_id).order_by(AuditoriaSistema.id.desc()).all()
    return [{"id": a.id, "fecha": a.fecha_hora, "usuario": nombre or "Usuario no disponible",
             "detalle": a.detalle} for a, nombre in registros]


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
    sum_amarillas = func.sum(case((or_(
        MovimientoKardex.requiere_auditoria_nodo == True,
        MovimientoKardex.requiere_auditoria_referencia == True,
        MovimientoKardex.fecha_estado == "PENDIENTE_HIL",
    ), 1), else_=0)).label('amarillas')
    
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
    tipo: Optional[Literal["saldo", "fecha", "area", "referencia"]] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Retorna movimientos con error de saldo o nodo dudoso para revisión HIL."""
    query = db.query(MovimientoKardex, Activo.nombre.label("articulo_nombre"))\
        .join(Activo, MovimientoKardex.articulo_id == Activo.id)\
        .filter(MovimientoKardex.lote_id.isnot(None), MovimientoKardex.estado == "ACTIVO", pendiente_hil_sql())
        
    if articulo_id:
        query = query.filter(MovimientoKardex.articulo_id == articulo_id)
        
    if tipo:
        condiciones = {"saldo": MovimientoKardex.tiene_error_saldo.is_(True),
                       "fecha": MovimientoKardex.fecha_estado == "PENDIENTE_HIL",
                       "area": or_(MovimientoKardex.requiere_auditoria_nodo.is_(True), MovimientoKardex.area_estado.in_(ESTADOS_AREA_PENDIENTES)),
                       "referencia": or_(MovimientoKardex.requiere_auditoria_referencia.is_(True), MovimientoKardex.referencia_estado.in_(("ILEGIBLE", "INCIERTA")))}
        query = query.filter(condiciones[tipo])
    errores = query.order_by(Activo.nombre.asc(), MovimientoKardex.lote_id.asc(),
                             MovimientoKardex.numero_pagina.asc(), MovimientoKardex.orden_fila.asc(),
                             MovimientoKardex.id.asc()).all()
        
    resultado = []
    for mov, articulo_nombre in errores:
        dto = MovimientoKardexOut.model_validate(mov).model_dump()
        dto["articulo_nombre"] = articulo_nombre
        dto["tipos_alerta"] = tipos_alerta(mov)
        if dto.get("ruta_imagen_respaldo"):
            path = dto["ruta_imagen_respaldo"].replace("\\", "/")
            dto["url_imagen"] = f"/{path}" 
        resultado.append(dto)
        
    return resultado


@router.get("/grafo/{articulo_id}")
def get_grafo_articulo(
    articulo_id: int,
    incluir_pendientes: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Genera nodos y enlaces dirigidos; un área puede tener entradas y salidas."""
    movimientos = db.query(
        MovimientoKardex.nodo_grafo,
        MovimientoKardex.area_estado,
        func.sum(MovimientoKardex.ingresos).label("total_ingresos"),
        func.sum(MovimientoKardex.salidas).label("total_salidas")
    ).filter(
        MovimientoKardex.articulo_id == articulo_id
    ).group_by(
        MovimientoKardex.nodo_grafo,
        MovimientoKardex.area_estado,
    ).all()
    
    totales_por_nodo = {}
    for mov in movimientos:
        total_ingresos = int(mov.total_ingresos or 0)
        total_salidas = int(mov.total_salidas or 0)
        nodo, pendiente_legacy = normalizar_nodo_grafo(
            mov.nodo_grafo,
            total_ingresos,
            total_salidas,
        )
        pendiente = mov.area_estado in ESTADOS_AREA_PENDIENTES or pendiente_legacy
        if pendiente and not incluir_pendientes:
            continue
        totales = totales_por_nodo.setdefault(
            nodo,
            {"ingresos": 0, "salidas": 0, "requiere_auditoria": False},
        )
        totales["ingresos"] += total_ingresos
        totales["salidas"] += total_salidas
        totales["requiere_auditoria"] = (
            totales["requiere_auditoria"] or pendiente
        )

    nodos_vistos = {"Almacén Central"}
    links = []

    for nodo, totales in totales_por_nodo.items():
        nodos_vistos.add(nodo)

        tot_in = totales["ingresos"]
        tot_out = totales["salidas"]

        if tot_out > 0:
            links.append({"source": "Almacén Central", "target": nodo, "value": tot_out})
        if tot_in > 0:
            links.append({"source": nodo, "target": "Almacén Central", "value": tot_in})
            
    nodos = []
    for nombre in nodos_vistos:
        nodo = {
            "name": nombre,
            "requiere_auditoria": totales_por_nodo.get(nombre, {}).get("requiere_auditoria", False),
        }
        if nombre == NODO_AREA_NO_CATALOGADA:
            nodo.update({
                "tipo": "no_catalogada",
                "requiere_auditoria": True,
                "itemStyle": {"color": "#f59e0b"},
            })
        elif nombre == NODO_PENDIENTE_CLASIFICACION:
            nodo.update({
                "tipo": "pendiente_hil",
                "requiere_auditoria": True,
                "itemStyle": {"color": "#ef4444"},
            })
        elif nombre in {
            NODO_ORIGEN_NO_ESPECIFICADO,
            NODO_DESTINO_NO_ESPECIFICADO,
        }:
            nodo.update({
                "tipo": "sin_area_registrada",
                "requiere_auditoria": False,
                "itemStyle": {"color": "#64748b"},
            })
        nodos.append(nodo)
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
        .order_by(
            MovimientoKardex.lote_id.asc(),
            MovimientoKardex.numero_pagina.asc().nullslast(),
            MovimientoKardex.orden_fila.asc().nullslast(),
            MovimientoKardex.id.asc()
        )\
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
    if not payload.nodo_grafo.strip():
        raise HTTPException(status_code=400, detail="Debe seleccionar un nodo para la operación.")

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
        requiere_auditoria_referencia=False,
        nodo_grafo=payload.nodo_grafo,
        area_estado=(
            AREA_RESUELTA_AUTOMATICAMENTE
            if payload.nodo_grafo.startswith("Área: ")
            else AREA_NO_APLICA
        ),
        referencia_estado=(
            REFERENCIA_PRESENTE
            if payload.referencia_documento
            else REFERENCIA_AUSENTE
        ),
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
