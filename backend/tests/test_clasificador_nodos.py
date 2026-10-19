from app.services.clasificador_nodos import (
    AREA_NO_APLICA,
    AREA_NO_CATALOGADA,
    AREA_PENDIENTE_HIL,
    AREA_SIN_REGISTRAR,
    NODO_AREA_NO_CATALOGADA,
    NODO_DESTINO_NO_ESPECIFICADO,
    NODO_ORIGEN_NO_ESPECIFICADO,
    NODO_PENDIENTE_CLASIFICACION,
    REFERENCIA_AUSENTE,
    REFERENCIA_ILEGIBLE,
    clasificar_movimiento,
    normalizar_nodo_grafo,
)


def test_ingreso_sin_area_usa_origen_no_especificado_sin_inventar_ubicacion():
    clasificacion = clasificar_movimiento(
        detalle="Registro sin datos de procedencia",
        ref=None,
        area=None,
        ingreso=10,
        salida=None,
    )

    assert clasificacion.nodo_grafo == NODO_ORIGEN_NO_ESPECIFICADO
    assert clasificacion.area_estado == AREA_SIN_REGISTRAR
    assert clasificacion.referencia_estado == REFERENCIA_AUSENTE
    assert clasificacion.requiere_auditoria_nodo is False


def test_salida_sin_area_usa_destino_no_especificado():
    clasificacion = clasificar_movimiento(
        detalle="Salida sin destino escrito",
        ref=None,
        area=None,
        ingreso=None,
        salida=3,
    )

    assert clasificacion.nodo_grafo == NODO_DESTINO_NO_ESPECIFICADO
    assert clasificacion.area_estado == AREA_SIN_REGISTRAR


def test_operacion_reconocible_no_se_pierde_aunque_falte_area():
    clasificacion = clasificar_movimiento(
        detalle="Venta directa de publicaciones",
        ref=None,
        area=None,
        ingreso=None,
        salida=2,
    )

    assert clasificacion.nodo_grafo == "Salida: Ventas"
    assert clasificacion.area_estado == AREA_NO_APLICA
    assert clasificacion.requiere_auditoria_nodo is False


def test_area_legible_sin_catalogo_se_distingue_de_ocr_ilegible():
    no_catalogada = clasificar_movimiento(
        detalle="Transferencia",
        ref="MEM-123",
        area="UNIDAD NUEVA",
        ingreso=None,
        salida=1,
    )
    ilegible = clasificar_movimiento(
        detalle="Transferencia",
        ref="MEM-124",
        area="''",
        ingreso=None,
        salida=1,
    )

    assert no_catalogada.nodo_grafo == NODO_AREA_NO_CATALOGADA
    assert no_catalogada.area_estado == AREA_NO_CATALOGADA
    assert no_catalogada.requiere_auditoria_nodo is True
    assert ilegible.nodo_grafo == NODO_PENDIENTE_CLASIFICACION
    assert ilegible.area_estado == AREA_PENDIENTE_HIL
    assert ilegible.requiere_auditoria_nodo is True


def test_referencia_ilegible_tiene_revision_independiente_del_area():
    clasificacion = clasificar_movimiento(
        detalle="Venta",
        ref="''",
        area=None,
        ingreso=None,
        salida=1,
    )

    assert clasificacion.nodo_grafo == "Salida: Ventas"
    assert clasificacion.referencia_estado == REFERENCIA_ILEGIBLE
    assert clasificacion.requiere_auditoria_nodo is False
    assert clasificacion.requiere_auditoria_referencia is True


def test_normaliza_etiquetas_legacy_segun_direccion_del_movimiento():
    assert normalizar_nodo_grafo("Desconocido / Sin Asignar", ingresos=4, salidas=0) == (
        NODO_ORIGEN_NO_ESPECIFICADO,
        False,
    )
    assert normalizar_nodo_grafo("   ", ingresos=0, salidas=2) == (
        NODO_DESTINO_NO_ESPECIFICADO,
        False,
    )
    assert normalizar_nodo_grafo("Salida: Ventas") == ("Salida: Ventas", False)


def test_fallo_catalogo_queda_pendiente_y_se_registra_sin_datos_privados(caplog):
    from sqlalchemy.exc import SQLAlchemyError
    class CatalogoNoDisponible:
        def execute(self, *args, **kwargs):
            raise SQLAlchemyError("contenido institucional privado")
    c = clasificar_movimiento(detalle="Entrega", ref=None, area="UNIDAD",
                             ingreso=None, salida=1, db=CatalogoNoDisponible())
    assert c.area_estado == AREA_PENDIENTE_HIL
    assert c.requiere_auditoria_nodo
    assert "clasificación pendiente HIL" in caplog.text
    assert "contenido institucional privado" not in caplog.text
