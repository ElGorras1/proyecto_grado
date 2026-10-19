import hashlib
import json
from copy import deepcopy
import pytest
from app.models.kardex import MovimientoKardex as M
from app.models.auditoria import AuditoriaSistema
from scripts.generar_plan_revision_hil import CAMPOS_BASE,digest
from scripts import aplicar_revision_hil as script
from app.services.revision_documental import snapshot_revision,aplicar_cambio
from test_analitica import historico


def preparar(db,historico,tmp_path,monkeypatch):
    monkeypatch.setattr(script,'BACKEND',tmp_path);monkeypatch.setattr(script,'DEST',tmp_path)
    (tmp_path/'storage').mkdir();foto=tmp_path/'storage/fuente.webp';foto.write_bytes(b'fotografia cotejada')
    policy={'criterio':'recuperar evidencia omitida'}
    (tmp_path/'criterios_version_1.json').write_text(json.dumps(policy),encoding='utf-8')
    m=db.query(M).filter_by(articulo_id=historico.id).order_by(M.id).first()
    m.ruta_imagen_respaldo='storage/fuente.webp';m.numero_pagina=1;m.orden_fila=1
    m.datos_originales={'fuente':'EXTRACCION_MLLM','orden_fila':1};m.fecha_original=m.fecha_movimiento
    db.commit();snap=snapshot_revision(m)
    plan={'criterio_sha256':digest(policy),'revisiones':[{
        'id':m.id,'articulo_id':m.articulo_id,'fuente':str(foto),'sha256_imagen':hashlib.sha256(foto.read_bytes()).hexdigest(),
        'esperado':{k:snap[k] for k in CAMPOS_BASE},'cambios':{'orden_fila':2},
        'revision':{'criterios':['T23'],'motivo':'Se recupera el renglón anterior omitido por el OCR.'}}],
        'observaciones_articulos':[],
        'recuperaciones':[{'clave':'fuente-inventario-fila1','fuente':str(foto),'sha256_imagen':hashlib.sha256(foto.read_bytes()).hexdigest(),
            'campos':{'articulo_id':m.articulo_id,'lote_id':m.lote_id,'ruta_imagen_respaldo':m.ruta_imagen_respaldo,'numero_pagina':1,'orden_fila':1,
                'fecha_movimiento':m.fecha_movimiento.isoformat(),'fecha_original':None,'detalle':'Saldo según inventario',
                'ingresos':None,'salidas':None,'saldo_registrado':0,'saldo_calculado':0,'estado':'ACTIVO','fecha_estado':'ESTIMADA_HIL',
                'datos_originales':{'fuente':'LECTURA_FOTO_HIL','fecha_documental':None,'saldo_registrado':0,'orden_fila':1}},
            'revision':{'criterios':['T22','T09'],'motivo':'Inventario visible omitido en la extracción; no es una nueva operación.',
                'origen_fecha':'HIPOTESIS','fecha_documental':None,'motivo_fecha':'La fila no tiene fecha.',
                'tipo_fila':'BASE_DOCUMENTAL','saldo_base':0,'origen_saldo_base':'DOCUMENTO','saldo_documental':0,'origen_saldo':'FOTO',
                'usar_saldo_esperado':True,'reconstruir_cadena':True}}]}
    return m,plan,foto


def test_recupera_evidencia_sin_sobrescribir_ocr_y_reintenta_sin_duplicados(historico,db_session,tmp_path,monkeypatch):
    m,plan,_=preparar(db_session,historico,tmp_path,monkeypatch)
    plan['observaciones_articulos']=[{'articulo_id':m.articulo_id,'observado':True,'excluir_entrenamiento':False,'motivo':'Se recuperó una fila omitida por OCR; foto y extracción previa conservadas.'}]
    cantidad=db_session.query(M).count();original=script.fuente_hash(db_session)
    r=script.aplicar(db_session,plan,confirmar=True)
    assert len(r['filas_recuperadas'])==1 and db_session.query(M).count()==cantidad+1
    nuevo=db_session.get(M,r['filas_recuperadas'][0])
    assert nuevo.fecha_original is None and nuevo.datos_originales['fuente']=='LECTURA_FOTO_HIL'
    assert m.orden_fila==2 and m.datos_originales['orden_fila']==1
    assert script.fuente_hash(db_session,excluir_ids=[nuevo.id])==original
    assert db_session.query(AuditoriaSistema).filter_by(accion='recuperar_fila_kardex_hil').count()==1
    assert r['observaciones_articulos']==1 and historico.observacion_hil['plan_sha256']==digest(plan)
    repetir=script.aplicar(db_session,plan,confirmar=True)
    assert repetir['filas_recuperadas']==[] and repetir['aplicadas']==0 and repetir['auditorias_movimientos']==0
    assert repetir['observaciones_articulos']==0
    aplicar_cambio(nuevo,{}, {'criterios':['T09'],'motivo':'Nuevo cotejo conserva la ausencia documental de fecha.'},criterio_sha256='a'*64,plan_sha256='b'*64)
    assert nuevo.fecha_original is None


def test_fallo_de_precondicion_revierte_tambien_fila_recuperada(historico,db_session,tmp_path,monkeypatch):
    m,plan,_=preparar(db_session,historico,tmp_path,monkeypatch)
    cantidad=db_session.query(M).count();original=script.fuente_hash(db_session)
    plan['revisiones'][0]['esperado']['detalle']='Lectura desactualizada'
    with pytest.raises(AssertionError,match='cambió desde el cotejo'):
        script.aplicar(db_session,plan,confirmar=True)
    db_session.rollback()
    assert db_session.query(M).count()==cantidad and script.fuente_hash(db_session)==original
    assert db_session.query(AuditoriaSistema).filter_by(accion='recuperar_fila_kardex_hil').count()==0
