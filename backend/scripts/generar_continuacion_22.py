"""Cambio climático, Mar de sueños y Luksic: 327 filas y 14 fotos completas."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(6780,6806),[-1,-3,-1,2,-3,-10,10,-2,-3,3,-20,-12,-1,-1,-1,-2,-3,-10,-1,-3,-1,-1,-59,-1,1,-1],
  [400,397,396,398,395,385,395,393,390,393,373,361,360,359,358,356,353,343,342,339,338,337,278,277,278,277]),
 (range(6806,6832),[-1,-2,2,-10,10,-20,-1,-3,-1,1,3,-1,-3,-1,-2,2,-3,-5,5,-5,2,-1,-1,1,3,-1],
  [276,274,276,266,276,256,255,252,251,252,255,254,251,250,248,250,247,242,247,242,244,243,242,243,246,245]),
 (range(6832,6858),[-1,1,1,-1,-1,-3,-10,3,-5,-1,5,-10,-1,-1,7,-1,1,10,-3,-5,-2,-2,2,-2,3,-1],
  [244,245,246,245,244,241,231,234,229,228,233,223,222,221,228,227,228,238,235,230,228,226,228,226,229,228]),
 (range(6858,6877),[-2,-3,-4,2,1,-1,-1,-1,-1,-1,-1,-8,-1,-1,3,-2,1,2,-15],
  [226,223,219,221,220,221,220,219,218,217,216,208,207,206,209,207,208,210,195]),
 (range(5992,6018),[50,-35,-15,423,-1,-5,8,-1,-1,-10,-1,-3,-5,-1,-12,-1,-225,-1,1,1,-1,-1,-1,-2,2,-10],
  [50,15,None,423,422,417,425,424,423,413,412,409,404,403,391,390,165,164,165,166,165,164,163,161,163,153]),
 (range(6018,6044),[-1,2,-2,-1,-1,1,-1,-1,1,1,-10,-5,8,-3,3,-5,-1,-1,5,-1,-1,-10,-3,-1,4,-2],
  [96,98,96,95,94,95,94,93,94,95,85,80,88,85,88,83,82,81,86,85,84,74,71,70,74,72]),
 (range(6044,6063),[-3,-5,-5,-4,1,-2,5,-2,-6,-10,-10,-5,-10,-3,-2,-1,-7,-1,1],
  [69,64,59,55,56,54,59,57,51,41,31,26,16,13,11,10,3,2,3]),
 (range(5277,5303),[200,-9,6,-89,-1,-1,1,-1,-1,20,-2,-1,-1,-10,-40,38,-10,-1,-3,-1,-8,-1,-5,-1,-15,19],
  [200,191,197,108,107,106,107,106,105,125,123,122,121,111,71,109,99,98,95,94,86,85,80,79,64,83]),
 (range(5303,5329),[-1,-1,-1,-15,-1,-1,-3,2,-5,-10,-1,-8,-5,-1,5,-3,-1,-10,-1,-5,0,1,-5,-5,-1,-5],
  [82,81,80,65,64,63,60,62,57,47,46,38,33,32,37,34,33,23,22,17,17,18,13,8,7,2]),
 (range(5329,5355),[100,100,250,50,-3,1,-2,2,-1,-10,-10,-3,-75,10,-2,-3,-10,1,-3,-30,-5,-10,14,-6,-1,1],
  [102,202,452,502,499,500,498,500,499,489,479,476,401,411,409,406,396,397,394,364,359,349,363,358,357,358]),
 (range(5355,5381),[-1,-2,4,-2,2,-2,-1,-1,1,-1,-1,1,-1,1,-1,-10,-5,-1,15,-3,-5,8,-5,-1,-1,5],
  [357,355,359,357,359,357,356,355,356,355,354,355,354,355,354,344,339,338,353,350,345,353,348,347,346,351]),
 (range(5381,5407),[-1,-1,-1,-10,-1,-1,7,-2,-1,-3,-5,-5,-4,1,-1,5,-2,-3,-3,2,-3,-2,-5,-1,-1,4],
  [350,349,348,338,337,336,343,341,340,337,332,327,323,324,323,328,326,323,320,322,319,317,312,311,310,314]),
 (range(5407,5433),[-1,-1,-1,-2,-1,-1,-2,-2,-5,1,-2,-2,-1,-1,-5,-3,-3,-2,-2,-2,-2,-3,-4,-5,2,-5],
  [313,312,311,309,308,307,305,303,298,299,297,295,294,293,288,285,282,280,278,276,274,271,267,262,264,259]),
 (range(5433,5436),[5,-8,-5],[264,256,251]),
]


def generar():
    snapshot='backups/continuacion_hil_22_20261015/articulos_97_90_85_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    for id,r in rows.items():
        if r['area'] in ('CEDOCAL','CEDIOC','CEDIOCC','CDOAL','CEDOOL'):
            cambios[id]={'area':'CEDOAL'};extras[id]={'motivo':'CEDOAL es la lectura del área en esta foto. No se crean áreas ni alias.'}
        if r['articulo_id']==85 and r['area'] in ('C A P','C.A.P'):
            cambios.setdefault(id,{})['area']='CAP'
            extras[id]={'motivo':'Se normaliza el espaciado de CAP escrito en la misma celda, sin crear equivalencias de instituciones distintas.'}
    for id,fields in {
        6798:{'fecha_movimiento':'2010-12-27','referencia':'OBQUIO'},6809:{'fecha_movimiento':'2011-08-01'},
        6833:{'detalle':'LETRAS PACEÑAS'},6838:{'referencia':'Galería'},6841:{'detalle':'PATIPIÑA','referencia':'DONACION','area':'CEDOAL'},
        6857:{'detalle':'LETRAS PACEÑAS FERIA','area':'CEDOAL'},6866:{'detalle':'LARGA NOCHE DE MUSEOS'},
        6870:{'detalle':'ORURO CASA CULTURA','referencia':'DONACION','area':'CEDOAL'},
        6873:{'detalle':'CM. JESUS DE MACHACA','referencia':'DONAC.','area':'CID'},
        5996:{'fecha_movimiento':'2010-10-04'},6017:{'fecha_movimiento':'2011-08-01'},
        6024:{'detalle':'LETRAS PACEÑAS','area':'CEDOAL'},6026:{'detalle':'LETRAS PACEÑAS','area':'CEDOAL'},
        6035:{'detalle':'CEDOAL'},6037:{'detalle':'INAUG. YOLANDA','area':'CEDOAL'},6046:{'area':'CAP'},
        6061:{'fecha_movimiento':'2017-09-27','detalle':'LA RAYUELA'},
        5308:{'detalle':'Escap. Cultural','referencia':'Ventas'},5323:{'ingresos':0,'area':'CEDOAL'},5341:{'fecha_movimiento':'2012-06-22'},
        5378:{'detalle':'PATIPIÑA'},5381:{'detalle':'INAUG. YOLANDA','area':'CEDOAL'},5399:{'referencia':None,'area':'Lucy'},
        5404:{'detalle':'CUEVA CUENTACUENTO'},5405:{'detalle':'BIBLIO - UNCIA','area':'CEDOAL'},
        5410:{'detalle':'LA PAZ LEE','area':'CEDOAL'},5416:{'detalle':'VENTAS CID','referencia':'DEV.','area':'CID'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        6794:('2010-11-13','SECUENCIA_AJUSTADA','2010-11-10','10-11 después del 13-11: consulta técnica del antecedente y literal conservada.'),
        6797:('2010-11-29','SECUENCIA_AJUSTADA','2010-11-07','07-11-10 está escrito después del 29-11-10. Se conserva noviembre como literal, sin convertirlo en diciembre para cuadrar.'),
        6823:('2012-08-08','SECUENCIA_AJUSTADA','2012-07-24','24-07 después del 08-08. Consulta técnica del antecedente, sin copiar fechas de otro artículo.'),
        6842:('2013-06-03','HIPOTESIS',None,'Devolución de Feria Santa Cruz sin fecha escrita; consulta técnica del antecedente.'),
        6864:('2016-01-14','HIPOTESIS','2015-01-14','El papel escribe 14-01-15 después de noviembre de 2015 y antes del 18-01-2016. Año 2016 solo como hipótesis de consulta.'),
        6869:('2016-09-19','HIPOTESIS',None,'FIL tiene fecha en blanco. La fecha técnica del antecedente no acredita su día propio.'),
        5994:('2010-08-26','SECUENCIA_AJUSTADA','2010-08-25','25-08 después del 26-08. Literal conservada y consulta técnica del antecedente.'),
        5998:('2010-10-21','SECUENCIA_AJUSTADA','2010-09-03','03-09 después del 21-10: consulta técnica del antecedente, sin alterar el ingreso 8.'),
        6002:('2010-11-22','SECUENCIA_AJUSTADA','2010-11-10','10-11 después de 22-11; literal conservada y consulta técnica.'),
        5307:('2009-09-10','SECUENCIA_AJUSTADA','2009-08-21','21-08 después del 10-09. Consulta técnica del antecedente y literal conservada.'),
        5327:('2010-11-22','SECUENCIA_AJUSTADA','2010-11-10','10-11 después del 22-11: consulta técnica del antecedente y literal conservada.'),
        **{id:('2012-08-21','SECUENCIA_AJUSTADA',fecha,'Fecha de julio/agosto escrita después del 21-08. Consulta técnica del antecedente y literal conservada.') for id,fecha in [(5349,'2012-07-24'),(5350,'2012-08-05'),(5351,'2012-08-14')]},
        5355:('2012-10-02','SECUENCIA_AJUSTADA','2012-09-26','26-09 después del 02-10 en la hoja anterior: consulta técnica sin cambiar el orden físico de las fotos.'),
        5411:('2017-04-20','HIPOTESIS',None,'FIL tiene FECHA en blanco. No se certifica el 04-05 atribuido por la extracción; se conserva ausencia y fecha técnica del antecedente.'),
    }
    extras.update({
        6780:{'motivo':'Primera salida 1 y saldo 400. Base 401 inferida solo para reconstruir, sin inventar un ingreso o conteo.'},
        6785:{'motivo':'El acercamiento permite leer 385: 395 - 10 = 385. No se introduce un supuesto error 285 por el trazo de la cifra.'},
        6807:{'revision':{'anotacion_documental':'Última cifra de saldo 274 repasada, conservada como lectura final visible.'}},
        6838:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'Galería está en REF y ÁREA tiene texto repasado; la atribución del área sigue pendiente y no se transforma en una institución por semejanza.',
            'revision':{'lectura_area_parcial':'Texto repasado; atribución no inequívoca.'}},
        6862:{'criterios':['T14','T05'],'motivo':'Ingreso 1 visible y cifra tachada en SALIDAS. Desde 221, el cálculo da 222, pero la última lectura de SALDO es 220 repasado. La siguiente salida 1 escribe 221 y recupera la cadena. Se conservan ambos saldos del papel sin cambiar el ingreso para cuadrarlo.',
            'revision':{'marcas_documentales':{'salidas':'Cifra tachada','saldo':'220 repasado'}}},
        6863:{'motivo':'La salida 1 deja 221 desde el reconstruido 222 y coincide otra vez con el papel. No se añade un ajuste para compensar el 220 de la fila anterior.'},
        6868:{'criterios':['T01'],'motivo':'FIL-2016 OBSQ. tiene salida 1, no 4: 217 - 1 = 216. Se recupera la cifra visible.'},
        5994:{'revision':{'lectura_saldo_parcial':'Guion escrito, no un cero numérico.','motivo':'Salida 15 desde 15: saldo de consulta 0; el documento presenta un guion. Se conserva esa distinción.'}},
        6001:{'criterios':['T02'],'motivo':'Jornadas Pedagógicas tiene salida 10, no ingreso 10: 423 - 10 = 413.'},
        6008:{'criterios':['T02'],'motivo':'Chuymampi tiene salida 225 visible, no ingreso: 390 - 225 = 165. No se reduce por su magnitud.'},
        6018:{'criterios':['T16'],'motivo':'La foto anterior termina en 153 y esta empieza con salida 1 y saldo 96. El salto neto de 56 unidades no está explicado por operaciones visibles. Se conserva la discontinuidad entre hojas, sin inventar una salida 56 ni un recuento.',
            'revision':{'discontinuidad_entre_hojas':{'anterior':6017,'saldo_anterior':153,'salida':1,'saldo_escrito':96,'diferencia_neta':-56},'hallazgos':['HOJA_COMPLETA_COTEJADA','DISCONTINUIDAD_ENTRE_HOJAS_NO_CONCILIADA']}},
        6032:{'motivo':'El acercamiento confirma saldo 88: 85 + 3 = 88. No se introduce un falso error de papel por confundir el 8 con 2.'},
        6043:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'CEDOAL cruza REF/ÁREA; la atribución actual de área conserva incertidumbre, sin certificarla como resuelta.'},
        6044:{'revision':{'lectura_detalle_parcial':'Noir... Quiro...; no se fusiona por semejanza con otros destinatarios.'}},
        5291:{'motivo':'Salida 40 visible desde 111 deja 71; la devolución 38 siguiente deja 109 y se conserva. No se modifica una fila correcta para compensar otra.'},
        5323:{'motivo':'La devolución escribe INGRESOS 0 y saldo 17. Se conserva el cero escrito, sin convertirlo en una recepción positiva ni borrar esa evidencia.'},
        5352:{'criterios':['T05'],'motivo':'La foto confirma salida 6 desde 363 y escribe saldo 358. El cálculo es 357; la diferencia de una unidad continúa después. No se sustituye 6 por 5 para cuadrar el papel.'},
        5366:{'criterios':['T14'],'motivo':'Hay ingreso 1 y una marca tachada en SALIDAS, con saldo documental corregido 355. Se conserva la entrada sin segundo descuento.',
            'revision':{'marcas_documentales':{'salidas':'Marca tachada','saldo':'Valor tachado y final 355'}}},
        **{id:{'criterios':['T02'],'motivo':motivo} for id,motivo in {
            5370:'Feria infantil tiene salida 10 en la foto, no ingreso; saldo documental 344.',
            5371:'Feria infantil tiene salida 5, no ingreso; saldo documental 339.',
            5384:'FIL tiene salida 10, no ingreso; saldo documental 338.',
            5392:'OBSQ. FIL tiene salida 5 con cifra anterior tachada, no ingreso. Se conserva el saldo documental final 327, sin anular la fila.'}.items()},
        5388:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'CEDOAL está entre REF/ÁREA. Se conserva su atribución actual en ÁREA, marcada como pendiente.'},
        5396:{'revision':{'anotacion_documental':'Ingreso final 5 legible con trazo anterior repasado; sin doble efecto.'}},
        5399:{'criterios':['T23'],'motivo':'Lucy ocupa ÁREA y REF está en blanco. Se recuperan sus columnas sin asociarla a otra institución.'},
        5416:{'criterios':['T14','T23'],'motivo':'DEV. está en REF y CID en ÁREA. Ingreso 1 con una marca tachada en SALIDAS: se conserva la devolución, no una segunda venta o descuento.',
            'revision':{'marcas_documentales':{'salidas':'Marca negra tachada'}}},
    })
    plan=construir(version=22,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(6808,6809),(6832,6833),(6852,6853),(5995,5996),(6016,6017),(6025,6026),(6058,6059),(5341,5342),(5365,5366),(5417,5418)],
        bases={97:{'primera_fila':6780,'saldo_base':401,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primera salida 1 con saldo 400: base 401 inferida, no un ingreso ni recuento documentado.'},
            90:{'primera_fila':5992,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 50: base cero inferida, sin acreditar recuento previo.'},
            85:{'primera_fila':5277,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 200: base cero inferida, sin acreditar recuento previo.'}},
        observaciones=[
            {'articulo_id':97,'observado':True,'excluir_entrenamiento':False,'motivo':'Cuatro fotos y 97 filas cotejadas. Salida 1 recuperada en FIL-2016, ingreso 1 con salida tachada conservado y saldos documentales 220/221 que se compensan identificados. Base inicial 401 inferida, fechas técnicas y área parcial siguen marcadas. Cierre 195 coincide con el papel.'},
            {'articulo_id':90,'observado':True,'excluir_entrenamiento':True,'motivo':'Tres fotos y 71 filas cotejadas. Entre las dos primeras hojas hay discontinuidad de 56 unidades sin operaciones visibles que la expliquen: 153 seguido de salida 1 y saldo 96. No se inventa salida ni recuento. Cierre escrito 3 conservado frente a acumulado único condicional 59; saldos incompatibles son hipótesis y apertura automática bloqueada. Artículo excluido del entrenamiento hasta conciliar el tramo.'},
            {'articulo_id':85,'observado':True,'excluir_entrenamiento':True,'motivo':'Siete fotos y 159 filas cotejadas, incluidas ambas cargas. Se recuperan cuatro salidas mal leídas como ingresos. La salida 6 desde 363 escribe 358 en lugar de 357 y deja una unidad de diferencia hasta el cierre. Se conserva cierre escrito 251 y cálculo 250, con aviso final y apertura bloqueada para conciliación. No se cambia 6 por 5 ni se inventa ajuste. Fechas técnicas, cero escrito, tachaduras y atribución REF/ÁREA pendiente conservados.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={97:195,90:59,85:250}
    assert plan['cotejo']['discrepancias']==[{'id':6862,'local':-2,'acumulada':-2},{'id':6863,'local':2,'acumulada':0},{'id':6018,'local':-56,'acumulada':-56},{'id':5352,'local':1,'acumulada':1}]
    for e in plan['revisiones']:
        if e['articulo_id']==90 and e['id']>=6018:
            e['revision']['origen_saldo']='HIPOTESIS'
            e['revision']['motivo']+=' Acumulado de consulta condicional a la continuidad de las fotos: no acredita existencias y el salto documental sigue pendiente.'
        if e['id'] in (6062,5435):
            e['cambios']['saldo_registrado']=3 if e['id']==6062 else 251
            e['revision'].update(origen_saldo='FOTO',usar_saldo_esperado=False)
            e['revision']['motivo']+=' Se conserva el cierre escrito con aviso de saldo y bloqueo de apertura automática, sin convertir el cálculo en existencia física confirmada.'
    plan['cotejo'].update(cierres={97:195,90:3,85:251},cierres_calculados={97:195,90:59,85:250},
        pendientes_documentales={'6062':['saldo'],'5435':['saldo']},
        limites_cierre={90:'Discontinuidad de 56 unidades entre fotos: cierre escrito 3 y acumulado condicional 59; pendiente, no operable.',
            85:'Error aritmético de una unidad que persiste en el papel: cierre escrito 251 y cálculo 250; pendiente de conciliación, no operable.'})
    return plan


if __name__=='__main__':congelar(generar())
