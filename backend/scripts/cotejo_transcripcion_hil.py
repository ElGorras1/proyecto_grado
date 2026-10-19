"""Construye planes desde transcripciones visuales explícitas; no ejecuta OCR ni escribe en la base."""
import hashlib,json
from pathlib import Path
from app.db.session import SessionLocal
from app.services.clasificador_nodos import clasificar_movimiento,_resolver_area_con_catalogo
from scripts.generar_plan_revision_hil import CAMPOS_BASE,DEST,digest

BACKEND=Path(__file__).resolve().parents[1]
DERIVADOS=('nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia')


def construir(*,version,instantanea,hojas,correcciones,tecnicas,grupos_fechas,bases,observaciones,extras=None):
    rows={r['id']:r for r in json.loads((BACKEND/instantanea).read_text(encoding='utf-8'))}
    assert all(not r['revision_documental'] for r in rows.values()),'Conservar cotejos previos'
    ids=[id for hs,_,_ in hojas for id in hs]
    assert len(ids)==len(set(ids)) and set(ids)==set(rows),'Transcribir todas las filas de las fotos'
    assert set(correcciones)<=set(rows) and set(tecnicas)<=set(rows)
    literales={id:correcciones.get(id,{}).get('fecha_movimiento',r['fecha_movimiento']) for id,r in rows.items()}
    fechas=dict(tecnicas)
    for grupo in grupos_fechas:
        assert not set(grupo)&set(fechas)
        for id,nueva in zip(grupo,sorted(literales[id] for id in grupo)):
            if nueva!=literales[id]:fechas[id]=(nueva,'SECUENCIA_AJUSTADA',literales[id],
                'Fechas vecinas ordenadas solo para consulta según T10/T11 después de cotejar cantidades. La fecha escrita de cada fila se conserva; no se certifica el día real.')
    calculos={aid:base['saldo_base'] for aid,base in bases.items()};papel=dict(calculos)
    entries=[];hashes={};diferencias=[];extras=extras or {}
    with SessionLocal() as db:
        for hs,qs,saldos in hojas:
            assert len(hs)==len(qs)==len(saldos)
            for id,q,escrito in zip(hs,qs,saldos):
                r=rows[id];aid=r['articulo_id'];calculos[aid]+=q;saldo=calculos[aid]
                cambios={'ingresos':q if q>0 else None,'salidas':-q if q<0 else None,'saldo_registrado':saldo,**correcciones.get(id,{})}
                # La matriz cotejada de cantidades es la fuente del recálculo.
                assert (cambios['ingresos'] or 0)-(cambios['salidas'] or 0)==q
                assert cambios['saldo_registrado']==saldo
                rev={'criterios':['T01'],'motivo':'Hoja completa cotejada con las filas previas y siguientes; se conservan la foto, los valores escritos y la extracción original.',
                    'tipo_fila':'MOVIMIENTO','saldo_documental':escrito,'origen_saldo':'HIPOTESIS' if escrito is None else ('FOTO' if saldo==escrito else 'RECONSTRUIDO'),
                    'origen_fecha':'FOTO','fecha_documental':literales[id],'usar_saldo_esperado':True,'reconstruir_cadena':True,
                    'cotejo_pagina_completa':True,'hallazgos':['HOJA_COMPLETA_COTEJADA']}
                if escrito is None:
                    papel[aid]+=q;rev['criterios'].append('T08');rev['motivo']+=' El saldo no está escrito; se representa como hipótesis por continuidad.'
                else:
                    delta=escrito-(papel[aid]+q);papel[aid]=escrito
                    if delta:
                        rev['criterios'].append('T05');rev['diferencia_local_papel']=delta
                        rev['hallazgos'].append('DESCUADRE_DEL_PAPEL_CONSERVADO');diferencias.append({'id':id,'local':delta,'acumulada':escrito-saldo})
                if id==bases[aid]['primera_fila']:
                    rev.update({k:v for k,v in bases[aid].items() if k!='primera_fila'});rev['criterios'].append('T22')
                if id in fechas:
                    nueva,origen,literal,motivo=fechas[id];cambios['fecha_movimiento']=nueva
                    rev.update(origen_fecha=origen,fecha_documental=literal,motivo_fecha=motivo)
                    rev['criterios'].append('T09' if origen=='HIPOTESIS' else 'T11')
                if any(cambios.get(k,r[k])!=r[k] for k in ('detalle','area','referencia','ingresos','salidas')):
                    c=clasificar_movimiento(cambios.get('detalle',r['detalle']),cambios.get('referencia',r['referencia']),cambios.get('area',r['area']),cambios['ingresos'],cambios['salidas'],db)
                    d={k:getattr(c,k) for k in DERIVADOS}
                    if q>0 and d['nodo_grafo'].startswith('Salida:'):
                        area=cambios.get('area',r['area']);n,e,p=(_resolver_area_con_catalogo(area,db) if area else ('Origen no especificado','SIN_AREA_REGISTRADA',False))
                        d.update(nodo_grafo=n,area_estado=e,requiere_auditoria_nodo=p)
                    cambios.update(d)
                extra=extras.get(id,{})
                rev['motivo']+=(' '+extra.get('motivo','')) if extra.get('motivo') else ''
                rev['criterios']=sorted(set(rev['criterios']+extra.get('criterios',[])))
                rev.update(extra.get('revision',{}));cambios.update(extra.get('clasificacion',{}))
                foto=(BACKEND/r['ruta_imagen_respaldo']).resolve()
                hashes.setdefault(str(foto),hashlib.sha256(foto.read_bytes()).hexdigest())
                entries.append({'id':id,'articulo_id':aid,'pagina':f"L{r['lote_id']:04d}-P{r['numero_pagina']:02d}",
                    'esperado':{k:r[k] for k in CAMPOS_BASE},'esperado_adicional':{k:r[k] for k in DERIVADOS},
                    'cambios':cambios,'revision':rev,'fuente':str(foto),'sha256_imagen':hashes[str(foto)]})
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    return {'version':version,'criterio_sha256':digest(policy),'revisiones':entries,'sin_reasociaciones_ni_borrados':True,
        'autorizacion_adicional':'Aplicación asistida de los 23 criterios del titular, quien delegó las decisiones de interpretación equivalentes.',
        'observaciones_articulos':observaciones,
        'cotejo':{'fotografias':len(hashes),'movimientos':len(entries),'cierres':calculos,'cierres_documentales':papel,'discrepancias':diferencias},
        'limites':['Los saldos reconstruidos no certifican existencias físicas.','Las hipótesis conservan sus exclusiones; no se inventan fechas confirmadas.','No se crean áreas ni alias ni se fusionan artículos por similitud.']}


def congelar(plan):
    path=DEST/f"plan_continuacion_{plan['version']:02d}.json"
    if path.exists():raise RuntimeError('Conservar el plan congelado; utilizar otro lote para revisiones posteriores.')
    path.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'plan':str(path),'sha256':digest(json.loads(path.read_text(encoding='utf-8'))),'cotejo':plan['cotejo']},ensure_ascii=False))
