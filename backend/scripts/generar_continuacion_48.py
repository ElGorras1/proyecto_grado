"""Siete fotos completas: Maritza Wilde, Voces y Música tradicional vinilo."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND
from scripts.generar_continuacion_28 import recuperada

HOJAS=[
 (range(1269,1294),[-1,-1,-5,-3,1,1,2,-1,-1,-3,1,1,23,-1,-1,1,-1,2,-1,-3,3,-5,-1,5,-1],
  [None,9,4,1,2,3,5,4,3,0,1,2,25,24,23,24,23,25,24,21,24,19,19,24,23]),
 (range(1294,1310),[-5,-1,5,-2,2,-3,-2,-2,1,3,-1,-4,-1,2,-1,-2],[18,17,22,20,22,19,17,15,16,19,18,14,13,15,14,12]),
 (range(6271,6296),[197,-1,-2,-3,3,-5,-1,4,-10,-2,5,-3,-2,-2,-15,4,2,-2,-2,-2,-6,2,-2,-3,-5],
  [197,196,194,191,194,189,188,192,182,180,185,182,180,178,163,167,169,167,165,163,157,159,157,154,149]),
 (range(6296,6312),[-3,5,-4,-6,-1,-2,-2,-1,-4,-4,-2,2,1,-2,-2,-3],[146,151,147,141,140,138,136,135,131,127,125,127,128,126,124,121]),
 (range(7614,7640),[0,-1,-1,1,0,22,-1,-1,-1,1,-1,-5,-1,1,1,-2,-2,-2,-2,-1,-5,2,-2,-2,1,-3],
  [30,29,28,29,15,37,36,35,34,35,34,29,28,29,30,28,26,24,22,21,16,18,16,14,15,12]),
 (range(7640,7663),[3,-1,10,-5,3,1,-1,1,-1,-5,4,-3,-5,5,1,-1,-6,4,-2,-2,-5,-1,-6],
  [15,14,24,19,22,23,22,23,22,17,21,18,13,18,19,18,12,16,14,12,7,6,0]),
 (range(7663,7668),[-1,-4,-7,2,-2],[11,7,0,2,0]),
]

def generar():
    snapshot='backups/continuacion_hil_48_20261015/articulos_30_93_137_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDOC','CEDOCAL','CEDEAL','CSDOAL','CDOAL')}
    for id,fields in {
        1269:{'detalle':'Edgar Brandia'},1282:{'detalle':'LETRAS PACEÑAS'},1284:{'detalle':'LETRAS PACEÑAS'},1287:{'fecha_movimiento':'2013-05-08'},
        1305:{'detalle':'CRITICA AMATEUR'},1309:{'detalle':'VENTAS CID'},
        6273:{'detalle':'VENTA-CEDOAL'},6274:{'detalle':'LARGO NOCHE MUSEOS'},6275:{'detalle':'LARGO NOCHE MUSEOS'},6283:{'detalle':'VENTAS-CEDOAL'},6290:{'detalle':'LARGO NOCHE DE MUSEOS'},
        6293:{'referencia':'CONSIG'},6294:{'referencia':'CBA / CONSIG','area':None},
        7618:{'detalle':'Cifra 15 sin leyenda ni cantidades','estado':'NOTA_DOCUMENTAL'},7625:{'area':'CEDOAL'},7648:{'detalle':'LLALLAGUA'},7665:{'detalle':'ADM'},7667:{'detalle':'FIL'},
    }.items():cambios.setdefault(id,{}).update(fields)
    for id in range(1269,1294):cambios.setdefault(id,{})['orden_fila']=rows[id]['orden_fila']+1
    tecnicas={
        1270:('2007-01-17','HIPOTESIS',None,'Vice de Cultura tiene FECHA vacía; consulta técnica del antecedente.'),
        **{id:('2007-10-17','HIPOTESIS',None,'Devolución sin fecha propia; consulta técnica del antecedente. Nota lateral 19-12-07 conservada sin asignación automática.') for id in (1273,1274,1275)},
        1288:('2013-06-07','FOTO','2013-06-07','La fotografía escribe 7-6-13, no 7-5-13.'),
        1289:('2013-06-07','SECUENCIA_AJUSTADA','2013-05-14','14-5-13 está después del 7-6-13. Se conserva literal y consulta técnica del antecedente.'),
        1290:('2013-06-07','SECUENCIA_AJUSTADA','2013-05-27','27-5-13 está después del 7-6-13. Literal y consulta técnica conservadas.'),
        1291:('2013-06-07','SECUENCIA_AJUSTADA','2013-06-03','3-6-13 está después del 7-6-13. Literal y consulta técnica conservadas, sin cambiar la salida 1 para cuadrar.'),
        6302:('2017-04-20','HIPOTESIS',None,'FIL carece de fecha propia. Consulta técnica del antecedente, sin confirmar 1 de junio.'),
        7614:('2006-06-26','HIPOTESIS',None,'La base escribe 26-6 sin año; gestión 2006 únicamente técnica por contexto previo a junio de 2007.'),
        7615:('2006-09-21','HIPOTESIS',None,'21-9 sin año; gestión 2006 solo técnica.'),
        7616:('2006-10-06','HIPOTESIS',None,'6-10 sin año; gestión 2006 solo técnica.'),
        7617:('2006-11-29','HIPOTESIS',None,'29-11 sin año; gestión 2006 solo técnica.'),
        **{id:('2006-11-29','HIPOTESIS',None,'Fila sin fecha propia; consulta técnica del contexto parcial anterior, sin certificar año ni fecha por semejanza con otra hoja.') for id in (7618,7619,7620,7621)},
        7625:('2007-10-17','SECUENCIA_AJUSTADA','2007-08-01','1-08-07 después de 17-10-07. Se conserva literal y consulta técnica del antecedente.'),
        **{id:('2007-11-15','HIPOTESIS',None,'Devolución sin fecha propia; consulta técnica del antecedente.') for id in (7627,7628)},
        7662:('2017-05-05','HIPOTESIS',None,'FIL tiene FECHA vacía; consulta técnica del antecedente. No se inventa fecha ni ingreso para conciliar la hoja siguiente.'),
    }
    extras={
        1269:{'criterios':['T08','T16'],'motivo':'SALDO está vacío tras salida 1; cálculo 10 solo hipotético. Apellido conservado como lectura literal Brandia, sin identificarlo con otra persona por semejanza.'},
        **{id:{'criterios':['T16'],'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'Código escrito en ÁREA se conserva junto a ESIP sin crear área numérica ni resolver su significado.'} for id in (1274,1277,1278)},
        1275:{'criterios':['T16'],'revision':{'anotacion_margen_fecha':'19-12-07 junto a devolución; no se asigna automáticamente a la fecha vacía.'}},
        1279:{'criterios':['T16'],'motivo':'El texto personal de la devolución se conserva sin normalizarlo a otra identidad por parecido.'},
        1287:{'motivo':'El día visible es 8-5-13, no 3-5-13.'},
        1291:{'criterios':['T05'],'motivo':'PATIPIÑA tiene SALIDA 1 legible desde saldo 19 y vuelve a escribir 19, frente a cálculo independiente 18. Diferencia +1 del papel persistente; no se borra la donación ni se inventa ingreso. Cierre escrito 12 frente a cálculo 11.'},
        6292:{'criterios':['T14'],'motivo':'Saldo anterior tachado y lectura corregida 159 visible; la corrección de celda no anula la devolución 2.'},
        6294:{'criterios':['T23'],'motivo':'CONSIG escrito en ÁREA describe consignación; CBA queda como referencia literal. Se conservan posiciones documentales sin crear área CONSIG.', 'revision':{'columnas_documentales':{'referencia':'CBA','area':'CONSIG'}}},
        6306:{'criterios':['T16'],'motivo':'Se conserva la lectura literal CIO sin convertirla automáticamente en CID ni crear alias por frecuencia.'},
        **{id:{'revision':{'fecha_documental_texto':texto}} for id,texto in ((7614,'26-6, sin año.'),(7615,'21-9, sin año.'),(7616,'6-10, sin año.'),(7617,'29-11, sin año.'))},
        7614:{'criterios':['T22'],'motivo':'Saldo inventario 30 es base documental sin cantidad de ingreso ni recuento actual.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL','fecha_documental_texto':'26-6, sin año.'}},
        7618:{'criterios':['T16'],'motivo':'Cifra aislada 15 sin fecha, detalle ni cantidades, después de saldo 29 y antes de ingreso 22 con saldo 37. No tiene leyenda de recuento y no acredita salida 14. Se conserva como nota sin efecto y no se cambia ingreso 22 para cuadrar.', 'revision':{'tipo_fila':'NOTA_DOCUMENTAL','detalle_documental':None,'origen_cantidades':'HIPOTESIS'}},
        7625:{'criterios':['T18'],'motivo':'Comillas inequívocas en ÁREA repiten CEDOAL; no se crea área de comillas.'},
        7631:{'criterios':['T16'],'motivo':'Dos salidas 2 del mismo día ocupan renglones distintos y saldos 24/22; no se deduplican por parecido.'},
        7662:{'criterios':['T02'],'motivo':'6 está en SALIDAS y escribe saldo cero. No se convierte en ingreso 6 para hacer coincidir la hoja siguiente.'},
        7663:{'criterios':['T16'],'motivo':'Después del cierre escrito cero de la foto anterior, salida 1 escribe saldo 11. Discontinuidad local +12 conservada. No se inventa recepción 12 ni se invierte la salida 6 anterior. Cierre escrito cero frente a cálculo condicional 2, tras discontinuidad anterior -14.'},
    }
    plan=construir(version=48,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={30:{'primera_fila':1269,'saldo_base':11,'origen_saldo_base':'FOTO','motivo_base':'Saldo inicial escrito 11 en fila omitida que se recupera sin ingreso ficticio.'},
            93:{'primera_fila':6271,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso 197 y saldo 197; base anterior cero inferida, no recuento acreditado.'},
            137:{'primera_fila':7614,'saldo_base':30,'origen_saldo_base':'FOTO','motivo_base':'Saldo inventario 30 escrito con cantidades vacías, sin ingreso inventado.'}},
        observaciones=[
            {'articulo_id':30,'observado':True,'excluir_entrenamiento':True,'motivo':'Dos fotos y 41 filas OCR cotejadas, más base inicial escrita 11 omitida recuperada sin ingreso ficticio. PATIPIÑA tiene salida 1 y saldo 19 repetido desde 19: diferencia +1 persistente; cierre escrito 12 frente a cálculo 11, apertura bloqueada y artículo excluido. Códigos en área y nota lateral conservados, primera salida sin saldo escrito, fechas vacías y retrocesos identificados.'},
            {'articulo_id':93,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 41 filas cotejadas. CEDOAL y textos de Museos recuperados del OCR, CONSIG no se trata como área institucional. Saldo corregido 159 visible se conserva sin anular devolución 2. FIL sin fecha y CIO/CID sin normalizar por frecuencia permanecen identificados; cierre 121 coincide.'},
            {'articulo_id':137,'observado':True,'excluir_entrenamiento':True,'motivo':'Tres fotos completas y 54 filas cotejadas. Base escrita 30 sin ingreso ficticio. Cifra 15 sin leyenda queda como nota sin efecto después de 29, discontinuidad -14 no compensada por operación inventada. FIL salida 6 legible cierra en cero, pero la siguiente foto empieza salida 1/saldo 11, discontinuidad local +12. No se invierte 6 ni se añade ingreso 12. Cierre escrito cero frente a cálculo condicional 2, apertura bloqueada y artículo excluido. Fechas parciales y vacías conservadas.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={30:11,93:121,137:2},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':1291,'local':1,'acumulada':1},{'id':7618,'local':-14,'acumulada':-14},{'id':7663,'local':12,'acumulada':-2}],plan['cotejo']
    for e in plan['revisiones']:
        if e['id']==1269:
            for k in ('saldo_base','origen_saldo_base','motivo_base'):e['revision'].pop(k,None)
        if e['articulo_id']==137 and e['id']>7618:e['revision']['origen_saldo']='HIPOTESIS'
        if e['id']==7618:e['cambios']['saldo_registrado']=15;e['revision'].update(saldo_documental=15,origen_saldo='FOTO',usar_saldo_esperado=False)
        if e['id'] in (1309,7667):e['cambios']['saldo_registrado']=12 if e['id']==1309 else 0;e['revision'].update(usar_saldo_esperado=False,origen_saldo='FOTO')
    nueva=recuperada(rows,1269,1,clave='art30-base11-inicial-antes1269-v1',detalle='Saldo inicial 11 sin fecha ni detalle documental',fecha='2007-01-17',saldo=11,tipo='BASE_DOCUMENTAL',
        motivo='La primera fila de la foto tiene únicamente SALDO 11, con fecha, detalle y cantidades vacíos. Se recupera base documental omitida, sin ingreso ficticio ni recuento acreditado. Fecha posterior usada solo como consulta técnica.')
    nueva['campos'].update(estado='ACTIVO',fecha_estado='ESTIMADA_HIL')
    nueva['campos']['datos_originales'].update(detalle=None,saldo_registrado=11)
    nueva['revision'].update(criterios=['T09','T22','T23'],tipo_fila='BASE_DOCUMENTAL',detalle_documental=None,saldo_documental=11,origen_saldo='FOTO',origen_cantidades='FOTO',saldo_base=11,origen_saldo_base='FOTO',motivo_base='Base inicial 11 escrita, sin cantidad de ingreso.')
    plan['recuperaciones']=[nueva]
    plan['cotejo'].update(movimientos=137,cierres={30:12,93:121,137:0},cierres_calculados={30:11,93:121,137:2},pendientes_documentales={1309:['saldo'],7667:['saldo']},
        limites_cierre={30:'Cierre escrito 12 frente a cálculo 11: salida 1 con saldo repetido dejó diferencia +1 persistente. Apertura bloqueada y artículo excluido del entrenamiento.',
            137:'Cierre escrito 0 frente a cálculo condicional 2. Cifra 15 sin leyenda después de 29 y discontinuidad +12 entre hojas permanecen sin operación compensatoria. Apertura bloqueada y artículo excluido del entrenamiento.'})
    return plan

if __name__=='__main__':congelar(generar())
