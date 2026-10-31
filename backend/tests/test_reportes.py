from datetime import date

from app.core.security import create_access_token
from app.models.activos import Activo, CategoriaActivo
from app.models.kardex import LoteCarga, MovimientoKardex
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.core.security import hash_password


def _cabecera(usuario):
    token = create_access_token(subject=usuario.id, extra_claims={"rol": usuario.rol.nombre})
    return {"Authorization": f"Bearer {token}"}


def _datos(db):
    rol = Rol(nombre="Auditor", estado="activo")
    db.add(rol)
    db.flush()
    usuario = Usuario(rol_id=rol.id, nombre="Auditora", email="aud@test.com",
                      password_hash=hash_password("Password123!"), estado="activo")
    categoria = CategoriaActivo(nombre="Libros", estado="activo")
    db.add_all([usuario, categoria])
    db.flush()
    a = Activo(categoria_id=categoria.id, codigo="LIB-001", nombre="Libro A")
    b = Activo(categoria_id=categoria.id, codigo="LIB-002", nombre="Libro B")
    lote = LoteCarga(total_imagenes=1)
    db.add_all([a, b, lote])
    db.flush()

    def mov(articulo, fecha, ingreso=0, salida=0, lote_id=None, nodo="Área: Biblioteca",
            pendiente=False, estado="ACTIVO", detalle="Registro"):
        db.add(MovimientoKardex(
            articulo_id=articulo.id, fecha_movimiento=fecha, detalle=detalle,
            ingresos=ingreso or None, salidas=salida or None, saldo_registrado=10,
            lote_id=lote_id, nodo_grafo=nodo, estado=estado,
            tiene_error_saldo=pendiente, requiere_auditoria_nodo=False,
            requiere_auditoria_referencia=False, area_estado="RESUELTA_AUTOMATICAMENTE",
            referencia_estado="AUSENTE",
        ))

    mov(a, date(2025, 12, 31), ingreso=30, lote_id=lote.id)
    mov(a, date(2026, 1, 2), ingreso=10, lote_id=lote.id)
    mov(a, date(2026, 2, 3), salida=3, lote_id=lote.id, pendiente=True, detalle="=SUM(1+1)")
    mov(b, date(2026, 2, 4), salida=2, nodo="Ventas")
    mov(a, date(2026, 2, 5), salida=99, nodo="Ventas", estado="ANULADO")
    db.commit()
    return usuario


def test_reporte_gestion_resumen_filtros_y_paginacion(client, db_session):
    usuario = _datos(db_session)
    url = "/api/v1/reportes/inventario"
    assert client.get(url, params={"gestion": 2026}).status_code == 401
    respuesta = client.get(url, headers=_cabecera(usuario), params={"gestion": 2026, "limite": 2})
    assert respuesta.status_code == 200, respuesta.text
    data = respuesta.json()
    assert data["resumen"] == {
        "movimientos": 3, "articulos": 2, "ingresos": 10, "salidas": 5,
        "pendientes_hil": 1, "historicos": 2, "modernos": 1,
    }
    assert len(data["filas"]) == 2
    assert data["mensual"][0]["ingresos"] == 10
    assert data["mensual"][1]["salidas"] == 5
    pagina2 = client.get(url, headers=_cabecera(usuario), params={"gestion": 2026, "limite": 2, "pagina": 2})
    assert len(pagina2.json()["filas"]) == 1
    assert pagina2.json()["resumen"] == data["resumen"]

    filtros = {"gestion": 2026, "mes": 2, "articulo": "LIB-001", "origen": "historico",
               "direccion": "salida", "nodo": "Área: Biblioteca", "revision": "pendiente"}
    filtrado = client.get(url, headers=_cabecera(usuario), params=filtros).json()
    assert filtrado["resumen"]["movimientos"] == 1
    assert filtrado["resumen"]["salidas"] == 3
    assert filtrado["filas"][0]["pendiente_hil"] is True
    assert client.get(url, headers=_cabecera(usuario), params={"gestion": 2026, "revision": "sin_alertas"}).json()["resumen"]["movimientos"] == 2
    assert client.get(url, headers=_cabecera(usuario), params={"gestion": 2025}).json()["resumen"]["ingresos"] == 30
    assert client.get(url, headers=_cabecera(usuario), params={"gestion": 2026, "mes": 13}).status_code == 422


def test_opciones_y_csv_respetan_filtros_y_evitan_formulas(client, db_session):
    usuario = _datos(db_session)
    cabecera = _cabecera(usuario)
    opciones = client.get("/api/v1/reportes/inventario/opciones", headers=cabecera).json()
    assert opciones["gestiones"] == [2026, 2025]
    assert opciones["gestiones_historicas"] == [2026, 2025]
    assert "Ventas" in opciones["nodos"]
    assert client.get("/api/v1/reportes/inventario.csv", params={"gestion": 2026}).status_code == 401
    respuesta = client.get("/api/v1/reportes/inventario.csv", headers=cabecera,
                           params={"gestion": 2026, "revision": "pendiente"})
    assert respuesta.status_code == 200, respuesta.text
    assert "text/csv" in respuesta.headers["content-type"]
    assert respuesta.content.startswith(b"\xef\xbb\xbf")
    assert "'=SUM(1+1)" in respuesta.text
    assert "Libro B" not in respuesta.text
