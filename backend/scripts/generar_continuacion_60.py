"""Cuatro hojas: bases sin ingresos, fechas parciales y anotación de ejemplares dañados."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(7668,7688),[14,-8,5,-3,5,-3,3,-1,-2,-5,-2,-2,5,-4,8,-1,-1,2,-2,-1],[14,6,11,8,13,10,13,12,10,5,3,1,6,2,10,9,8,10,8,7]),
 (range(9631,9651),[0,-2,2,-2,-1,1,2,-2,-5,2,40,-2,-2,-1,1,3,-3,3,-34,-2],[15,13,15,13,12,13,15,13,8,10,50,48,46,45,46,49,46,49,15,13]),
 (range(10410,10433),[20,-3,-5,-5,-3,-2,-1,-2,2,-1,20,-10,-5,2,-2,-2,-1,5,-1,-2,-2,-1,-1],[20,None,None,None,None,None,None,None,1,None,20,10,5,7,5,3,2,7,6,4,2,1,0]),
 (range(11850,11869),[0,-2,1,-2,10,-3,-5,4,-2,2,-2,-2,2,-3,0,-1,1,10,-1],[4,2,3,1,11,None,3,7,5,7,5,3,5,2,2,1,2,12,11]),
]

def generar():
    snapshot='backups/continuacion_hil_60_20261016/articulos_138_244_304_383_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area']=='Cedoal'}
    for id,fields in {
        7668:{'referencia':'SB','area':None},7680:{'detalle':'Ingreso sin detalle documental'},
        9631:{'detalle':'Saldo según inventario','referencia':None},9634:{'detalle':'CEDOAL P/llallanta'},9637:{'area':'Feria'},
        10423:{'area':'CEDOAL'},10424:{'area':'CEDOAL'},
        11853:{'detalle':'CEDOAL al Paraguay'},11854:{'detalle':'Ingresa Santa Cruz'},11858:{'detalle':'CEDOAL Oruro'},11861:{'detalle':'Oruro'},11862:{'referencia':None,'area':'CEDOAL'},11863:{'referencia':None,'area':'CEDOAL'},11864:{'estado':'NOTA_DOCUMENTAL'},11868:{'area':'Lucy'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        7673:('2012-07-30','SECUENCIA_AJUSTADA','2012-07-24','24-7-12 aparece después de 30-7-12; literal y orden físico conservados, sin mover cantidades.'),
        7680:('2014-07-29','HIPOTESIS',None,'Ingreso 5 sin FECHA ni DETALLE; consulta técnica del antecedente, no fecha ni texto certificado.'),
        7682:('2016-09-19','HIPOTESIS',None,'Ingreso 8 tiene FECHA vacía; consulta técnica del antecedente, sin certificar día real.'),
        7687:('2022-08-05','HIPOTESIS',None,'FECHA vacía, FIL-24 está solo en DETALLE. Se conserva contexto técnico existente, sin afirmar día de 2022 ni fabricar fecha exacta de 2024.'),
        **{id:(fecha,'HIPOTESIS',None,'Fecha escrita solo con día y mes, sin año. Gestión 2006 técnica por contexto previo a primer año explícito 2007; no año documental certificado.') for id,fecha in ((9631,'2006-06-26'),(9632,'2006-10-06'),(9633,'2006-11-29'))},
        9639:('2007-10-17','SECUENCIA_AJUSTADA','2007-08-01','01-08-07 aparece después de 17-10-07; literal y consulta técnica conservados.'),
        9640:('2007-10-17','HIPOTESIS',None,'Devolución Potosí tiene FECHA vacía; nota lateral DH 14-12-07 conservada sin asignarla automáticamente. Consulta técnica del antecedente.'),
        9641:('2008-07-01','HIPOTESIS',None,'La foto solo escribe Julio-2008, sin día. El día 1 es técnico para consulta, no fecha exacta del ingreso.'),
        **{id:('2006-01-01','HIPOTESIS',None,'FECHA vacía en las primeras cinco filas; se conserva consulta técnica existente sin certificar 1 de enero ni gestión 2006 del hecho.') for id in range(10410,10415)},
        10418:('2007-02-02','SECUENCIA_AJUSTADA','2006-11-29','29-11-06 literal aparece después de 2-02-07. Se conserva, sin cambiarlo a 2007 para ordenar.'),
        10421:('2007-08-08','HIPOTESIS',None,'Para la Feria no tiene fecha propia; consulta técnica del antecedente, no fecha escrita.'),
        10423:('2007-10-17','HIPOTESIS',None,'Devolución Potosí no tiene fecha propia. Nota lateral DH 14-12-07 conservada sin asignarla automáticamente; consulta técnica del antecedente.'),
        11853:('2005-10-13','HIPOTESIS',None,'CEDOAL al Paraguay tiene FECHA vacía; consulta técnica del antecedente.'),
        11854:('2006-08-08','HIPOTESIS',None,'08-06 es una fecha parcial; puede expresar mes/año o día/mes sin año. Consulta técnica existente conservada, sin completar fecha documental.'),
        **{id:('2006-08-08','HIPOTESIS',None,'Fila sin fecha propia después de la fecha parcial 08-06; consulta técnica existente conservada, sin fecha exacta confirmada.') for id in (11855,11856,11857)},
        11858:('2006-10-09','HIPOTESIS',None,'9.10 escrito sin año; 2006 solo técnico por contexto, no gestión documental certificada.'),
        11860:('2006-11-29','SECUENCIA_AJUSTADA','2006-02-02','2-02-06 está escrito después de 29-11-06. Se conserva día, mes y año literal, sin cambiarlo a 2007.'),
        11862:('2007-06-15','HIPOTESIS',None,'Devolución tiene FECHA vacía; nota lateral DH 19-12-07 conservada sin asignarla automáticamente. Consulta técnica del antecedente.'),
        11864:('2009-01-12','SECUENCIA_AJUSTADA','2008-12-16','16/12/08 está escrito después de Gestión 2009 del 12-01-09. Nota de saldo, no recuento físico ni transacción; literal conservado.'),
    }
    extras={
        7668:{'criterios':['T23'],'motivo':'SB es procedencia en ÁREA del ingreso; se conserva en referencia sin crear institución ni alias.', 'revision':{'columnas_documentales':{'area':'SB'}}},
        7670:{'criterios':['T16'],'motivo':'Saldo 11 e ingreso 5 legibles. Nota lateral dice 6 en mal estado y un 5 está rodeado junto al saldo; las filas siguientes continúan desde 11. Se conserva la anotación sin inventar salida 6, recuento 5 ni baja física.', 'revision':{'anotacion_margen':'6 en mal estado; 5 rodeado junto al saldo 11.','ambito_anotacion_pendiente':True,'marcas_documentales':{'saldo':'11 y anotación 5 rodeada al costado.'}}},
        7680:{'criterios':['T23'],'motivo':'Cantidad 5 en INGRESOS explícita; la etiqueta describe ausencia de detalle y no pretende ser texto del papel.', 'revision':{'detalle_documental':None,'etiqueta_descriptiva_sin_texto_en_fuente':True}},
        7687:{'criterios':['T07'],'motivo':'FIL-24 escribe 1 en INGRESOS pero saldo baja de 8 a 7. Se interpreta una salida 1, conservando la columna documental, sin segunda operación.', 'revision':{'columnas_documentales':{'ingresos':1},'fecha_documental_texto':'FECHA vacía; FIL-24 escrito en DETALLE.'}},
        9631:{'criterios':['T22','T23'],'motivo':'Saldo inicial según inventario 15 sin cantidades; inventario continúa la frase sobre REF/ÁREA, no constituye institución ni nueva recepción.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL','fecha_documental_texto':'26-6, sin año.'}},
        9632:{'criterios':['T09'],'revision':{'fecha_documental_texto':'6-10, sin año.'}},9633:{'criterios':['T09'],'revision':{'fecha_documental_texto':'29-11, sin año.'}},
        9634:{'criterios':['T23'],'motivo':'P/llallanta se conserva como texto literal; no se fusiona por semejanza con otra localidad.'},
        9640:{'criterios':['T16'],'revision':{'anotacion_margen_fecha':'DH 14-12-07 al costado, no fecha propia inequívoca.'}},
        9641:{'criterios':['T09'],'revision':{'fecha_documental_texto':'Julio-2008, sin día.'}},
        9649:{'criterios':['T02'],'motivo':'Devolución escribe SALIDA 34 y saldo 15 desde 49; se conserva egreso por columna, sin invertir por el nombre.'},
        10417:{'criterios':['T05','T08'],'motivo':'Salida 2 legible con SALDO vacío produce acumulado condicional -1. Se conserva sin recortar a cero ni reducir cantidad; la devolución siguiente literal de 2006 se mantiene fuera de orden.', 'revision':{'saldo_negativo_reconstruido':True}},
        10419:{'criterios':['T08'],'motivo':'SALDO contiene guiones y punto, no un cero numérico; cero queda como cálculo técnico.', 'revision':{'marcas_documentales':{'saldo':'— · —'}}},
        10423:{'criterios':['T16'],'revision':{'anotacion_margen_fecha':'DH 14-12-07 al costado, no asignada automáticamente.'}},
        10424:{'criterios':['T18'],'motivo':'Salida 2 tenue legible y comillas inequívocas en ÁREA repiten CEDOAL; no se añade operación.'},
        11850:{'criterios':['T22'],'motivo':'Base según inventario 4 escrita sin ingreso; no se añade recepción ficticia.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL'}},
        11854:{'criterios':['T09'],'revision':{'fecha_documental_texto':'08-06, sin fecha completa inequívoca.'}},
        11858:{'criterios':['T09'],'revision':{'fecha_documental_texto':'9.10, sin año.'}},
        11862:{'criterios':['T16','T23'],'motivo':'CEDOAL ocupa ÁREA, no referencia; se conserva columna desde foto sin crear alias.', 'revision':{'anotacion_margen_fecha':'DH 19-12-07 al costado, no asignada automáticamente.'}},
        11864:{'criterios':['T16'],'motivo':'Saldo 2 escrito sin cantidades ni leyenda de recuento físico. Se conserva como NOTA_DOCUMENTAL sin efecto ni reinicio de la cadena; no ingreso ni salida.', 'revision':{'tipo_fila':'NOTA_DOCUMENTAL','origen_cantidades':'HIPOTESIS'}},
    }
    plan=construir(version=60,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={138:{'primera_fila':7668,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Ingreso y saldo 14 explícitos; base previa cero inferida.'},244:{'primera_fila':9631,'saldo_base':15,'origen_saldo_base':'FOTO','motivo_base':'Base escrita según inventario 15, sin ingreso adicional.'},304:{'primera_fila':10410,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Ingreso y saldo 20 explícitos; base previa cero inferida.'},383:{'primera_fila':11850,'saldo_base':4,'origen_saldo_base':'FOTO','motivo_base':'Base escrita según inventario 4, sin ingreso ficticio.'}},
        observaciones=[
            {'articulo_id':138,'observado':True,'excluir_entrenamiento':True,'motivo':'Foto completa y veinte filas cotejadas. Nota 6 en mal estado y 5 rodeado junto a saldo 11 conservados; las filas siguientes siguen desde 11, sin baja 6 ni recuento inventado. Ámbito físico pendiente, artículo excluido. Ingreso 5 sin fecha/detalle y recepción 8 sin fecha marcados; FIL-24 sin fecha se interpreta salida 1 desde columna INGRESOS por saldo 8 a 7. Cierre 7 condicional, sin atribuir bloqueo automático solo por exclusión.'},
            {'articulo_id':244,'observado':True,'excluir_entrenamiento':False,'motivo':'Foto completa y veinte filas cotejadas. Base escrita 15 sin ingreso, tres fechas iniciales sin año y Julio-2008 sin día conservan hipótesis. Fecha 01-08-07 fuera de orden y devolución sin fecha mantienen literal/contexto; nota marginal no se asigna automáticamente. Salida 34 de Devolución conservada por columna. Cierre 13 coincide.'},
            {'articulo_id':304,'observado':True,'excluir_entrenamiento':True,'motivo':'Foto completa y veintitrés filas cotejadas. Cinco fechas iniciales ausentes y ocho saldos vacíos o guiones no se certifican. Salida 2 legible genera acumulado condicional -1 antes de devolución 2; literal 29-11-06 después de 2-02-07 conserva orden físico sin inventar operaciones. Artículo excluido por tramo pendiente; comillas de ÁREA y notas marginales conservadas. Cierre cero condicional, sin atribuir bloqueo automático solo por exclusión.'},
            {'articulo_id':383,'observado':True,'excluir_entrenamiento':False,'motivo':'Foto completa y diecinueve filas cotejadas. Base 4 sin ingreso, saldo vacío y fechas ausentes/parciales identificados. 2-02-06 después de 29-11-06 y nota Saldo del 16/12/08 después de Gestión 2009 conservan literal. Nota saldo 2 queda sin efecto, no recuento físico. Lucy, Oruro y columnas CEDOAL recuperados por foto, sin alias ni asignación automática de fechas marginales. Cierre 11 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['discrepancias']==[] and plan['cotejo']['cierres']=={138:7,244:13,304:0,383:11},plan['cotejo']
    plan['cotejo']['limites_cierre']={138:'Cierre escrito 7 coincide condicionalmente. Nota 6 en mal estado pendiente de ámbito; artículo excluido, sin afirmar bloqueo automático.',304:'Cierre escrito 0 coincide condicionalmente. Tramo calculado -1 con saldo vacío y fechas fuera de orden permanece señalado; no se inventan ajustes.'}
    return plan

if __name__=='__main__':congelar(generar())
