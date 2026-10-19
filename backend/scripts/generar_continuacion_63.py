"""Ocho fotos completas con ámbitos documentales pendientes y una fila anulada omitida."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND
from scripts.generar_continuacion_28 import recuperada

HOJAS=[
 (range(6943,6969),[50,-35,60,-10,-1,-3,40,-10,-1,-1,-1,-1,-6,-2,-6,-1,-2,-2,-1,-3,-2,-4,-3,3,-2,-1],[None,15,75,65,64,61,101,91,90,89,88,87,81,79,73,72,70,68,67,64,62,58,55,58,56,55]),
 (range(6969,6983),[-4,-2,-2,-2,-2,-3,-2,-3,-7,-2,-2,-2,2,-10],[51,49,47,45,43,40,38,35,28,26,24,22,24,14]),
 (range(8406,8432),[20,-3,-3,-2,-2,-1,-1,-1,-4,10,-8,-4,20,-3,-10,-5,-1,5,-1,-1,-2,1,-2,2,-2,15],[20,17,14,12,10,9,8,7,3,13,5,1,21,18,8,3,2,7,6,5,3,4,2,4,2,17]),
 (range(8432,8441),[-3,1,-5,-8,9,-1,-1,-7,-1],[14,15,10,2,11,10,9,2,1]),
 (range(8891,8917),[20,20,-5,-13,13,-2,-2,2,-2,-2,-3,3,-1,-5,0,-1,1,-1,15,-10,8,-3,-1,-2,-5,6],[20,20,15,2,15,13,11,13,11,9,6,9,8,3,3,2,3,2,17,7,15,12,11,9,4,10]),
 (range(8917,8938),[2,-1,-1,-6,-2,4,-2,-2,10,-6,5,-5,-4,-2,15,-1,-3,2,-2,-6,-4],[12,11,10,4,2,6,4,2,10,4,11,6,2,0,15,14,11,13,11,5,1]),
 (range(11395,11421),[20,-5,30,-5,-10,-10,17,-5,5,-2,-5,4,-1,-10,-10,10,-4,1,-3,-1,-1,1,-1,1,-10,6],[20,15,50,45,35,25,42,37,42,40,35,39,38,28,18,28,24,25,22,21,20,21,20,21,11,17]),
 (range(11421,11441),[-2,2,-5,-5,9,5,-10,8,-10,10,-1,-1,-2,-2,-2,-2,2,-2,-1,-1],[15,17,12,7,16,21,11,19,9,19,18,17,15,13,11,9,11,9,8,7]),
]

def generar():
    snapshot='backups/continuacion_hil_63_20261016/articulos_100_181_199_356_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDOOL','CDOAL','CSDOAL')}
    for id,fields in {
        6946:{'fecha_movimiento':'2015-09-29'},6959:{'fecha_movimiento':'2017-04-20'},6968:{'fecha_movimiento':'2021-10-01'},
        8418:{'referencia':'Cbba.','area':None},8420:{'detalle':'FERIA INTER. LIBRO'},8424:{'area':'GALERIA'},8428:{'detalle':'LLALLAGUA'},8429:{'detalle':'LLALLAGUA'},8431:{'referencia':'CBB','area':None},
        8893:{'fecha_movimiento':'2009-08-07'},8905:{'ingresos':0},
        11417:{'detalle':'LLALLAGUA'},11418:{'detalle':'LLALLAGUA'},11420:{'fecha_movimiento':'2011-08-17'},11438:{'detalle':'VENTAS-ESIP'},
    }.items():cambios.setdefault(id,{}).update(fields)
    for id in range(8933,8938):cambios.setdefault(id,{})['orden_fila']=rows[id]['orden_fila']+1
    tecnicas={
        6951:('2015-10-30','SECUENCIA_AJUSTADA','2015-10-29','29-10-15 aparece después de 30-10-15; literal y consulta técnica del antecedente conservados.'),
        6960:('2017-04-20','HIPOTESIS',None,'FIL tiene FECHA vacía después de La Paz Lee del 20-4-17; no fecha propia certificada.'),
        6974:('2023-06-12','SECUENCIA_AJUSTADA','2023-03-07','7-3-23 aparece después de 12-6-23; se conserva marzo literal, sin cambiarlo para ordenar.'),
        8430:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11; literal y consulta técnica conservados.'),
        8892:('2009-07-30','SECUENCIA_AJUSTADA','2009-07-24','24-7-09 después del primer ingreso 30-7-09; conservar ambas filas y fechas literales, sin deduplicar.'),
        8929:('2016-09-19','HIPOTESIS',None,'FIL sin fecha propia; consulta técnica del antecedente, no fecha documental.'),
        11397:('2009-07-29','SECUENCIA_AJUSTADA','2009-07-17','17-7-09 después de la fila 29-7-09 entre paréntesis; literal y orden físico conservados, sin anular ni fusionar filas para ordenar.'),
        11419:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11; literal y consulta técnica conservados.'),
        11434:('2015-09-17','HIPOTESIS',None,'FIL tiene FECHA vacía; consulta técnica del antecedente, sin inventar otra gestión.'),
    }
    extras={
        6943:{'criterios':['T19'],'motivo':'Saldo inicial está parcialmente cubierto por papel adherido. Ingreso 50 legible; saldo calculado 50 solo hipotético, sin afirmar lectura bajo la cubierta.', 'revision':{'saldo_documental_cubierto':True}},
        6946:{'criterios':['T01'],'motivo':'La foto escribe 29-9-15, no 28-9-15.'},6959:{'criterios':['T01'],'motivo':'La foto escribe 20-4-17, no 2-4-17.'},6968:{'criterios':['T01'],'motivo':'La foto escribe 1-10-21, no 10-1-21.'},
        6980:{'criterios':['T14'],'motivo':'Salida 2 final legible junto a marca ennegrecida; no se anula el renglón ni se añade otra salida.'},
        6981:{'criterios':['T16'],'motivo':'Devolución ingreso 2 está acreditada. Nombre posterior BROMOA/BROMDA no inequívoco; lectura vigente conservada como texto pendiente, sin alias.', 'revision':{'detalle_documental_ambiguo':True,'candidatos_detalle_documental':['DEVOLUCIÓN BROMOA','DEVOLUCIÓN BROMDA']}},
        8418:{'criterios':['T23'],'motivo':'Cbba. está en REF, no ÁREA; se recupera columna desde foto sin crear institución.', 'revision':{'columnas_documentales':{'referencia':'Cbba.','area':None}}},
        8419:{'criterios':['T14'],'motivo':'Salida final 3 y saldo 18 finales legibles junto a cifras anteriores tachadas; no se anula toda la fila.'},
        8431:{'criterios':['T23'],'motivo':'Procedencia CBB en ÁREA del ingreso se conserva en referencia con su columna original, sin nueva institución.', 'revision':{'columnas_documentales':{'area':'CBB'}}},
        8892:{'criterios':['T05','T21'],'motivo':'Dos filas físicas distintas escriben ingreso 20 y saldo 20 cada una con fechas diferentes. No se elimina ni fusiona una por similitud; al conservar ambas, cálculo 40 frente a segundo saldo 20, diferencia -20 de ámbito pendiente.', 'revision':{'posible_duplicidad_documental':True,'ambito_ingresos_pendiente':True}},
        8905:{'criterios':['T23'],'motivo':'INGRESOS escribe cero numérico; se conserva 0, no vacío ni fila cancelada.'},
        8925:{'criterios':['T04','T16'],'motivo':'Celda principal escribe saldo 10 y anotación marginal 12; se conservan ambas lecturas. No se inventa salida 2 para cuadrar.', 'revision':{'saldo_corregido_margen':12,'anotacion_margen':'12 junto al saldo principal 10.'}},
        8926:{'criterios':['T04','T16'],'motivo':'Celda principal escribe saldo 4 y anotación marginal 6; se conservan ambas. El siguiente ingreso 5 escribe 11 y compensa la diferencia local, sin recuento ni operación adicional.', 'revision':{'saldo_corregido_margen':6,'anotacion_margen':'6 junto al saldo principal 4.'}},
        11396:{'criterios':['T03','T16','T21'],'motivo':'Renglón completo Feria del libro, salida (5) y saldo (15) están entre paréntesis, sin tachadura inequívoca. (15) no es -15. Ámbito como operación/anotación pendiente: se conserva salida vigente 5 solo hipotética, sin anular ni fusionar con otra salida 5 del mismo día. No se resuelve únicamente por la suma.', 'revision':{'origen_cantidades':'HIPOTESIS','ambito_parentesis_pendiente':True,'marcas_documentales':{'detalle':'(Feria del libro)','salidas':'(5)','saldo':'(15)'}}},
        11397:{'criterios':['T05'],'motivo':'Conservando provisionalmente la salida 5 entre paréntesis, ingreso 30 escribe saldo 50 frente a cálculo condicional 45. Diferencia +5 de ámbito pendiente; no se inventa recepción 5 ni se declara anulación tácita.'},
        11420:{'criterios':['T01'],'motivo':'La foto escribe 17-08-11, no 12-08-11.'},
    }
    plan=construir(version=63,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={aid:{'primera_fila':id,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':f'Primer ingreso {q} legible; base previa cero inferida, sin recepción adicional.'} for aid,id,q in ((100,6943,50),(181,8406,20),(199,8891,20),(356,11395,20))},
        observaciones=[
            {'articulo_id':100,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 40 filas cotejadas. Saldo inicial parcialmente cubierto conserva hipótesis, sin leer bajo el adhesivo. Fechas 29-9-15, 20-4-17 y 1-10-21 recuperadas; 29-10-15 y 7-3-23 fuera de orden conservan literal. FIL sin fecha propio identificado. Devolución 2 acreditada pero nombre BROMOA/BROMDA pendiente; corrección de celda no anula fila. Cierre 14 coincide.'},
            {'articulo_id':181,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 35 filas cotejadas. Columnas Cbba./CBB, GALERIA y Llallagua recuperadas desde foto, sin alias. Salida 3 y saldo 18 corregidos sobre celdas no anulan toda la fila. Literal 1-08-11 posterior a 02-08-11 conserva fecha escrita y consulta técnica. Cierre 1 coincide.'},
            {'articulo_id':199,'observado':True,'excluir_entrenamiento':True,'motivo':'Dos fotos completas y 47 filas OCR cotejadas, más renglón completamente tachado omitido recuperado sin efecto. Dos ingresos iniciales 20 con saldos 20 se conservan separados, con ámbito pendiente y diferencia -20 al contarlos ambos. Saldo principal 10/4 y correcciones marginales 12/6 conservados; la diferencia local -2 se compensa en ingreso 5/saldo 11, sin inventar ajustes. Cero numérico de ingreso preservado. Cierre escrito 1 frente a cálculo condicional 21, artículo excluido y apertura bloqueada. No se elimina una recepción por similitud.'},
            {'articulo_id':356,'observado':True,'excluir_entrenamiento':True,'motivo':'Dos fotos completas y 46 filas cotejadas. Fila completa entre paréntesis conserva salida vigente 5 solo hipotética y saldo documental (15), no negativo -15. Ámbito operación/anotación pendiente, sin anulación ni deduplicación por suma. Con esa salida, ingreso 30 escribe 50 frente a cálculo 45; cierre escrito 7 frente a cálculo condicional 2, exclusión y apertura bloqueada. Fechas fuera de orden, FIL sin fecha y 17-08-11 OCR corregido conservados.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={100:14,181:1,199:21,356:2},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':8892,'local':-20,'acumulada':-20},{'id':8925,'local':-2,'acumulada':-22},{'id':8927,'local':2,'acumulada':-20},{'id':11397,'local':5,'acumulada':5}],plan['cotejo']['discrepancias']
    for id,escrito in ((8937,1),(11440,7)):
        cierre=next(e for e in plan['revisiones'] if e['id']==id)
        cierre['cambios']['saldo_registrado']=escrito;cierre['revision'].update(usar_saldo_esperado=False,origen_saldo='FOTO')
    anulada=recuperada(rows,8932,rows[8932]['orden_fila']+1,clave='art199-fila-tachada-despues8932-v1',detalle='Renglón completamente tachado antes de FIL LP 9-9-21',fecha='2019-08-12',saldo=34,tipo='ANULADO',motivo='Fila completamente tachada en FECHA, DETALLE, ÁREA, SALIDAS y SALDO entre FIL-2019 y FIL LP 9-9-21. Se recupera ANULADO_DOCUMENTO sin efecto; fecha y saldo son técnicos del antecedente, no lectura de lo tachado ni nueva operación.')
    anulada['campos']['numero_pagina']=2
    anulada['revision']['marcas_documentales']={'fecha':'Completamente tachada.','detalle':'Completamente tachado.','area':'Completamente tachada.','salidas':'Cifra ennegrecida.','saldo':'Cifra ennegrecida.'}
    plan['recuperaciones']=[anulada]
    plan['cotejo'].update(movimientos=169,cierres={100:14,181:1,199:1,356:7},cierres_calculados={100:14,181:1,199:21,356:2},pendientes_documentales={8937:['saldo'],11440:['saldo']},limites_cierre={199:'Cierre escrito 1 frente a cálculo condicional 21, con dos ingresos iniciales de ámbito pendiente y correcciones marginales conservadas. Exclusión y apertura bloqueada.',356:'Cierre escrito 7 frente a cálculo condicional 2, pendiente el ámbito de la fila completa entre paréntesis. Exclusión y apertura bloqueada; no se anula ni fusiona por aritmética.'})
    return plan

if __name__=='__main__':congelar(generar())
