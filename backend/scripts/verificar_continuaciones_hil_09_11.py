"""Consulta institucional sin iniciar lifespan; verifica lotes 09–12 y pendientes."""
import json
from collections import Counter,defaultdict
from datetime import datetime,UTC
from sqlalchemy import inspect,text
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import SessionLocal,engine
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.kardex import MovimientoKardex as M
from app.services.calidad_kardex import tipos_alerta
from scripts.aplicar_revision_hil import DEST,fuente_hash
from scripts.preparar_analitica import digest_tablas


def main():
    with engine.connect() as c:antes=digest_tablas(c,inspect(c).get_table_names())
    with SessionLocal() as db:
        usuario=db.query(Usuario).join(Rol).filter(Usuario.estado=='activo',Rol.nombre=='Administrador').order_by(Usuario.id).first()
        assert usuario is not None
        token=create_access_token(usuario.id)
    # No usar el context manager: no iniciar el trabajador ni reentrenar.
    cliente=TestClient(app);rutas=[];historiales={}
    for aid,cantidad,cierre in ((95,138,208),(133,25,56),(94,35,666),(91,111,129),(28,102,18),(87,167,365),(96,239,298)):
        ruta=f'{settings.API_V1_PREFIX}/kardex/historial/{aid}'
        respuesta=cliente.get(ruta,headers={'Authorization':'Bearer '+token})
        assert respuesta.status_code==200,(aid,respuesta.status_code)
        filas=respuesta.json();historiales[aid]={r['id']:r for r in filas}
        assert len(filas)==cantidad and filas[-1]['saldo_registrado']==cierre
        assert all(m['revision_documental'] and m['datos_originales'] and m['ruta_imagen_respaldo'] for m in filas)
        rutas.append({'articulo':aid,'filas':cantidad,'saldo_reconstruido':cierre,'estado_http':200})
    dibujo=historiales[91];nuevas=[m for m in dibujo.values() if m['revision_documental'].get('recuperacion_clave')]
    assert len(nuevas)==2
    assert sorted((m['orden_fila'],m['saldo_registrado']) for m in nuevas)==[(1,283),(7,275)]
    assert all(m['fecha_original'] is None and m['fecha_estado']=='ESTIMADA_HIL' and m['datos_originales']['no_existia_en_extraccion_ocr'] for m in nuevas)
    assert dibujo[6063]['orden_fila']==2 and dibujo[6063]['datos_originales']['orden_fila']==1
    assert historiales[28][1209]['saldo_registrado']==18
    assert all(historiales[95][id]['estado']=='NOTA_DOCUMENTAL' for id in (6410,6411,6412,6443))
    assert historiales[133][7506]['ingresos']==14 and historiales[133][7506]['revision_documental']['origen_cantidades']=='HIPOTESIS'
    assert historiales[87][5618]['salidas']==10 and historiales[87][5690]['ingresos']==2 and historiales[87][5692]['ingresos']==4
    assert historiales[87][5654]['revision_documental']['fecha_documental']=='2019-09-14'
    assert historiales[96][6662]['salidas']==1 and historiales[96][6677]['saldo_registrado']==330
    assert historiales[96][6666]['revision_documental']['saldo_documental']==244
    assert historiales[96][6666]['saldo_registrado']==344
    assert historiales[96][6720]['ingresos']==6 and historiales[96][6719]['ingresos']==1
    catalogo=cliente.get(f'{settings.API_V1_PREFIX}/kardex/articulos',headers={'Authorization':'Bearer '+token})
    assert catalogo.status_code==200
    articulo=next(a for a in catalogo.json() if a['id']==91)
    assert articulo['observacion_hil'] and '129 frente a 127' in articulo['observacion_hil']['motivo']
    with SessionLocal() as db:
        db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
        filas=db.query(M).all();hist=[m for m in filas if m.lote_id is not None];activos=[m for m in hist if m.estado=='ACTIVO']
        avisos=[m for m in activos if tipos_alerta(m)];fotos=defaultdict(list)
        for m in hist:fotos[m.ruta_imagen_respaldo].append(m)
        estado={'generado_en':datetime.now(UTC).isoformat(),'movimientos_totales':len(filas),'historicos_conservados':len(hist),
            'historicos_activos':len(activos),'modernos':len(filas)-len(hist),'revisados_distintos':sum(bool(m.revision_documental) for m in hist),
            'historicos_sin_cotejar':sum(not m.revision_documental for m in hist),'filas_con_avisos_hil':len(avisos),
            'filas_con_avisos_aun_sin_cotejar':sum(not m.revision_documental for m in avisos),
            'tipos_avisos':dict(Counter(t for m in avisos for t in tipos_alerta(m))),
            'fotos_historicas':len(fotos),'fotos_con_filas_sin_cotejar':sum(any(not m.revision_documental for m in ms) for ms in fotos.values()),
            'fotos_completamente_cotejadas':sum(all(m.revision_documental for m in ms) for ms in fotos.values()),
            'fuente_sha256':fuente_hash(db),'fuente_preexistente_sha256':fuente_hash(db,excluir_ids=[m['id'] for m in nuevas]),
            'rutas_verificadas':rutas,'recuperaciones_visibles':[m['id'] for m in nuevas]}
        estado['observacion_dibujo_visible_en_catalogo']=True
        assert estado['fuente_preexistente_sha256']=='379b382e2287defd520210853844207c3c0192a65160f25d15b0b9dd6926f726'
    with engine.connect() as c:despues=digest_tablas(c,inspect(c).get_table_names())
    assert antes==despues,'La consulta no debe escribir en ninguna tabla'
    estado['tablas_modificadas_por_prueba']=[]
    (DEST/'verificacion_rutas_y_pendientes_09_12.json').write_text(json.dumps(estado,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(estado,ensure_ascii=False))


if __name__=='__main__':main()
