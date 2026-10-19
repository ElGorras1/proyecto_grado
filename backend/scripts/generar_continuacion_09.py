"""Cotejo de Lenguajes Gráficos 1, Música de los Guaraní y Donde todo es posible."""
import hashlib
import json
from pathlib import Path
from app.db.session import SessionLocal
from app.services.clasificador_nodos import clasificar_movimiento, _resolver_area_con_catalogo
from scripts.generar_plan_revision_hil import CAMPOS_BASE,DEST,digest

BACKEND=Path(__file__).resolve().parents[1]
ANTES=BACKEND/'backups/continuacion_hil_09_20261014'
HOJAS=[
 (6347,[-28,26,-5,9,-1,-21,-1,-1,-3,-11,-30,30,-10,-437,20,-20,20,-2,-1,-1,-2,-1,-1,-1,-1,-1],
  [458,484,479,488,487,466,465,464,461,450,420,450,440,3,23,3,23,21,20,19,17,16,15,14,13,12]),
 (6373,[-1,-5,-1,8,-1,44,1,50,44,-3,-2,2,-10,-1,-30,264,0,0,0,0,0,0,-4,-10,-10,-10],
  [11,6,5,13,12,56,57,107,151,148,146,148,138,137,107,371,370,369,354,353,None,371,367,357,347,337]),
 (6399,[-7,15,10,-4,1,-4,-15,-1,-10,-10,-28,0,0,0,-12,-2,-2,-1,-4,7,8,1,-2,-4,-2,-1],
  [330,345,355,351,352,348,333,332,322,312,284,None,None,None,272,270,268,267,263,270,278,279,277,273,271,270]),
 (6425,[-1,5,-1,-1,-1,-1,-2,-1,-1,-1,-5,2,-2,-1,-1,-4,-1,-5,0,-1,-1,-1,-1,-10,-4,-2],
  [269,274,273,272,271,270,268,267,266,265,260,262,260,259,258,254,253,248,None,247,246,245,244,234,230,228]),
 (6451,[-1,-1,-1,-4,-1,-1,-5,-2,1,-1,-2,-1,-2,1,-1,14,-2,7,4,-2,-1,-2,-1,-2,-1,-1],
  [227,226,225,221,220,219,214,212,213,212,210,209,207,208,207,221,219,226,230,228,227,225,224,222,221,220]),
 (6477,[1,-2,-1,-1,-1,-1,-1,-6],[221,219,218,217,216,215,214,208]),
 (7501,[0,-1,-3,1,-1,14,1,-1,-1,-1,16,-1,10,-1,-2,-3,3,5,-3,-5,-1,-10,-1,3,-2],
  [40,39,36,37,36,50,51,50,None,48,64,63,73,None,70,67,70,75,72,67,66,56,55,58,56]),
 (6312,[400,-6,-100,-2,458,-8,-5,-4,-2,3,-1,-3,-5,-2,-2,-2,-7,-3,-3,-3,-3,-2,-2,-3,-2,-2],
  [400,394,294,292,750,742,737,730,728,731,730,727,722,720,718,716,709,706,703,700,697,695,693,690,688,686]),
 (6338,[-10,-2,-5,2,-3,-5,-1,3,-2],[676,674,669,671,668,663,662,665,663]),
]
DESGLOSE={6410:5,6411:1,6412:22}
NOTAS={*DESGLOSE,6443,6393,6394}
ANULADOS={6389,6390,6391,6392}
HIP_CANT={6425:('salidas',1),6436:('ingresos',2),7506:('ingresos',14)}
FECHAS_FOTO={7516:'2007-06-15',7518:'2007-08-29'}
TECNICAS={
 6359:('2016-11-30','SECUENCIA_AJUSTADA','2016-11-18','18-11-16 después de 30-11-16: consulta técnica con fecha literal conservada.'),
 6374:('2016-12-22','SECUENCIA_AJUSTADA','2016-12-21','21-12-16 después de 22-12-16: ajuste de consulta sin confirmar día del hecho.'),
 6375:('2016-12-22','SECUENCIA_AJUSTADA','2016-12-21','Fecha escrita anterior al antecedente: se preserva y se ajusta consulta.'),
 6376:('2016-12-22','SECUENCIA_AJUSTADA','2016-12-08','La foto dice 8-12-16, no 18. Es anterior al tramo; se usa fecha técnica 22-12-16.'),
 6413:('2017-04-21','SECUENCIA_AJUSTADA','2017-04-04','04-04-17 después de 21-04-17: fecha técnica del antecedente.'),
 6414:('2017-04-21','SECUENCIA_AJUSTADA','2017-02-17','17-02-17 escrito después de abril: fecha de consulta ajustada.'),
 6415:('2017-04-21','HIPOTESIS',None,'Fecha en blanco en La Rayuela; fecha técnica del antecedente.'),
 6416:('2017-04-21','SECUENCIA_AJUSTADA','2017-03-23','23-03-17 después de abril: fecha técnica del antecedente.'),
 6417:('2017-04-21','SECUENCIA_AJUSTADA','2017-03-24','24-03-17 después de abril: fecha técnica del antecedente.'),
 6421:('2017-04-25','SECUENCIA_AJUSTADA','2017-03-23','23-03-17 después de 25-04-17: fecha de consulta ajustada.'),
 6422:('2017-04-25','HIPOTESIS',None,'Lectura 24-3/5-17; no se confirma el mes. Se usa técnicamente la fecha previa de abril.'),
 6423:('2017-04-25','SECUENCIA_AJUSTADA','2017-04-20','20-04-17 después de 25-04-17: consulta ajustada.'),
 6477:('2022-09-07','HIPOTESIS',None,'La devolución inicial de la última foto no tiene fecha; se conserva como hipótesis la del cierre anterior, sin confirmar el día.'),
 7501:('2006-06-26','HIPOTESIS',None,'Solo consta 26-6; año técnico 2006 anterior al primer año completo legible de enero de 2007.'),
 7502:('2006-09-23','HIPOTESIS',None,'Solo consta 23-9, sin año; 2006 técnico por contexto, no confirmado.'),
 7503:('2006-10-06','HIPOTESIS',None,'6-10 sin año; se usa técnicamente 2006.'),
 7504:('2006-11-29','HIPOTESIS',None,'29-11 sin año; se usa técnicamente 2006.'),
 7505:('2006-11-29','HIPOTESIS',None,'14-09 sin año, después de noviembre; se conserva la parcial y se usa técnicamente la fecha previa.'),
 7506:('2007-01-15','HIPOTESIS',None,'15-01 sin año, a lápiz; 2007 técnico por la fila siguiente de 17-01-07.'),
 7507:('2007-01-15','HIPOTESIS',None,'15-01 sin año; se utiliza técnicamente 2007, sin confirmar el año escrito.'),
 **{id:('2007-01-17','HIPOTESIS',None,'Fecha en blanco; para consulta se utiliza la del antecedente, sin acreditar el día.') for id in (7509,7510,7511)},
 **{id:('2007-03-29','HIPOTESIS',None,'Fecha en blanco; fecha técnica del ingreso anterior de marzo.') for id in (7514,7515)},
 7522:('2007-11-13','SECUENCIA_AJUSTADA','2007-08-01','01-08-07 después de noviembre: fecha técnica del antecedente, conservando la escrita.'),
 7524:('2007-11-15','SECUENCIA_AJUSTADA','2007-11-05','05-11-07 después de 15-11-07: consulta ajustada, lectura literal conservada.'),
 6321:('2022-09-18','HIPOTESIS',None,'Fecha en blanco de la devolución: fecha técnica del antecedente, no día confirmado.'),
}
PARES=[(6438,6439),(6451,6452,6453),(6464,6465)]


def generar():
    rows={r['id']:r for aid in (95,133,94) for r in json.loads((ANTES/f'articulo_{aid}_antes.json').read_text(encoding='utf-8'))}
    assert len(rows)==198
    literales={id:r['fecha_movimiento'] for id,r in rows.items()};literales.update(FECHAS_FOTO)
    fechas=dict(TECNICAS)
    for grupo in PARES:
        for id,nueva in zip(grupo,sorted(literales[id] for id in grupo)):
            if nueva!=literales[id]:fechas[id]=(nueva,'SECUENCIA_AJUSTADA',literales[id],'Fechas permutadas para consulta según T10/T11 tras cotejar cantidades; la fecha documental se conserva.')
    calc={95:486,133:40,94:0};paper=dict(calc);revs=[];hashes={};discrepancias=[]
    with SessionLocal() as db:
        for start,qs,saldos in HOJAS:
            assert len(qs)==len(saldos)
            for off,(q,escrito) in enumerate(zip(qs,saldos)):
                id=start+off;r=rows[id];aid=r['articulo_id'];calc[aid]+=q;saldo=calc[aid]
                cambios={'ingresos':q if q>0 else None,'salidas':-q if q<0 else None,'saldo_registrado':saldo}
                rev={'tipo_fila':'MOVIMIENTO','saldo_documental':escrito,'origen_saldo':'HIPOTESIS' if escrito is None else ('FOTO' if escrito==saldo else 'RECONSTRUIDO'),
                    'origen_fecha':'FOTO','fecha_documental':literales[id],'usar_saldo_esperado':True,'reconstruir_cadena':True,
                    'cotejo_pagina_completa':True,'motivo':'Foto completa y filas vecinas cotejadas. Se conservan fuente, datos originales y diferencias con la reconstrucción.'}
                tipos={'T01'};hallazgos=['HOJA_COMPLETA_COTEJADA']
                if id in ANULADOS or id in NOTAS:
                    cambios={}
                    if id in ANULADOS:
                        rev.update(tipo_fila='ANULADO',origen_saldo='NO_APLICA',usar_saldo_esperado=False,
                            motivo='Se conserva la anulación expresa de los cuatro registros, indicada por la nota de la hoja. No se reactivan sus salidas ni se borran sus valores.')
                        tipos.add('T14')
                    else:
                        tipo='DESGLOSE' if id in DESGLOSE else ('CONTINUACION' if id==6443 else 'NOTA')
                        cambios={'estado':'NOTA_DOCUMENTAL'}
                        rev.update(tipo_fila=tipo,origen_saldo='NO_APLICA',usar_saldo_esperado=False)
                        tipos.update(['T13','T16'])
                        if id in DESGLOSE:
                            rev.update(movimiento_total_id=6409,origen_interpretacion='DECISION_ASISTIDA_SEGUN_CRITERIOS_DEL_TITULAR',
                                origen_fecha='HIPOTESIS',fecha_documental=None,motivo_fecha='Sin fecha propia; contexto del total de presentación, sin acreditar una fecha independiente.',
                                motivo='5 Lewi Libros + 1 UGRM + 22 UP Santa Cruz = 28 de la presentación anterior. Sin fecha ni saldo propio: desglose del mismo total, no tres salidas adicionales. Se conserva la fila con su cantidad documental, sin volver a reducir el saldo.')
                        elif id==6443:
                            cambios.update(ingresos=None,salidas=None,fecha_movimiento='2017-11-16')
                            rev.update(movimiento_total_id=6442,origen_fecha='HIPOTESIS',fecha_documental=None,motivo_fecha='Renglón de continuación sin fecha; se vincula técnicamente al movimiento anterior.',
                                motivo='La flecha y Wojciechowski continúan la lista de destinatarios anterior. No hay fecha, cantidad ni saldo en este renglón. Se conserva como continuación, sin la salida 1 inventada por el OCR.')
                        else:rev['motivo']='Se conserva el renglón de nota que elimina las cuatro salidas anteriores; no es otra operación.'
                    hallazgos.append('SIN_EFECTO_EN_CADENA_VIGENTE')
                else:
                    if escrito is None:
                        tipos.add('T08');hallazgos.append('SALDO_EN_BLANCO_RECONSTRUIDO')
                        rev['motivo']+=' Saldo escrito en blanco: valor de consulta hipotético por continuidad.'
                    else:
                        delta=escrito-(paper[aid]+q)
                        if delta:
                            tipos.add('T05');hallazgos.append('DESCUADRE_DEL_PAPEL_CONSERVADO')
                            rev['diferencia_local_papel']=delta;discrepancias.append({'id':id,'local':delta,'acumulada':escrito-saldo})
                        paper[aid]=escrito
                    if escrito is None:paper[aid]+=q
                if id==6347:
                    rev.update(saldo_base=486,origen_saldo_base='HIPOTESIS',motivo_base='Base anterior no visible: 458 + salida 28 = 486, solo como hipótesis de consulta. No se inventa un ingreso de 486.')
                    tipos.add('T22')
                if id==7501:
                    cambios.update(area=None);rev.update(tipo_fila='BASE_DOCUMENTAL',saldo_base=40,origen_saldo_base='DOCUMENTO')
                    tipos.update(['T15','T22','T23']);rev['motivo']+=' Saldo según inventario 40 sin ingreso. Inventario forma parte del detalle, no es un área.'
                if id==6312:rev.update(saldo_base=0,origen_saldo_base='HIPOTESIS',motivo_base='Base cero inferida de primer ingreso y saldo iguales; no acredita un conteo previo.')
                if id in HIP_CANT:
                    campo,numero=HIP_CANT[id];tipos.add('T19')
                    rev.update(origen_cantidades='HIPOTESIS',cantidades_documentales={'ingresos':None,'salidas':None})
                    rev['motivo']+=f' La cantidad está en blanco: {campo} {numero} se infiere condicionalmente de los saldos escritos. Hipótesis excluida del entrenamiento, no lectura confirmada.'
                if id in (6449,6450,6314):tipos.add('T02')
                if id==6386:
                    tipos.add('T02');rev['motivo']+=' El 1 de URNA está en SALIDAS, no en INGRESOS.'
                if id==7507:
                    tipos.add('T07');rev.update(origen_cantidades='INTERPRETACION_HUMANA',marcas_documentales={'salidas':1})
                    rev['motivo']+=' La fuente pone 1 en SALIDAS pero aumenta 50→51: devolución interpretada como ingreso 1, con error de columna conservado.'
                if id==7515:
                    cambios['detalle']='Donacion Cancilleria';tipos.add('T18');rev['motivo']+=' La comilla repite Donación; Cancillería no significa cancelación del movimiento.'
                if id==6442:
                    cambios['detalle']=r['detalle']+', WOJCIECHOWSKI';tipos.add('T16')
                    rev['motivo']+=' La lista continúa en el renglón siguiente, vinculado como nota sin cantidad propia.'
                if id in (6321,6341,6345):
                    cambios.update(area=None);tipos.add('T23');rev['motivo']+=' La cifra está en INGRESOS; no es un nombre de área.'
                if id in FECHAS_FOTO:cambios['fecha_movimiento']=FECHAS_FOTO[id]
                if id in fechas:
                    nueva,origen,literal,motivo=fechas[id];cambios['fecha_movimiento']=nueva
                    rev.update(origen_fecha=origen,fecha_documental=literal,motivo_fecha=motivo)
                    tipos.add('T09' if origen=='HIPOTESIS' else 'T11')
                if id==6422:rev['lectura_fecha_parcial']='24-3/5-17'
                if id==7521:
                    tipos.add('T16');rev['anotacion_margen']='55 al margen, que coincide con el cierre después de las dos salidas siguientes. Se conserva sin adelantar ese saldo a esta fila.'
                if id==6425:rev['anotacion_cabecera']='Saldo 61 cajas en nota sin fecha ni equivalencia de unidades; no se utiliza como movimiento ni recuento.'
                if id==6319:rev['motivo']+=' El papel dice salida 4 y saldo 730 después de 737. El esperado es 733: diferencia 3 conservada y propagada, sin cambiar la cantidad para cuadrarla.'
                if id not in NOTAS|ANULADOS and any(cambios.get(k,r[k])!=r[k] for k in ('ingresos','salidas','area','referencia','detalle')):
                    clas=clasificar_movimiento(cambios.get('detalle',r['detalle']),cambios.get('referencia',r['referencia']),cambios.get('area',r['area']),cambios.get('ingresos',r['ingresos']),cambios.get('salidas',r['salidas']),db)
                    d={k:getattr(clas,k) for k in ('nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia')}
                    if q>0 and d['nodo_grafo'].startswith('Salida:'):
                        area=cambios.get('area',r['area']);n,e,p=(_resolver_area_con_catalogo(area,db) if area else ('Origen no especificado','SIN_AREA_REGISTRADA',False))
                        d.update(nodo_grafo=n,area_estado=e,requiere_auditoria_nodo=p)
                    cambios.update(d)
                rev['criterios']=sorted(tipos);rev['hallazgos']=hallazgos
                foto=(BACKEND/r['ruta_imagen_respaldo']).resolve();hashes.setdefault(str(foto),hashlib.sha256(foto.read_bytes()).hexdigest())
                revs.append({'id':id,'articulo_id':aid,'pagina':f"L{r['lote_id']:04d}-P{r['numero_pagina']:02d}",
                    'esperado':{k:r[k] for k in CAMPOS_BASE},'esperado_adicional':{k:r[k] for k in ('nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia')},
                    'cambios':cambios,'revision':rev,'fuente':str(foto),'sha256_imagen':hashes[str(foto)]})
    assert calc=={95:208,133:56,94:666},calc
    assert len(hashes)==9
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    return {'version':9,'criterio_sha256':digest(policy),'revisiones':revs,
        'autorizacion_adicional':'El usuario indicó tomar las decisiones con sus criterios anteriores; el desglose se interpreta en su contexto y queda auditado.',
        'observaciones_articulos':[{'articulo_id':aid,'observado':True,'excluir_entrenamiento':False,'motivo':motivo} for aid,motivo in [
            (95,'Seis fotos cotejadas. Cierre 208; base anterior 486 inferida, cantidades ausentes marcadas y notas de desglose/continuación preservadas sin efecto. No se cambia el caso previo de los cuatro ingresos confirmado por el titular.'),
            (133,'Hoja cotejada. Cierre 56. Ingreso 14 inferido de saldos con cantidad ausente, devolución 1 interpretada por dirección del saldo y fechas parciales conservadas. Hipótesis excluidas de entrenamiento.'),
            (94,'Dos fotos cotejadas. Cierre reconstruido 666 frente a 663 escrito: error 3 del papel conservado, sin inventar una salida adicional.')]],
        'sin_reasociaciones_ni_borrados':True,
        'cotejo':{'fotografias':9,'movimientos':198,'cierres':calc,'cierres_documentales':{95:208,133:56,94:663},'discrepancias':discrepancias},
        'limites':['Las cantidades hipotéticas no entrenan ni generan alertas como hechos confirmados.','Las notas y las anulaciones siguen guardadas; solo cambia su efecto vigente.','No se normalizan áreas por similitud.']}


if __name__=='__main__':
    path=DEST/'plan_continuacion_09.json'
    if path.exists():raise RuntimeError('Conservar el plan congelado; cambios posteriores requieren otro lote.')
    plan=generar();path.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    congelado=json.loads(path.read_text(encoding='utf-8'))
    print(json.dumps({'plan':str(path),'sha256':digest(congelado),'cotejo':plan['cotejo']},ensure_ascii=False))
