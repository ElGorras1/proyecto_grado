from datetime import date
from copy import deepcopy
import pytest
from app.models.kardex import MovimientoKardex
from app.services.revision_documental import aplicar_cambio, recalcular_revision
from app.services.datos_analitica import leer_corte, seleccionar
from app.services.kardex_service import recalcular_saldos_posteriores
from app.services.inventario import ultimo_cierre_kardex
from test_analitica import historico, cabecera

def fila(i, ingreso=None, salida=None, saldo=0, rev=None):
    return MovimientoKardex(id=i, articulo_id=1, lote_id=1, fecha_movimiento=date(2020, 1, 1),
        detalle="Feria", ingresos=ingreso, salidas=salida, saldo_registrado=saldo,
        estado="ACTIVO", fecha_estado="SIN_ALERTA", revision_documental=rev)

def aplicar(m, cambios, rev=None):
    aplicar_cambio(m, cambios, {"motivo":"Cotejo de la fotografía", "criterios":["T01"], **(rev or {})},
        criterio_sha256="a"*64, plan_sha256="b"*64)

def test_corrige_ocr_sin_borrar_extraccion_y_sin_corregir_fila_vecina_buena():
    anterior=fila(1, ingreso=1, saldo=1)
    m=fila(2, ingreso=10, saldo=11)
    m.datos_originales={"ingresos":10,"saldo_registrado":11}
    original=deepcopy(m.datos_originales)
    aplicar(m, {"ingresos":40,"saldo_registrado":41}, {"saldo_documental":41})
    siguiente=fila(3,salida=5,saldo=36)
    recalcular_revision([anterior,m,siguiente])
    assert m.datos_originales==original
    assert m.saldo_calculado==41 and not m.tiene_error_saldo
    assert siguiente.saldo_calculado==36 and not siguiente.tiene_error_saldo


def test_comilla_en_detalle_se_resuelve_sin_borrar_marca_original():
    m=fila(1,ingreso=3,saldo=3)
    m.detalle='"'
    m.datos_originales={'detalle':'"','ingresos':3}
    aplicar(m,{'detalle':'Feria del Libro'},{'criterios':['T18']})
    assert m.detalle=='Feria del Libro' and m.datos_originales['detalle']=='"'
    for invalid in (None,3,'   '):
        with pytest.raises(ValueError):aplicar(m,{'detalle':invalid})


def test_repetir_plan_antiguo_no_revierte_observacion_posterior(historico,db_session,tmp_path,monkeypatch):
    import json,hashlib
    from scripts import aplicar_revision_hil as script
    from scripts.generar_plan_revision_hil import CAMPOS_BASE,digest
    from app.services.revision_documental import snapshot_revision
    monkeypatch.setattr(script,'BACKEND',tmp_path)
    monkeypatch.setattr(script,'DEST',tmp_path)
    (tmp_path/'storage').mkdir()
    foto=tmp_path/'storage'/'fuente.webp';foto.write_bytes(b'fuente para comprobar huellas')
    policy={'criterio':'T18 recibido'}
    (tmp_path/'criterios_version_1.json').write_text(json.dumps(policy),encoding='utf-8')
    m=db_session.query(MovimientoKardex).filter_by(articulo_id=historico.id).order_by(MovimientoKardex.id).first()
    m.ruta_imagen_respaldo='storage/fuente.webp';m.fecha_original=m.fecha_movimiento
    m.datos_originales={'detalle':m.detalle};db_session.commit()
    def plan(texto,motivo):
        snap=snapshot_revision(m)
        return {'criterio_sha256':digest(policy),'revisiones':[{
            'id':m.id,'articulo_id':m.articulo_id,'fuente':str(foto),'sha256_imagen':hashlib.sha256(foto.read_bytes()).hexdigest(),
            'esperado':{k:snap[k] for k in CAMPOS_BASE},'cambios':{'detalle':texto},
            'revision':{'criterios':['T18'],'motivo':motivo}}],
            'observaciones_articulos':[{'articulo_id':m.articulo_id,'observado':True,'excluir_entrenamiento':False,'motivo':motivo}]}
    p1=plan('Detalle cotejado','Primera lectura')
    script.aplicar(db_session,p1,confirmar=True)
    p2=plan('Detalle cotejado después','Nueva lectura de columna correcta')
    script.aplicar(db_session,p2,confirmar=True)
    replay=script.aplicar(db_session,p1,confirmar=True)
    db_session.refresh(historico)
    assert replay['aplicadas']==0 and replay['observaciones_articulos']==0
    assert historico.observacion_hil['motivo']=='Nueva lectura de columna correcta'
    assert m.detalle=='Detalle cotejado después'
    pendiente=plan('Otro cotejo','Nueva propuesta')
    pendiente['revisiones'][0]['esperado_adicional']={'nodo_grafo':m.nodo_grafo}
    m.nodo_grafo='Clasificación editada después de preparar el plan'
    db_session.commit()
    with pytest.raises(AssertionError,match='Cambió la clasificación'):
        script.aplicar(db_session,pendiente,confirmar=False)
    assert m.detalle=='Detalle cotejado después'
    db_session.rollback()

def test_reconstruccion_independiente_conserva_error_persistente_del_papel():
    a=fila(1,ingreso=133,saldo=133)
    b=fila(2,salida=40,saldo=73,rev={"saldo_documental":73,"reconstruir_cadena":True,"usar_saldo_esperado":True})
    c=fila(3,salida=4,saldo=69,rev={"saldo_documental":69,"usar_saldo_esperado":True})
    recalcular_revision([a,b,c])
    assert (b.saldo_registrado,c.saldo_registrado)==(93,89)
    assert b.revision_documental["saldo_documental"]==73
    assert b.revision_documental["diferencia_saldo_documental"]==-20
    assert c.revision_documental["diferencia_saldo_documental"]==-20

def test_recuento_registra_diferencia_sin_crear_una_salida():
    a=fila(1,ingreso=21,saldo=21)
    b=fila(2,saldo=3,rev={"tipo_fila":"RECUENTO"})
    c=fila(3,salida=1,saldo=2)
    recalcular_revision([a,b,c])
    assert b.revision_documental["diferencia_con_cadena_previa"]==-18
    assert b.ingresos is None and b.salidas is None
    assert not b.tiene_error_saldo and not c.tiene_error_saldo

def test_version_posterior_conserva_identidad_del_lote_para_no_reaplicar_el_anterior():
    m=fila(1,ingreso=2,saldo=2)
    aplicar(m,{"saldo_registrado":3})
    aplicar_cambio(m,{"saldo_registrado":2},{"motivo":"Revisión posterior confirmada","criterios":["T05"]},
        criterio_sha256="a"*64,plan_sha256="c"*64)
    assert m.revision_documental["planes_aplicados"]==["b"*64,"c"*64]
    assert m.revision_documental["plan_sha256"]=="c"*64

def test_anulado_documental_permanece_pero_no_reduce_saldo():
    a=fila(1,ingreso=10,saldo=10)
    b=fila(2,salida=8,saldo=2)
    aplicar(b,{"estado":"ANULADO_DOCUMENTO"},{"tipo_fila":"ANULADO"})
    c=fila(3,salida=3,saldo=7)
    recalcular_revision([a,b,c])
    assert b.salidas==8 and b.saldo_registrado==2
    assert c.saldo_calculado==7 and not c.tiene_error_saldo

def test_nota_disponibilidad_conserva_total_y_no_inventa_baja():
    a=fila(1,ingreso=9,saldo=9)
    b=fila(2,ingreso=8,saldo=14,rev={"saldo_documental":17,"ajuste_disponibilidad":-3})
    c=fila(3,salida=3,saldo=11)
    recalcular_revision([a,b,c])
    assert b.ingresos==8 and b.salidas is None
    assert b.saldo_calculado==14 and c.saldo_calculado==11

def test_fecha_estimada_exige_marca_y_no_entrena(historico,db_session):
    rows=db_session.query(MovimientoKardex).order_by(MovimientoKardex.id).all()
    m=rows[0]
    aplicar(m,{"fecha_movimiento":"2020-01-01"},{"origen_fecha":"HIPOTESIS","fecha_documental":None,"motivo_fecha":"La foto no tiene fecha"})
    db_session.commit()
    corte=leer_corte(db_session)
    assert m.id in corte["exclusiones"]["fecha_inferida_hil"]
    assert m.fecha_estado=="ESTIMADA_HIL"
    with pytest.raises(ValueError):
        aplicar(rows[1],{"fecha_movimiento":"2020-01-02"},{"origen_fecha":"HIPOTESIS"})


def test_cantidad_inferida_no_entrena_aunque_fecha_y_saldo_sean_legibles(historico,db_session):
    m=db_session.query(MovimientoKardex).filter_by(articulo_id=historico.id).order_by(MovimientoKardex.id).first()
    aplicar(m,{}, {'origen_cantidades':'HIPOTESIS','origen_fecha':'FOTO','origen_saldo':'FOTO',
                   'motivo':'La cantidad está en blanco; el saldo permite una reconstrucción condicional.'})
    db_session.commit()
    corte=leer_corte(db_session)
    assert m.id in corte['exclusiones']['cantidad_hipotetica_hil']
    elegibles,_=seleccionar(corte['filas'])
    assert m.id not in {f['id'] for f in elegibles}

def test_orden_validado_modifica_cierre_sin_cambiar_numero_foto(historico,db_session):
    rows=db_session.query(MovimientoKardex).filter(MovimientoKardex.lote_id==10).all()
    for r in rows:r.numero_pagina=1;r.orden_pagina_validado=2
    ultimo=rows[-1]
    ultimo.numero_pagina=2;ultimo.orden_pagina_validado=1
    db_session.commit()
    cierre=ultimo_cierre_kardex(db_session,historico.id)
    assert cierre.id==rows[-2].id
    assert ultimo.numero_pagina==2
    recalcular_saldos_posteriores(db_session,historico.id,confirmar=False)

def test_articulo_observado_excluye_historico_y_no_elimina_cierre(historico,db_session):
    historico.observacion_hil={"observado":True,"excluir_entrenamiento":True,"motivo":"Dos filas ambiguas"}
    db_session.commit()
    corte=leer_corte(db_session)
    assert corte["perfil"]["elegibles"]==0
    assert len(corte["exclusiones"]["articulos_observados_hil"])==200
    assert ultimo_cierre_kardex(db_session,historico.id) is not None

def test_observacion_requiere_rol_y_cierra_con_historial(client,db_session,historico,usuario_admin,usuario_operador):
    ruta=f"/api/v1/kardex/articulos/{historico.id}/observacion-hil"
    body={"observado":True,"excluir_entrenamiento":True,"motivo":"Dos filas pendientes de aclaración"}
    assert client.put(ruta,json=body).status_code==401
    assert client.put(ruta,json=body,headers=cabecera(usuario_operador)).status_code==403
    assert client.put(ruta,json=body,headers=cabecera(usuario_admin)).status_code==200
    lista=client.get("/api/v1/kardex/articulos",headers=cabecera(usuario_admin)).json()
    art=next(a for a in lista if a["id"]==historico.id)
    assert art["observacion_hil"]["excluir_entrenamiento"] is True
    assert client.put(ruta,json=body|{"observado":False},headers=cabecera(usuario_admin)).status_code==422
    assert client.put(ruta,json=body|{"observado":False,"excluir_entrenamiento":False},headers=cabecera(usuario_admin)).status_code==200

