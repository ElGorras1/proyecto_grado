"""Relaciones explícitas y evidencia, sin deducir recorridos físicos del saldo."""
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Literal
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.api.v1.endpoints.kardex_digital import consultar_kardex_digital
from app.db.session import get_db
from app.models.area import Area
from app.models.auditoria import AuditoriaSistema
from app.models.inventario import AperturaInventario, ConciliacionInicial, CustodiaExterna, EventoCustodiaExterna, TransferenciaArea
from app.models.kardex import MovimientoKardex
from app.models.usuario import Usuario
from app.services.clasificador_nodos import normalizar_nodo_grafo

router = APIRouter(prefix="/kardex/articulos", tags=["Trazabilidad"])
BOLIVIA = timezone(timedelta(hours=-4))


def imagen_publica(ruta):
    if not ruta:
        return None
    path = PurePosixPath(ruta.replace("\\", "/").lstrip("/"))
    if not path.parts or path.parts[0] != "storage" or ".." in path.parts:
        return None
    return "/" + quote(str(path), safe="/")


def dia_operacion(valor):
    if isinstance(valor, datetime):
        return (valor.replace(tzinfo=timezone.utc) if valor.tzinfo is None else valor).astimezone(BOLIVIA).date()
    return valor


@router.get("/{articulo_id}/trazabilidad")
def consultar_trazabilidad(
    articulo_id: int,
    ambito: Literal["TODOS", "HISTORICO", "OPERATIVO"] = "TODOS",
    desde: date | None = None, hasta: date | None = None,
    ubicacion: str | None = Query(None, max_length=200),
    tanda: int | None = Query(None, ge=1, le=9999),
    relacion: Literal["CONFIRMADA", "PENDIENTE"] | None = None,
    offset: int = Query(0, ge=0), limite: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user),
):
    if desde and hasta and desde > hasta:
        raise HTTPException(422, "La fecha inicial debe ser anterior o igual a la final.")
    libro = consultar_kardex_digital(articulo_id, db, usuario)
    filas = db.query(MovimientoKardex).options(joinedload(MovimientoKardex.lote)).filter_by(
        articulo_id=articulo_id).all()
    movimientos = {m.id: m for m in filas}
    apertura = db.get(AperturaInventario, articulo_id)
    areas = {a.id: a.nombre for a in db.query(Area).all()}
    transferencias = {t.id: t for t in db.query(TransferenciaArea).filter_by(articulo_id=articulo_id)}
    custodias = {c.id: c for c in db.query(CustodiaExterna).filter_by(articulo_id=articulo_id)}
    eventos_custodia = {c.id: c for c in db.query(EventoCustodiaExterna).filter_by(articulo_id=articulo_id)}
    eventos, lugares = {}, {}
    usuarios = {u.id: u.nombre for u in db.query(Usuario).all()}

    def lugar(identificador, etiqueta, tipo):
        lugares[identificador] = {"id": identificador, "label": etiqueta, "tipo": tipo}
        return identificador

    def area(identificador):
        if identificador in areas:
            return lugar(f"area:{identificador}", areas[identificador], "AREA")
        return lugar("ubicacion:sin-confirmar", "Sin ubicación confirmada", "PENDIENTE")

    def registrar(evento, conexiones, vinculos=()):
        evento["conexiones"] = conexiones
        evento["vinculos"] = list(vinculos)
        evento["estado_relacion"] = ("PENDIENTE" if any(
            c["certeza"] == "PENDIENTE" for c in conexiones) else "CONFIRMADA")
        eventos[evento["clave"]] = evento

    for m in filas:
        if m.lote_id is None:
            continue
        clave = f"HISTORICO:{m.id}"
        nodo, _ = normalizar_nodo_grafo(m.nodo_grafo, m.ingresos or 0, m.salidas or 0)
        contraparte = lugar("historico:" + sha256(nodo.encode()).hexdigest()[:16], nodo, "REFERENCIA_HISTORICA")
        documental = lugar("saldo:documental", "Saldo documental · ubicación no indicada", "DOCUMENTAL")
        manual = m.area_estado == "RESUELTA_POR_HUMANO" and not m.requiere_auditoria_nodo
        registrar({
            "clave": clave, "id": m.id, "clase": "HISTORICO", "ambito": "HISTORICO",
            "descripcion": m.detalle, "fecha": m.fecha_movimiento,
            "fecha_documental": m.fecha_movimiento, "fecha_registro": None,
            "fecha_estado": m.fecha_estado, "area_estado": m.area_estado,
            "ingreso": m.ingresos or 0, "salida": m.salidas or 0,
            "cantidad": (m.ingresos or 0) + (m.salidas or 0),
            "documento": m.referencia, "referencia_estado": m.referencia_estado,
            "imagen_url": imagen_publica(m.ruta_imagen_respaldo),
            "lote_id": m.lote_id, "tanda": m.tanda,
            "pagina": m.numero_pagina, "fila": m.orden_fila,
            "saldo_documental": m.saldo_registrado, "afecta_stock_actual": False,
            "encargado": None, "registrador": None, "receptor": None,
            "observaciones": m.observaciones, "estado": m.estado,
        }, [
            {"ubicacion": documental, "direccion": "REGISTRO", "etiqueta": "Asiento documental", "certeza": "PENDIENTE"},
            {"ubicacion": contraparte, "direccion": "REGISTRO", "etiqueta": "Referencia revisada" if manual else "Clasificación por revisar",
             "certeza": "CONFIRMADA" if manual else "PENDIENTE"},
        ])

    for e in libro["eventos"]:
        clave = f"{e['clase']}:{e['id']}"
        conexiones, vinculos = [], []
        correccion = e.get("corrige_movimiento_id")
        if e["clase"] == "OPERACION":
            m = movimientos[e["id"]]
            aid = area(m.area_operativa_id)
            direccion = "REGISTRO" if correccion or m.tipo_operacion in (
                "Ajuste operativo", "Ajuste de Conciliación Inicial") else ("ENTRADA" if e["ingreso"] else "SALIDA")
            conexiones.append({"ubicacion": aid, "direccion": direccion,
                "etiqueta": "Ajusta saldo" if direccion == "REGISTRO" else "Ingresa a" if direccion == "ENTRADA" else "Sale de",
                "certeza": "CONFIRMADA" if m.area_operativa_id in areas else "PENDIENTE"})
            if correccion:
                vinculos.append({"destino": f"OPERACION:{correccion}", "tipo": "RECTIFICA"})
            elif m.movimiento_origen_id:
                vinculos.append({"destino": f"OPERACION:{m.movimiento_origen_id}", "tipo": "DEVUELVE"})
            persona = m.devuelto_por if m.movimiento_origen_id else m.receptor
            if persona and not correccion:
                rid = lugar(f"receptor:{clave}", persona, "RECEPTOR")
                conexiones.append({"ubicacion": rid, "direccion": "SALIDA" if m.movimiento_origen_id else "ENTRADA",
                    "etiqueta": "Devuelve" if m.movimiento_origen_id else "Recibe", "certeza": "CONFIRMADA"})
        elif e["clase"] == "TRANSFERENCIA":
            t = transferencias[e["id"]]
            for aid, direccion in ((t.area_origen_id, "SALIDA"), (t.area_destino_id, "ENTRADA")):
                conexiones.append({"ubicacion": area(aid), "direccion": direccion,
                    "etiqueta": "Traslada", "certeza": "CONFIRMADA" if aid in areas else "PENDIENTE"})
        else:
            c = custodias[e["custodia_id"]]
            externo = lugar(f"custodia:{c.id}", f"{c.ubicacion_externa} · custodia #{c.id}", "CUSTODIA")
            if e["clase"] == "CUSTODIA_ENTREGA":
                conexiones += [{"ubicacion": area(c.area_origen_id), "direccion": "SALIDA", "etiqueta": "Entrega", "certeza": "CONFIRMADA"},
                               {"ubicacion": externo, "direccion": "ENTRADA", "etiqueta": "Mantiene en custodia", "certeza": "CONFIRMADA"}]
            else:
                conexiones.append({"ubicacion": externo, "direccion": "SALIDA", "etiqueta": "Sale de custodia", "certeza": "CONFIRMADA"})
                vinculos.append({"destino": f"CUSTODIA_ENTREGA:{c.id}", "tipo": "RESULTADO_CUSTODIA"})
                if e["clase"] == "CUSTODIA_RETORNO":
                    aid = eventos_custodia[e["id"]].area_destino_id
                    conexiones.append({"ubicacion": area(aid), "direccion": "ENTRADA", "etiqueta": "Retorna a", "certeza": "CONFIRMADA" if aid in areas else "PENDIENTE"})
                else:
                    rid = lugar(f"receptor:{clave}", e["receptor"] or "Comprador no indicado", "RECEPTOR")
                    conexiones.append({"ubicacion": rid, "direccion": "ENTRADA", "etiqueta": "Compra", "certeza": "CONFIRMADA" if e["receptor"] else "PENDIENTE"})
        registrar({**e, "clave": clave, "ambito": "OPERATIVO",
                   "fecha": e["fecha_operacion"] or e["fecha_documental"],
                   "cantidad": e["cantidad_original"], "imagen_url": None,
                   "afecta_stock_actual": e["estado"] == "ACTIVO" and bool(e["ingreso"] or e["salida"])}, conexiones, vinculos)

    if apertura:
        vinculos = [{"destino": f"HISTORICO:{apertura.movimiento_historico_id}", "tipo": "BASE_HISTORICA"}] if apertura.movimiento_historico_id else []
        registrar({"clave": f"BASE:{articulo_id}", "id": articulo_id, "clase": "BASE", "ambito": "OPERATIVO",
            "descripcion": "Base operativa fijada", "fecha": apertura.aprobado_en,
            "fecha_registro": apertura.aprobado_en, "cantidad": apertura.cantidad_inicial,
            "ingreso": 0, "salida": 0, "documento": apertura.referencia_documento,
            "imagen_url": None, "origen": apertura.origen,
            "observaciones": apertura.justificacion, "afecta_stock_actual": False,
            "estado": "ACTIVO", "encargado": None, "registrador": usuarios.get(apertura.aprobado_por)}, [], vinculos)

    for revision in db.query(AuditoriaSistema).filter_by(
        accion="asignar_existencia_area", recurso="existencia", recurso_id=articulo_id, resultado="exito",
    ):
        d = revision.detalle or {}
        aid = d.get("area_id")
        registrar({"clave": f"UBICACION:{revision.id}", "id": revision.id, "clase": "UBICACION", "ambito": "OPERATIVO",
            "descripcion": "Confirmación documental de ubicación", "fecha": revision.fecha_hora,
            "fecha_registro": revision.fecha_hora, "cantidad": d.get("cantidad", 0), "ingreso": 0, "salida": 0,
            "documento": d.get("referencia_documento"), "imagen_url": None,
            "encargado": usuarios.get(d.get("encargado_id")), "registrador": usuarios.get(revision.usuario_id),
            "observaciones": d.get("justificacion"), "afecta_stock_actual": False, "estado": "ACTIVO"},
            [{"ubicacion": area(aid), "direccion": "REGISTRO", "etiqueta": "Ubica unidades existentes",
              "certeza": "CONFIRMADA" if aid in areas else "PENDIENTE"}])

    conteo = db.get(ConciliacionInicial, articulo_id)
    if conteo:
        conexiones = [{"ubicacion": area(a["area_id"]), "direccion": "REGISTRO",
                       "etiqueta": f"Conteo: {a['cantidad']} u.", "certeza": "CONFIRMADA" if a["area_id"] in areas else "PENDIENTE"}
                      for a in conteo.areas]
        vinculos = [{"destino": f"BASE:{articulo_id}", "tipo": "CONCILIA_BASE"}]
        if conteo.ajuste_movimiento_id:
            vinculos.append({"destino": f"OPERACION:{conteo.ajuste_movimiento_id}", "tipo": "AJUSTE_CONTEO"})
        registrar({"clave": f"CONTEO:{articulo_id}", "id": articulo_id, "clase": "CONTEO", "ambito": "OPERATIVO",
            "descripcion": "Conciliación inicial por conteo físico", "fecha": conteo.fecha_conteo,
            "fecha_registro": conteo.registrado_en, "cantidad": conteo.cantidad_fisica, "ingreso": 0, "salida": 0,
            "documento": conteo.referencia_documento, "imagen_url": None, "afecta_stock_actual": False,
            "observaciones": conteo.justificacion, "encargado": usuarios.get(conteo.encargado_id),
            "registrador": usuarios.get(conteo.registrado_por), "estado": "ACTIVO"}, conexiones, vinculos)

    # Las operaciones anteriores al corte son antecedentes, no entradas al saldo vigente.
    for m in filas:
        if m.lote_id is not None or f"OPERACION:{m.id}" in eventos:
            continue
        registrar({"clave": f"ANTECEDENTE:{m.id}", "id": m.id, "clase": "ANTECEDENTE", "ambito": "OPERATIVO",
            "descripcion": m.detalle, "fecha": m.ocurrido_en or m.fecha_movimiento,
            "fecha_registro": m.registrado_en, "ingreso": m.ingresos or 0, "salida": m.salidas or 0,
            "cantidad": (m.ingresos or 0) + (m.salidas or 0), "documento": m.referencia_documento,
            "imagen_url": imagen_publica(m.ruta_imagen_respaldo), "afecta_stock_actual": False,
            "estado": m.estado, "encargado": m.encargado_nombre, "registrador": m.usuario_operador},
            [{"ubicacion": area(m.area_operativa_id), "direccion": "REGISTRO", "etiqueta": "Antecedente anterior al corte", "certeza": "PENDIENTE"}])

    filtrados = []
    for e in eventos.values():
        dia = dia_operacion(e["fecha"])
        if ambito != "TODOS" and e["ambito"] != ambito:
            continue
        if tanda is not None and e.get("tanda") != tanda:
            continue
        if desde and (dia is None or dia < desde) or hasta and (dia is None or dia > hasta):
            continue
        if ubicacion and not any(c["ubicacion"] == ubicacion for c in e["conexiones"]):
            continue
        if relacion and e["estado_relacion"] != relacion:
            continue
        filtrados.append(e)
    def orden_evento(e):
        valor = e["fecha"]
        if isinstance(valor, datetime):
            valor = valor.replace(tzinfo=timezone.utc) if valor.tzinfo is None else valor
        else:
            valor = datetime.combine(valor or date.min, datetime.min.time(), tzinfo=BOLIVIA)
        return valor, e["clase"], e["id"]
    filtrados.sort(key=orden_evento, reverse=True)
    pagina = filtrados[offset:offset + limite]
    seleccion = {e["clave"]: e for e in pagina}
    contexto, links, avisos = {}, [], []
    # Conservar la cadena de respaldos: p.ej. rectificación -> devolución -> venta.
    # El conjunto visitado evita ciclos en relaciones heredadas.
    por_visitar, visitados = list(pagina), set()
    while por_visitar:
        e = por_visitar.pop()
        if e["clave"] in visitados:
            continue
        visitados.add(e["clave"])
        for v in e["vinculos"]:
            original = eventos.get(v["destino"])
            if original is None:
                avisos.append(f"{e['clave']}: respaldo vinculado {v['destino']} no disponible en este artículo.")
                continue
            if original["clave"] not in seleccion:
                contexto[original["clave"]] = original
            if original["clave"] not in visitados:
                por_visitar.append(original)
            links.append({"source": f"evento:{original['clave']}", "target": f"evento:{e['clave']}",
                          "label": v["tipo"], "certeza": "CONFIRMADA", "tipo": "VINCULO"})
    nodos = []
    usados = set()
    for clave, e in {**seleccion, **contexto}.items():
        nodos.append({"id": f"evento:{clave}", "label": f"{e['clase']} #{e['id']}",
                      "tipo": "EVENTO", "clave": clave, "contexto": clave in contexto})
        for c in e["conexiones"]:
            usados.add(c["ubicacion"])
            source, target = c["ubicacion"], f"evento:{clave}"
            if c["direccion"] == "ENTRADA":
                source, target = target, source
            links.append({"source": source, "target": target, "label": c["etiqueta"],
                          "certeza": c["certeza"], "tipo": c["direccion"]})
    nodos += [lugares[u] for u in sorted(usados)]
    for i, link in enumerate(links):
        link["id"] = f"enlace:{i}"
    return {
        "articulo_id": articulo_id, "articulo": libro["articulo"],
        "eventos": pagina, "contexto": list(contexto.values()), "nodes": nodos, "links": links,
        "ubicaciones": sorted(lugares.values(), key=lambda u: u["label"]),
        "total": len(filtrados), "offset": offset, "limite": limite,
        "pendientes": sum(e["estado_relacion"] == "PENDIENTE" for e in filtrados),
        "saldo_actual": libro["saldo_final"], "integridad_libro": libro["integridad"],
        "estado_libro": libro["estado"], "avisos": avisos,
        "criterio": "Fechas de operación en Bolivia; en el histórico, fecha documental (puede requerir HIL). Los enlaces expresan registros y vínculos explícitos, no un recorrido físico deducido ni stock por ubicación.",
    }
