"""Las estaciones y Boletín 11: fotos completas, nota pendiente y tachaduras."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(4602,4628),[50,-35,-15,449,-1,-5,8,-1,-10,-1,-3,-5,-1,-3,-12,-1,-225,-1,1,1,-1,-1,-1,-2,2,-10],
  [50,15,None,449,448,443,451,450,440,439,436,431,430,427,415,414,189,188,189,190,189,188,187,185,187,177]),
 (range(4628,4654),[8,-3,-3,1,-5,-2,-1,-10,-10,-3,10,-2,-3,-3,-10,-5,-10,10,-5,-1,1,-2,-2,1,1,-1],
  [185,182,179,180,175,173,172,162,152,149,159,157,154,151,141,136,126,136,131,130,131,129,127,128,129,128]),
 (range(4654,4680),[-2,2,-2,-1,-1,1,-1,-1,1,1,-10,-5,12,-3,-5,8,-5,-1,-1,-1,5,-1,-1,-10,-1,7],
  [126,128,126,125,124,125,124,123,124,125,115,110,122,119,114,122,117,116,115,114,119,118,117,107,106,113]),
 (range(4680,4705),[-2,-3,-5,-5,-2,-2,5,-20,-20,-10,-2,-20,-2,-7,-2,-3,-2,-5,-1,5,-1,4,-1,-1,-2],
  [111,108,103,98,96,94,99,79,59,49,47,27,25,18,16,13,11,6,5,10,9,13,12,11,9]),
 (range(4705,4711),[-2,-1,-3,-1,-1,-2],[7,6,3,2,1,None]),
 # 8262 está tachada en fecha, detalle, área, cantidad y saldo. Se conserva
 # después en ANULADO_DOCUMENTO; el cero de esta matriz solo omite su efecto.
 (range(8253,8278),[20,-3,-3,3,-2,-2,-1,-1,-1,0,-8,-1,20,-3,-10,-2,-4,8,-1,-1,-2,1,-2,2,-5],
  [20,17,14,17,15,13,12,11,10,None,2,1,21,18,8,6,2,10,9,8,6,7,5,7,2]),
 (range(8278,8294),[15,3,-3,-3,2,10,-5,-9,13,1,-1,-10,6,-6,-4,-2],[17,20,17,14,16,26,21,12,25,26,25,15,21,15,11,9]),
]


def generar():
    snapshot='backups/continuacion_hil_26_20261015/articulos_80_169_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    for id,r in rows.items():
        if r['area'] in ('CEDOOL','CDOAL','CEDOCAL','CEDOC','Cedoal','CDOOL','CECOL','CSDOOL','CSDOAL'):
            cambios[id]={'area':'CEDOAL'};extras[id]={'motivo':'La celda se lee CEDOAL en esta foto; no se crean áreas ni alias.'}
        if r['articulo_id']==169 and r['numero_pagina']==1 and id>=8268:
            cambios.setdefault(id,{})['orden_fila']=r['orden_fila']+1
    for id,fields in {
        4609:{'detalle':'DE SARTIGES'},4618:{'detalle':'CHUYHAMPI'},4672:{'detalle':'CEDOAL'},4675:{'detalle':'INAUG. YOLANDA'},
        4685:{'detalle':'VENTAS - CEDOAL'},4694:{'detalle':'VENTAS - CEDOAL'},4698:{'detalle':'CUEVA CUENTACUENTOS','referencia':'OBS.'},
        4704:{'detalle':'LA PAZ LEE'},4709:{'detalle':'LA RAYUELA'},
        8260:{'detalle':'D. PRO EDUCA EL ALTO'},8265:{'referencia':'CBBA','area':None},8271:{'area':'GALERIA'},
        8275:{'detalle':'LLALLAGUA'},8280:{'detalle':'VENTAS CEDOAL'},8288:{'detalle':'VENTA CEDOAL'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        4604:('2010-08-26','SECUENCIA_AJUSTADA','2010-08-25','25-08 después del 26-08: consulta técnica del antecedente y fecha literal conservada.'),
        4608:('2010-10-21','SECUENCIA_AJUSTADA','2010-09-03','03-09 después del 21-10. Se conserva literal y se usa consulta técnica del antecedente.'),
        4611:('2010-11-22','SECUENCIA_AJUSTADA','2010-11-10','10-11 después del 22-11. Consulta técnica sin alterar la fecha documental.'),
        4627:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','La foto dice 1-08-11 después del 02-08-11, no 11-08. Se conserva literal y consulta técnica del antecedente.'),
        **{id:('2012-08-21','SECUENCIA_AJUSTADA',fecha,'Fecha de julio/agosto escrita después del 21-08. Consulta técnica del antecedente y literal conservada.') for id,fecha in [(4643,'2012-07-24'),(4644,'2012-08-05'),(4645,'2012-08-14')]},
        4707:('2017-07-06','HIPOTESIS',None,'FIL tiene fecha en blanco; el antecedente 06-07-17 se usa solo para consulta.'),
        4709:('2017-10-05','SECUENCIA_AJUSTADA','2017-09-27','La foto escribe 27-9-17 después del 05-10-17. Se conserva literal y consulta técnica del antecedente.'),
        8274:('2011-04-28','SECUENCIA_AJUSTADA','2011-04-18','18-04-11 está escrito después del 28-04-11. Se conserva abril literal, sin convertirlo automáticamente en mayo.'),
        8277:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después del 02-08-11. Consulta técnica y literal conservadas.'),
        8284:('2012-07-30','SECUENCIA_AJUSTADA','2012-07-24','24-07-12 aparece después del ingreso 30-07-12; consulta técnica del antecedente.'),
        8293:('2016-09-14','HIPOTESIS',None,'Día 14/19 de septiembre de 2016 no inequívoco en la foto. Se mantiene el 14 solo como consulta hipotética, conservando la lectura parcial.'),
    }
    extras.update({
        4604:{'motivo':'El saldo de la foto es un guion, no un cero escrito. La resta 15 - 15 produce cero de consulta y se mantiene la distinción.',
            'revision':{'lectura_saldo_parcial':'Guion, sin cifra numérica.'}},
        4618:{'criterios':['T02'],'motivo':'La foto escribe salida 225, no ingreso: 414 - 225 = 189. Se conserva la cantidad legible y su saldo repasado.',
            'revision':{'marcas_documentales':{'saldo':'Cifra anterior tachada y lectura final 189.'}}},
        4699:{'criterios':['T14'],'motivo':'La devolución escribe ingreso 5 y una marca tachada en SALIDAS; no se añade un segundo descuento.',
            'revision':{'marcas_documentales':{'salidas':'Marca tachada sin cantidad adicional legible.'}}},
        4710:{'criterios':['T23'],'motivo':'La nota adherida dice FALTA SALIDA, FIL 2019, 12-8-19, (2 libros), con INGRESAR tachado. Corresponde a la fila FIL-2019 ya existente, cuyas celdas de cantidades y saldo están vacías. Se recupera SALIDA 2 desde esa nota, sin duplicar operación. Desde el saldo previo 1 produce -1: se conserva la insuficiencia documental, sin inventar un ingreso para evitarla.',
            'revision':{'anotacion_documental':'FALTA SALIDA; INGRESAR tachado; FIL 2019; 12-8-19; (2 libros).',
                'origen_cantidad':'NOTA_EN_MISMA_FOTOGRAFIA','saldo_documental':None,'origen_saldo':'HIPOTESIS',
                'hallazgos':['HOJA_COMPLETA_COTEJADA','CANTIDAD_RECUPERADA_DE_NOTA','CADENA_NEGATIVA_PENDIENTE_CONCILIACION']}},
        8262:{'criterios':['T14'],'motivo':'Jessica Freud está tachada en fecha, detalle, CAP, salida 4 y saldo 6. Es una anulación expresa de la fila completa; se conserva sin efecto. La siguiente salida 8 deja 2 desde 10, comprobando el contexto sin usar el saldo como única evidencia de anulación.'},
        8265:{'criterios':['T23'],'motivo':'CBBA está en REF y ÁREA está vacía. Se recupera la columna sin crear un área nueva.'},
        8285:{'criterios':['T14'],'motivo':'SALIDAS tiene 10 tachado y cifra final 9, que deja 12 desde 21. Se conserva la corrección visible, no dos salidas.',
            'revision':{'marcas_documentales':{'salidas':'10 tachado y lectura final 9.'}}},
        8293:{'criterios':['T07'],'motivo':'FIL-2016 escribe 2 en INGRESOS, pero el saldo disminuye de 11 a 9 y el detalle corresponde a la salida a FIL. Se interpreta salida 2 conservando la columna documental INGRESOS, sin inventar otra operación.',
            'revision':{'columna_documental_cantidad':'INGRESOS','interpretacion_cantidad':'SALIDA','cantidad_documental':2,'lectura_fecha_parcial':'14/19-9-16.'}},
    })
    plan=construir(version=26,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(4605,4606),(4615,4616,4617),(4648,4649),(4651,4652,4653),(4661,4662)],
        bases={80:{'primera_fila':4602,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso 50 y saldo 50: base cero inferida, sin recuento previo acreditado.'},
            169:{'primera_fila':8253,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso 20 y saldo 20: base cero inferida, sin ingreso adicional ni recuento ficticio.'}},
        observaciones=[
            {'articulo_id':80,'observado':True,'excluir_entrenamiento':True,'motivo':'Cinco fotografías y 109 filas cotejadas completas. Se recupera salida 225 mal leída como ingreso y la salida 2 de FIL-2019 indicada expresamente en una nota adherida a la última foto, en la misma fila ya existente. La tabla terminaba en saldo 1 y deja sin saldo esa salida: acumulado condicional -1, que no acredita existencia y bloquea apertura automática por ser negativo. Pendiente conciliar el tramo, sin inventar entrada ni ajuste; artículo excluido del entrenamiento.'},
            {'articulo_id':169,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos cotejadas, con 41 filas previamente extraídas y una fila tachada omitida recuperada como evidencia no operativa. Se conserva la anulación de Jessica Freud y sus cifras originales, sin efecto sobre la siguiente salida 8. La última cifra 2 en INGRESOS se interpreta salida por el contexto y el saldo 11 a 9, manteniendo la columna documental. Se conservan correcciones tachadas y fechas técnicas; cierre 9 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={80:-1,169:9} and not plan['cotejo']['discrepancias'],plan['cotejo']
    anulada=next(e for e in plan['revisiones'] if e['id']==8262)
    anulada['cambios'].update(ingresos=None,salidas=4,saldo_registrado=6,estado='ANULADO_DOCUMENTO')
    anulada['revision'].update(tipo_fila='ANULADO',saldo_documental=6,origen_saldo='NO_APLICA',usar_saldo_esperado=False,
        marcas_documentales={'fila':'Tachaduras en fecha, detalle, área, cantidad 4 y saldo 6.'})
    anulada['revision']['motivo']=extras[8262]['motivo']+' Se conservan la foto y la extracción original, con salida 4 y saldo 6 documentales sin efecto operativo.'
    anulada['revision']['criterios']=[c for c in anulada['revision']['criterios'] if c!='T08']
    anulada['revision']['hallazgos'].append('FILA_ANULADA_EN_DOCUMENTO_CONSERVADA')
    r=rows[8267];foto=next(e for e in plan['revisiones'] if e['id']==8267)
    detalle='FERIA INT. LIBRO (fila completamente tachada)'
    rev={'criterios':['T09','T14','T23'],'motivo':'Renglón completamente tachado entre la solicitud del 13-08-10 y la feria del 21-08-10, omitido por OCR. Se recupera solo como evidencia anulada. Fecha y cifras bajo tachadura no se certifican; saldo 8 es un valor técnico de almacenamiento sin efecto, no una lectura del saldo tachado.',
        'tipo_fila':'ANULADO','origen_fecha':'HIPOTESIS','fecha_documental':None,'motivo_fecha':'Fecha tachada no inequívoca: consulta técnica del antecedente 13-08-2010.',
        'saldo_documental':None,'origen_saldo':'HIPOTESIS','origen_cantidades':'HIPOTESIS','usar_saldo_esperado':False,
        'cotejo_pagina_completa':True,'hallazgos':['HOJA_COMPLETA_COTEJADA','FILA_OMITIDA_RECUPERADA_DESDE_FOTO','FILA_ANULADA_EN_DOCUMENTO_CONSERVADA'],
        'lectura_parcial':'Feria Int. Libro, CEDOAL; fecha, salida y saldo bajo tachaduras.'}
    campos={'articulo_id':169,'lote_id':r['lote_id'],'ruta_imagen_respaldo':r['ruta_imagen_respaldo'],'numero_pagina':1,'orden_fila':rows[8268]['orden_fila'],
        'fecha_movimiento':'2010-08-13','fecha_original':None,'detalle':detalle,'referencia':None,'area':'CEDOAL','ingresos':None,'salidas':None,
        'saldo_registrado':8,'saldo_calculado':8,'fecha_estado':'NO_APLICA_DOCUMENTAL','estado':'ANULADO_DOCUMENTO',
        'nodo_grafo':'Destino no especificado','area_estado':'PENDIENTE_HIL','referencia_estado':'AUSENTE','requiere_auditoria_nodo':False,'requiere_auditoria_referencia':False,
        'datos_originales':{'fuente':'LECTURA_FOTO_HIL','fecha_documental':None,'detalle':detalle,'ingresos':None,'salidas':None,'saldo_registrado':None,
            'orden_fila':rows[8268]['orden_fila'],'no_existia_en_extraccion_ocr':True,'limite':'Renglón tachado recuperado; no se certifican sus cantidades o saldo.'}}
    plan['recuperaciones']=[{'clave':f'art169-lote{r["lote_id"]}-p1-tachada-entre8267y8268-v1','fuente':foto['fuente'],'sha256_imagen':foto['sha256_imagen'],'campos':campos,'revision':rev}]
    plan['cotejo'].update(movimientos=151,filas_anuladas_preexistentes=[8262],filas_recuperadas_anuladas=1,cierres_no_operables=[80],
        limites_cierre={80:'La nota pide registrar salida 2 desde saldo previo 1, con saldo final en blanco: acumulado condicional -1. Pendiente de conciliación; apertura bloqueada, sin ingreso inventado.'})
    plan['cotejo']['cierres_documentales'][80]=None
    return plan


if __name__=='__main__':congelar(generar())
