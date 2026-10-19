"""Cotejo completo de artículos parcialmente revisados, conservando sus anclajes.

Es una vía explícita y distinta del constructor para artículos sin revisión.
Exige enumerar todos los anclajes, cotejarlos y conservar cantidades, fechas,
saldos y decisiones anteriores. No borra revisiones para reutilizar el otro flujo.
"""
from copy import deepcopy
import hashlib,json
from app.db.session import SessionLocal
from app.services.clasificador_nodos import clasificar_movimiento,_resolver_area_con_catalogo
from scripts.cotejo_transcripcion_hil import BACKEND,DERIVADOS
from scripts.generar_plan_revision_hil import CAMPOS_BASE,DEST,digest

PROTEGIDOS=('ingresos','salidas','saldo_registrado','fecha_movimiento','estado','orden_fila','orden_pagina_validado')


def construir_con_anclajes(*,version,instantanea,anclajes,hojas,correcciones,tecnicas,grupos_fechas,bases,tipos,observaciones,extras=None):
    rows={r['id']:r for r in json.loads((BACKEND/instantanea).read_text(encoding='utf-8'))}
    assert set(anclajes)=={id for id,r in rows.items() if r['revision_documental']},'Enumerar exactamente todos los cotejos anteriores'
    assert anclajes,'Este constructor requiere anclajes previos'
    ids=[id for hs,_,_ in hojas for id in hs]
    assert len(ids)==len(set(ids)) and set(ids)==set(rows),'Cotejar también los vecinos y anclajes de todas las fotos'
    assert set(correcciones)<=set(rows) and set(tecnicas)<=set(rows) and set(tipos)<=set(rows)
    assert not set(tecnicas)&set(anclajes),'No sustituir fechas técnicas ya revisadas'
    for id in anclajes:
        assert not set(correcciones.get(id,{}))&set(PROTEGIDOS),'Un anclaje material distinto requiere otro plan específico'
    literales={id:correcciones.get(id,{}).get('fecha_movimiento',r['fecha_movimiento']) for id,r in rows.items()}
    fechas=dict(tecnicas)
    for grupo in grupos_fechas:
        assert not set(grupo)&(set(fechas)|set(anclajes))
        for id,nueva in zip(grupo,sorted(literales[id] for id in grupo)):
            if nueva!=literales[id]:fechas[id]=(nueva,'SECUENCIA_AJUSTADA',literales[id],
                'Fechas vecinas ordenadas solo para consulta, después del cotejo de cantidades. Se conserva la fecha escrita y el orden físico.')
    calculos={aid:base['saldo_base'] for aid,base in bases.items()};papel=dict(calculos)
    entries=[];hashes={};diferencias=[];recuentos=[];extras=extras or {};guardados={}
    with SessionLocal() as db:
        for hs,qs,saldos in hojas:
            assert len(hs)==len(qs)==len(saldos)
            for id,q,escrito in zip(hs,qs,saldos):
                r=rows[id];aid=r['articulo_id'];previa=deepcopy(r['revision_documental'] or {})
                tipo=tipos.get(id,previa.get('tipo_fila','MOVIMIENTO'))
                calculos[aid]+=q;saldo=calculos[aid]
                if tipo in ('BASE_DOCUMENTAL','RECUENTO'):
                    assert q==0 and escrito is not None,'Un anclaje documental no inventa ingreso ni salida'
                    if tipo=='RECUENTO':
                        assert previa.get('tipo_fila')=='RECUENTO','Este flujo conserva recuentos previamente revisados, no declara nuevos'
                        recuentos.append({'id':id,'previo':saldo,'escrito':escrito,'diferencia':escrito-saldo})
                    calculos[aid]=saldo=escrito;papel[aid]=escrito
                cambios={'ingresos':q if q>0 else None,'salidas':-q if q<0 else None,'saldo_registrado':saldo,**correcciones.get(id,{})}
                assert (cambios['ingresos'] or 0)-(cambios['salidas'] or 0)==q and cambios['saldo_registrado']==saldo
                rev={'criterios':['T01'],'motivo':'Hoja completa cotejada con filas previas y siguientes; fuente y extracción inicial conservadas.',
                    'tipo_fila':tipo,'saldo_documental':escrito,'origen_saldo':'HIPOTESIS' if escrito is None else ('FOTO' if escrito==saldo else 'RECONSTRUIDO'),
                    'origen_fecha':'FOTO','fecha_documental':literales[id],'usar_saldo_esperado':True,'reconstruir_cadena':True,
                    'cotejo_pagina_completa':True,'hallazgos':['HOJA_COMPLETA_COTEJADA']}
                if tipo=='MOVIMIENTO':
                    if escrito is None:papel[aid]+=q;rev['criterios'].append('T08')
                    else:
                        delta=escrito-(papel[aid]+q);papel[aid]=escrito
                        if delta:
                            diferencias.append({'id':id,'local':delta,'acumulada':escrito-saldo})
                            rev.update(diferencia_local_papel=delta);rev['criterios'].append('T05')
                            rev['hallazgos'].append('DESCUADRE_DEL_PAPEL_CONSERVADO')
                if id==bases[aid]['primera_fila']:
                    rev.update({k:v for k,v in bases[aid].items() if k!='primera_fila'});rev['criterios'].append('T22')
                if id in fechas:
                    nueva,origen,literal,motivo=fechas[id];cambios['fecha_movimiento']=nueva
                    rev.update(origen_fecha=origen,fecha_documental=literal,motivo_fecha=motivo)
                    rev['criterios'].append('T09' if origen=='HIPOTESIS' else 'T11')
                if any(cambios.get(k,r[k])!=r[k] for k in ('detalle','referencia','area','ingresos','salidas')):
                    c=clasificar_movimiento(cambios.get('detalle',r['detalle']),cambios.get('referencia',r['referencia']),cambios.get('area',r['area']),cambios['ingresos'],cambios['salidas'],db)
                    d={k:getattr(c,k) for k in DERIVADOS}
                    if q>0 and d['nodo_grafo'].startswith('Salida:'):
                        area=cambios.get('area',r['area']);n,e,p=(_resolver_area_con_catalogo(area,db) if area else ('Origen no especificado','SIN_AREA_REGISTRADA',False))
                        d.update(nodo_grafo=n,area_estado=e,requiere_auditoria_nodo=p)
                    cambios.update(d)
                if previa:
                    assert all(cambios.get(k,r[k])==r[k] for k in PROTEGIDOS),'La transcripción contradice un anclaje; no sobrescribirlo'
                    assert 'saldo_documental' not in previa or previa['saldo_documental']==escrito
                    assert previa.get('tipo_fila','MOVIMIENTO')==tipo
                    criterios=rev['criterios'];hallazgos=rev['hallazgos'];rev={**rev,**previa}
                    rev['criterios']=sorted(set(criterios+previa.get('criterios',[])))
                    rev['hallazgos']=sorted(set(hallazgos+previa.get('hallazgos',[])))
                    rev['motivo']=previa['motivo']+' Se amplía el cotejo a toda la hoja, conservando esta decisión anterior.'
                    rev['cotejo_pagina_completa']=True
                    rev['revision_previa_cotejo_completo']=deepcopy(previa)
                    guardados[str(id)]={'valores':{k:r[k] for k in PROTEGIDOS},'revision':deepcopy(previa)}
                extra=extras.get(id,{})
                rev['motivo']+=(' '+extra['motivo']) if extra.get('motivo') else ''
                rev['criterios']=sorted(set(rev['criterios']+extra.get('criterios',[])))
                assert not previa or not set(extra.get('revision',{}))&set(previa),'No sobrescribir metadatos de anclaje'
                rev.update(extra.get('revision',{}));cambios.update(extra.get('clasificacion',{}))
                foto=(BACKEND/r['ruta_imagen_respaldo']).resolve();hashes.setdefault(str(foto),hashlib.sha256(foto.read_bytes()).hexdigest())
                adicionales={k:r[k] for k in DERIVADOS}
                if previa:adicionales['revision_documental']=deepcopy(previa)
                entries.append({'id':id,'articulo_id':aid,'pagina':f"L{r['lote_id']:04d}-P{r['numero_pagina']:02d}",
                    'esperado':{k:r[k] for k in CAMPOS_BASE},'esperado_adicional':adicionales,
                    'cambios':cambios,'revision':rev,'fuente':str(foto),'sha256_imagen':hashes[str(foto)]})
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    return {'version':version,'criterio_sha256':digest(policy),'revisiones':entries,'sin_reasociaciones_ni_borrados':True,
        'autorizacion_adicional':'Cotejo asistido completo conservando los 23 criterios y las decisiones anteriores, por delegación del titular.',
        'observaciones_articulos':observaciones,'cotejo':{'fotografias':len(hashes),'movimientos':len(entries),'cierres':calculos,
            'cierres_documentales':papel,'discrepancias':diferencias,'recuentos_conservados':recuentos,'anclajes_previos':guardados,'nuevos_distintos':len(entries)-len(guardados)},
        'limites':['Revisión asistida, no validación institucional.','Se conservan los anclajes y sus motivos; no se reimportan artículos.','Las fechas técnicas e hipótesis no se certifican como hechos.']}


def verificar_anclajes(plan,por_id):
    """Comprobación independiente del constructor sobre filas ya aplicadas."""
    for id,ancla in plan['cotejo'].get('anclajes_previos',{}).items():
        m=por_id[int(id)];rev=m.revision_documental
        from app.services.revision_documental import snapshot_revision
        actual=snapshot_revision(m)
        assert all(actual[k]==v for k,v in ancla['valores'].items()),'Se alteraron valores materiales de un anclaje'
        assert rev['revision_previa_cotejo_completo']==ancla['revision'],'No se conserva íntegra la revisión anterior'
        for k,v in ancla['revision'].items():
            if k in ('plan_sha256','revisado_en','autor_registro'):continue
            if k in ('criterios','hallazgos','planes_aplicados'):assert set(v)<=set(rev[k])
            elif k=='motivo':assert rev[k].startswith(v)
            else:assert rev[k]==v,(id,k)
