"""Trencito y Respeto: cinco fotos completas, ocho saldos tapados protegidos."""
import json
from scripts.cotejo_transcripcion_hil import congelar,BACKEND
from scripts.cotejo_con_anclajes_hil import construir_con_anclajes

HOJAS=[
 (range(9210,9236),[6,-4,-2,20,-1,-1,30,-5,-5,-10,-10,22,-3,2,-2,-3,1,-1,20,-10,-10,0,-4,-3,-1,1],[6,2,0,20,19,18,48,43,38,28,18,40,37,39,37,34,35,34,54,44,34,34,30,27,26,27]),
 (range(9236,9261),[-1,1,-10,8,-1,-2,-5,-10,1,1,-2,20,-10,6,-1,-10,20,3,-2,-1,-6,-3,-2,-1,-3],[26,27,17,None,None,None,None,None,None,None,None,None,17,23,22,12,32,35,33,32,26,23,21,20,17]),
 (range(9261,9265),[-1,-1,-2,2],[16,15,13,15]),
 (range(9369,9395),[50,-5,-5,-10,-10,17,-3,3,-2,-3,2,-1,20,-10,-10,0,-4,1,-3,-1,1,-1,1,-10,5,-2],[50,45,40,30,20,37,34,37,35,32,34,33,53,43,33,33,29,30,27,26,27,26,27,17,22,20]),
 (range(9395,9419),[-3,-5,-10,-1,10,-3,20,-10,6,-1,-1,-10,20,2,-1,-7,-6,-2,1,-3,-3,-2,-2,2],[17,12,2,1,11,8,28,18,24,23,22,12,32,34,33,26,20,18,19,16,13,11,9,11]),
]

def generar():
    snapshot='backups/continuacion_hil_64_20261016/articulos_221_228_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    anclajes=list(range(9240,9248))
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area']=='Cedoal'}
    for id,fields in {
        9214:{'detalle':'Emb. Británica'},9215:{'detalle':'Sra. María P. Rincón'},9222:{'detalle':'Feria libro Potosí','referencia':'Ventas'},9224:{'detalle':'F. libro ECUADOR','referencia':'Ventas'},9226:{'fecha_movimiento':'2010-06-11'},9231:{'ingresos':0},9236:{'detalle':'LLALLAGUA'},9237:{'detalle':'LLALLAGUA'},9257:{'fecha_movimiento':'2015-08-03'},9261:{'area':'CEDOAL'},
        9376:{'detalle':'Devolu. F. Libro','referencia':'Potosí'},9384:{'ingresos':0},9417:{'area':'CID'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        9211:('2007-08-08','HIPOTESIS',None,'Para la Feria tiene FECHA vacía; consulta técnica del antecedente sin fecha escrita certificada.'),
        9212:('2007-08-18','HIPOTESIS',None,'Día de 1?-08-07 muy repasado 17/18 no inequívoco; consulta técnica existente conservada, sin decidir por secuencia.'),
        9214:('2008-02-08','HIPOTESIS',None,'Último dígito del año 8-02-0? no inequívoco 07/08; consulta técnica existente conservada, sin certificar por secuencia.'),
        9238:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 aparece después de 02-08-11; literal y orden físico conservados.'),
        9248:('2013-04-22','SECUENCIA_AJUSTADA','2013-04-18','18-4-13 después de 22-4-13; literal conservado y consulta técnica del antecedente.'),
        9259:('2015-09-10','SECUENCIA_AJUSTADA','2015-08-10','10-8-15 después de 10-9-15; agosto literal conservado, sin mover cantidades.'),
        9261:('2016-09-19','HIPOTESIS',None,'Primera FIL de la tercera foto tiene FECHA vacía; consulta técnica del último antecedente, sin copiar 14-8-18 de la fila siguiente.'),
        9392:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','La foto escribe 1-08-11, no 11-08-11; aparece después de 02-08-11. Literal y consulta técnica conservados.'),
        9395:('2012-06-26','SECUENCIA_AJUSTADA','2012-06-25','25-6-12 al comenzar segunda hoja sigue al 26-6-12 de la anterior; literal y orden físico conservados.'),
        9402:('2013-04-22','SECUENCIA_AJUSTADA','2013-04-18','18-4-13 después de 22-4-13; literal y consulta técnica del antecedente conservados.'),
        9413:('2015-09-10','SECUENCIA_AJUSTADA','2015-08-10','10-8-15 después de 10-9-15; recepción 1 legible en INGRESOS y saldo sube 18 a 19. Se conservan columna, literal y consulta técnica.'),
    }
    extras={
        9212:{'criterios':['T16'],'revision':{'fecha_documental_texto':'1?-08-07, día repasado 17/18 no inequívoco.','candidatos_fecha_documental':['2007-08-17','2007-08-18'],'marcas_documentales':{'saldo':'—0—, cero entre guiones.'}}},
        9213:{'criterios':['T16'],'revision':{'anotacion_margen_fecha':'13/12/07 al costado, no atribuida automáticamente al ingreso.'}},
        9214:{'criterios':['T16','T23'],'motivo':'DETALLE se lee Emb. Británica, sin crear alias ni área institucional.', 'revision':{'fecha_documental_texto':'8-02-0?, último dígito 07/08 no inequívoco.','candidatos_fecha_documental':['2007-02-08','2008-02-08']}},
        9215:{'criterios':['T23'],'motivo':'Apellido se lee Rincón, no Rivera, conservado solo como texto documental sin identidad ni alias nuevos.'},
        **{id:{'criterios':['T23'],'motivo':'Ventas ocupa REF y no forma otra área; se recupera columna desde foto.', 'revision':{'columnas_documentales':{'referencia':'Ventas'}}} for id in (9222,9224)},
        9226:{'criterios':['T01'],'motivo':'La foto escribe 11-6-10, no 12-6-10.'},
        **{id:{'criterios':['T23'],'motivo':'Cero numérico en INGRESOS explícito: conservar 0, no vacío ni cancelación.'} for id in (9231,9384)},
        9239:{'criterios':['T14','T16','T19'],'motivo':'Fecha y parte del detalle anteriores tachados, con corrección 17-8-11 al margen y DEVOLUCIÓN legible. Ingreso 8 sigue activo; saldo parcialmente cubierto se conserva hipotético, sin leer debajo del pliegue.', 'revision':{'saldo_documental_cubierto':True,'marcas_documentales':{'fecha':'Corrección marginal 17-8-11 tras tachadura.','detalle':'DEVOLUCIÓN legible junto a texto anterior tachado.'}}},
        **{id:{'criterios':['T19'],'revision':{'saldo_documental_cubierto':True}} for id in anclajes},
        9257:{'criterios':['T01'],'motivo':'La foto escribe 3-8-15, no 8-3-15.'},
        9261:{'criterios':['T23'],'motivo':'ÁREA se lee CEDOAL, no LETRAS; FECHA vacía no se completa desde la fila siguiente.'},
        9376:{'criterios':['T23'],'motivo':'Potosí está en REF, no unido al detalle; columnas visibles conservadas sin crear alias.', 'revision':{'columnas_documentales':{'detalle':'Devolu. F. Libro','referencia':'Potosí'}}},
        9411:{'criterios':['T14'],'motivo':'Último dígito de saldo 20 repasado pero legible, con salida 6. Se conserva fila activa, sin cancelar toda la operación por corrección de una celda.'},
        9413:{'criterios':['T02'],'motivo':'Cantidad 1 está en INGRESOS y saldo pasa de 18 a 19; se conserva recepción aunque el detalle diga FIL.'},
        9417:{'criterios':['T23'],'motivo':'ÁREA se lee CID en esta fotografía, no CCD. Corrección de lectura sin crear alias ni fusionar instituciones.'},
    }
    plan=construir_con_anclajes(version=64,instantanea=snapshot,anclajes=anclajes,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],tipos={},
        bases={221:{'primera_fila':9210,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 6 explícitos; base previa cero inferida, sin recepción adicional.'},228:{'primera_fila':9369,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 50 explícitos; base previa cero inferida, sin recepción adicional.'}},
        observaciones=[
            {'articulo_id':221,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos completas y 55 filas cotejadas; ocho revisiones de saldos cubiertos permanecen íntegras e hipotéticas. Saldo de la fila anterior también parcialmente tapado, sin simular lectura bajo pliegue. Emb. Británica, Rincón, Llallagua y columnas de Ventas recuperados por foto, sin alias. Día/año repasados y FIL sin fecha propia identificados; 11-6-10 y 3-8-15 corregidos, literales fuera de orden conservados. Ingreso cero numérico preservado. Cierre 15 coincide.'},
            {'articulo_id':228,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 50 filas cotejadas. Ingreso cero numérico y recepción 1 del detalle FIL conservados por columna visible, sin invertir por nombre. Literal 1-08-11 corregido del OCR 11-08-11, 25-6-12, 18-4-13 y 10-8-15 posteriores conservan fecha escrita y consulta técnica. Potosí en REF y CID en ÁREA recuperados por foto sin alias; saldo 20 repasado conserva fila activa. Cierre 11 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={221:15,228:11} and plan['cotejo']['discrepancias']==[],plan['cotejo']
    return plan

if __name__=='__main__':congelar(generar())
