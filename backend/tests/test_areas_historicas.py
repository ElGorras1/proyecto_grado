from copy import deepcopy
import pytest
from app.services.areas_historicas import construir_indices, proponer_area

CATALOGO = [
    {"id": 1, "nombre_oficial": "CEDOAL", "abreviatura": "CEDOAL", "tipo": "departamento", "activa": True},
    {"id": 2, "nombre_oficial": "CEDOC", "abreviatura": "CEDOC", "tipo": "departamento", "activa": True},
    {"id": 3, "nombre_oficial": "Capacitación", "abreviatura": "CAP", "tipo": "departamento", "activa": True},
    {"id": 4, "nombre_oficial": "C+C", "abreviatura": "C+C", "tipo": "departamento", "activa": False},
    {"id": 5, "nombre_oficial": "Sala", "abreviatura": "SALA", "tipo": "departamento", "activa": True},
    {"id": 6, "nombre_oficial": "Ventas", "abreviatura": None, "tipo": "operacion", "activa": True},
]

def proponer(texto, articulo=None, pagina=None):
    return proponer_area(texto, CATALOGO, {"CEDOAL": 4000, "CEDOC": 70, "Capacitación": 500},
                         articulo or {}, pagina or {})


def test_contexto_distingue_cedoc_y_cedoal_aunque_cedoal_sea_mayoritario():
    assert proponer("CEDO.", {"CEDOC": 12}, {"CEDOC": 10})["area"] == "CEDOC"
    assert proponer("CEDO.", {"CEDOAL": 12}, {"CEDOAL": 10})["area"] == "CEDOAL"
    assert proponer("CEDOC")["area"] == "CEDOC"
    assert proponer("CEDOC", {"CEDOAL": 1000}, {"CEDOAL": 1000})["area"] == "CEDOC"


@pytest.mark.parametrize("texto", [None, ".", "C", "Lucy", "Yachaywasy", "DIFUSI", "DIF.", "SALIDA", "Ventas"])
def test_no_reemplaza_textos_distintos_o_marcas_por_el_area_mayoritaria(texto):
    assert proponer(texto, {"CEDOAL": 1000}, {"CEDOAL": 1000})["area"] is None


@pytest.mark.parametrize("texto", ["CTC", "CtC", "CyC", "CFC"])
def test_area_cerrada_sigue_disponible_para_el_historico(texto):
    r = proponer(texto)
    assert r["area"] == "C+C" and r["activa"] is False
    assert r["version"] == "correlacion-areas-v1"
    assert r["regla"] == "variante_grafica_C+C"


def test_indices_no_se_realimentan_con_sugerencias_o_filas_inferidas():
    def fila(mid, area, estado="NO_APLICA", pendiente=False):
        return {"id": mid, "articulo_id": 1, "lote_id": 1, "estado": "ACTIVO",
                "area": area, "area_estado": estado, "requiere_auditoria_nodo": pendiente,
                "ruta_imagen_respaldo": "storage/foto.webp"}
    filas = [fila(1, "CAP"), fila(2, "COP", "PENDIENTE_HIL", True), fila(3, "SALIDA")]
    aliases = [{"texto_sucio": "SALIDA", "area_oficial_id": 5, "confirmado": False}]
    antes = deepcopy(filas)
    g, a, p = construir_indices(filas, CATALOGO, aliases)
    assert dict(g) == {"Capacitación": 1}
    assert dict(a[1]) == dict(p["storage/foto.webp"]) == dict(g)
    assert filas == antes


def test_coincidencia_solo_produce_inferencia_con_soporte_no_una_confirmacion():
    r = proponer("CDP", {"Capacitación": 5}, {"Capacitación": 3})
    assert r["area"] == "Capacitación" and r["soporte"] == "MEDIO"
    assert r["semejanza_textual"] < r["afinidad_regla"]
    assert "no confirmada" in r["motivo"]
