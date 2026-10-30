"""Informe institucional: saldos actuales, período digital y cobertura documental separados."""

import json
from collections import Counter
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.v1.endpoints.kardex_digital import consultar_kardex_digital
from app.db.session import get_db
from app.models.activos import Activo
from app.models.cierre_anual import CierreAnual
from app.models.control_alertas import CasoControl
from app.models.inventario import AperturaInventario, ConciliacionInicial
from app.services.datos_analitica import leer_corte
from app.services.inventario import base_kardex_dict, distribucion_dict
from app.services.cierre_documental import fuentes_cierre

router = APIRouter(prefix="/reportes/institucional", tags=["Informe institucional"])
lector = require_roles("Administrador", "Auditor", "Operador")


def construir(db, gestion):
    aperturas = {a.articulo_id: a for a in db.query(AperturaInventario)}
    conciliados = {c.articulo_id for c in db.query(ConciliacionInicial)}
    fuentes = fuentes_cierre(db)
    inventario, movimientos, errores = [], [], []
    for a in db.query(Activo).order_by(Activo.id):
        apertura = aperturas.get(a.id)
        fuente = fuentes.get(a.id)
        base = base_kardex_dict(fuente.cierre, fuente) if fuente else None
        if apertura:
            libro = consultar_kardex_digital(a.id, db, None)
            d = distribucion_dict(db, a.id, apertura)
            if not libro["integridad"]:
                errores.append(a.id)
            origen = (
                "CONTEO_FISICO_INICIAL"
                if a.id in conciliados or apertura.origen == "CONTEO_FISICO"
                else "BASE_DOCUMENTAL_PROVISIONAL"
            )
            for e in libro["eventos"]:
                registrado = e["fecha_registro"]
                if registrado is None:
                    errores.append(a.id)
                    continue
                instante = registrado if registrado.tzinfo else registrado.replace(tzinfo=UTC)
                if instante.astimezone(ZoneInfo("America/La_Paz")).year == gestion:
                    movimientos.append({**e, "articulo_id": a.id, "articulo": a.nombre})
            total = apertura.cantidad_actual
        elif base:
            d = distribucion_dict(db, a.id, base=base)
            total = base["saldo"] if base["operable"] else None
            origen = "BASE_DOCUMENTAL_PROVISIONAL" if base["operable"] else "BASE_BLOQUEADA"
        else:
            d = distribucion_dict(db, a.id)
            total = None
            origen = "SIN_BASE"
        inventario.append(
            dict(
                articulo_id=a.id,
                articulo=a.nombre,
                codigo=a.codigo,
                saldo_actual=total,
                origen=origen,
                operativo=apertura is not None,
                distribucion=d,
                base_documental=base,
            )
        )
    movimientos.sort(
        key=lambda e: (
            (
                e["fecha_registro"].replace(tzinfo=UTC)
                if e["fecha_registro"].tzinfo is None
                else e["fecha_registro"]
            ),
            e["clase"],
            e["id"],
        )
    )
    perfil = leer_corte(db)["perfil"]
    vigente = db.query(CierreAnual).filter_by(gestion_activa=gestion).first()
    return jsonable_encoder(
        dict(
            gestion=gestion,
            generado_en=datetime.now(UTC),
            criterio_periodo="FECHA_REGISTRO_AMERICA_LA_PAZ",
            inventario_actual=inventario,
            totales_actuales=dict(
                operativo=sum(v["saldo_actual"] or 0 for v in inventario if v["operativo"]),
                documental_sin_activar=sum(
                    v["saldo_actual"] or 0 for v in inventario if not v["operativo"]
                ),
                articulos_sin_saldo_confiable=sum(v["saldo_actual"] is None for v in inventario),
            ),
            movimientos=movimientos,
            resumen_periodo=dict(
                eventos=len(movimientos),
                ingresos_y_ajustes=sum(e["ingreso"] for e in movimientos),
                salidas_y_ajustes=sum(e["salida"] for e in movimientos),
                trasladado=sum(e["cantidad_transferida"] for e in movimientos if e["clase"] != "RECTIFICACION_LOGISTICA"),
                rectificaciones_logisticas=sum(e["clase"] == "RECTIFICACION_LOGISTICA" for e in movimientos),
                por_clase=dict(Counter(e["clase"] for e in movimientos)),
            ),
            cobertura_historica=dict(
                historicos=perfil["historicos_activos"],
                elegibles=perfil["elegibles"],
                exclusiones=perfil["exclusiones"],
                por_gestion=perfil["por_gestion"],
                porcentaje_fisico=None,
            ),
            alertas=dict(Counter(c.estado for c in db.query(CasoControl))),
            articulos_con_error_integridad=sorted(set(errores)),
            cierre_vigente=(
                {
                    "id": vigente.id,
                    "version": vigente.version,
                    "huella": vigente.huella,
                    "snapshot": vigente.snapshot,
                }
                if vigente
                else None
            ),
            limites="Los saldos son actuales; el período enumera registros digitales "
            "por fecha de registro. Los balances por año se conservan "
            "dentro del alcance de un cierre guardado. Una base documental no es "
            "conteo físico actual. La cobertura física sigue desconocida.",
        )
    )


@router.get("")
def consultar(
    gestion: int = Query(..., ge=1900, le=9998), db: Session = Depends(get_db), _=Depends(lector)
):
    return construir(db, gestion)


@router.get("/exportar.json")
def exportar(
    gestion: int = Query(..., ge=1900, le=9998), db: Session = Depends(get_db), _=Depends(lector)
):
    dato = construir(db, gestion)
    return Response(
        json.dumps(dato, ensure_ascii=False, indent=2, allow_nan=False),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="informe_institucional_{gestion}.json"'
        },
    )
