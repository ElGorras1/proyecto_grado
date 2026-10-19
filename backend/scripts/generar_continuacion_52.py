"""Seis fotos completas de cinco artículos con avisos, sin nuevas extracciones."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(510,534),[0,-1,-1,-3,1,-1,13,2,-1,-1,-1,-1,-3,-5,4,-1,-1,-1,-2,2,-2,1,-1,1],
  [5,4,3,None,1,None,13,15,14,13,12,11,8,3,7,6,5,4,2,4,2,3,2,3]),
 (range(7245,7266),[10,-5,-2,-3,2,15,-10,8,-3,-2,1,5,-5,3,-1,-1,-5,-2,-2,1,-3],
  [10,5,3,None,2,17,7,15,12,10,11,16,11,14,13,12,7,5,3,4,1]),
 (range(8028,8054),[-3,3,-1,-10,10,-1,1,-1,1,-10,4,-3,-2,20,-5,4,1,-10,7,-2,1,-10,-2,-13,-3,-2],
  [23,26,25,15,25,24,25,24,25,15,19,16,14,34,29,33,34,24,31,29,30,20,18,5,2,0]),
 (range(11685,11710),[20,-10,9,-3,-2,1,-5,-5,7,1,-10,20,9,-10,20,10,-1,-2,-34,-1,-2,2,-2,-2,-1],
  [20,10,19,16,14,15,10,5,12,13,3,23,32,22,42,52,51,49,15,14,12,14,12,10,9]),
 ([11710],[-1],[8]),
 (range(12098,12124),[0,10,-2,-5,-5,-3,-2,20,-2,-2,2,-4,20,-10,-3,-10,8,-3,3,-2,-1,-2,2,-3,12,-10],
  [7,17,None,None,None,None,0,20,None,16,18,14,34,None,None,11,19,None,19,None,16,14,16,13,25,15]),
]

def generar():
    snapshot='backups/continuacion_hil_52_20261015/articulos_9_118_154_374_394_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CSODAL','CSODAL.','COSHL','CDOAL','CIDOAL','Cedid','Ciudad')}
    for id,fields in {
        521:{'detalle':'C. Interyungueño'},7250:{'referencia':'SC','area':None},7251:{'referencia':'CEDOAL'},7259:{'detalle':'Dr. MARIANO BAPTISTA'},7260:{'detalle':'CEDOAL'},8046:{'detalle':'FIL'},
        11685:{'referencia':'STC','area':None},11688:{'detalle':'VENTAS'},11690:{'area':'CEDOAL'},11695:{'detalle':'FERIA INFANTIL'},11702:{'detalle':'VENTAS-CEDOAL'},11703:{'area':'ADM'},
        12106:{'detalle':'Cedoal Feria Sopocachi'},12107:{'detalle':'Cedoal Paraguay'},12108:{'detalle':'Devolución - Cedoal Feria'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        510:('2007-12-19','HIPOTESIS',None,'La base Recuento físico no tiene fecha en su celda. Nota lateral 19-12-07 conservada sin asignación automática; consulta técnica de contexto.'),
        512:('2008-01-15','SECUENCIA_AJUSTADA','2008-01-05','La foto escribe 5-01-08 después del 15-01-08. Se conserva literal, sin copiar marzo de otra hoja parecida; consulta técnica del antecedente.'),
        7257:('2012-07-30','SECUENCIA_AJUSTADA','2012-07-24','24-7-12 aparece después de ingreso 30-7-12; literal y consulta técnica conservadas.'),
        8037:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 aparece después de 02-08-11; literal y consulta técnica del antecedente conservadas.'),
        8042:('2012-07-30','SECUENCIA_AJUSTADA','2012-07-24','24-7-12 aparece después de ingreso 30-7-12. Literal y consulta técnica conservadas.'),
        8052:('2016-09-19','HIPOTESIS',None,'FIL 17 tiene FECHA vacía. Consulta técnica del antecedente, sin confirmar fecha del año 2017.'),
        11704:('2016-12-08','HIPOTESIS',None,'FIL tiene FECHA vacía; consulta técnica del antecedente sin inventar día de 2017.'),
        **{id:('2005-07-05','HIPOTESIS',None,'La base escribe únicamente 7-05, fecha parcial no inequívoca; las filas siguientes tienen FECHA vacía. Se conserva consulta técnica existente sin certificar día, mes y año completos.') for id in range(12098,12105)},
        **{id:('2006-10-11','HIPOTESIS',None,'Movimiento sin fecha propia; consulta técnica del antecedente explícito 11-10-06, no fecha escrita confirmada.') for id in range(12106,12115)},
        12115:('2006-10-11','SECUENCIA_AJUSTADA','2006-10-06','6-10-06 aparece después de 11-10-06. Se conserva literal y consulta técnica del antecedente.'),
    }
    extras={
        510:{'criterios':['T15','T22'],'motivo':'El papel dice Recuento físico y saldo 5 con cantidades vacías. Se conserva como base histórica inicial procedente de ese recuento escrito; no acredita recuento actual ni diferencia respecto de una cadena anterior desconocida.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL','recuento_documental_inicial':True,'anotacion_margen_fecha':'19-12-07, fuera de la celda de FECHA.'}},
        **{id:{'criterios':['T16'],'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'Código numérico escrito en ÁREA junto a ESIP se conserva pendiente de interpretación, sin crear institución numérica.'} for id in (512,513)},
        **{id:{'criterios':['T08'],'motivo':'SALDO es guion, no cero numérico escrito. Se conserva ausencia de cifra documental y cálculo cero hipotético.', 'revision':{'saldo_documental_texto':'Guion.'}} for id in (513,515,7248)},
        531:{'criterios':['T02'],'motivo':'Devolución escribe 1 en INGRESOS, no SALIDAS; se corrige columna OCR con saldo 2 a 3.'},
        7250:{'criterios':['T23'],'motivo':'SC está en ÁREA como procedencia literal de recepción. Se conserva como referencia y posición documental, sin crear nueva área abreviada.', 'revision':{'columnas_documentales':{'area':'SC'}}},
        7251:{'criterios':['T23'],'motivo':'La foto escribe CEDOAL tanto en REF como en ÁREA; se recuperan ambas lecturas, conservando su doble posición documental.', 'revision':{'columnas_documentales':{'referencia':'CEDOAL','area':'CEDOAL'}}},
        7259:{'motivo':'La foto escribe Dr. MARIANO BAPTISTA, sin crear identidad ni alias.'},
        7262:{'criterios':['T16'],'motivo':'Dos salidas 2 del mismo día son renglones distintos, con saldos 5 y 3; no se deduplican por semejanza.'},
        11685:{'criterios':['T23'],'motivo':'STC aparece en ÁREA como procedencia literal de recepción. Se conserva como referencia y columna documental, sin crear institución abreviada.', 'revision':{'columnas_documentales':{'area':'STC'}}},
        11690:{'criterios':['T18'],'motivo':'Comillas claras en ÁREA repiten CEDOAL, sin nueva área de comillas.'},
        11703:{'criterios':['T02'],'motivo':'Devolución escribe SALIDA 34 legible, no INGRESO 34; reduce 49 a 15. Se corrige columna OCR, sin invertir el sentido por su nombre. ÁREA visible ADM, no DOM.'},
        12098:{'criterios':['T22'],'motivo':'Saldo según inventario 7 con cantidades vacías es base documental sin ingreso ficticio.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL','fecha_documental_texto':'7-05, fecha parcial no inequívoca.'}},
        12101:{'criterios':['T14'],'motivo':'Cantidad 5 visible con trazo repasado en SALIDAS se conserva; una corrección de celda no anula el renglón.'},
        **{id:{'criterios':['T08'],'motivo':'SALDO está vacío en esta fila; el cálculo es hipótesis y no cifra escrita.'} for id in (12100,12101,12102,12103,12106,12111,12112,12115,12117)},
        12117:{'criterios':['T01','T08'],'motivo':'La foto escribe SALIDA 2, no 3, y deja SALDO vacío. Se recupera cantidad por columna visible; cálculo 17 hipotético, sin completar la celda.'},
        12104:{'motivo':'Se conserva el cero numérico escrito entre guiones, distinto de una celda vacía.'},
    }
    plan=construir(version=52,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={9:{'primera_fila':510,'saldo_base':5,'origen_saldo_base':'FOTO','motivo_base':'Base inicial escrita 5 procedente de recuento documental, sin ingreso ficticio ni cadena previa acreditada.'},
            118:{'primera_fila':7245,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 10; base anterior cero inferida, sin recuento previo.'},
            154:{'primera_fila':8028,'saldo_base':26,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primera salida 3 y saldo 23; base 26 inferida, sin recepción inventada.'},
            374:{'primera_fila':11685,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 20; base anterior cero inferida.'},
            394:{'primera_fila':12098,'saldo_base':7,'origen_saldo_base':'FOTO','motivo_base':'Base documental escrita 7 sin cantidad de ingreso.'}},
        observaciones=[
            {'articulo_id':9,'observado':True,'excluir_entrenamiento':False,'motivo':'Una foto completa y 24 filas cotejadas. Base inicial 5 procedente de recuento físico escrito conservada sin ingreso ni recuento actual; fecha de celda vacía con nota lateral identificada. Devolución 1 es ingreso por columna visible. Guiones de saldo y códigos en área quedan identificados; 5-01-08 literal no se cambia a marzo por otra hoja parecida. Cierre 3 coincide.'},
            {'articulo_id':118,'observado':True,'excluir_entrenamiento':False,'motivo':'Una foto completa y 21 filas cotejadas. Guion de saldo no se certifica como cero; CEDOAL en REF/ÁREA, SC como procedencia y Mariano Baptista recuperados por foto sin alias nuevos. Dos salidas 2 del mismo día permanecen distintas; 24-7-12 fuera de orden conserva literal. Cierre 1 coincide.'},
            {'articulo_id':154,'observado':True,'excluir_entrenamiento':False,'motivo':'Una foto completa y 26 filas cotejadas. CEDOAL recuperado, fechas 1-08-11 y 24-7-12 fuera de orden conservan literal y consulta técnica. FIL 17 sin fecha y base 26 inferida siguen identificados; cierre cero numérico coincide.'},
            {'articulo_id':374,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 26 filas cotejadas. Devolución salida 34 extraída como ingreso corregida por columna visible, con ADM y saldo 49 a 15. Comillas de CEDOAL y procedencia STC conservadas; FIL sin fecha sigue técnico. Cierre 8 escrito en 2025 coincide.'},
            {'articulo_id':394,'observado':True,'excluir_entrenamiento':False,'motivo':'Una foto completa y 26 filas cotejadas. Base escrita 7 sin ingreso ficticio; muchos saldos vacíos y fechas ausentes o parciales conservados. Para la Venta escribe salida 2, no 3, con saldo vacío; no se completa la celda. Cero escrito entre guiones conservado, 6-10-06 fuera de orden identificado y CEDOAL recuperado del OCR. Artículo separado de Los primeros 30 según confirmación del titular. Cierre 15 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={9:3,118:1,154:0,374:8,394:15} and plan['cotejo']['discrepancias']==[],plan['cotejo']
    # La corrección de una celda conserva también su trazo documental junto a la ausencia del saldo.
    next(e for e in plan['revisiones'] if e['id']==12101)['revision'].setdefault('marcas_documentales',{})['salidas']='5 con trazo repasado; fila conservada.'
    return plan

if __name__=='__main__':congelar(generar())
