import os
import uuid
import hashlib
import hmac
import json
from datetime import datetime, timedelta, UTC
from zoneinfo import ZoneInfo
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, Query
from pydantic import AwareDatetime, BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, func, or_, case, text
from starlette.concurrency import run_in_threadpool
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.kardex import MovimientoKardex, LotePendiente, SolicitudCargaKardex, LoteCarga
from app.models.activos import Activo, CategoriaActivo
from app.models.area import Area
from app.models.usuario import Usuario
from app.models.inventario import AperturaInventario, ConciliacionInicial
from app.services.inventario import (
    auditar, apertura_dict, asegurar_apertura_desde_kardex,
    base_kardex_dict, ultimos_cierres_kardex, ultimo_cierre_kardex,
    cambiar_existencia_area, verificar_distribucion, distribucion_dict,
    cantidad_efectiva_movimiento, cantidad_devuelta_efectiva,
)
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
from app.services.control_movimientos import CATALOGO_OPERACIONES, evaluar_movimiento, firma_confirmacion, validar_operacion
from app.services.control_alertas import registrar_caso
from app.services.control_movimientos import (
    parametros_control, politica_control, evaluar_ubicacion,
    cantidades_comparables, aviso_repeticion, stock_ubicacion,
)
from app.services.calidad_kardex import pendiente_hil_sql, tipos_alerta, snapshot_original
from app.services.validacion_carga import preparar_imagen, limites_carga
from app.core.config import settings

router = APIRouter()

STORAGE_DIR = "storage/kardex_images"
SERVER_INSTANCE_ID = str(uuid.uuid4())


@router.get("/tandas")
def listar_tandas(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    filas = db.query(LoteCarga.tanda, func.count(MovimientoKardex.id)).join(
        MovimientoKardex, MovimientoKardex.lote_id == LoteCarga.id,
    ).filter(MovimientoKardex.estado == "ACTIVO").group_by(LoteCarga.tanda).all()
    conteos = dict(filas)
    lotes = dict(db.query(LoteCarga.tanda, func.count(LoteCarga.id)).group_by(LoteCarga.tanda).all())
    disponibles = sorted({1, 2, settings.KARDEX_TANDA_ACTUAL} | set(conteos) | set(lotes))
    return {"tanda_nuevas_cargas": settings.KARDEX_TANDA_ACTUAL, "tandas": [
        {"id": n, "nombre": f"Tanda {n}", "movimientos": conteos.get(n, 0), "escaneos": lotes.get(n, 0)}
        for n in disponibles
    ]}


@router.get("/limites-carga")
def limites_upload(current_user: Usuario = Depends(get_current_user)):
    return limites_carga()


@router.get("/solicitudes")
def estado_solicitudes(
    articulo_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    """Permite distinguir OCR en curso, confirmación y reintento tras reinicio."""
    filas = db.query(SolicitudCargaKardex).filter_by(articulo_id=articulo_id).order_by(
        SolicitudCargaKardex.id.desc()).limit(20).all()
    return [{"id": s.id, "estado": s.estado, "tanda": s.tanda, "huella": s.huella,
             "lote_id": s.lote_id, "pendiente_id": s.pendiente_id,
             "intento": s.intento, "creado_en": s.creado_en,
             "reintentable": s.estado in ("FALLIDO", "CANCELADO") or (
                 s.estado == "PROCESANDO" and s.servidor_instancia is not None
                 and s.servidor_instancia != SERVER_INSTANCE_ID)} for s in filas]

# ============================================================
# Schemas Locales
# ============================================================

class NuevoArticulo(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)


class DecisionLote(BaseModel):
    confirmar: bool

class MovimientoActualCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    articulo_id: int
    solicitud_id: uuid.UUID
    encargado_id: Optional[int] = Field(default=None, gt=0)
    tipo: Literal["ingreso", "salida"]
    cantidad: int = Field(strict=True, le=2147483647)
    fecha_operacion: Optional[AwareDatetime] = None
    nodo_grafo: str
    observaciones: str = ""
    # Campos enriquecidos
    tipo_operacion: Optional[str] = None
    receptor: Optional[str] = Field(default=None, max_length=200)
    receptor_tipo: Optional[Literal["PERSONA", "INSTITUCION", "PUBLICO_GENERAL"]] = None
    area_operativa_id: Optional[int] = Field(default=None, gt=0)
    feria_id: Optional[int] = None
    ciudad_feria: Optional[str] = None
    canal_venta: Optional[str] = None
    motivo_baja: Optional[str] = None
    movimiento_origen_id: Optional[int] = Field(default=None, gt=0)
    devuelto_por: Optional[str] = Field(default=None, max_length=200)
    referencia_documento: str = Field(min_length=3, max_length=200)
    confirmacion_alertas: Optional[str] = Field(default=None, min_length=64, max_length=64)
    motivo_alertas: str = Field(default="", max_length=1000)


# ============================================================
# 1. Digitalización de Kárdex Histórico (Legacy)
# ============================================================

@router.post("/upload-lote")
async def upload_lote(
    request: Request,
    articulo_id: int = Form(...),
    tanda: int | None = Form(None, ge=1, le=9999),
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
        usuario_id=current_user.id, tanda=tanda or settings.KARDEX_TANDA_ACTUAL,
        intento=1, servidor_instancia=SERVER_INSTANCE_ID,
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
                    "duplicado": True, "tanda": solicitud.tanda}
        if solicitud.estado == "PENDIENTE":
            if solicitud.usuario_id != current_user.id:
                raise HTTPException(409, "El lote espera confirmación de otro operador")
            pendiente = db.get(LotePendiente, solicitud.pendiente_id)
            if pendiente and pendiente.estado == "PENDIENTE":
                datos = pendiente.extraccion
                return {"requiere_confirmacion": True, "pendiente_id": pendiente.id,
                        "articulo_nombre": datos["articulo_nombre"],
                        "diferencias": datos["diferencias"], "duplicado": True, "tanda": solicitud.tanda}
        estado_previo = solicitud.estado
        intento_previo = solicitud.intento
        recuperable = estado_previo in ("FALLIDO", "CANCELADO") or (
            estado_previo == "PROCESANDO" and solicitud.servidor_instancia is not None
            and solicitud.servidor_instancia != SERVER_INSTANCE_ID)
        if recuperable:
            # UPDATE condicional: dos reintentos simultáneos no pueden reclamar
            # el mismo intento fallido para producir dos nuevos lotes.
            reclamadas = db.query(SolicitudCargaKardex).filter(
                SolicitudCargaKardex.id == solicitud.id,
                SolicitudCargaKardex.estado == estado_previo,
                SolicitudCargaKardex.intento == intento_previo,
            ).update({"estado": "PROCESANDO", "pendiente_id": None,
                      "usuario_id": current_user.id,
                      "intento": intento_previo + 1,
                      "servidor_instancia": SERVER_INSTANCE_ID}, synchronize_session=False)
            if reclamadas != 1:
                db.rollback()
                raise HTTPException(409, "Estas mismas páginas ya se están procesando. Espera antes de reintentar.")
            db.commit()
            solicitud = db.query(SolicitudCargaKardex).filter_by(
                articulo_id=articulo_id, huella=huella,
            ).one()
        else:
            raise HTTPException(409, "Estas mismas páginas ya se están procesando. Espera antes de reintentar.")

    intento_actual = solicitud.intento
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

        db.refresh(solicitud)
        if (solicitud.estado != "PROCESANDO" or solicitud.intento != intento_actual
                or solicitud.servidor_instancia != SERVER_INSTANCE_ID):
            raise HTTPException(409, "Este intento fue recuperado por otra instancia. Consulta el estado antes de repetirlo.")

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
                    "articulo_nombre": activo.nombre, "diferencias": diferencias, "tanda": solicitud.tanda}

        lote = procesar_y_guardar_lote(
            db=db, articulo_id=articulo_id, paginas=paginas_extraidas,
            imagenes_paths=imagenes_paths, confirmar=False, tanda=solicitud.tanda,
        )
        solicitud.estado = "COMPLETADO"
        solicitud.lote_id = lote.id
        registrar_evento_auditoria(
            db, usuario_id=current_user.id, accion="subir_lote_kardex",
            recurso="lotes_carga", recurso_id=lote.id, resultado="exito",
            ip_origen=request.client.host if request.client else None,
            detalle={"articulo_id": articulo_id, "total_imagenes": len(archivos), "tanda": lote.tanda},
        )
        return {"mensaje": "Lote procesado exitosamente", "lote_id": lote.id, "tanda": lote.tanda}
    except Exception:
        db.rollback()
        # El cliente puede reintentar el mismo lote si OCR/almacenamiento falló.
        solicitud = db.query(SolicitudCargaKardex).filter_by(
            articulo_id=articulo_id, huella=huella,
        ).first()
        if solicitud and solicitud.estado == "PROCESANDO" and (
            solicitud.intento == intento_actual
            and solicitud.servidor_instancia == SERVER_INSTANCE_ID
        ):
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
        return {"lote_id": pendiente.lote_id, "mensaje": "Lote ya guardado", "tanda": db.get(LoteCarga, pendiente.lote_id).tanda}
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
            datos["imagenes_paths"], confirmar=False, tanda=solicitud.tanda if solicitud else 1,
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
                 "diferencias": datos["diferencias"], "tanda": solicitud.tanda if solicitud else 1},
    )
    return {"lote_id": pendiente.lote_id, "mensaje": "Lote guardado" if payload.confirmar else "Lote cancelado", "tanda": solicitud.tanda if solicitud else 1}


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
                       "fecha_estado", "area_estado", "referencia", "referencia_estado", "revision_documental")
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
        origen = payload.origen_fecha or "FOTO"
        revision = dict(movimiento.revision_documental or {})
        revision.update(origen_fecha=origen, motivo_fecha=payload.motivo.strip(),
                        motivo=payload.motivo.strip(), criterios=revision.get("criterios", ["HIL_MANUAL"]))
        if origen == "FOTO":
            revision["fecha_documental"] = payload.fecha_movimiento.isoformat()
        else:
            revision.setdefault("fecha_documental", None)
        movimiento.revision_documental = revision
        movimiento.fecha_estado = "ESTIMADA_HIL" if origen != "FOTO" else "CORREGIDA"
    elif payload.decision_fecha == "confirmar_documento":
        movimiento.fecha_estado = "CONFIRMADA_DOCUMENTO"
    
    if "ingresos" in payload.model_fields_set:
        movimiento.ingresos = payload.ingresos
    if "salidas" in payload.model_fields_set:
        movimiento.salidas = payload.salidas
    movimiento.saldo_registrado = payload.saldo_registrado
    if movimiento.revision_documental:
        revision = dict(movimiento.revision_documental)
        if payload.saldo_registrado != valores_previos["saldo_registrado"]:
            revision["usar_saldo_esperado"] = False
            revision["origen_saldo"] = "REVISION_HUMANA"
        revision["ultima_revision_manual"] = payload.motivo.strip()
        movimiento.revision_documental = revision
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
    return [{"id": a.id, "fecha": a.fecha_hora, "usuario": nombre or (a.detalle or {}).get("autor_registro", "Usuario no disponible"),
             "detalle": a.detalle} for a, nombre in registros]


class ObservacionHilArticulo(BaseModel):
    observado: bool
    excluir_entrenamiento: bool = False
    motivo: str = Field(min_length=8, max_length=2000)


@router.put("/articulos/{articulo_id}/observacion-hil")
def revisar_observacion_articulo(
    articulo_id: int, payload: ObservacionHilArticulo, request: Request,
    db: Session = Depends(get_db), usuario: Usuario = Depends(require_roles("Administrador", "Auditor")),
):
    if payload.excluir_entrenamiento and not payload.observado:
        raise HTTPException(422, "La exclusión documental requiere una observación vigente")
    articulo = db.query(Activo).filter_by(id=articulo_id).with_for_update().first()
    if not articulo:
        raise HTTPException(404, "Artículo no encontrado")
    anterior = articulo.observacion_hil
    articulo.observacion_hil = {"observado": payload.observado,
        "excluir_entrenamiento": payload.excluir_entrenamiento, "motivo": payload.motivo.strip(),
        "revisado_por": usuario.id, "revisado_en": datetime.now(UTC).isoformat()}
    auditar(db, usuario, request, "revisar_observacion_hil", "activo", articulo_id,
            {"previo": anterior, "nuevo": articulo.observacion_hil})
    db.commit()
    return articulo.observacion_hil


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

    nombre = payload.nombre.strip().upper()
    if len(nombre) > 150:
        raise HTTPException(422, "El nombre normalizado supera los 150 caracteres")
    try:
        cat = db.query(CategoriaActivo).filter_by(nombre="Digitalizados").first()
        if cat is None:
            # La restricción única arbitra dos altas iniciales concurrentes.
            try:
                with db.begin_nested():
                    cat = CategoriaActivo(nombre="Digitalizados", descripcion="Artículos creados desde Kárdex Digital")
                    db.add(cat)
                    db.flush()
            except IntegrityError:
                cat = db.query(CategoriaActivo).filter_by(nombre="Digitalizados").one()

        nuevo_activo = Activo(categoria_id=cat.id, codigo=f"KDX-{uuid.uuid4().hex}",
                              nombre=nombre, unidad_medida="unidad")
        db.add(nuevo_activo)
        db.flush()
        registrar_evento_auditoria(
            db, usuario_id=current_user.id, accion="crear_articulo", recurso="activo",
            recurso_id=nuevo_activo.id, resultado="exito",
            ip_origen=request.client.host if request.client else None,
            detalle={"codigo": nuevo_activo.codigo, "nombre": nuevo_activo.nombre}, commit=False,
        )
        resultado = {"id": nuevo_activo.id, "nombre": nuevo_activo.nombre, "codigo": nuevo_activo.codigo}
        db.commit()
        return resultado
    except Exception:
        db.rollback()
        raise


@router.get("/articulos")
def get_articulos_typeahead(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listado de artículos con conteo de alertas y stock actual calculado."""
    historico_activo = and_(MovimientoKardex.estado == "ACTIVO", MovimientoKardex.lote_id.isnot(None))
    sum_rojas = func.sum(case((and_(historico_activo, MovimientoKardex.tiene_error_saldo.is_(True)), 1), else_=0)).label('rojas')
    sum_amarillas = func.sum(case((and_(historico_activo, or_(
        MovimientoKardex.requiere_auditoria_nodo == True,
        MovimientoKardex.requiere_auditoria_referencia == True,
        MovimientoKardex.fecha_estado == "PENDIENTE_HIL",
        MovimientoKardex.area_estado.in_(ESTADOS_AREA_PENDIENTES),
        MovimientoKardex.referencia_estado.in_(("ILEGIBLE", "INCIERTA")),
    )), 1), else_=0)).label('amarillas')
    
    resultados = db.query(Activo.id, Activo.nombre, Activo.codigo, Activo.observacion_hil, sum_rojas, sum_amarillas)\
        .outerjoin(MovimientoKardex, Activo.id == MovimientoKardex.articulo_id)\
        .filter(or_(Activo.estado == "activo", MovimientoKardex.id.isnot(None)))\
        .group_by(Activo.id)\
        .all()
    
    aperturas = {a.articulo_id: a for a in db.query(AperturaInventario).all()}
    conciliaciones = {c.articulo_id: c for c in db.query(ConciliacionInicial).all()}
    cierres = ultimos_cierres_kardex(db)
    lista = []
    for a in resultados:
        apertura = aperturas.get(a.id)
        conciliacion = conciliaciones.get(a.id)
        base_kardex = base_kardex_dict(cierres.get(a.id))
        stock = apertura.cantidad_actual if apertura else (
            base_kardex["saldo"] if base_kardex else None)
        diferencia = None
        if apertura and apertura.origen == "KARDEX_HISTORICO" and base_kardex:
            if (base_kardex["movimiento_id"] != apertura.movimiento_historico_id
                    or base_kardex["saldo"] != apertura.cantidad_inicial):
                diferencia = {
                    "saldo_base_congelada": apertura.cantidad_inicial,
                    "saldo_cierre_disponible": base_kardex["saldo"],
                    "diferencia": base_kardex["saldo"] - apertura.cantidad_inicial,
                    "nuevo_movimiento_id": base_kardex["movimiento_id"],
                    "requiere_conciliacion": True,
                }
        lista.append({
            "id": a.id, 
            "nombre": a.nombre, 
            "codigo": a.codigo,
            "observacion_hil": a.observacion_hil,
            "alertas_rojas": a.rojas or 0,
            "alertas_amarillas": a.amarillas or 0,
            "stock_actual": stock,
            "apertura": apertura_dict(apertura),
            "conciliacion_inicial": ({"fecha_conteo": conciliacion.fecha_conteo,
                                     "cantidad_base": conciliacion.cantidad_base,
                                     "cantidad_fisica": conciliacion.cantidad_fisica,
                                     "diferencia": conciliacion.diferencia,
                                     "ajuste_movimiento_id": conciliacion.ajuste_movimiento_id}
                                    if conciliacion else None),
            "base_kardex": base_kardex,
            "diferencia_documental": diferencia,
            "corte_operativo": ({
                "fecha_inicio": apertura.aprobado_en,
                "base": apertura.origen,
                "estado": ("CONTEO_FISICO_CONCILIADO" if conciliacion else
                           "BASE_DOCUMENTAL_PROVISIONAL" if apertura.origen == "KARDEX_HISTORICO"
                           else "CONTEO_FISICO_VERIFICADO"),
                "movimientos_previos_no_registrados": (
                    "SALDO_CONCILIADO_DETALLE_PENDIENTE" if conciliacion else
                    "POR_CONCILIAR" if apertura.origen == "KARDEX_HISTORICO"
                    else "CUBIERTOS_POR_CONTEO"),
            } if apertura else None),
        })
    return lista


@router.get("/errores")
def get_errores_human_in_the_loop(
    articulo_id: Optional[int] = None,
    tipo: Optional[Literal["saldo", "fecha", "area", "referencia"]] = None,
    tanda: Optional[int] = Query(None, ge=1, le=9999),
    tratamiento: Optional[Literal["POR_CATEGORIZAR", "CATEGORIZADO_CON_MARCA", "REQUIERE_RECATEGORIZAR"]] = None,
    categoria: Optional[Literal["DISCREPANCIA_DOCUMENTAL", "AMBITO_DOCUMENTAL_INCIERTO", "DEPENDENCIA_OTRA_FILA", "POSIBLE_DUPLICIDAD_DOCUMENTAL", "CATALOGO_NO_CONFIRMADO", "LECTURA_INCIERTA", "MARCA_NO_INTERPRETADA", "EFECTO_INDETERMINADO"]] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Avisos históricos: el tratamiento documentado no retira la incertidumbre."""
    query = db.query(MovimientoKardex, Activo.nombre.label("articulo_nombre"))\
        .join(Activo, MovimientoKardex.articulo_id == Activo.id)\
        .filter(MovimientoKardex.lote_id.isnot(None), MovimientoKardex.estado == "ACTIVO", pendiente_hil_sql())
        
    query = query.options(selectinload(MovimientoKardex.lote))
    if tanda is not None:
        query = query.join(LoteCarga, LoteCarga.id == MovimientoKardex.lote_id).filter(LoteCarga.tanda == tanda)
    if articulo_id:
        query = query.filter(MovimientoKardex.articulo_id == articulo_id)
        
    if tipo:
        condiciones = {"saldo": MovimientoKardex.tiene_error_saldo.is_(True),
                       "fecha": MovimientoKardex.fecha_estado == "PENDIENTE_HIL",
                       "area": or_(MovimientoKardex.requiere_auditoria_nodo.is_(True), MovimientoKardex.area_estado.in_(ESTADOS_AREA_PENDIENTES)),
                       "referencia": or_(MovimientoKardex.requiere_auditoria_referencia.is_(True), MovimientoKardex.referencia_estado.in_(("ILEGIBLE", "INCIERTA")))}
        query = query.filter(condiciones[tipo])
    errores = query.order_by(Activo.nombre.asc(), MovimientoKardex.lote_id.asc(),
                             func.coalesce(MovimientoKardex.orden_pagina_validado, MovimientoKardex.numero_pagina).asc(), MovimientoKardex.orden_fila.asc(),
                             MovimientoKardex.id.asc()).all()
        
    resultado = []
    for mov, articulo_nombre in errores:
        dto = MovimientoKardexOut.model_validate(mov).model_dump()
        dto["articulo_nombre"] = articulo_nombre
        dto["tipos_alerta"] = tipos_alerta(mov)
        resumen = dto["tratamiento_hil"] or {}
        if tratamiento and resumen.get("estado") != tratamiento:
            continue
        if categoria and categoria not in resumen.get("categorias", []):
            continue
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
        MovimientoKardex.articulo_id == articulo_id,
        MovimientoKardex.estado == "ACTIVO",
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


@router.get("/encargados")
def listar_encargados(
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    """Cuentas activas seleccionables como responsables del movimiento."""
    usuarios = db.query(Usuario).filter(Usuario.estado == "activo").order_by(
        Usuario.nombre, Usuario.id,
    ).all()
    return [{"id": usuario.id, "nombre": usuario.nombre} for usuario in usuarios]


@router.get("/operaciones-inventario")
def operaciones_inventario(_current_user: Usuario = Depends(get_current_user)):
    """Operaciones modernas; el catálogo de nodos OCR no define reglas de stock."""
    return [{**op, "habilitada": op.get("habilitada", True)}
            for op in CATALOGO_OPERACIONES]


@router.get("/politica-control")
def consultar_politica_control(_usuario: Usuario = Depends(get_current_user)):
    return politica_control()


@router.get("/areas-operativas")
def areas_operativas(db: Session = Depends(get_db),
                    _usuario: Usuario = Depends(get_current_user)):
    """Ubicaciones físicas registradas; no incluye nodos de operación del OCR."""
    return [{"id": a.id, "nombre": a.nombre} for a in db.query(Area).filter(
        Area.estado == "activo").order_by(Area.nombre).all()]


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
    tanda: Optional[int] = Query(None, ge=1, le=9999),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Escaneos del papel; la tanda es procedencia, independiente de su gestión."""
    query = db.query(MovimientoKardex).options(selectinload(MovimientoKardex.lote)).filter(
        MovimientoKardex.articulo_id == articulo_id,
        MovimientoKardex.lote_id.isnot(None),
    )
    if tanda is not None:
        query = query.join(LoteCarga, LoteCarga.id == MovimientoKardex.lote_id).filter(LoteCarga.tanda == tanda)
    return query.order_by(
        MovimientoKardex.lote_id.asc(), func.coalesce(MovimientoKardex.orden_pagina_validado, MovimientoKardex.numero_pagina).asc().nullslast(),
        MovimientoKardex.orden_fila.asc().nullslast(), MovimientoKardex.id.asc(),
    ).all()


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

@router.get("/devoluciones-disponibles/{articulo_id}")
def devoluciones_disponibles(
    articulo_id: int,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    if db.get(Activo, articulo_id) is None:
        raise HTTPException(404, "Artículo no encontrado")
    apertura = db.get(AperturaInventario, articulo_id)
    if apertura is None:
        return []
    salidas = db.query(MovimientoKardex).filter(
        MovimientoKardex.articulo_id == articulo_id,
        MovimientoKardex.lote_id.is_(None),
        MovimientoKardex.id > apertura.ultimo_moderno_id,
        MovimientoKardex.estado == "ACTIVO",
        MovimientoKardex.tipo_operacion.in_(("Ventas", "Obsequios y Donaciones")),
    ).order_by(MovimientoKardex.id.desc()).all()
    resultado = []
    for salida in salidas:
        cantidad_vigente = cantidad_efectiva_movimiento(db, salida)
        devuelto = cantidad_devuelta_efectiva(db, salida.id)
        pendiente = cantidad_vigente - devuelto
        if pendiente > 0:
            resultado.append({"id": salida.id, "tipo_operacion": salida.tipo_operacion,
                              "receptor": salida.receptor, "cantidad_original": cantidad_vigente,
                              "cantidad_devuelta": devuelto, "cantidad_pendiente": pendiente,
                              "referencia_documento": salida.referencia_documento,
                              "ocurrido_en": salida.ocurrido_en})
    return resultado

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
    solicitud_id = str(payload.solicitud_id)
    contenido_huella = payload.model_dump(mode="json", exclude={
        "confirmacion_alertas", "motivo_alertas"})
    contenido_huella["usuario_registrador_id"] = current_user.id
    solicitud_huella = hashlib.sha256(json.dumps(
        contenido_huella, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode()).hexdigest()

    def movimiento_previo():
        previo = db.query(MovimientoKardex).filter_by(solicitud_id=solicitud_id).first()
        if previo is not None:
            if previo.solicitud_huella != solicitud_huella:
                raise HTTPException(409, "Esta clave de solicitud ya corresponde a otra operación. Inicia una transacción nueva.")
            if previo.estado == "ANULADO":
                raise HTTPException(409, "Esta operación ya fue anulada. Consulta el historial antes de registrar otra.")
            return previo
        return None

    previo = movimiento_previo()
    if previo is not None:
        return previo
    if payload.cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a 0.")
    if (payload.tipo_operacion or "").strip().casefold() == "transferencia interna":
        raise HTTPException(409, "Usa la transferencia entre áreas con origen y destino; no registres el traslado como salida del stock institucional.")
    es_devolucion = (payload.tipo_operacion or "").strip() == "Devolución"
    if es_devolucion:
        if payload.movimiento_origen_id is None:
            raise HTTPException(409, "La devolución debe vincularse a una venta o donación original.")
        if not (payload.devuelto_por or "").strip():
            raise HTTPException(422, "Identifica a la persona o institución que devuelve.")
        if payload.area_operativa_id is None:
            raise HTTPException(422, "Indica el área que recibe físicamente la devolución.")
    elif payload.movimiento_origen_id is not None or payload.devuelto_por:
        raise HTTPException(422, "La salida original y quien devuelve solo corresponden a una devolución.")
    operacion_pendiente = next((op for op in CATALOGO_OPERACIONES
                               if op["valor"] == (payload.tipo_operacion or "").strip()
                               and not op.get("habilitada", True)), None)
    if operacion_pendiente:
        raise HTTPException(409, operacion_pendiente["motivo_pendiente"])
    error_operacion = validar_operacion(
        tipo=payload.tipo, operacion=payload.tipo_operacion,
        receptor=payload.receptor, feria_id=payload.feria_id,
        ciudad_feria=payload.ciudad_feria, motivo_baja=payload.motivo_baja,
        receptor_tipo=payload.receptor_tipo,
        referencia_documento=payload.referencia_documento,
    )
    if error_operacion:
        raise HTTPException(422, error_operacion)
    if not payload.nodo_grafo.strip():
        raise HTTPException(status_code=400, detail="Debe seleccionar un nodo para la operación.")

    # Los clientes anteriores asignan por defecto al usuario autenticado.
    # El formulario nuevo permite designar a otra cuenta activa como encargado.
    encargado_id = payload.encargado_id or current_user.id
    encargado = db.query(Usuario).filter(
        Usuario.id == encargado_id, Usuario.estado == "activo",
    ).first()
    if encargado is None:
        raise HTTPException(422, "Selecciona un encargado activo.")

    ahora = datetime.now(UTC)
    ocurrido_en = payload.fecha_operacion.astimezone(UTC) if payload.fecha_operacion else ahora
    if ocurrido_en > ahora + timedelta(minutes=5):
        raise HTTPException(422, "La fecha de la operación no puede estar en el futuro.")
    apertura, creada_en_solicitud = asegurar_apertura_desde_kardex(
        db, payload.articulo_id, current_user, request, devolver_estado=True)
    # La otra petición del mismo artículo pudo terminar mientras esperábamos el bloqueo.
    previo = movimiento_previo()
    if previo is not None:
        db.rollback()
        return previo
    if creada_en_solicitud and ocurrido_en < ahora - timedelta(seconds=30):
        db.rollback()
        raise HTTPException(409, "Para registrar una operación anterior al corte, primero establece y concilia la apertura del artículo.")
    inicio = apertura.aprobado_en
    if inicio.tzinfo is None:  # SQLite en pruebas; PostgreSQL devuelve timestamptz.
        inicio = inicio.replace(tzinfo=UTC)
    if creada_en_solicitud and ocurrido_en < inicio:
        # La base documental se activa en el instante del primer hecho registrado.
        apertura.aprobado_en = ocurrido_en
        inicio = ocurrido_en
    if not creada_en_solicitud and ocurrido_en < inicio:
        db.rollback()
        raise HTTPException(409, "La operación ocurrió antes del corte de apertura; concilia ese periodo antes de registrarla.")
    if es_devolucion:
        original = db.get(MovimientoKardex, payload.movimiento_origen_id)
        if (original is None or original.articulo_id != payload.articulo_id
                or original.lote_id is not None or original.id <= apertura.ultimo_moderno_id
                or original.estado != "ACTIVO"
                or original.tipo_operacion not in ("Ventas", "Obsequios y Donaciones")
                or not original.salidas):
            db.rollback()
            raise HTTPException(409, "La salida original no es una venta o donación activa posterior al corte.")
        if original.ocurrido_en is not None:
            fecha_original = original.ocurrido_en
            if fecha_original.tzinfo is None:
                fecha_original = fecha_original.replace(tzinfo=UTC)
            if ocurrido_en < fecha_original:
                db.rollback()
                raise HTTPException(409, "La devolución no puede ocurrir antes de la entrega original.")
        elif ocurrido_en.date() < original.fecha_movimiento:
            db.rollback()
            raise HTTPException(409, "La devolución no puede ocurrir antes de la entrega original.")
        cantidad_vigente = cantidad_efectiva_movimiento(db, original)
        ya_devuelto = cantidad_devuelta_efectiva(db, original.id)
        if payload.cantidad > cantidad_vigente - ya_devuelto:
            db.rollback()
            raise HTTPException(409, "La devolución supera las unidades pendientes de la entrega original.")
    saldo_anterior = apertura.cantidad_actual
    ing = payload.cantidad if payload.tipo == "ingreso" else 0
    sal = payload.cantidad if payload.tipo == "salida" else 0
    nuevo_saldo = saldo_anterior + ing - sal
    
    # 2. Validar stock suficiente
    if nuevo_saldo < 0:
        db.rollback()  # También revierte la base histórica creada en esta petición.
        raise HTTPException(
            status_code=400, 
            detail=f"Stock insuficiente. Saldo actual: {saldo_anterior} unidades. "
                   f"No se pueden retirar {sal} unidades."
        )
    
    if nuevo_saldo > 2147483647:
        db.rollback()
        raise HTTPException(400, "El saldo supera la cantidad máxima admitida.")

    ahora_local = ahora.astimezone(ZoneInfo("America/La_Paz"))
    saldo_ubicacion = stock_ubicacion(db, apertura, payload.area_operativa_id)
    if payload.tipo == "salida" and payload.cantidad > saldo_ubicacion:
        db.rollback()
        raise HTTPException(409, "Stock insuficiente en la ubicación seleccionada.")
    cantidades_previas = cantidades_comparables(db,
        articulo_id=payload.articulo_id, ultimo_moderno_id=apertura.ultimo_moderno_id,
        tipo=payload.tipo, operacion=payload.tipo_operacion, area_id=payload.area_operativa_id)
    ventana = ahora - timedelta(minutes=settings.CONTROL_REPETICION_MINUTOS)
    recientes = db.query(MovimientoKardex).filter(
        MovimientoKardex.articulo_id == payload.articulo_id,
        MovimientoKardex.lote_id.is_(None),
        MovimientoKardex.estado == "ACTIVO",
        MovimientoKardex.corrige_movimiento_id.is_(None),
        MovimientoKardex.id > apertura.ultimo_moderno_id,
        MovimientoKardex.registrado_en >= ventana,
    ).all()
    ultimo_movimiento_id = db.query(func.max(MovimientoKardex.id)).filter(
        MovimientoKardex.articulo_id == payload.articulo_id,
        MovimientoKardex.lote_id.is_(None),
        MovimientoKardex.id > apertura.ultimo_moderno_id,
    ).scalar() or apertura.ultimo_moderno_id
    alertas = evaluar_movimiento(
        tipo=payload.tipo, cantidad=payload.cantidad, saldo=saldo_anterior,
        fecha_local=ahora_local, cantidades_previas=cantidades_previas,
        fecha_operacion_local=ocurrido_en.astimezone(ZoneInfo("America/La_Paz")) if payload.fecha_operacion else None,
        **parametros_control(),
    )
    if payload.tipo == "salida" and saldo_ubicacion < saldo_anterior:
        sin_area = payload.area_operativa_id is None
        alertas += evaluar_ubicacion(cantidad=payload.cantidad, saldo=saldo_ubicacion,
            codigo_total="AGOTA_SIN_UBICACION" if sin_area else "AGOTA_AREA",
            codigo_mayoria="SALIDA_MAYORITARIA_SIN_UBICACION" if sin_area else "SALIDA_MAYORITARIA_AREA",
            etiqueta="saldo sin ubicación confirmada" if sin_area else "el área de origen",
            porcentaje=settings.CONTROL_PORCENTAJE_MAYORITARIO,
            minimo=settings.CONTROL_STOCK_MINIMO_MAYORITARIO)
    def identidad_movimiento(m):
        return dict(id=m.id, cantidad=cantidad_efectiva_movimiento(db, m), documento=m.referencia_documento,
                    operacion=m.tipo_operacion, tipo="ingreso" if m.ingresos else "salida",
                    area_id=m.area_operativa_id, receptor=m.receptor or m.devuelto_por,
                    origen_id=m.movimiento_origen_id)
    alertas += aviso_repeticion([identidad_movimiento(m) for m in recientes],
        dict(cantidad=payload.cantidad, documento=payload.referencia_documento,
             operacion=payload.tipo_operacion, tipo=payload.tipo, area_id=payload.area_operativa_id,
             receptor=payload.receptor or payload.devuelto_por, origen_id=payload.movimiento_origen_id))
    if alertas:
        firma = firma_confirmacion(
            settings.JWT_SECRET_KEY,
            payload=payload.model_dump(exclude={"confirmacion_alertas", "motivo_alertas"})
                    | {"saldo_ubicacion": saldo_ubicacion},
            usuario_id=current_user.id, saldo=saldo_anterior,
            hora_local=ahora_local.strftime("%Y-%m-%dT%H"),
            alertas=alertas, ultimo_movimiento_id=ultimo_movimiento_id,
        )
        if not payload.confirmacion_alertas or not hmac.compare_digest(
            payload.confirmacion_alertas, firma,
        ):
            db.rollback()  # La vista previa tampoco crea una apertura.
            raise HTTPException(409, detail={
                "codigo": "ALERTAS_CONTROL", "alertas": alertas,
                "firma_confirmacion": firma, "saldo_previo": saldo_anterior,
            })
        if len(payload.motivo_alertas.strip()) < 10:
            db.rollback()
            raise HTTPException(422, "Justifica la operación alertada con al menos 10 caracteres.")
    elif payload.confirmacion_alertas:
        db.rollback()
        raise HTTPException(409, detail={"codigo": "CONTROL_DESACTUALIZADO",
            "mensaje": "La operación cambió; vuelve a revisarla antes de guardar."})

    cambiar_existencia_area(
        db, apertura, payload.area_operativa_id,
        ing - sal,
    )
    nuevo_mov = MovimientoKardex(
        articulo_id=payload.articulo_id,
        fecha_movimiento=ocurrido_en.astimezone(ZoneInfo("America/La_Paz")).date(),
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
        usuario_registrador_id=current_user.id,
        encargado_id=encargado.id,
        encargado_nombre=encargado.nombre,
        registrado_en=ahora,
        ocurrido_en=ocurrido_en,
        solicitud_id=solicitud_id,
        solicitud_huella=solicitud_huella,
        alertas_control=alertas or None,
        justificacion_alertas=payload.motivo_alertas.strip() if alertas else None,
        tipo_operacion=payload.tipo_operacion,
        receptor=payload.receptor,
        receptor_tipo=payload.receptor_tipo,
        area_operativa_id=payload.area_operativa_id,
        feria_id=payload.feria_id,
        ciudad_feria=payload.ciudad_feria,
        canal_venta=payload.canal_venta,
        motivo_baja=payload.motivo_baja,
        referencia_documento=payload.referencia_documento,
        movimiento_origen_id=payload.movimiento_origen_id if es_devolucion else None,
        devuelto_por=payload.devuelto_por.strip() if es_devolucion else None,
    )
    db.add(nuevo_mov)
    try:
        db.flush()  # La restricción única resuelve carreras entre artículos distintos.
        registrar_caso(db, nuevo_mov, "MOVIMIENTO")
    except IntegrityError:
        db.rollback()
        previo = movimiento_previo()
        if previo is not None:
            return previo
        raise
    apertura.cantidad_actual = nuevo_saldo
    verificar_distribucion(db, apertura)
    auditar(db, current_user, request, "crear_movimiento_inventario", "movimientos_kardex",
            nuevo_mov.id, {"articulo_id": payload.articulo_id, "tipo": payload.tipo,
            "cantidad": payload.cantidad, "nuevo_saldo": nuevo_saldo,
            "operacion": payload.tipo_operacion,
            "encargado_id": encargado.id,
            "area_operativa_id": payload.area_operativa_id,
            "usuario_registrador_id": current_user.id,
            "solicitud_id": solicitud_id,
            "ocurrido_en": ocurrido_en.isoformat(),
            "registrado_en": ahora.isoformat(),
            "referencia_documento": payload.referencia_documento,
            "movimiento_origen_id": payload.movimiento_origen_id if es_devolucion else None,
            "devuelto_por": payload.devuelto_por.strip() if es_devolucion else None,
            "alertas_control": [aviso["codigo"] for aviso in alertas],
            "justificacion_alertas": payload.motivo_alertas.strip() if alertas else None})
    db.commit()
    db.refresh(nuevo_mov)

    return nuevo_mov


@router.post("/movimiento-actual/{movimiento_id}/anular", deprecated=True)
def anular_movimiento_actual(
    movimiento_id: int,
    _usuario: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    """Ruta histórica deshabilitada: las correcciones actuales son asientos nuevos."""
    raise HTTPException(410, "La anulación que reescribía saldos está deshabilitada. Usa una rectificación o un ajuste operativo documentado.")

class AperturaCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    cantidad: int = Field(strict=True, ge=0, le=2147483647)
    referencia_documento: str = Field(min_length=3, max_length=255)
    justificacion: str = Field(min_length=10, max_length=2000)
    conteo_verificado: Literal[True]


class AsignarAreaCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    area_id: int = Field(gt=0)
    cantidad: int = Field(strict=True, gt=0, le=2147483647)
    encargado_id: int = Field(gt=0)
    referencia_documento: str = Field(min_length=3, max_length=255)
    justificacion: str = Field(min_length=10, max_length=2000)


@router.get("/articulos/{articulo_id}/existencias-area")
def consultar_existencias_area(
    articulo_id: int, db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    if db.get(Activo, articulo_id) is None:
        raise HTTPException(404, "Artículo no encontrado")
    apertura = db.get(AperturaInventario, articulo_id)
    cierre = ultimo_cierre_kardex(db, articulo_id) if apertura is None else None
    return distribucion_dict(db, articulo_id, apertura,
                             base_kardex_dict(cierre) if cierre else None)


@router.post("/articulos/{articulo_id}/asignar-area")
def asignar_ubicacion_inicial(
    articulo_id: int, payload: AsignarAreaCrear, request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_roles("Administrador")),
):
    """Ubica unidades del saldo desconocido sin variar el total institucional."""
    encargado = db.query(Usuario).filter_by(id=payload.encargado_id,
                                            estado="activo").first()
    if encargado is None:
        raise HTTPException(422, "Selecciona un encargado activo para la ubicación.")
    apertura = asegurar_apertura_desde_kardex(db, articulo_id, usuario, request)
    if db.get(Area, payload.area_id) is None:
        raise HTTPException(422, "Área no encontrada")
    if payload.cantidad > apertura.cantidad_sin_ubicacion:
        raise HTTPException(409, "La cantidad sin ubicación confirmada es insuficiente")
    cambiar_existencia_area(db, apertura, None, -payload.cantidad)
    cambiar_existencia_area(db, apertura, payload.area_id, payload.cantidad)
    verificar_distribucion(db, apertura)
    auditar(db, usuario, request, "asignar_existencia_area", "existencia",
            articulo_id, {"area_id": payload.area_id, "cantidad": payload.cantidad,
                          "encargado_id": encargado.id,
                          "referencia_documento": payload.referencia_documento,
                          "justificacion": payload.justificacion})
    db.commit()
    return distribucion_dict(db, articulo_id, apertura)


@router.post("/articulos/{articulo_id}/apertura")
def aprobar_apertura(
    articulo_id: int, payload: AperturaCrear, request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    # La fila del artículo existe incluso antes de su primera apertura.
    articulo = db.query(Activo).filter_by(id=articulo_id).with_for_update().first()
    if articulo is None:
        raise HTTPException(404, "Artículo no encontrado")
    if db.get(AperturaInventario, articulo_id):
        raise HTTPException(409, "El artículo ya tiene una apertura aprobada. No se puede reemplazar.")
    ultimo = db.query(func.max(MovimientoKardex.id)).filter(
        MovimientoKardex.articulo_id == articulo_id,
        MovimientoKardex.lote_id.is_(None),
    ).scalar() or 0
    apertura = AperturaInventario(
        articulo_id=articulo_id, cantidad_inicial=payload.cantidad,
        cantidad_actual=payload.cantidad, ultimo_moderno_id=ultimo,
        cantidad_sin_ubicacion=payload.cantidad,
        aprobado_por=current_user.id, aprobado_en=datetime.now(UTC),
        referencia_documento=payload.referencia_documento, justificacion=payload.justificacion,
        origen="CONTEO_FISICO",
    )
    db.add(apertura)
    auditar(db, current_user, request, "aprobar_apertura_inventario", "apertura_inventario",
            articulo_id, {**payload.model_dump(), "ultimo_moderno_id": ultimo})
    db.commit()
    db.refresh(apertura)
    return apertura_dict(apertura)
