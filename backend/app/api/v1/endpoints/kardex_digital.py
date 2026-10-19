"""Vista de libro mayor digital por artículo a partir del corte operativo."""
import csv
import io
from datetime import UTC, datetime, time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.activos import Activo
from app.models.area import Area
from app.models.inventario import (
    AperturaInventario, TransferenciaArea, CustodiaExterna, EventoCustodiaExterna,
)
from app.models.kardex import MovimientoKardex
from app.models.usuario import Usuario
from app.services.inventario import base_kardex_dict, ultimo_cierre_kardex


router = APIRouter(prefix="/kardex/articulos", tags=["Kárdex digital"])


def instante(fecha: datetime | None, fecha_documental=None):
    if fecha is None:
        return datetime.combine(fecha_documental, time.min, tzinfo=UTC)
    return fecha.replace(tzinfo=UTC) if fecha.tzinfo is None else fecha.astimezone(UTC)


def celda_texto(valor):
    """Evita que un texto institucional sea interpretado como fórmula al abrir el CSV."""
    texto = str(valor or "")
    return "'" + texto if texto.lstrip().startswith(("=", "+", "-", "@")) else texto


@router.get("/{articulo_id}/kardex-digital")
def consultar_kardex_digital(
    articulo_id: int, db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    articulo = db.get(Activo, articulo_id)
    if articulo is None:
        raise HTTPException(404, "Artículo no encontrado")
    apertura = db.get(AperturaInventario, articulo_id)
    if apertura is None:
        cierre = ultimo_cierre_kardex(db, articulo_id)
        documental = base_kardex_dict(cierre) if cierre else None
        return {"articulo_id": articulo_id, "articulo": articulo.nombre,
                "estado": "BASE_DOCUMENTAL_SIN_CORTE" if documental else "SIN_BASE",
                "base": {"cantidad": documental["saldo"], "origen": "KARDEX_HISTORICO",
                         "movimiento_historico_id": documental["movimiento_id"],
                         "lote_historico_id": documental["lote_id"],
                         "fecha_corte": None, "referencia_documento": None} if documental else None,
                "eventos": [], "saldo_final": documental["saldo"] if documental else None,
                "integridad": None}

    movimientos = db.query(MovimientoKardex).filter(
        MovimientoKardex.articulo_id == articulo_id,
        MovimientoKardex.lote_id.is_(None),
        MovimientoKardex.id > apertura.ultimo_moderno_id,
    ).all()
    transferencias = db.query(TransferenciaArea).filter_by(
        articulo_id=articulo_id).all()
    custodias = db.query(CustodiaExterna).filter_by(articulo_id=articulo_id).all()
    eventos_custodia = db.query(EventoCustodiaExterna).filter_by(articulo_id=articulo_id).all()
    custodias_por_id = {c.id: c for c in custodias}
    areas = {a.id: a.nombre for a in db.query(Area).all()}
    usuarios = {u.id: u.nombre for u in db.query(Usuario).all()}
    secuencia = [(instante(m.registrado_en, m.fecha_movimiento), 0, m.id, "OPERACION", m)
                 for m in movimientos]
    secuencia += [(instante(t.registrado_en), 1, t.id, "TRANSFERENCIA", t)
                  for t in transferencias]
    secuencia += [(instante(c.registrado_en), 2, c.id, "CUSTODIA_ENTREGA", c)
                  for c in custodias]
    secuencia += [(instante(e.registrado_en), 3, e.id, "CUSTODIA_EVENTO", e)
                  for e in eventos_custodia]
    secuencia.sort(key=lambda fila: fila[:3])

    saldo = apertura.cantidad_inicial
    eventos = []
    for _, _, _, clase, fila in secuencia:
        if clase == "OPERACION":
            activo = fila.estado == "ACTIVO"
            ingreso = (fila.ingresos or 0) if activo else 0
            salida = (fila.salidas or 0) if activo else 0
            saldo += ingreso - salida
            eventos.append({
                "clase": "OPERACION", "id": fila.id,
                "fecha_operacion": fila.ocurrido_en,
                "fecha_documental": fila.fecha_movimiento,
                "fecha_registro": fila.registrado_en,
                "descripcion": fila.tipo_operacion or fila.nodo_grafo or fila.detalle,
                "ingreso": ingreso, "salida": salida,
                "cantidad_original": fila.ingresos or fila.salidas or 0,
                "cantidad_transferida": 0,
                "area_origen": areas.get(fila.area_operativa_id) if fila.salidas else None,
                "area_destino": areas.get(fila.area_operativa_id) if fila.ingresos else None,
                "documento": fila.referencia_documento,
                "encargado": fila.encargado_nombre,
                "registrador": fila.usuario_operador,
                "receptor": fila.receptor,
                "movimiento_origen_id": fila.movimiento_origen_id,
                "devuelto_por": fila.devuelto_por,
                "corrige_movimiento_id": fila.corrige_movimiento_id,
                "cantidad_anterior": fila.cantidad_anterior,
                "cantidad_corregida": fila.cantidad_corregida,
                "motivo_correccion": fila.motivo_correccion,
                "autorizado_por_id": fila.autorizado_por_id,
                "custodia_id": None,
                "estado": fila.estado,
                "saldo_institucional": saldo,
            })
        elif clase == "TRANSFERENCIA":
            eventos.append({
                "clase": "TRANSFERENCIA", "id": fila.id,
                "fecha_operacion": fila.ocurrido_en,
                "fecha_documental": None,
                "fecha_registro": fila.registrado_en,
                "descripcion": "Transferencia entre áreas",
                "ingreso": 0, "salida": 0,
                "cantidad_original": fila.cantidad,
                "cantidad_transferida": fila.cantidad,
                "area_origen": areas.get(fila.area_origen_id),
                "area_destino": areas.get(fila.area_destino_id),
                "documento": fila.referencia_documento,
                "encargado": usuarios.get(fila.encargado_id),
                "registrador": usuarios.get(fila.registrado_por),
                "receptor": None,
                "movimiento_origen_id": None,
                "devuelto_por": None,
                "custodia_id": None,
                "estado": "ACTIVO",
                "saldo_institucional": saldo,
            })
        elif clase == "CUSTODIA_ENTREGA":
            eventos.append({
                "clase": clase, "id": fila.id, "custodia_id": fila.id,
                "fecha_operacion": fila.ocurrido_en,
                "fecha_documental": None, "fecha_registro": fila.registrado_en,
                "descripcion": "Entrega a feria" if fila.tipo == "FERIA" else "Entrega en consignación",
                "ingreso": 0, "salida": 0,
                "cantidad_original": fila.cantidad_entregada,
                "cantidad_transferida": fila.cantidad_entregada,
                "area_origen": areas.get(fila.area_origen_id),
                "area_destino": fila.ubicacion_externa,
                "documento": fila.referencia_documento,
                "encargado": usuarios.get(fila.encargado_id),
                "registrador": usuarios.get(fila.registrado_por),
                "receptor": fila.receptor_nombre,
                "movimiento_origen_id": None, "devuelto_por": None,
                "estado": "ACTIVO", "saldo_institucional": saldo,
            })
        else:
            custodia = custodias_por_id[fila.custodia_id]
            venta = fila.tipo == "VENTA"
            if venta:
                saldo -= fila.cantidad
            eventos.append({
                "clase": "CUSTODIA_VENTA" if venta else "CUSTODIA_RETORNO",
                "id": fila.id, "custodia_id": custodia.id,
                "fecha_operacion": fila.ocurrido_en,
                "fecha_documental": None, "fecha_registro": fila.registrado_en,
                "descripcion": "Venta desde feria o consignación" if venta else "Retorno de custodia externa",
                "ingreso": 0, "salida": fila.cantidad if venta else 0,
                "cantidad_original": fila.cantidad,
                "cantidad_transferida": 0 if venta else fila.cantidad,
                "area_origen": custodia.ubicacion_externa,
                "area_destino": areas.get(fila.area_destino_id) if not venta else None,
                "documento": fila.referencia_documento,
                "encargado": usuarios.get(fila.encargado_id),
                "registrador": usuarios.get(fila.registrado_por),
                "receptor": fila.comprador if venta else None,
                "movimiento_origen_id": None, "devuelto_por": None,
                "estado": "ACTIVO", "saldo_institucional": saldo,
            })
        eventos[-1].update({"alertas_control": fila.alertas_control,
                           "justificacion_alertas": fila.justificacion_alertas})
    return {"articulo_id": articulo_id, "articulo": articulo.nombre,
            "estado": "OPERATIVO", "base": {
                "cantidad": apertura.cantidad_inicial,
                "origen": apertura.origen,
                "movimiento_historico_id": apertura.movimiento_historico_id,
                "lote_historico_id": apertura.lote_historico_id,
                "fecha_corte": apertura.aprobado_en,
                "referencia_documento": apertura.referencia_documento,
            }, "eventos": eventos, "saldo_final": saldo,
            "custodia_externa_final": sum(c.cantidad_fuera for c in custodias),
            "integridad": (saldo == apertura.cantidad_actual
                           and sum(c.cantidad_fuera for c in custodias)
                           == apertura.cantidad_custodia_externa)}


@router.get("/{articulo_id}/kardex-digital.csv")
def descargar_kardex_digital(
    articulo_id: int, db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    libro = consultar_kardex_digital(articulo_id, db, usuario)
    if libro["base"] is None:
        raise HTTPException(409, "Este artículo todavía no tiene una base para generar el Kárdex digital.")
    salida = io.StringIO()
    escritor = csv.writer(salida, delimiter=";")
    escritor.writerow(("tipo", "fecha_operacion", "fecha_registro", "descripcion",
                       "area_origen", "area_destino", "ingreso", "salida",
                       "cantidad_transferida", "saldo_institucional",
                       "documento", "encargado", "registrador", "entrega_original_id",
                       "devuelto_por", "custodia_id", "receptor", "estado",
                       "corrige_movimiento_id", "cantidad_anterior",
                       "cantidad_corregida", "motivo_correccion", "autorizado_por_id"))
    base = libro["base"]
    escritor.writerow(("BASE", "", base["fecha_corte"] or "",
                       celda_texto(f"{base['origen']} · movimiento histórico {base['movimiento_historico_id'] or ''}"),
                       "", "", "", "", "", base["cantidad"],
                       celda_texto(base["referencia_documento"]), "", "", "", "", "", "",
                       libro["estado"], "", "", "", "", ""))
    for evento in libro["eventos"]:
        escritor.writerow((evento["clase"], evento["fecha_operacion"] or evento["fecha_documental"] or "",
                           evento["fecha_registro"] or "", celda_texto(evento["descripcion"]),
                           celda_texto(evento["area_origen"]), celda_texto(evento["area_destino"]),
                           evento["ingreso"], evento["salida"],
                           evento["cantidad_transferida"], evento["saldo_institucional"],
                           celda_texto(evento["documento"]), celda_texto(evento["encargado"]),
                           celda_texto(evento["registrador"]),
                           evento["movimiento_origen_id"] or "",
                           celda_texto(evento["devuelto_por"]),
                           evento["custodia_id"] or "", celda_texto(evento["receptor"]),
                           evento["estado"], evento.get("corrige_movimiento_id") or "",
                           evento.get("cantidad_anterior") if evento.get("cantidad_anterior") is not None else "",
                           evento.get("cantidad_corregida") if evento.get("cantidad_corregida") is not None else "",
                           celda_texto(evento.get("motivo_correccion")),
                           evento.get("autorizado_por_id") or ""))
    return Response("\ufeff" + salida.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition":
                             f'attachment; filename="kardex_digital_articulo_{articulo_id}.csv"'})
