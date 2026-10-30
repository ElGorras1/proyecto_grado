"""Un circuito enlazado con datos simulados y reloj local de prueba, nunca del equipo."""
from datetime import UTC, date, datetime, timedelta
import importlib
import json
from uuid import uuid4
import pytest
from PIL import Image
from app.api import evidencia
from app.models.activos import Activo, Existencia
from app.models.auditoria import AuditoriaSistema
from app.models.control_alertas import CasoControl
from app.models.inventario import AperturaInventario, ConciliacionInicial
from app.models.kardex import LoteCarga, MovimientoKardex
from app.services import cierre_documental
from test_kardex import auth_headers, usuario_auditor


def test_circuito_completo_con_conteo_compensaciones_cierre_y_reapertura(
    client, db_session, usuario_admin, usuario_operador, usuario_auditor, monkeypatch, tmp_path,
    record_testsuite_property,
):
    class Reloj(datetime):
        instante = datetime(2025, 11, 3, 14, 0, tzinfo=UTC)  # 10:00 Bolivia
        @classmethod
        def now(cls, tz=None):
            return cls.instante.astimezone(tz) if tz else cls.instante.replace(tzinfo=None)
    for nombre in (
        "app.api.v1.endpoints.kardex", "app.api.v1.endpoints.cobertura",
        "app.api.v1.endpoints.conciliacion", "app.api.v1.endpoints.transferencias",
        "app.api.v1.endpoints.custodias_externas", "app.api.v1.endpoints.rectificaciones_logisticas",
        "app.api.v1.endpoints.ajustes_operativos", "app.api.v1.endpoints.control_alertas",
        "app.services.inventario", "app.services.cierre_anual", "app.services.control_alertas",
    ):
        monkeypatch.setattr(importlib.import_module(nombre), "datetime", Reloj)
    monkeypatch.setattr(cierre_documental, "RAIZ_STORAGE", tmp_path)
    monkeypatch.setattr(evidencia, "RAIZ", tmp_path)
    Image.new("RGB", (12, 12), "white").save(tmp_path / "piloto.png")
    pasos = []
    def post(url, datos, usuario=usuario_admin, esperado=200):
        respuesta = client.post(url, headers=auth_headers(usuario), json=datos)
        detalle = respuesta.json().get("detail") if respuesta.headers.get("content-type", "").startswith("application/json") else None
        if respuesta.status_code == 409 and isinstance(detalle, dict) and detalle.get("codigo") == "ALERTAS_CONTROL":
            datos = {**datos, "confirmacion_alertas": detalle["firma_confirmacion"],
                     "motivo_alertas": "Escenario técnico ficticio cotejado para probar avisos; no es un hecho institucional."}
            respuesta = client.post(url, headers=auth_headers(usuario), json=datos)
        assert respuesta.status_code == esperado, (url, respuesta.status_code, respuesta.text)
        Reloj.instante += timedelta(minutes=2)
        return respuesta.json()
    def get(url, usuario=usuario_admin):
        r = client.get(url, headers=auth_headers(usuario))
        assert r.status_code == 200, (url, r.text)
        return r.json()
    # Áreas y artículo nuevos, explícitamente identificados como prueba.
    areas = [post("/api/v1/administracion/areas", {"nombre": n, "codigo": c,
        "motivo": "Alta ficticia de ubicación para el circuito técnico QA."}, esperado=201)
        for n, c in (("Galería QA", "QA-GAL"), ("Depósito QA", "QA-DEP"))]
    gal, dep = [a["id"] for a in areas]
    aid = post("/api/v1/kardex/articulos", {"nombre": "PRUEBA PILOTO C05 AISLADO"}, usuario_operador)["id"]
    base = f"/api/v1/kardex/articulos/{aid}"
    lote = LoteCarga(total_imagenes=1)
    db_session.add(lote); db_session.flush()
    fila = MovimientoKardex(articulo_id=aid, lote_id=lote.id, fecha_movimiento=date(2024, 12, 31),
        detalle="Saldo documental ficticio de preparación QA", ingresos=20, saldo_registrado=20,
        saldo_calculado=20, numero_pagina=1, orden_fila=1, estado="ACTIVO", ruta_imagen_respaldo="storage/piloto.png")
    db_session.add(fila); db_session.commit()
    cobertura = get(f"/api/v1/kardex/cobertura/{aid}", usuario_auditor)
    r = client.put(f"/api/v1/kardex/cobertura/{aid}/revision", headers=auth_headers(usuario_auditor), json={
        "estado": "CIERRE_CONFIRMADO", "referencia": "DOC-QA-FICTICIO", "observacion": "Cotejo técnico de una imagen simulada, no es validación institucional.",
        "cierre_movimiento_id": fila.id, "huella_fuente_esperada": cobertura["huella_fuente"], "evidencia_revisada": True})
    assert r.status_code == 200
    assert client.get("/storage/piloto.png", headers=auth_headers(usuario_auditor)).status_code == 200
    conteo = {"fecha_conteo": str(Reloj.now(UTC).date()), "areas": [{"area_id": gal, "cantidad": 12}, {"area_id": dep, "cantidad": 6}],
        "encargado_id": usuario_operador.id, "referencia_documento": "ACTA-CONTEO-QA", "justificacion": "Conteo ficticio de 18 unidades frente al saldo documental 20.",
        "alcance_total": True, "conteo_verificado": True}
    post(base + "/conciliacion-inicial", conteo)
    def comprobar(nombre, total, galeria, deposito, externa):
        db_session.expire_all()
        a = db_session.get(AperturaInventario, aid)
        cantidades = {e.area_id: int(e.cantidad) for e in db_session.query(Existencia).filter_by(activo_id=aid)}
        assert (a.cantidad_actual, cantidades.get(gal, 0), cantidades.get(dep, 0), a.cantidad_custodia_externa, a.cantidad_sin_ubicacion) == (total, galeria, deposito, externa, 0)
        libro = get(base + "/kardex-digital", usuario_auditor)
        assert libro["integridad"] and libro["saldo_final"] == total
        pasos.append(dict(paso=nombre, total=total, galeria=galeria, deposito=deposito, externa=externa))
    comprobar("Conciliación 20 documental → 18 contadas", 18, 12, 6, 0)
    def movimiento(tipo, operacion, cantidad, area, documento, **otros):
        return post("/api/v1/kardex/movimiento-actual", {
            "articulo_id": aid, "solicitud_id": str(uuid4()), "encargado_id": usuario_operador.id,
            "tipo": tipo, "tipo_operacion": operacion, "nodo_grafo": operacion, "cantidad": cantidad,
            "area_operativa_id": area, "referencia_documento": documento, **otros}, usuario_operador)
    movimiento("ingreso", "Inventario / Compra", 5, gal, "ING-QA")
    comprobar("Ingreso", 23, 17, 6, 0)
    venta = movimiento("salida", "Ventas", 3, gal, "VENTA-QA", receptor="Biblioteca QA", receptor_tipo="INSTITUCION")
    comprobar("Venta directa", 20, 14, 6, 0)
    movimiento("ingreso", "Devolución", 1, gal, "DEV-QA", movimiento_origen_id=venta["id"], devuelto_por="Biblioteca QA")
    comprobar("Devolución vinculada", 21, 15, 6, 0)
    transferencia = post(base + "/transferencias", {"solicitud_id": str(uuid4()), "area_origen_id": gal, "area_destino_id": dep,
        "cantidad": 4, "encargado_id": usuario_operador.id, "referencia_documento": "TR-QA"}, usuario_operador)["registro"]
    comprobar("Transferencia", 21, 11, 10, 0)
    def rectificar(clase, registro, **cambios):
        payload = dict(solicitud_id=str(uuid4()), registro_id=registro["id"], version_esperada=registro["version_rectificacion"],
            cambios={**registro["datos_vigentes"], "clase": clase, **cambios},
            referencia_documento="CORR-QA-" + str(uuid4())[:8], motivo="Corrección ficticia cotejada dentro del circuito de prueba.", evidencia_revisada=True)
        primera = post(base + "/rectificaciones-logisticas", payload)
        repetida = post(base + "/rectificaciones-logisticas", payload)
        assert repetida["registro"]["id"] == primera["registro"]["id"]
    rectificar("TRANSFERENCIA", transferencia, cantidad=3)
    comprobar("Rectificación de transferencia", 21, 12, 9, 0)
    custodia = post(base + "/custodias-externas", {"solicitud_id": str(uuid4()), "tipo": "FERIA", "area_origen_id": dep,
        "cantidad": 5, "receptor_nombre": "Feria QA", "receptor_tipo": "INSTITUCION", "ubicacion_externa": "Puesto QA", "ciudad": "La Paz",
        "encargado_id": usuario_operador.id, "referencia_documento": "FERIA-QA"}, usuario_operador)["registro"]
    cid = custodia["id"]
    comprobar("Entrega a feria", 21, 12, 4, 5)
    def evento(custodia_id, tipo, cantidad, **otros):
        return post(base + f"/custodias-externas/{custodia_id}/eventos", {"solicitud_id": str(uuid4()), "tipo": tipo, "cantidad": cantidad,
            "encargado_id": usuario_operador.id, "referencia_documento": "EV-QA-" + str(uuid4())[:8], **otros}, usuario_operador)["registro"]
    ven = evento(cid, "VENTA", 2, comprador="Comprador QA")
    comprobar("Venta externa", 19, 12, 4, 3)
    ret = evento(cid, "RETORNO", 1, area_destino_id=gal)
    comprobar("Retorno externo", 19, 13, 4, 2)
    def vigente_custodia():
        return next(c for c in get(base + "/custodias-externas") if c["id"] == cid)
    rectificar("EVENTO_CUSTODIA", next(e for e in vigente_custodia()["eventos"] if e["id"] == ven["id"]), cantidad=1)
    comprobar("Rectificación de venta externa", 20, 13, 4, 3)
    rectificar("EVENTO_CUSTODIA", next(e for e in vigente_custodia()["eventos"] if e["id"] == ret["id"]), area_destino_id=dep)
    comprobar("Rectificación del área de retorno", 20, 12, 5, 3)
    rectificar("ENTREGA", vigente_custodia(), ubicacion_externa="Puesto QA corregido")
    comprobar("Rectificación del contexto", 20, 12, 5, 3)
    cons = post(base + "/custodias-externas", {"solicitud_id": str(uuid4()), "tipo": "CONSIGNACION", "area_origen_id": gal, "cantidad": 2,
        "receptor_nombre": "Consignatario QA", "receptor_tipo": "INSTITUCION", "ubicacion_externa": "Local QA",
        "encargado_id": usuario_operador.id, "referencia_documento": "CONSIG-QA"}, usuario_operador)["registro"]
    comprobar("Consignación", 20, 10, 5, 5)
    evento(cons["id"], "RETORNO", 2, area_destino_id=dep)
    comprobar("Retorno completo de consignación", 20, 10, 7, 3)
    # Las decisiones de las alertas ficticias las registra otra cuenta.
    for caso in db_session.query(CasoControl).filter_by(articulo_id=aid):
        detalle = get(f"/api/v1/control-alertas/{caso.id}", usuario_auditor)
        post(f"/api/v1/control-alertas/{caso.id}/revision", {
            "solicitud_id": str(uuid4()), "revision_esperada": detalle["revision_numero"],
            "huella_contexto": detalle["huella_contexto"], "estado": "JUSTIFICADO", "prioridad": detalle["prioridad"],
            "asignado_id": usuario_auditor.id, "conclusion": "LEGITIMO", "motivo": "Escenario ficticio del piloto técnico; revisión independiente en QA.",
            "documento": "REV-QA"}, usuario_auditor)
    prep = get("/api/v1/inventario/preparacion")
    preparado = next(a for a in prep["articulos"] if a["articulo_id"] == aid)
    assert preparado["conciliacion_registrada"] and preparado["sin_ubicacion"] == 0 and preparado["integridad"]
    assert "FUENTE_DOCUMENTAL_PENDIENTE" not in preparado["pendientes"]
    grafo = get(base + "/trazabilidad?ambito=OPERATIVO&limite=100", usuario_auditor)
    assert grafo["integridad_libro"] and any(l["label"] == "RECTIFICA" for l in grafo["links"])
    archivo = client.get(base + "/kardex-digital.csv", headers=auth_headers(usuario_auditor))
    assert archivo.status_code == 200 and "RECTIFICACION_LOGISTICA" in archivo.text
    informe = get("/api/v1/reportes/institucional?gestion=2025", usuario_auditor)
    assert informe["articulos_con_error_integridad"] == [] and informe["resumen_periodo"]["rectificaciones_logisticas"] == 4
    # Año siguiente en el proceso QA: no se cambia el reloj del equipo ni la base real.
    Reloj.instante = datetime(2026, 1, 15, 14, tzinfo=UTC)
    previa = get("/api/v1/cierres-anuales/2025/vista-previa", usuario_auditor)
    assert previa["puede_cerrar"], previa["impedimentos"]
    balance = next(a for a in previa["snapshot"]["articulos"] if a["articulo_id"] == aid)
    assert balance["total"] == 20 and balance["custodia"] == 3
    datos_cierre = {"solicitud_id": str(uuid4()), "huella_esperada": previa["huella"],
        "documento": "CIERRE-QA", "motivo": "Cierre de datos ficticios cotejados en el circuito QA.", "balance_revisado": True}
    cierre = post("/api/v1/cierres-anuales/2025", datos_cierre, esperado=201)
    assert post("/api/v1/cierres-anuales/2025", datos_cierre, esperado=201)["id"] == cierre["id"]
    # Se comprueba el bloqueo de escrituras con el reloj QA situado en la gestión cerrada.
    Reloj.instante = datetime(2025, 12, 31, 14, tzinfo=UTC)
    nuevo = post("/api/v1/kardex/articulos", {"nombre": "PRUEBA SIN APERTURA EN CIERRE QA"}, usuario_operador)
    post(f"/api/v1/kardex/articulos/{nuevo['id']}/apertura", {"cantidad": 1, "referencia_documento": "ACTA-QA",
        "justificacion": "Intento de apertura en la gestión cerrada de QA.", "conteo_verificado": True}, esperado=409)
    post(base + "/transferencias", {"solicitud_id": str(uuid4()), "area_origen_id": gal, "area_destino_id": dep,
        "cantidad": 1, "encargado_id": usuario_operador.id, "referencia_documento": "BLOQUEO-QA"}, usuario_operador, esperado=409)
    Reloj.instante = datetime(2026, 1, 16, 14, tzinfo=UTC)
    reabierto = post(f"/api/v1/cierres-anuales/registro/{cierre['id']}/reabrir", {"motivo": "Reapertura ficticia autorizada para probar conservación del balance."})
    assert reabierto["estado"] == "REABIERTO" and reabierto["snapshot"] == cierre["snapshot"]
    nueva_previa = get("/api/v1/cierres-anuales/2025/vista-previa")
    assert nueva_previa["huella"] == previa["huella"]
    cierre2 = post("/api/v1/cierres-anuales/2025", {**datos_cierre, "solicitud_id": str(uuid4())}, esperado=201)
    assert cierre2["version"] == 2 and cierre2["id"] != cierre["id"]
    record_testsuite_property("circuito_c05", json.dumps(dict(
        datos="Ficticios en base aislada; reloj solo del proceso de prueba", pasos=pasos,
        saldo_final=20, galeria=10, deposito=7, custodia=3,
        cierre_reapertura_y_versionado="APROBADO", aceptacion_institucional=False), ensure_ascii=False))
