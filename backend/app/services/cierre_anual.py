"""Reconstruye balances al fin del año por fecha de registro, sin mover documentos."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from app.models.activos import Activo
from app.models.auditoria import AuditoriaSistema
from app.models.control_alertas import CasoControl
from app.models.inventario import (
    AperturaInventario,
    ConciliacionInicial,
    CustodiaExterna,
    EventoCustodiaExterna,
    TransferenciaArea,
)
from app.models.kardex import MovimientoKardex, SolicitudCargaKardex
from app.services.control_alertas import operacion
from app.services.datos_analitica import huella
from app.services.inventario import distribucion_dict


def ahora():
    return datetime.now(UTC)


def instante(d):
    return d if d.tzinfo else d.replace(tzinfo=UTC)


def reconstruir(db, gestion):
    corte = datetime(gestion + 1, 1, 1, tzinfo=ZoneInfo("America/La_Paz")).astimezone(UTC)
    nombres = {a.id: a.nombre for a in db.query(Activo)}
    filas, impedimentos, fuentes = [], [], []
    if ahora() < corte:
        impedimentos.append("La gestión todavía no terminó.")
    for apertura in db.query(AperturaInventario).order_by(AperturaInventario.articulo_id):
        if instante(apertura.aprobado_en) >= corte:
            continue
        a = apertura.articulo_id
        d = distribucion_dict(db, a, apertura)
        areas = {v["area_id"]: v["cantidad"] for v in d["areas"]}
        estado = dict(
            total=d["total_institucional"],
            sin_ubicacion=d["sin_ubicacion_confirmada"],
            custodia=d["en_custodia_externa"],
        )
        if sum(areas.values()) + estado["sin_ubicacion"] + estado["custodia"] != estado["total"]:
            impedimentos.append(f"Artículo {a}: la distribución actual no coincide con el total.")
        movimientos = (
            db.query(MovimientoKardex)
            .filter(
                MovimientoKardex.articulo_id == a,
                MovimientoKardex.lote_id.is_(None),
                MovimientoKardex.id > apertura.ultimo_moderno_id,
                MovimientoKardex.estado == "ACTIVO",
            )
            .all()
        )
        entregas = db.query(CustodiaExterna).filter_by(articulo_id=a).all()
        eventos = db.query(EventoCustodiaExterna).filter_by(articulo_id=a).all()
        transferencias = db.query(TransferenciaArea).filter_by(articulo_id=a).all()
        esperado_actual = (
            apertura.cantidad_inicial
            + sum((m.ingresos or 0) - (m.salidas or 0) for m in movimientos)
            - sum(e.cantidad for e in eventos if e.tipo == "VENTA")
        )
        if (
            esperado_actual != estado["total"]
            or sum(c.cantidad_fuera for c in entregas) != estado["custodia"]
        ):
            impedimentos.append(
                f"Artículo {a}: el libro digital no reconcilia con el stock actual."
            )
        conciliacion = db.get(ConciliacionInicial, a)
        reset = conciliacion is not None and instante(conciliacion.registrado_en) >= corte
        if conciliacion is not None and not reset:
            fuentes.append(
                dict(
                    clase="CONCILIACION",
                    id=a,
                    areas=conciliacion.areas,
                    documento=conciliacion.referencia_documento,
                    registrado_en=conciliacion.registrado_en.isoformat(),
                )
            )
        revertir, total_al_corte, custodia_al_corte = [], apertura.cantidad_inicial, 0
        for clase, registros in (
            ("MOVIMIENTO", movimientos),
            ("TRANSFERENCIA", transferencias),
            ("CUSTODIA", entregas),
            ("EVENTO_CUSTODIA", eventos),
        ):
            for f in registros:
                if not f.registrado_en:
                    impedimentos.append(
                        f"Artículo {a}: {clase} {f.id} sin fecha de registro verificable."
                    )
                    continue
                antes = instante(f.registrado_en) < corte
                if antes:
                    fuentes.append(operacion(f, clase))
                    if clase == "MOVIMIENTO":
                        total_al_corte += (f.ingresos or 0) - (f.salidas or 0)
                    elif clase == "CUSTODIA":
                        custodia_al_corte += f.cantidad_entregada
                    elif clase == "EVENTO_CUSTODIA":
                        custodia_al_corte -= f.cantidad
                        if f.tipo == "VENTA":
                            total_al_corte -= f.cantidad
                elif not (
                    reset and clase == "MOVIMIENTO" and f.id == conciliacion.ajuste_movimiento_id
                ):
                    revertir.append((instante(f.registrado_en), clase, f.id, f))
        if reset:
            revertir.append((instante(conciliacion.registrado_en), "CONCILIACION", a, conciliacion))
        for asignacion in db.query(AuditoriaSistema).filter_by(
            accion="asignar_existencia_area", recurso_id=a
        ):
            if instante(asignacion.fecha_hora) >= corte:
                revertir.append(
                    (instante(asignacion.fecha_hora), "ASIGNACION", asignacion.id, asignacion)
                )
            else:
                fuentes.append(
                    {"clase": "ASIGNACION", "id": asignacion.id, "detalle": asignacion.detalle}
                )

        def ubicar(area_id, delta):
            if area_id is None:
                estado["sin_ubicacion"] += delta
            else:
                areas[area_id] = areas.get(area_id, 0) + delta

        for _, clase, _, f in sorted(revertir, key=lambda v: v[:3], reverse=True):
            if clase == "MOVIMIENTO":
                delta = (f.ingresos or 0) - (f.salidas or 0)
                estado["total"] -= delta
                ubicar(f.area_operativa_id, -delta)
            elif clase == "TRANSFERENCIA":
                ubicar(f.area_origen_id, f.cantidad)
                ubicar(f.area_destino_id, -f.cantidad)
            elif clase == "CUSTODIA":
                ubicar(f.area_origen_id, f.cantidad_entregada)
                estado["custodia"] -= f.cantidad_entregada
            elif clase == "EVENTO_CUSTODIA":
                estado["custodia"] += f.cantidad
                if f.tipo == "VENTA":
                    estado["total"] += f.cantidad
                else:
                    ubicar(f.area_destino_id, -f.cantidad)
            elif clase == "ASIGNACION":
                detalle = f.detalle or {}
                if not {"cantidad", "area_id"} <= detalle.keys():
                    impedimentos.append(
                        f"Asignación {f.id}: evidencia insuficiente para reconstruir ubicación."
                    )
                else:
                    ubicar(detalle["area_id"], -detalle["cantidad"])
                    ubicar(None, detalle["cantidad"])
            else:
                previo = f.distribucion_anterior
                estado = dict(
                    total=previo["total_institucional"],
                    sin_ubicacion=previo["sin_ubicacion_confirmada"],
                    custodia=previo["en_custodia_externa"],
                )
                areas = {v["area_id"]: v["cantidad"] for v in previo["areas"]}
        if (
            estado["total"] != total_al_corte
            or estado["custodia"] != custodia_al_corte
            or sum(areas.values()) + estado["sin_ubicacion"] + estado["custodia"] != estado["total"]
            or min([*estado.values(), *areas.values()]) < 0
        ):
            impedimentos.append(f"Artículo {a}: no se pudo reconciliar el balance al corte.")
        filas.append(
            dict(
                articulo_id=a,
                articulo=nombres[a],
                **estado,
                areas=[{"area_id": k, "cantidad": v} for k, v in sorted(areas.items()) if v],
                origen_base=apertura.origen,
                apertura_inicial=apertura.cantidad_inicial,
                movimiento_historico_id=apertura.movimiento_historico_id,
                apertura_registrada_en=apertura.aprobado_en.isoformat(),
                documento_base=apertura.referencia_documento,
            )
        )
    if not filas:
        impedimentos.append(
            "No existen aperturas operativas anteriores al corte para cerrar esta gestión."
        )
    abiertos = (
        db.query(CasoControl)
        .filter(
            CasoControl.estado.in_(("PENDIENTE", "EN_REVISION", "SEGUIMIENTO")),
            CasoControl.creado_en < corte,
        )
        .count()
    )
    if abiertos:
        impedimentos.append(
            f"Hay {abiertos} alertas operativas anteriores al corte pendientes de resolución."
        )
    if (
        db.query(SolicitudCargaKardex)
        .filter(SolicitudCargaKardex.estado.in_(("PROCESANDO", "PENDIENTE")))
        .first()
    ):
        impedimentos.append("Hay escaneos en proceso o pendientes de confirmar.")
    snapshot = jsonable_encoder(
        dict(
            gestion=gestion,
            criterio="FECHA_REGISTRO",
            corte_exclusivo=corte,
            articulos=filas,
            fuentes=sorted(fuentes, key=lambda f: (f["clase"], f["id"])),
            alcance="Inventario digital activado; no certifica cobertura física ni conteo anual.",
            total=sum(f["total"] for f in filas),
            alertas_pendientes=abiertos,
        )
    )
    return dict(
        snapshot=snapshot,
        huella=huella(snapshot),
        puede_cerrar=not impedimentos,
        impedimentos=impedimentos,
    )


def verificar_periodo_abierto(db):
    from app.models.cierre_anual import CierreAnual

    gestion = ahora().astimezone(ZoneInfo("America/La_Paz")).year
    if db.query(CierreAnual.id).filter_by(gestion_activa=gestion).first():
        raise HTTPException(
            409,
            "El año de registro está cerrado; verifica la fecha del servidor "
            "o solicita reapertura documentada.",
        )
