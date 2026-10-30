import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session

from app.services.clasificador_nodos import (
    AREA_NO_APLICA,
    AREA_NO_CATALOGADA,
    AREA_PENDIENTE_HIL,
    AREA_RESUELTA_AUTOMATICAMENTE,
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


@pytest.fixture
def catalogo():
    engine = create_engine("sqlite:///:memory:")
    @event.listens_for(engine, "connect")
    def unicode_upper(conexion, _):
        # SQLite solo convierte ASCII por defecto; PostgreSQL reconoce estas tildes.
        conexion.create_function("upper", 1, lambda s: s.upper() if s is not None else None)
    with Session(engine) as db:
        db.execute(text("CREATE TABLE catalogo_areas (id INTEGER PRIMARY KEY, nombre_oficial TEXT, abreviatura TEXT, tipo TEXT, activa BOOLEAN)"))
        db.execute(text("CREATE TABLE sinonimos_area (id INTEGER PRIMARY KEY, texto_sucio TEXT UNIQUE, area_oficial_id INTEGER, confirmado BOOLEAN, activa BOOLEAN DEFAULT TRUE)"))
        for id_, nombre, abrev, tipo, activa in [
            (1,"Ventas",None,"operacion",True),
            (2,"Galería","GAL","departamento",True),
            (3,"C+C","C+C","departamento",False),
            (4,"Inventario / Compra",None,"operacion",True),
            (5,"Baja / Pérdida",None,"operacion",True),
            (6,"Transferencia Interna",None,"operacion",True),
            (7,"Salida a Feria",None,"operacion",True),
        ]:
            db.execute(text("INSERT INTO catalogo_areas VALUES (:id,:nombre,:abrev,:tipo,:activa)"),
                       dict(id=id_,nombre=nombre,abrev=abrev,tipo=tipo,activa=activa))
        db.commit()
        yield db
    engine.dispose()


def test_venta_escrita_en_columna_area_es_operacion_y_preserva_referencia(catalogo):
    c=clasificar_movimiento("Escaparate Cultural","''","Ventas",None,1,catalogo)
    assert c.nodo_grafo=="Salida: Ventas"
    assert c.area_estado==AREA_NO_APLICA and not c.requiere_auditoria_nodo
    assert c.referencia_estado==REFERENCIA_ILEGIBLE and c.requiere_auditoria_referencia


@pytest.mark.parametrize("confirmado",[True,False])
def test_alias_operacion_respeta_tipo_y_confirmacion(catalogo,confirmado):
    catalogo.execute(text("INSERT INTO sinonimos_area (texto_sucio,area_oficial_id,confirmado) VALUES ('VTA',1,:confirmado)"),{"confirmado":confirmado})
    c=clasificar_movimiento("Escaparate Cultural",None,"VTA",None,1,catalogo)
    assert c.nodo_grafo=="Salida: Ventas"
    assert c.area_estado==(AREA_NO_APLICA if confirmado else AREA_PENDIENTE_HIL)
    assert c.requiere_auditoria_nodo is (not confirmado)


def test_sugerencia_operacion_no_se_presenta_como_area_ni_como_confirmada(catalogo):
    c=clasificar_movimiento("Entrega",None,"VENTAZ",None,2,catalogo)
    assert c.nodo_grafo=="Salida: Ventas" and c.area_estado==AREA_PENDIENTE_HIL
    assert c.requiere_auditoria_nodo
    assert catalogo.execute(text("SELECT confirmado FROM sinonimos_area WHERE texto_sucio='VENTAZ'")).scalar()==0


@pytest.mark.parametrize("area",["Galería","GAL","C+C"])
def test_departamento_conserva_prefijo_e_inactivos_son_validos_en_historico(catalogo,area):
    c=clasificar_movimiento("Entrega",None,area,None,1,catalogo)
    assert c.nodo_grafo==("Área: C+C" if area=="C+C" else "Área: Galería")
    assert c.area_estado==AREA_RESUELTA_AUTOMATICAMENTE and not c.requiere_auditoria_nodo
    assert catalogo.execute(text("SELECT activa FROM catalogo_areas WHERE nombre_oficial='C+C'")).scalar()==0


@pytest.mark.parametrize("ingreso,salida",[(1,None),(1,1),(None,None)])
def test_venta_en_catalogo_con_direccion_incompatible_requiere_revision(catalogo,ingreso,salida):
    c=clasificar_movimiento("Registro",None,"Ventas",ingreso,salida,catalogo)
    assert c.nodo_grafo==NODO_PENDIENTE_CLASIFICACION
    assert c.area_estado==AREA_PENDIENTE_HIL and c.requiere_auditoria_nodo


@pytest.mark.parametrize("operacion,ingreso,salida,nodo",[
    ("Inventario / Compra",10,None,"Entrada: Inventario / Compra"),
    ("Baja / Pérdida",None,2,"Salida: Baja / Pérdida"),
    ("Salida a Feria",None,2,"Salida: Feria del Libro (FIL)"),
    ("Transferencia Interna",None,2,"Transferencia Interna"),
])
def test_operaciones_catalogadas_no_generan_departamentos(catalogo,operacion,ingreso,salida,nodo):
    c=clasificar_movimiento("Registro",None,operacion,ingreso,salida,catalogo)
    assert c.nodo_grafo==nodo and c.area_estado==AREA_NO_APLICA
    assert not c.requiere_auditoria_nodo
