import pytest

from app.core.security import verify_password
from app.models.rol import Rol
from app.models.usuario import Usuario
from scripts.seed_admin import crear


def test_inicializa_tres_roles_con_clave_elegida_sin_reemplazar_cuentas(db_session):
    id = crear(db_session, "primero@example.org", "ClaveElegida123!", "Responsable QA")
    assert {r.nombre for r in db_session.query(Rol)} == {"Administrador", "Operador", "Auditor"}
    u = db_session.get(Usuario, id)
    assert verify_password("ClaveElegida123!", u.password_hash)
    with pytest.raises(ValueError, match="Ya existe"):
        crear(db_session, "segundo@example.org", "OtraClave123!", "Otra persona QA")
    assert db_session.query(Usuario).count() == 1


def test_no_crea_cuentas_con_clave_corta(db_session):
    with pytest.raises(ValueError, match="doce"):
        crear(db_session, "primero@example.org", "corta", "Responsable QA")
    assert db_session.query(Usuario).count() == 0
