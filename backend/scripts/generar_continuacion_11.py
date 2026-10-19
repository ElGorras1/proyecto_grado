"""Cotejo completo de las siete fotos de Óscar Cerruto, artículo 87."""
import hashlib,json
from pathlib import Path
from app.db.session import SessionLocal
from app.services.clasificador_nodos import clasificar_movimiento,_resolver_area_con_catalogo
from scripts.generar_plan_revision_hil import CAMPOS_BASE,DEST,digest

BACKEND=Path(__file__).resolve().parents[1]
HOJAS=[
 (range(5528,5554),[483,-1,-8,-1,-5,-1,-50,-15,17,-1,-1,-1,-1,-74,-3,3,-5,-10,-15,-1,-8,-5,-1,-1,3,-3],
  [483,482,474,473,468,467,417,402,419,418,417,416,415,341,338,341,336,326,311,310,302,297,296,295,298,295]),
 (range(5554,5580),[-1,-10,-2,-100,-10,-1,-5,10,1,-5,-5,-1,-5,-1,-3,-1,-1,1,-1,100,100,300,-1,-2,2,-10],
  [294,284,282,182,172,171,166,176,177,172,167,166,161,160,157,156,155,156,155,255,355,655,654,652,654,644]),
 (range(5580,5606),[8,-3,1,-2,2,-1,-10,-10,-3,-75,-5,9,-2,-3,1,-3,-1,-30,-5,-10,10,-5,-1,1,-2,-2],
  [652,649,650,648,650,649,639,629,626,551,546,555,553,550,551,548,547,517,512,502,512,507,506,507,505,503]),
 (range(5606,5632),[4,-2,2,-2,-1,-1,1,5,-1,-1,1,1,-10,-5,15,-3,-5,7,-5,-1,-1,5,-1,-1,-10,-1],
  [507,502,504,502,501,500,501,506,505,504,505,506,496,491,506,503,498,505,500,499,498,503,502,501,491,490]),
 (range(5632,5657),[-1,8,-2,-3,-5,-5,-4,2,-1,5,-1,-3,-2,-5,2,-3,-2,-5,-1,-1,-1,4,-2,-1,-3],
  [489,497,495,492,487,482,478,480,479,484,483,480,478,473,475,472,470,465,464,463,462,466,464,463,460]),
 (range(5657,5683),[-1,-2,-2,-1,-2,-1,-1,-1,-5,-5,-2,-1,-2,-5,10,-5,-2,-1,-3,-2,-2,-1,2,-7,-3,-2],
  [459,457,455,454,452,451,450,449,444,439,437,436,434,429,439,434,432,431,428,426,424,423,425,418,415,413]),
 (range(5683,5695),[-2,-2,-5,-1,-4,-20,-5,2,-5,4,-8,-5],
  [411,409,404,403,399,379,374,376,371,375,367,362]),
]
FECHAS_FOTO={5552:'2010-06-11',5681:'2023-10-02'}
PARES=[(5564,5565),(5572,5573),(5578,5579),(5603,5604),(5615,5616),(5662,5663),(5673,5674)]
FECHAS_TECNICAS={
 5539:('2009-08-31','SECUENCIA_AJUSTADA','2009-08-21','21-08-09 escrito después del 31-08: consulta técnica con el antecedente, conservando la fecha del papel.'),
 5557:('2010-08-04','HIPOTESIS',None,'Día repasado de lectura 4/19 no inequívoca. Se conserva el 4 técnico del OCR, sin confirmar su lectura.'),
 5590:('2012-05-22','SECUENCIA_AJUSTADA','2012-05-09','09-05-12 escrito después del 22-05. Fecha técnica del antecedente; no se cambia el orden de cantidades.'),
 5591:('2012-05-22','SECUENCIA_AJUSTADA','2012-05-19','19-05-12 escrito después del 22-05. Se conserva el literal; consulta técnica del antecedente.'),
 5598:('2012-08-21','SECUENCIA_AJUSTADA','2012-07-24','24-07-12 intercalado después del 21-08. Fecha técnica del antecedente.'),
 5599:('2012-08-21','SECUENCIA_AJUSTADA','2012-08-05','05-08-12 intercalado después del 21-08. Fecha técnica del antecedente.'),
 5600:('2012-08-21','SECUENCIA_AJUSTADA','2012-08-14','14-08-12 intercalado después del 21-08. Fecha técnica del antecedente.'),
 5654:('2016-09-14','SECUENCIA_AJUSTADA','2019-09-14','La fuente escribe 14-09-19 pero el detalle dice FIL-2016, entre agosto de 2016 y marzo de 2017. Año técnico 2016 según contexto, excluido del entrenamiento; el 19 escrito permanece.'),
 5661:('2017-07-06','HIPOTESIS',None,'Fecha en blanco. Se usa técnicamente el antecedente 06-07-17, sin acreditar el día.'),
 5679:('2022-10-17','HIPOTESIS',None,'Fecha en blanco de devolución. Consulta con la del antecedente, sin confirmar una fecha propia.'),
}


def generar():
    rows=json.loads((BACKEND/'backups/continuacion_hil_11_20261015/articulo_87_antes.json').read_text(encoding='utf-8'))
    rows={r['id']:r for r in rows};assert len(rows)==167 and not any(r['revision_documental'] for r in rows.values())
    literal={id:r['fecha_movimiento'] for id,r in rows.items()};literal.update(FECHAS_FOTO)
    fechas=dict(FECHAS_TECNICAS)
    for par in PARES:
        for id,nueva in zip(par,sorted(literal[id] for id in par)):
            if nueva!=literal[id]:fechas[id]=(nueva,'SECUENCIA_AJUSTADA',literal[id],'Fechas contiguas permutadas para consulta según T10/T11 tras comprobar cantidades. Se preserva la fecha de cada renglón del papel.')
    calc=papel=0;entries=[];hashes={};diferencias=[]
    with SessionLocal() as db:
        for ids,qs,saldos in HOJAS:
            assert len(ids)==len(qs)==len(saldos)
            for id,q,escrito in zip(ids,qs,saldos):
                r=rows[id];calc+=q;delta=escrito-(papel+q);papel=escrito
                cambios={'ingresos':q if q>0 else None,'salidas':-q if q<0 else None,'saldo_registrado':calc}
                rev={'criterios':['T01'],'motivo':'Siete hojas completas cotejadas con contexto anterior y posterior. Se conserva la extracción original y el saldo escrito.',
                    'tipo_fila':'MOVIMIENTO','saldo_documental':escrito,'origen_saldo':'FOTO' if calc==escrito else 'RECONSTRUIDO',
                    'origen_fecha':'FOTO','fecha_documental':literal[id],'usar_saldo_esperado':True,'reconstruir_cadena':True,
                    'cotejo_pagina_completa':True,'hallazgos':['HOJA_COMPLETA_COTEJADA']}
                if delta:
                    rev['criterios'].append('T05');rev['diferencia_local_papel']=delta
                    rev['hallazgos'].append('DESCUADRE_DEL_PAPEL_CONSERVADO');diferencias.append({'id':id,'local':delta,'acumulada':escrito-calc})
                if id==5528:
                    rev.update(saldo_base=0,origen_saldo_base='HIPOTESIS',motivo_base='Primer ingreso 483 igual al saldo 483: base cero inferida, sin acreditar un recuento anterior.')
                    rev['criterios'].append('T22')
                if id==5574:rev['motivo']+=' La foto dice saldo 355, no 356: 255 + ingreso 100 = 355.'
                if id==5606:rev['motivo']+=' La foto tiene ingreso 4 y saldo 507 repasado, no 504. La fila siguiente salta a 502 al restar 2: allí se origina la diferencia 3 del papel.'
                if id==5607:rev['motivo']+=' 507 - salida 2 = 505; el documento escribe 502. Se conserva y propaga la diferencia -3 del papel, sin inventar otra salida.'
                if id==5618:rev['motivo']+=' SALIDAS dice 10 y SALDO 496 repasado, no salida 15 ni saldo 491. El siguiente movimiento de salida 5 llega a 491.'
                if id==5625:rev['criterios'].append('T02');rev['motivo']+=' Donación Patipiña: 1 está en SALIDAS, no en INGRESOS.'
                if id==5632:rev['motivo']+=' La salida 1 de Gerardo Bolaños es visible en SALIDAS; no es una cantidad inferida de los saldos.'
                if id in (5690,5692):
                    cambios['area']=None;rev['criterios'].append('T23');rev['motivo']+=' La cifra 2/4 de devolución pertenece a INGRESOS, no a ÁREA.'
                if id==5547:cambios.update(referencia='Bibliot.',area='Dirección');rev['criterios'].append('T23')
                if id in (5542,5549):cambios.update(referencia='Ventas',area='Cedoal');rev['criterios'].append('T23')
                if id==5534:cambios['detalle']='10% Chuymampi'
                if id in (5614,5616):cambios['detalle']='Letras Paceñas'
                if id==5635:cambios['detalle']='Noira Quiroga'
                if id==5650:cambios['detalle']='Larga Noche de Museos'
                if id==5651:cambios['area']='CAP'
                if r['area'] in ('CEDOOL','CEDOOL.','CEDOC','CPTOL'):
                    cambios['area']='CEDOAL';rev['motivo']+=' Se recupera el texto CEDOAL visible en ÁREA; no se crea un área por similitud.'
                if id in FECHAS_FOTO:cambios['fecha_movimiento']=FECHAS_FOTO[id]
                if id in fechas:
                    nueva,origen,fecha,motivo=fechas[id];cambios['fecha_movimiento']=nueva
                    rev.update(origen_fecha=origen,fecha_documental=fecha,motivo_fecha=motivo)
                    rev['criterios'].append('T09' if origen=='HIPOTESIS' else 'T11')
                if id==5557:rev['lectura_fecha_parcial']='4/19-08-10, día repasado'
                if any(cambios.get(k,r[k])!=r[k] for k in ('detalle','area','referencia','ingresos','salidas')):
                    clas=clasificar_movimiento(cambios.get('detalle',r['detalle']),cambios.get('referencia',r['referencia']),cambios.get('area',r['area']),cambios['ingresos'],cambios['salidas'],db)
                    d={k:getattr(clas,k) for k in ('nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia')}
                    if q>0 and d['nodo_grafo'].startswith('Salida:'):
                        area=cambios.get('area',r['area']);n,e,p=(_resolver_area_con_catalogo(area,db) if area else ('Origen no especificado','SIN_AREA_REGISTRADA',False))
                        d.update(nodo_grafo=n,area_estado=e,requiere_auditoria_nodo=p)
                    cambios.update(d)
                if id==5634:
                    cambios.update(area_estado='PENDIENTE_HIL',requiere_auditoria_nodo=True)
                    rev['motivo']+=' CEDOAL cruza REF/ÁREA: se conserva en REF y se deja pendiente su atribución; no se certifica área ausente.'
                rev['criterios']=sorted(set(rev['criterios']))
                foto=(BACKEND/r['ruta_imagen_respaldo']).resolve();hashes.setdefault(str(foto),hashlib.sha256(foto.read_bytes()).hexdigest())
                entries.append({'id':id,'articulo_id':87,'pagina':f"L{r['lote_id']:04d}-P{r['numero_pagina']:02d}",
                    'esperado':{k:r[k] for k in CAMPOS_BASE},'esperado_adicional':{k:r[k] for k in ('nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia')},
                    'cambios':cambios,'revision':rev,'fuente':str(foto),'sha256_imagen':hashes[str(foto)]})
    assert len(hashes)==7 and calc==365 and papel==362,(calc,papel)
    assert diferencias==[{'id':5607,'local':-3,'acumulada':-3}],diferencias
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    return {'version':11,'criterio_sha256':digest(policy),'revisiones':entries,'sin_reasociaciones_ni_borrados':True,
        'autorizacion_adicional':'El usuario delegó las decisiones de interpretación en base a sus 23 criterios previos.',
        'observaciones_articulos':[{'articulo_id':87,'observado':True,'excluir_entrenamiento':False,
            'motivo':'Siete fotos y 167 filas cotejadas. Cierre reconstruido 365 frente a 362 escrito: diferencia -3 del papel en Taller Metodología, preservada. Salida infantil 10 y devoluciones 2/4 recuperadas de sus columnas. Fechas técnicas y atribución REF/ÁREA dudosa siguen identificadas.'}],
        'cotejo':{'fotografias':7,'movimientos':167,'cierres':{87:365},'cierres_documentales':{87:362},'discrepancias':diferencias},
        'limites':['Los saldos reconstruidos no certifican existencias físicas.','Las fechas técnicas no entrenan el modelo.','No se crean áreas, alias ni movimientos operativos.']}


if __name__=='__main__':
    path=DEST/'plan_continuacion_11.json'
    if path.exists():raise RuntimeError('Conservar el plan congelado; cambios posteriores requieren otro lote.')
    plan=generar();path.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'plan':str(path),'sha256':digest(json.loads(path.read_text(encoding='utf-8'))),'cotejo':plan['cotejo']},ensure_ascii=False))
