"""Prioridades de puesta en operación: consulta, nunca certifica conteos ni mueve stock."""
from collections import Counter, defaultdict
import re
from zoneinfo import ZoneInfo
from sqlalchemy import func
from app.models.activos import Activo, Existencia
from app.models.area import Area
from app.models.cierre_anual import CierreAnual
from app.models.inventario import AperturaInventario, ConciliacionInicial, CustodiaExterna, EventoCustodiaExterna, TransferenciaArea
from app.models.kardex import MovimientoKardex
from app.models.rectificacion_logistica import RectificacionLogistica
from app.services.cierre_anual import ahora
from app.services.cierre_documental import fuentes_cierre
from app.services.inventario import base_kardex_dict


def preparar(db):
    fuentes = fuentes_cierre(db)
    aperturas = {a.articulo_id: a for a in db.query(AperturaInventario)}
    conciliaciones = {c.articulo_id: c for c in db.query(ConciliacionInicial)}
    areas = [{"id": a.id, "nombre": a.nombre} for a in db.query(Area).filter_by(estado="activo").order_by(Area.nombre)]
    ubicados = dict(db.query(Existencia.activo_id, func.sum(Existencia.cantidad)).group_by(Existencia.activo_id))
    externos = dict(db.query(CustodiaExterna.articulo_id, func.sum(CustodiaExterna.cantidad_fuera)).group_by(CustodiaExterna.articulo_id))
    posteriores = defaultdict(int)
    for aid, mid in db.query(MovimientoKardex.articulo_id, MovimientoKardex.id).filter(MovimientoKardex.lote_id.is_(None)):
        if aid in aperturas and mid > aperturas[aid].ultimo_moderno_id:
            posteriores[aid] += 1
    for modelo in (TransferenciaArea, CustodiaExterna, EventoCustodiaExterna, RectificacionLogistica):
        for aid, n in db.query(modelo.articulo_id, func.count()).group_by(modelo.articulo_id):
            posteriores[aid] += n
    filas = []
    for art in db.query(Activo).order_by(Activo.nombre, Activo.id):
        a, c, fuente = aperturas.get(art.id), conciliaciones.get(art.id), fuentes.get(art.id)
        base = base_kardex_dict(fuente.cierre, fuente) if fuente else None
        pendientes = []
        indicio_prueba = bool(re.search(r"\b(prueba|test|dummy|demo)\b", art.nombre or "", re.I))
        if indicio_prueba:
            pendientes.append("REVISAR_REGISTRO_PRUEBA")
        if a:
            integridad = (
                a.cantidad_actual == int(ubicados.get(art.id, 0)) + a.cantidad_sin_ubicacion + a.cantidad_custodia_externa
                and a.cantidad_custodia_externa == int(externos.get(art.id, 0))
            )
            if not integridad:
                pendientes.append("INTEGRIDAD_PENDIENTE")
            if a.cantidad_sin_ubicacion:
                pendientes.append("UBICACION_PENDIENTE")
            if not c and a.origen == "KARDEX_HISTORICO":
                pendientes.append("CONTEO_POSTERIOR" if posteriores[art.id] else "CONCILIACION_INICIAL")
        else:
            integridad = None
            pendientes.append("SIN_BASE" if not base else "BASE_BLOQUEADA" if not base["operable"] else "CONTEO_INICIAL")
        if fuente and fuente.estado != "CONFIRMADA":
            pendientes.append("FUENTE_DOCUMENTAL_PENDIENTE")
        acciones = []
        if indicio_prueba:
            acciones.append("El nombre contiene una marca de prueba. Cotejar su condición antes de incluir sus cantidades en el inventario institucional; conservar sus registros.")
        if "INTEGRIDAD_PENDIENTE" in pendientes:
            acciones.append("Revisar libro y distribución antes de nuevas operaciones.")
        if "CONTEO_POSTERIOR" in pendientes:
            acciones.append("Realizar conteo físico actual y documentar diferencias con un ajuste autorizado; conservar el corte y las operaciones previas.")
        if "CONCILIACION_INICIAL" in pendientes:
            acciones.append("Cotejar un conteo completo por áreas y registrar la conciliación inicial con su acta.")
        if "UBICACION_PENDIENTE" in pendientes:
            acciones.append("Verificar la ubicación física de las unidades pendientes antes de asignarlas a un área.")
        if "BASE_BLOQUEADA" in pendientes:
            acciones.append("Revisar la fuente histórica o aportar un conteo físico de apertura respaldado.")
        if "SIN_BASE" in pendientes or "CONTEO_INICIAL" in pendientes:
            acciones.append("Realizar conteo físico por áreas y documentar la apertura o conciliación que corresponda.")
        if "FUENTE_DOCUMENTAL_PENDIENTE" in pendientes:
            acciones.append("Cotejar y confirmar la fila/foto de cierre en Cobertura documental.")
        filas.append(dict(
            articulo_id=art.id, articulo=art.nombre, codigo=art.codigo, estado_articulo=art.estado,
            indicio_prueba=indicio_prueba,
            apertura=a is not None, origen=a.origen if a else None,
            saldo_operativo=a.cantidad_actual if a else None,
            saldo_documental=base["saldo"] if base else None,
            motivo_bloqueo=base["motivo_bloqueo"] if base else None,
            sin_ubicacion=a.cantidad_sin_ubicacion if a else None,
            en_areas=int(ubicados.get(art.id, 0)) if a else None,
            en_custodia=a.cantidad_custodia_externa if a else None,
            integridad=integridad, conciliacion_registrada=c is not None,
            conteo_aprobado=bool(c or (a and a.origen == "CONTEO_FISICO")),
            referencia_base=a.referencia_documento if a else None,
            fecha_base=a.aprobado_en.isoformat() if a else None,
            registros_posteriores=posteriores[art.id],
            fuente_cierre=fuente.estado if fuente else None,
            pendientes=pendientes, acciones=acciones,
            prioridad=0 if "INTEGRIDAD_PENDIENTE" in pendientes else 1 if a and pendientes else 2,
        ))
    filas.sort(key=lambda f: (f["prioridad"], f["articulo"], f["articulo_id"]))
    conteos = Counter(p for f in filas for p in f["pendientes"])
    gestion = ahora().astimezone(ZoneInfo("America/La_Paz")).year
    return dict(generado_en=ahora().isoformat(), gestion=gestion,
        periodo_abierto=db.query(CierreAnual.id).filter_by(gestion_activa=gestion).first() is None,
        resumen=dict(articulos=len(filas), aperturas=len(aperturas), conciliaciones=len(conciliaciones),
            unidades_sin_ubicacion=sum(a.cantidad_sin_ubicacion for a in aperturas.values()),
            articulos_con_unidades_sin_ubicacion=conteos["UBICACION_PENDIENTE"],
            unidades_sin_ubicacion_con_indicio_prueba=sum((f["sin_ubicacion"] or 0) for f in filas if f["indicio_prueba"]),
            unidades_sin_ubicacion_sin_indicio_prueba=sum((f["sin_ubicacion"] or 0) for f in filas if not f["indicio_prueba"]),
            bases_bloqueadas=sum(f["motivo_bloqueo"] is not None for f in filas),
            fuentes_sin_confirmar=conteos["FUENTE_DOCUMENTAL_PENDIENTE"],
            pendientes_por_tipo=dict(conteos)),
        areas_activas=areas, transferencias_entre_areas_disponibles=len(areas) >= 2,
        articulos=filas,
        alcance="Preparación técnica basada en registros del sistema. El conteo, la ubicación y la aceptación deben cotejarse con personal y documentos reales.")
