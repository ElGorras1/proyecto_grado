import io
import pytest
from PIL import Image
from app.api.v1.endpoints import documentos_operativos as api
from app.core.security import create_access_token
from app.models.activos import Activo, CategoriaActivo
from app.models.documento_operativo import DocumentoOperativo


def preparar(db, tmp_path, monkeypatch):
    monkeypatch.setattr(api, 'RAIZ', tmp_path)
    c = CategoriaActivo(nombre='Adjuntos QA')
    db.add(c); db.flush()
    a = Activo(categoria_id=c.id, codigo='DOC-QA', nombre='Libro QA')
    db.add(a); db.commit()
    foto = io.BytesIO()
    Image.new('RGB', (12, 12), 'white').save(foto, 'PNG')
    return a.id, foto.getvalue()


def cab(u):
    return {'Authorization': 'Bearer ' + create_access_token(u.id)}


def test_adjunta_descarga_verifica_y_exige_autenticacion(client, db_session, usuario_operador, tmp_path, monkeypatch):
    aid, foto = preparar(db_session, tmp_path, monkeypatch)
    url = f'/api/v1/kardex/articulos/{aid}/documentos'
    assert client.get(url).status_code == 401
    h = cab(usuario_operador)
    r = client.post(url, headers=h, data={'referencia':'ACTA-01'}, files={'archivo':('acta.png', foto, 'image/png')})
    assert r.status_code == 201, r.text
    doc = r.json()
    assert 'archivo' not in doc
    assert len(client.get(url, headers=h).json()) == 1
    archivo = url + f'/{doc["id"]}/archivo'
    assert client.get(archivo).status_code == 401
    r = client.get(archivo, headers=h)
    assert r.content == foto
    assert r.headers['cache-control'] == 'private, no-store'
    assert 'attachment' in r.headers['content-disposition']
    next(tmp_path.iterdir()).write_bytes(b'alterado')
    assert client.get(archivo, headers=h).status_code == 409


def test_adjunto_fallido_revierte_metadata_y_copia(client, db_session, usuario_admin, tmp_path, monkeypatch):
    aid, foto = preparar(db_session, tmp_path, monkeypatch)
    def fallar(*args, **kwargs): raise RuntimeError('auditoria fallida')
    monkeypatch.setattr(api, 'auditar', fallar)
    with pytest.raises(RuntimeError):
        client.post(f'/api/v1/kardex/articulos/{aid}/documentos', headers=cab(usuario_admin),
            data={'referencia':'ACTA-01'}, files={'archivo':('a.png', foto, 'image/png')})
    assert db_session.query(DocumentoOperativo).count() == 0
    assert not list(tmp_path.iterdir())


def test_rechaza_ejecutables_y_auditor_no_carga(client, db_session, usuario_admin, tmp_path, monkeypatch):
    aid, foto = preparar(db_session, tmp_path, monkeypatch)
    url = f'/api/v1/kardex/articulos/{aid}/documentos'
    h = cab(usuario_admin)
    assert client.post(url, headers=h, data={'referencia':'ACTA-01'}, files={'archivo':('a.pdf',b'MZmalicioso','application/pdf')}).status_code == 422
    usuario_admin.rol.nombre = 'Auditor'; db_session.commit()
    assert client.post(url, headers=h, data={'referencia':'ACTA-01'}, files={'archivo':('a.png',foto,'image/png')}).status_code == 403
    assert client.get(url, headers=h).status_code == 200
