"""Nueve fotos completas: Betshabé, Voltea y Bolivia Ecológica 33."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND
from scripts.generar_continuacion_28 import recuperada

HOJAS=[
 (range(1125,1151),[150,-5,-14,-4,-1,-1,-3,-2,-1,-1,-3,-1,-12,-1,1,1,-1,-2,2,-10,10,-1,-1,-2,-1,1],
  [150,145,131,127,126,125,122,120,119,118,115,114,102,101,102,103,102,100,102,92,102,101,100,98,97,98]),
 (range(1099,1125),[1,-1,-1,-10,-1,10,-2,1,-5,5,-5,-1,4,-1,-5,5,-1,1,-1,1,-1,-3,3,-5,-1,5],
  [99,98,97,87,86,96,94,95,90,95,90,89,93,92,87,92,91,92,91,92,91,88,91,86,85,98]),
 (range(1078,1099),[-5,-1,3,-1,1,-3,-2,-2,1,-1,3,-1,-3,-1,-1,-1,-1,-2,2,1,-1],
  [85,84,87,86,87,84,82,80,81,80,83,82,79,78,77,76,75,73,75,76,75]),
 (range(3878,3904),[175,100,-20,-10,-10,-17,1,-130,-30,-15,90,-10,-1,-15,-4,-1,-10,-1,-1,-1,-1,-2,-2,-5,-3,-1],
  [175,275,255,245,235,218,219,89,59,44,134,124,123,108,104,103,93,92,91,90,89,87,85,80,77,76]),
 (range(3904,3930),[-1,-3,-1,-4,-2,-2,-10,-1,-14,-5,5,-2,-3,-3,-1,-1,-10,-3,-5,-1,-1,3,-3,-2,-1,-1],
  [75,72,71,67,65,63,53,52,38,33,38,36,33,30,29,28,18,15,10,9,8,11,8,6,5,4]),
 (range(3930,3934),[-2,-2,8,-6],[2,0,8,2]),
 (range(10122,10148),[0,-2,-2,-2,5,-1,-2,1,-1,20,-3,-5,-5,-3,3,-2,-2,-1,2,-2,1,-6,13,-10,-3,6],
  [8,6,4,2,7,None,4,5,4,24,None,None,None,8,11,None,7,6,8,6,7,1,14,4,1,7]),
 (range(10148,10174),[-5,2,-2,50,-10,-5,2,-2,-2,-5,3,-3,-1,-10,-10,14,1,-1,-3,2,-5,6,-10,8,-3,3],
  [2,4,2,52,42,37,39,37,35,30,33,30,29,19,9,23,24,23,20,22,17,22,12,20,17,20]),
 (range(10174,10184),[-5,3,-10,9,-1,-1,-5,1,-1,-1],[15,18,8,17,16,15,10,11,10,9]),
]

def generar():
    snapshot='backups/continuacion_hil_29_20261015/articulos_27_69_290_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    # La secuencia documental es foto 3 -> 2 -> 1, no la numeración del escaneo.
    for id,r in rows.items():
        if r['articulo_id']==27:cambios[id]={'orden_pagina_validado':{3:1,2:2,1:3}[r['numero_pagina']]}
        if r['articulo_id']==290 and r['numero_pagina']==3 and id==10183:cambios[id]={'orden_fila':r['orden_fila']+1}
        if r['area'] in ('GODOOL','CEDOC','CEDOC.','SDOAL','Cedocl','Cedoal','Cedual','CEDO'):
            cambios.setdefault(id,{})['area']='CEDOAL'
            extras[id]={'motivo':'La foto se lee CEDOAL en esta celda; se corrige la lectura sin crear un área ni un alias.'}
    for id,fields in {
        1079:{'area':'CEDOAL'},1093:{'referencia':'DONACION','detalle':'CASA CULTURA - ORURO'},
        1100:{'detalle':'COMPA TRONO'},1111:{'detalle':'DEVO. CULCINA'},1116:{'area':'CEDOAL'},1120:{'detalle':'LARGA NOCHE MUSEO'},
        1130:{'fecha_movimiento':'2010-11-09'},1149:{'detalle':'A.P.A.C. PALCA'},
        3884:{'area':None},3888:{'area':None},3893:{'detalle':'PORTADAS SALVAJES'},3896:{'detalle':'U. COSTA RICA'},
        3904:{'detalle':'Montserrat Fernandez','referencia':'POTOSI'},3912:{'area':'LUCY'},
        3917:{'detalle':'LOS AMIGOS LIBRO - CBBA','referencia':'CONSIG.','area':None},3919:{'detalle':'U.E. TAIWAN'},
        10124:{'detalle':'FERIA DEL LIBRO'},10125:{'detalle':'FERIA DEL LIBRO'},10127:{'detalle':'Feria Sopocachi'},
        10128:{'detalle':'Pared Paraguay'},10132:{'detalle':'Sale a la Feria'},10133:{'detalle':'Sale a la Feria'},
        10134:{'detalle':'Sale a la Feria'},10135:{'detalle':'Sale a la Feria'},10147:{'detalle':'Devolucion Feria','area':None},
        10171:{'area':'CEDOAL'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        1081:('2013-11-04','HIPOTESIS',None,'Ventas DIR no tiene fecha propia; consulta técnica del antecedente.'),
        1084:('2014-05-19','HIPOTESIS',None,'Librería Akademia tiene FECHA en blanco; consulta técnica del antecedente.'),
        1144:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08 después del 02-08-11: literal conservada y consulta técnica del antecedente.'),
        3899:('2014-12-10','SECUENCIA_AJUSTADA','2014-05-19','19-5-14 está escrito después de 10-12-14, incluso antes de la recepción inicial de julio. Se conserva literal sin inventar otra gestión; consulta técnica del antecedente.'),
        10127:('2005-10-13','HIPOTESIS',None,'Feria Sopocachi sin fecha propia; consulta técnica del antecedente.'),
        10128:('2005-10-13','HIPOTESIS',None,'Pared Paraguay sin fecha propia; consulta técnica del antecedente.'),
        10129:('2005-10-13','HIPOTESIS',None,'Devolución Feria sin fecha propia; consulta técnica del antecedente.'),
        10130:('2005-10-13','HIPOTESIS',None,'Venta sin fecha propia; consulta técnica del antecedente.'),
        10131:('2006-06-08','HIPOTESIS',None,'La foto escribe 08-06 sin año inequívoco. Se usa 2006 por contexto anterior a febrero de 2007, solo para consulta; no se certifica fecha completa.'),
        10132:('2006-06-08','HIPOTESIS',None,'Sale a la feria sin fecha; consulta técnica del antecedente parcial.'),
        10133:('2006-06-08','HIPOTESIS',None,'Repetición del detalle, FECHA vacía; consulta técnica sin certificar una fecha escrita.'),
        10134:('2006-06-08','HIPOTESIS',None,'Repetición del detalle, FECHA vacía; consulta técnica sin certificar una fecha escrita.'),
        10135:('2006-06-08','HIPOTESIS',None,'Repetición del detalle, FECHA vacía; consulta técnica sin certificar una fecha escrita.'),
        10136:('2006-06-08','HIPOTESIS',None,'Devolución sin fecha propia; consulta técnica del antecedente.'),
        10137:('2006-10-09','HIPOTESIS',None,'09-10 sin año escrito inequívoco; 2006 es gestión técnica de contexto, no fecha completa confirmada.'),
        10140:('2007-04-23','SECUENCIA_AJUSTADA','2006-11-29','29-11-06 está después del 23-04-07. Se conserva literal y consulta técnica del antecedente.'),
        10142:('2007-06-16','HIPOTESIS',None,'Devolución tiene FECHA en blanco; consulta técnica del antecedente.'),
        10143:('2007-08-08','HIPOTESIS',None,'Año de 8-08-0… repasado, lectura 2008 de OCR no inequívoca y antes de agosto de 2007. Se conserva lectura parcial; gestión 2007 solo técnica.'),
        10144:('2007-08-08','HIPOTESIS',None,'Marca de repetición en FECHA de una fecha con año dudoso. Se conserva la marca y la fecha técnica, sin certificar el año.'),
        10149:('2007-10-17','HIPOTESIS',None,'Devolución Potosí tiene FECHA en blanco; consulta técnica del antecedente, sin asignarle automáticamente la nota lateral.'),
        10162:('2010-08-13','SECUENCIA_AJUSTADA','2010-04-23','23-04-10 en el papel después de 13-08-10. Se conserva literal y consulta técnica del antecedente, sin cambiar el mes para cuadrar el orden.'),
        10170:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11; consulta técnica del antecedente y literal conservada.'),
    }
    extras.update({
        1079:{'criterios':['T18'],'motivo':'Comillas inequívocas en ÁREA repiten el CEDOAL de la fila anterior; no se crea un área llamada comillas.'},
        1104:{'criterios':['T03'],'motivo':'Ingreso 10 y (10) en SALIDAS corresponden a devolución y anotación de la cantidad remitida; el saldo 86 a 96 confirma un solo ingreso. Se conserva la anotación, sin segunda salida.', 'revision':{'anotacion_salidas_documental':'(10)'}},
        1112:{'criterios':['T23'],'motivo':'DOSSIER tiene salida 1 legible, omitida por OCR: 93 a 92.'},
        1116:{'criterios':['T18'],'motivo':'Comillas claras en ÁREA repiten CEDOAL de Letras Paceñas anterior; se conserva la marca documental.'},
        1124:{'criterios':['T05'],'motivo':'El saldo de la devolución 5 se lee 98, no 90. Se conserva el 98 escrito y el cálculo independiente 90; la hoja siguiente inicia 85 tras salida 5. La discrepancia local +8 se compensa con -8 en la siguiente hoja, sin cambiar ninguna cantidad.'},
        1139:{'criterios':['T07'],'motivo':'DEV. FERIA UCB escribe 1 en SALIDAS, pero aumenta 101 a 102. Se interpreta como ingreso 1 por devolución, conservando columna documental SALIDAS.', 'revision':{'columna_documental_cantidad':'SALIDAS','interpretacion_cantidad':'INGRESO','cantidad_documental':1}},
        1141:{'criterios':['T14'],'motivo':'QUIME escribe salida 1 con una marca tachada en INGRESOS; se conserva la salida y el tachón sin crear otra entrada.', 'revision':{'marcas_documentales':{'ingresos':'Marca tachada.'}}},
        3881:{'motivo':'Obsequio FIL (1) y FIL (2) son dos renglones y salidas 10 distintos. No se deduplican por semejanza.'},
        3884:{'criterios':['T23'],'motivo':'El 1 está en INGRESOS y ÁREA vacía; se recupera la columna, 218 a 219, sin área numérica.'},
        3885:{'motivo':'Entrega autoras tiene salida 130 legible y saldo 89 desde 219. No se reduce la cantidad por su magnitud.'},
        3888:{'criterios':['T23'],'motivo':'La recepción 90 está en INGRESOS, no ÁREA: 44 a 134. Se recupera la cifra sin crear un área 90.'},
        3917:{'criterios':['T23'],'motivo':'CBBA está en REF y CONSIG en ÁREA. Se guarda consignación como referencia y CBBA en detalle; se conservan las columnas documentales, sin inventar un área Consignación.', 'revision':{'columnas_documentales':{'referencia':'CBBA','area':'CONSIG'}}},
        10122:{'criterios':['T22'],'motivo':'Saldo según inventario 8 es base documental escrita, sin ingreso 8 añadido.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL'}},
        **{id:{'criterios':['T18'],'motivo':'Comillas claras en DETALLE repiten la Feria del libro o Sale a la Feria anterior en esa columna; se conserva la marca.'} for id in (10124,10125,10133,10134,10135)},
        10135:{'criterios':['T18'],'motivo':'Comillas claras repiten Sale a la Feria; el saldo 8 está repasado. Se conserva el trazo anterior sin certificar otra cantidad.', 'revision':{'marcas_documentales':{'saldo':'8 con trazo anterior repasado.'}}},
        10147:{'criterios':['T07'],'motivo':'Devolución Feria escribe 6 en SALIDAS y FERIA en ÁREA; el texto y saldo 1 a 7 sustentan ingreso 6. Se conserva la columna escrita y FERIA en detalle, sin crear un área Feria.', 'revision':{'columna_documental_cantidad':'SALIDAS','interpretacion_cantidad':'INGRESO','cantidad_documental':6,'columnas_documentales':{'area':'FERIA'}}},
        10169:{'criterios':['T05'],'motivo':'La devolución LLALLAGUA escribe INGRESOS 6 y saldo 22 desde 17. El cálculo independiente es 23, no se cambia el 6 a 5 para cuadrar. La diferencia -1 del papel persiste hasta cierre escrito 9 frente a cálculo 10.'},
        10171:{'criterios':['T18'],'motivo':'Comillas inequívocas en ÁREA repiten CEDOAL del FIL anterior; no se crea un alias nuevo.'},
        10180:{'criterios':['T16'],'motivo':'Aunque el texto dice Devolución, hay SALIDA 5 y saldo 10 desde 15. Se conserva el egreso escrito consistente; no se invierte automáticamente todo texto de devolución.'},
    })
    plan=construir(version=29,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(1131,1132,1133,1134),(3878,3879,3880),(3884,3885),(3907,3908),(3909,3910)],
        bases={27:{'primera_fila':1125,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 150, base cero inferida sin recuento acreditado.'},
            69:{'primera_fila':3878,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 175, base cero inferida sin recuento acreditado.'},
            290:{'primera_fila':10122,'saldo_base':8,'origen_saldo_base':'FOTO','motivo_base':'Saldo según inventario 8 escrito, sin ingreso ficticio.'}},
        observaciones=[
            {'articulo_id':27,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos completas y 73 filas cotejadas. Orden documental corregido 3-2-1 manteniendo número original. Se recupera salida 1 de Dossier y devolución 1 escrita en SALIDAS; la anotación (10) no se duplica. Saldo 98 escrito frente a cálculo 90 al final de hoja intermedia y retorno a 85 en la siguiente quedan como discrepancia compensada. Fechas vacías y fuera de orden identificadas. Cierre 75 coincide sin ajuste ficticio.'},
            {'articulo_id':69,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos y 56 filas cotejadas. Ingresos 1 y 90 desplazados por OCR recuperados; salida 130 a autoras y dos obsequios 10 distintos conservados. Fechas fuera de orden, incluso 19-5-14 después de diciembre, mantienen literal y consulta técnica. Cierre 2 coincide.'},
            {'articulo_id':290,'observado':True,'excluir_entrenamiento':True,'motivo':'Tres fotos y 62 filas OCR cotejadas, con renglón totalmente tachado omitido recuperado sin efecto. Base documental 8, fechas parciales y saldos vacíos preservados. Devolución 6 de Feria escrita en SALIDAS se interpreta por contexto; devolución 5 posterior se conserva como salida consistente. Llallagua escribe ingreso 6 pero saldo 22 desde 17; no se cambia el 6 para cuadrar. Diferencia persistente -1: cierre escrito 9 frente a cálculo 10, apertura bloqueada y exclusión del entrenamiento.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={27:75,69:2,290:10},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':1124,'local':8,'acumulada':8},{'id':1078,'local':-8,'acumulada':0},{'id':10169,'local':-1,'acumulada':-1}],plan['cotejo']
    for e in plan['revisiones']:
        if e['articulo_id']==290 and e['id']>=10169:e['revision']['origen_saldo']='HIPOTESIS'
        if e['id']==10183:
            e['cambios']['saldo_registrado']=9;e['revision'].update(usar_saldo_esperado=False,origen_saldo='FOTO')
    plan['recuperaciones']=[recuperada(rows,10183,rows[10183]['orden_fila'],clave='art290-lote-b7086406-p3-fila-tachada-antes10183-v1',
        detalle='FIL (renglón completamente tachado)',fecha='2019-08-12',saldo=11,tipo='ANULADO',
        motivo='Entre FIL-19 y FIL-25 hay una fila totalmente tachada en fecha, detalle, cantidad y saldo, omitida por OCR. Se conserva como evidencia anulada sin certificar las cifras ocultas; fecha y saldo 11 son almacenamiento técnico sin efecto, no lectura documental.')]
    plan['recuperaciones'][0]['campos']['numero_pagina']=3
    plan['cotejo'].update(movimientos=192,cierres={27:75,69:2,290:9},cierres_calculados={27:75,69:2,290:10},
        pendientes_documentales={10183:['saldo']},limites_cierre={290:'Cierre escrito 9 frente a cálculo 10 por ingreso 6 legible y saldo 22 desde 17. Pendiente de conciliación, con apertura bloqueada y artículo excluido del entrenamiento.'})
    return plan

if __name__=='__main__':congelar(generar())
