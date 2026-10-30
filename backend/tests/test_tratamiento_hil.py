from copy import deepcopy
from datetime import date
import pytest
from app.core.security import create_access_token
from app.models.activos import Activo, CategoriaActivo
from app.models.kardex import LoteCarga, MovimientoKardex as M
from app.models.auditoria import AuditoriaSistema
from app.services.calidad_kardex import tipos_alerta
from app.services.datos_analitica import leer_corte, seleccionar
from app.services.revision_documental import snapshot_revision
from app.services.tratamiento_hil import huella_datos, resumen_tratamiento

def registrar(m):
    decisiones=[{'campo':campo,'categoria':'DISCREPANCIA_DOCUMENTAL' if campo=='saldo' else 'LECTURA_INCIERTA',
                 'motivo':'Cotejo fotográfico conservado; no acredita un dato confirmado.',
                 'criterios':['T05' if campo=='saldo' else 'T19']} for campo in tipos_alerta(m)]
    revision=deepcopy(m.revision_documental or {})
    revision['tratamiento_hil']={'version':1,'avisos':tipos_alerta(m),'decisiones':decisiones,
                               'huella_datos':huella_datos(m),'autor':'Revisión asistida'}
    m.revision_documental=revision

@pytest.fixture
def filas(db_session):
    c=CategoriaActivo(nombre='Libros');db_session.add(c);db_session.flush()
    a=Activo(categoria_id=c.id,nombre='Poemas',codigo='POEM-1')
    l=LoteCarga(total_imagenes=1);db_session.add_all([a,l]);db_session.flush()
    def crear(orden,**extra):
        valores=dict(articulo_id=a.id,lote_id=l.id,fecha_movimiento=date(2020,1,orden),detalle='Venta',
                     salidas=1,saldo_registrado=8,saldo_calculado=7,area_estado='NO_APLICA',
                     referencia_estado='AUSENTE',tiene_error_saldo=False,fecha_estado='SIN_ALERTA',
                     numero_pagina=1,orden_fila=orden,ruta_imagen_respaldo='storage/kardex_images/evidencia.webp',
                     revision_documental={'criterios':['T05'],'motivo':'Diferencia cotejada con el papel.',
                                          'saldo_documental':8,'origen_saldo':'FOTO','origen_fecha':'FOTO',
                                          'fecha_documental':f'2020-01-0{orden}'})
        valores.update(extra);m=M(**valores);db_session.add(m);db_session.flush();return m
    saldo=crear(1,tiene_error_saldo=True)
    doble=crear(2,area='Texto no inequívoco',area_estado='PENDIENTE_HIL',requiere_auditoria_nodo=True,
                referencia='.',referencia_estado='INCIERTA',requiere_auditoria_referencia=True)
    moderno=crear(3,lote_id=None)
    db_session.commit()
    return a,saldo,doble,moderno

def test_categorizar_no_borra_avisos_fuentes_ni_habilita_entrenamiento(db_session,filas):
    _,saldo,doble,moderno=filas
    antes={m.id:snapshot_revision(m) for m in [saldo,doble]}
    elegibles,_=seleccionar(leer_corte(db_session)['filas'])
    for m in [saldo,doble]: registrar(m)
    db_session.flush()
    for m in [saldo,doble]:
        resumen=resumen_tratamiento(m)
        assert resumen['estado']=='CATEGORIZADO_CON_MARCA'
        assert not resumen['datos_confirmados'] and not resumen['habilita_entrenamiento']
        assert resumen['avisos_conservados']==tipos_alerta(m)
        posterior=snapshot_revision(m)
        assert all(posterior[k]==v for k,v in antes[m.id].items() if k!='revision_documental')
    assert resumen_tratamiento(moderno) is None
    assert seleccionar(leer_corte(db_session)['filas'])[0]==elegibles

@pytest.mark.parametrize('campo,nuevo',[('salidas',2),('area','Otra lectura'),('fecha_estado','PENDIENTE_HIL'),('ruta_imagen_respaldo','otra.webp')])
def test_cambio_posterior_invalida_tratamiento_que_no_corresponde(db_session,filas,campo,nuevo):
    _,saldo,_,_=filas;registrar(saldo)
    anterior=deepcopy(saldo.revision_documental['tratamiento_hil'])
    setattr(saldo,campo,nuevo)
    assert resumen_tratamiento(saldo)['estado']=='REQUIERE_RECATEGORIZAR'
    assert saldo.revision_documental['tratamiento_hil']==anterior

@pytest.mark.parametrize('daño',['incompleto','desconocido','huella','lista_avisos','sin_decisiones'])
def test_metadata_invalida_nunca_se_muestra_como_tratamiento_completo(db_session,filas,daño):
    _,_,doble,_=filas;registrar(doble)
    r=deepcopy(doble.revision_documental);t=r['tratamiento_hil']
    if daño=='incompleto':t['decisiones']=t['decisiones'][:1]
    elif daño=='desconocido':t['decisiones'][0]['categoria']='APROBADO_SIN_EVIDENCIA'
    elif daño=='huella':t['huella_datos']='obsoleta'
    elif daño=='lista_avisos':t['avisos']=None
    else:t['decisiones']=None
    doble.revision_documental=r
    assert resumen_tratamiento(doble)['estado']=='REQUIERE_RECATEGORIZAR'

def test_api_conserva_observados_y_filtra_tratamiento_sin_escrituras(client,db_session,usuario_operador,filas):
    a,saldo,doble,_=filas;registrar(saldo);db_session.commit()
    antes={m.id:snapshot_revision(m) for m in db_session.query(M)}
    n=db_session.query(AuditoriaSistema).count()
    h={'Authorization':'Bearer '+create_access_token(usuario_operador.id)}
    url='/api/v1/kardex/errores';p={'articulo_id':a.id}
    r=client.get(url,headers=h,params=p);assert r.status_code==200
    assert {f['id'] for f in r.json()}=={saldo.id,doble.id}
    def ids(**params):
        rr=client.get(url,headers=h,params={**p,**params});assert rr.status_code==200;return {f['id'] for f in rr.json()}
    assert ids(tratamiento='CATEGORIZADO_CON_MARCA')=={saldo.id}
    assert ids(tratamiento='POR_CATEGORIZAR')=={doble.id}
    assert ids(categoria='DISCREPANCIA_DOCUMENTAL',tipo='saldo')=={saldo.id}
    assert ids(categoria='DISCREPANCIA_DOCUMENTAL',tipo='area')==set()
    assert client.get(url,headers=h,params={'categoria':'inventada'}).status_code==422
    hist=client.get(f'/api/v1/kardex/historial/{a.id}',headers=h)
    assert hist.status_code==200
    assert next(f for f in hist.json() if f['id']==saldo.id)['tratamiento_hil']['estado']=='CATEGORIZADO_CON_MARCA'
    assert antes=={m.id:snapshot_revision(m) for m in db_session.query(M)}
    assert db_session.query(AuditoriaSistema).count()==n

def test_revision_manual_posterior_no_conserva_categoria_obsoleta(db_session,filas):
    _,saldo,_,_=filas;registrar(saldo)
    r=deepcopy(saldo.revision_documental);r['ultima_revision_manual']='Nueva evidencia humana';saldo.revision_documental=r
    assert resumen_tratamiento(saldo)['estado']=='REQUIERE_RECATEGORIZAR'


def test_area_inferida_conserva_lectura_otras_marcas_y_exclusion(db_session,filas):
    from app.services.areas_historicas import aplicar_asignacion, VERSION
    _,_,doble,moderno=filas
    registrar(doble)
    previo=snapshot_revision(doble)
    propuesta={'area':'Capacitación','version':VERSION,'soporte':'MEDIO',
               'motivo':'Variante propuesta por correlación; identidad no confirmada.'}
    assert aplicar_asignacion(doble,propuesta,plan_sha256='plan1',autor='Titular vía revisión asistida',registrado_en='2026-10-28')
    assert doble.area==previo['area'] and doble.nodo_grafo=='Área: Capacitación'
    assert doble.requiere_auditoria_nodo and doble.area_estado=='PENDIENTE_HIL'
    posterior=snapshot_revision(doble)
    permitidos={'nodo_grafo','area_estado','requiere_auditoria_nodo','revision_documental'}
    assert {k:v for k,v in previo.items() if k not in permitidos}=={k:v for k,v in posterior.items() if k not in permitidos}
    t=resumen_tratamiento(doble)
    assert t['estado']=='CATEGORIZADO_CON_MARCA' and not t['habilita_entrenamiento']
    assert {d['campo']:d['categoria'] for d in t['decisiones']}=={'area':'ASIGNACION_INFERIDA','referencia':'LECTURA_INCIERTA'}
    assert not aplicar_asignacion(doble,propuesta,plan_sha256='plan1',autor='Otro',registrado_en='otro')
    db_session.flush()
    assert doble.id not in {f['id'] for f in seleccionar(leer_corte(db_session)['filas'])[0]}
    rev=deepcopy(doble.revision_documental);rev['asignacion_area']['area']='CEDOAL';doble.revision_documental=rev
    assert resumen_tratamiento(doble)['estado']=='REQUIERE_RECATEGORIZAR'
    with pytest.raises(ValueError,match='históricos'):
        aplicar_asignacion(moderno,propuesta,plan_sha256='plan1',autor='Otro',registrado_en='otro')


def test_api_filtra_inferencias_y_no_las_confirma_sin_decision_de_nodo(client,db_session,usuario_operador,filas):
    from app.services.areas_historicas import aplicar_asignacion, VERSION
    a,_,doble,_=filas;registrar(doble)
    aplicar_asignacion(doble,{'area':'Capacitación','version':VERSION,'soporte':'MEDIO','motivo':'Correlación de siglas'},
                       plan_sha256='plan1',autor='Revisión asistida',registrado_en='2026-10-28')
    db_session.commit()
    h={'Authorization':'Bearer '+create_access_token(usuario_operador.id)}
    r=client.get('/api/v1/kardex/errores',headers=h,params={'articulo_id':a.id,'categoria':'ASIGNACION_INFERIDA'})
    assert r.status_code==200 and {f['id'] for f in r.json()}=={doble.id}
    url=f'/api/v1/kardex/movimiento/{doble.id}'
    datos={'saldo_registrado':doble.saldo_registrado,'motivo':'Revisión de referencia únicamente'}
    r=client.put(url,headers=h,json=datos)
    assert r.status_code==200,r.text
    assert r.json()['area_estado']=='PENDIENTE_HIL'
    assert r.json()['revision_documental']['asignacion_area']['estado']=='INFERIDA'
    r=client.put(url,headers=h,json=datos|{'nodo_grafo':'Área: CID'})
    assert r.status_code==200,r.text
    assert r.json()['revision_documental']['asignacion_area']['estado']=='SUSTITUIDA_REVISION_MANUAL'
