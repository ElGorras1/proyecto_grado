"""Once fotos completas; cancelación omitida y cantidades no numéricas conservadas."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND
from scripts.generar_continuacion_28 import recuperada

HOJAS=[
 (range(1310,1336),[246,-15,-1,-3,3,-1,-10,9,-3,1,-2,-1,-3,-1,-1,1,-1,-2,2,-10,10,-1,-1,-5,-1,4],
  [246,231,230,227,230,229,219,228,225,226,224,223,220,219,218,219,218,216,218,208,218,217,216,211,210,214]),
 (range(1336,1362),[-3,-1,-1,-1,-2,-1,2,-5,5,-5,-1,2,-1,-1,1,-1,-1,1,-1,2,-1,-3,3,-5,-1,5],
  [211,210,209,208,206,205,207,202,207,202,201,203,202,201,202,201,200,201,200,202,201,198,201,196,195,200]),
 (range(1362,1381),[-1,-5,-1,5,-2,2,-3,-2,-2,1,3,-1,-1,-1,-4,-1,-1,2,-1],
  [199,194,193,198,196,198,195,193,191,192,195,194,193,192,188,187,186,188,187]),
 (range(1493,1519),[27,6,-1,-1,-3,1,-25,25,-1,-1,-1,-5,4,-1,-1,1,-1,-1,-1,-1,-5,-13,17,-3,3,-3],
  [27,33,32,31,28,29,4,29,28,27,26,21,25,24,23,24,23,22,21,20,15,2,19,16,19,16]),
 (range(1519,1544),[-1,-3,3,-1,-5,4,-5,-1,-3,-1,1,-1,-2,2,-1,24,-1,0,-1,1,-1,2,-1,-3,3],
  [15,12,15,14,9,13,8,7,4,3,4,3,1,3,2,26,25,25,24,25,24,26,25,22,25]),
 (range(1544,1564),[-5,-1,5,-1,-5,-1,5,-2,2,-3,-2,-2,1,-1,3,-1,-1,-4,2,1],[20,19,24,23,18,17,22,20,22,19,17,15,16,15,18,17,16,12,14,15]),
 (range(7552,7578),[0,-1,-1,-1,1,-12,22,-1,-1,-2,-1,-1,1,1,-1,-5,-1,1,-2,39,-2,-1,-2,-2,1,-1],
  [15,14,13,12,13,1,23,22,21,19,18,17,18,19,18,13,12,13,11,50,48,47,45,43,44,43]),
 (range(7578,7604),[-2,-5,3,-2,-2,-2,1,-1,-3,3,-1,-5,4,1,-1,1,-1,1,-5,3,20,-5,3,-6,4,-2],
  [41,36,39,37,35,33,34,33,30,33,32,27,31,32,31,32,31,32,27,30,50,45,48,42,46,44]),
 (range(7604,7614),[-2,-4,-6,-1,-6,-2,-7,-5,-6,-5],[42,38,32,31,25,23,16,11,5,0]),
 (range(11640,11666),[50,-5,-10,-10,13,-5,3,-2,-5,3,-1,-10,-10,7,-4,1,-3,-1,-1,1,-1,1,-8,8,-2,2],
  [50,45,35,25,38,33,36,34,29,32,31,21,11,18,14,15,12,11,10,11,10,11,3,11,9,11]),
 (range(11666,11685),[-5,-4,6,5,-10,20,7,-10,20,9,-1,-2,-30,-2,-2,2,-2,-1,-1],[6,2,8,13,3,23,30,20,40,49,48,46,16,14,12,14,12,11,10]),
]

def generar():
    snapshot='backups/continuacion_hil_56_20261015/articulos_31_36_136_373_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDOOL.','CEDODL','CEDOD','CEDOOL','CDOOL')}
    for id,fields in {
        1312:{'referencia':'CBA'},1313:{'referencia':'Ventas'},1317:{'fecha_movimiento':'2010-09-08'},1318:{'fecha_movimiento':'2010-09-29'},1322:{'referencia':'ESIP'},1326:{'detalle':'QUIÑE'},1327:{'detalle':'LLALLAGUA'},1328:{'detalle':'LLALLAGUA'},1334:{'detalle':'APAC - PALCA'},1337:{'detalle':'COMPRA TRONO'},1351:{'detalle':'LETRAS PACEÑAS'},1353:{'detalle':'LETRAS PACEÑAS'},1356:{'fecha_movimiento':'2013-05-03'},1358:{'detalle':'LARGA NOCHE MUSEOS'},1360:{'detalle':'PATIPIÑA'},1366:{'detalle':'VENTAS - CEDOAL'},
        1493:{'detalle':'Ingresa del depósito Materiales','referencia':None,'area':None},1503:{'detalle':'Donación UMSA'},1508:{'fecha_movimiento':'2008-11-14'},1510:{'detalle':'Dona. Casa de las Américas','referencia':'Cuba'},1512:{'detalle':'C. Interyungueño'},1551:{'detalle':'VENTAS CEDOAL ACTIV.'},1554:{'fecha_movimiento':'2014-07-25'},
        7569:{'area':'CEDOAL'},7587:{'fecha_movimiento':'2010-06-11'},7594:{'detalle':'LLALLAGUA'},7595:{'detalle':'LLALLAGUA'},7605:{'area':'Lucy'},7607:{'detalle':'VENTAS-CEDOAL'},7609:{'detalle':'VENTAS-CEDOAL'},7611:{'detalle':'FIL-2019'},
        11655:{'fecha_movimiento':'2010-10-11'},11660:{'detalle':'LLALLAGUA'},11661:{'detalle':'LLALLAGUA'},11665:{'area':'CEDOAL'},11676:{'fecha_movimiento':'2014-07-29'},11677:{'detalle':'VENTAS-CEDOAL'},
    }.items():cambios.setdefault(id,{}).update(fields)
    for id in range(1528,1544):cambios.setdefault(id,{})['orden_fila']=rows[id]['orden_fila']+1
    tecnicas={
        1329:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 aparece después de 02-08-11; literal y consulta técnica conservadas.'),
        1353:('2013-03-06','SECUENCIA_AJUSTADA','2013-03-05','5-3-13 aparece después de 6-3-13. La foto conserva el día 5, sin cambiarlo al 6.'),
        1374:('2015-02-10','HIPOTESIS',None,'FIL sin fecha propia después de Para Dirección; consulta técnica del antecedente, no fecha escrita.'),
        1494:('2007-12-13','HIPOTESIS',None,'Ingreso devoluciones tiene FECHA vacía; consulta técnica del antecedente. Nota marginal 14-12-07 no se asigna automáticamente.'),
        1500:('2008-04-16','HIPOTESIS',None,'Devolución sin fecha propia; consulta técnica del antecedente, sin certificar el día del retorno.'),
        1502:('2008-05-19','HIPOTESIS',None,'Donación UPEA sin fecha propia; consulta técnica del antecedente.'),
        1538:('2013-03-06','SECUENCIA_AJUSTADA','2013-03-05','5-3-13 aparece después de 6-3-13. Se conserva literal y consulta técnica del antecedente.'),
        **{id:(rows[id]['fecha_movimiento'],'HIPOTESIS',None,'Fecha inicial escrita solo con día y mes, sin año. Gestión 2006 solo técnica por contexto anterior al primer año explícito 2007; no año documental confirmado.') for id in range(7552,7558)},
        7558:('2006-12-15','HIPOTESIS',None,'Ingreso Cedoal tiene FECHA vacía; consulta técnica del antecedente parcial, sin certificar gestión ni día real.'),
        7560:('2007-01-17','HIPOTESIS',None,'Vice de Cultura sin fecha propia; consulta técnica del antecedente 17-01-07.'),
        7564:('2007-06-15','HIPOTESIS',None,'Devolución sin fecha propia; consulta técnica del antecedente 15-06-07.'),
        7567:('2007-10-17','SECUENCIA_AJUSTADA','2007-08-01','01-08-07 aparece después de 17-10-07; se conserva literal y orden físico, sin mover la salida ni cambiar mes.'),
        7569:('2007-11-15','HIPOTESIS',None,'Devolución sin fecha propia; consulta técnica del antecedente 15-11-07.'),
        7596:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 aparece después de 02-08-11; literal y consulta técnica conservadas.'),
        7599:('2012-07-30','SECUENCIA_AJUSTADA','2012-07-24','24-7-12 aparece después de 30-7-12; literal y consulta técnica conservadas.'),
        7608:('2017-05-05','HIPOTESIS',None,'FIL 17 tiene FECHA vacía; consulta técnica del antecedente 5-5-17, no día confirmado.'),
        11656:('2010-10-13','HIPOTESIS',None,'Mes de 13-1?-10 está muy repasado, 10/11 no inequívoco. Consulta técnica existente conservada, sin elegir por otra hoja ni por secuencia.'),
        11662:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 aparece después de 02-08-11; literal y consulta técnica conservadas.'),
        11666:('2012-07-19','SECUENCIA_AJUSTADA','2012-03-24','24-3-12 literal al comenzar segunda hoja después de 19-7-12. Se conserva marzo, sin copiar julio de otro artículo; consulta técnica del antecedente.'),
        11679:('2016-12-08','HIPOTESIS',None,'FIL tiene FECHA vacía después de devolución 8-12-16; consulta técnica del antecedente sin inventar fecha del año siguiente.'),
    }
    extras={
        1317:{'criterios':['T01'],'motivo':'La fotografía escribe 08-09-10 y no 03-09-10.'},1318:{'criterios':['T01'],'motivo':'La foto escribe 29-09-10 y no 29-07-10.'},
        1328:{'criterios':['T14'],'motivo':'Saldo final 218 legible con primer dígito repasado; recepción 2 conservada sin anular la fila.'},
        1356:{'criterios':['T01'],'motivo':'La foto escribe 3-5-13 y no 5-3-13.'},1358:{'criterios':['T18'],'motivo':'Comillas claras en DETALLE repiten LARGA NOCHE MUSEOS, sin añadir operación.'},
        1380:{'criterios':['T14'],'motivo':'Salida final 1 visible junto a marca ennegrecida posterior; no se cuenta 18 ni se anula el egreso.', 'revision':{'marcas_documentales':{'salidas':'1 final junto a cifra anterior ennegrecida.'}}},
        1493:{'criterios':['T23'],'motivo':'Ingreso 27 y saldo 27 están explícitos; depósito Materiales completa la frase que cruza DETALLE/REF/ÁREA, sin nueva institución Materiales ni recepción adicional.', 'revision':{'columnas_documentales':{'detalle':'Ingresa del','referencia':'depósito','area':'Materiales'}}},
        1494:{'criterios':['T16'],'revision':{'anotacion_margen_fecha':'14-12-07 fuera de la celda; no asignada automáticamente.'}},
        1495:{'criterios':['T14'],'motivo':'Marca ennegrecida sin cifra legible en INGRESOS junto a salida 1; no se añade una recepción ni se anula la fila.'},
        **{id:{'criterios':['T16'],'motivo':'Código numérico en ÁREA junto a ESIP conservado pendiente, sin nueva institución numérica.', 'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True}} for id in (1496,1499)},
        1502:{'criterios':['T18'],'motivo':'Comillas en DETALLE repiten Donación, con UPEA como texto del mismo renglón.'},
        1507:{'criterios':['T16'],'motivo':'200 pertenece a REF y Sala a ÁREA; no se toma el código como cantidad.'},1508:{'criterios':['T01'],'motivo':'La foto escribe 14-11-08, no 19-11-08.'},
        1510:{'criterios':['T23'],'motivo':'Cuba está en REF y Casa de las Américas en DETALLE; se conservan columnas sin crear alias.'},
        1536:{'criterios':['T16'],'motivo':'Ventas tiene cruces X en ambas columnas de cantidades y saldo 25 repetido. No hay cantidad numérica acreditada ni anulación de toda la fila. Se conserva sin efecto cuantificado solo como continuidad condicional; artículo excluido del entrenamiento.', 'revision':{'origen_cantidades':'HIPOTESIS','efecto_cuantitativo_no_acreditado':True,'columnas_documentales':{'ingresos':'X','salidas':'X'}}},
        1554:{'criterios':['T01'],'motivo':'La foto escribe 25-7-14 y no 25-5-14.'},
        7552:{'criterios':['T22'],'motivo':'Saldo inventario 15 con cantidades vacías es base documental, sin ingreso ficticio.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL'}},
        **{id:{'criterios':['T16'],'revision':{'fecha_documental_texto':literal}} for id,literal in ((7552,'26-6, sin año.'),(7553,'21-9, sin año.'),(7554,'6-10, sin año.'),(7555,'9-11, sin año.'),(7556,'29-11, sin año.'),(7557,'15-12, sin año.'))},
        7569:{'criterios':['T18'],'motivo':'Comillas claras en ÁREA repiten CEDOAL de la fila anterior.'},
        7573:{'criterios':['T16'],'motivo':'Dos filas 14-08-08 con salidas 2 y 1 son distintas, igual que las dos salidas 2 del 19-08-08; no se deduplican por fecha y texto semejantes.'},
        7587:{'criterios':['T01'],'motivo':'La foto escribe 11-6-10 y no 6-6-10.'},
        11655:{'criterios':['T01'],'motivo':'La foto escribe 11-10-10 y no 14-10-10.'},
        11656:{'criterios':['T16'],'revision':{'fecha_documental_texto':'13-1?-10, mes repasado 10/11 no inequívoco.','candidatos_fecha_documental':['2010-10-13','2010-11-13']}},
        11665:{'criterios':['T18'],'motivo':'Comillas claras en ÁREA repiten CEDOAL, sin nueva área de comillas.'},
        11676:{'criterios':['T01','T14'],'motivo':'La foto escribe 29-7-14, no 7-7-14. Salida 1 y saldo 48 finales legibles junto a trazos anteriores; fila activa conservada.'},
        11678:{'criterios':['T02'],'motivo':'Devolución tiene SALIDA 30 legible y reduce 46 a 16. Se conserva egreso y ADM, sin invertir por el nombre.'},
    }
    # La base documental también conserva su texto de fecha parcial.
    extras[7552].update(criterios=['T16','T22'],motivo='Saldo inventario 15 con cantidades vacías es base documental, sin ingreso ficticio.')
    extras[7552]['revision']['tipo_fila']='BASE_DOCUMENTAL'
    plan=construir(version=56,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={31:{'primera_fila':1310,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 246; base anterior cero inferida.'},
            36:{'primera_fila':1493,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 27; base anterior cero inferida.'},
            136:{'primera_fila':7552,'saldo_base':15,'origen_saldo_base':'FOTO','motivo_base':'Base documental escrita 15 sin cantidad de ingreso.'},
            373:{'primera_fila':11640,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 50; base anterior cero inferida.'}},
        observaciones=[
            {'articulo_id':31,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos completas y 71 filas cotejadas. Fechas 08-09-10, 29-09-10, 5-3-13 y 3-5-13 recuperadas, conservando retroceso literal del 5 de marzo. Comillas de Larga Noche Museos y textos de columnas visibles recuperados, sin alias ni anular filas por correcciones de celda. FIL sin fecha permanece técnico. Cierre 187 coincide.'},
            {'articulo_id':36,'observado':True,'excluir_entrenamiento':True,'motivo':'Tres fotos y 71 filas OCR cotejadas, más fila completamente tachada omitida recuperada sin efecto. Ingreso inicial 27 explícito se conserva y depósito Materiales completa la frase, sin nueva institución. Ventas con X en ambas cantidades tiene efecto no acreditado; se mantiene sin cantidad inventada y artículo excluido. Códigos numéricos de ÁREA, nota lateral, fechas vacías y retrocesos permanecen identificados. Fechas 14-11-08 y 25-7-14 recuperadas. Cierre 15 coincide condicionalmente, sin afirmar bloqueo automático solo por exclusión.'},
            {'articulo_id':136,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos completas y 62 filas cotejadas. Base escrita 15 sin ingreso ficticio; seis fechas iniciales sin año y recepciones o salidas sin fecha propia conservan consultas técnicas. 01-08-07, 1-08-11 y 24-7-12 fuera de orden mantienen literales. Devolución 11-6-10, comillas CEDOAL y Lucy recuperados. Movimientos de igual fecha siguen separados; FIL 17 sin fecha identificado. Cierre cero coincide.'},
            {'articulo_id':373,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 45 filas cotejadas. Fecha 11-10-10 y 29-7-14 recuperadas; mes repasado 10/11 no se certifica por secuencia. Literal 24-3-12 después de 19-7-12 se conserva, sin sustituir marzo por julio de otro artículo. Llallagua, comillas CEDOAL y salida 30 de Devolución cotejados por columna; FIL sin fecha sigue técnico. Cierre 10 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={31:187,36:15,136:0,373:10} and plan['cotejo']['discrepancias']==[],plan['cotejo']
    anulada=recuperada(rows,1527,rows[1527]['orden_fila']+1,clave='art36-donacion-tachada-despues1527-v1',detalle='Donación completamente tachada antes de Eric Altorfer',fecha='2011-01-10',saldo=4,tipo='ANULADO',
        motivo='Después de OBSEQUIO PERSONAL y antes de Eric Altorfer hay un renglón completamente tachado en fecha, detalle, área, cantidad y saldo. Se recupera como ANULADO_DOCUMENTO sin efecto, sin certificar cifras ocultas ni crear operación compensatoria. Fecha 2011-01-10 y saldo 4 son almacenamiento técnico del antecedente, no lectura del renglón.')
    anulada['campos']['numero_pagina']=2
    anulada['revision'].update(fecha_documental_texto='Fecha completamente tachada; no inequívoca.',marcas_documentales={'detalle':'DONACIÓN y texto posterior tachados.','salidas':'Cifra completamente tachada.','saldo':'Cifra completamente tachada.'})
    plan['recuperaciones']=[anulada]
    plan['cotejo'].update(movimientos=250,limites_cierre={36:'Cierre escrito 15 coincide condicionalmente. Ventas con X en ambas cantidades mantiene efecto no acreditado; artículo excluido del entrenamiento, sin afirmar bloqueo automático solo por exclusión.'})
    return plan

if __name__=='__main__':congelar(generar())
