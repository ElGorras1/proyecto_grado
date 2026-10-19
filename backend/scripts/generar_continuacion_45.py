"""Cuatro fotografías: Guaraní, Festival disco, Boletín 17 y Ecología 5."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND
from scripts.generar_continuacion_28 import recuperada

HOJAS=[
 (range(7526,7545),[-3,-3,-1,-3,-10,5,-2,-2,-2,1,-5,-1,-5,3,-2,-6,-3,-15,-2],
  [53,50,49,46,36,41,39,37,35,36,31,30,25,28,26,20,17,2,0]),
 (range(8335,8360),[0,-1,-5,-1,2,2,-1,1,-1,-1,-1,1,-5,20,2,-2,-1,-1,1,-1,-2,-2,-1,-3,1],
  [25,24,19,18,20,22,21,7,6,5,4,5,0,20,22,None,19,18,19,18,16,14,13,10,11]),
 (range(8787,8813),[50,-5,-10,-10,-5,-1,-1,-2,1,-2,2,-10,5,-3,-3,2,-5,1,1,-1,-1,10,-8,4,-6,-2],
  [50,45,35,25,20,19,18,16,17,15,17,7,12,9,6,8,3,4,5,4,3,13,5,9,3,1]),
 (range(9783,9795),[0,-2,-1,1,1,0,0,0,0,0,-1,1],[3,1,0,1,2,None,None,None,None,2,1,2]),
]

def generar():
    snapshot='backups/continuacion_hil_45_20261015/articulos_256_134_177_194_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedral','Cedral.','CEDOOL','EODOL','GEDOC')}
    for id,fields in {8336:{'detalle':'Para Colombia'},8337:{'detalle':'Cedoal Oruro'},8338:{'detalle':'Cedoal Oruro'},8339:{'detalle':'Devolución Cedoal'},8340:{'detalle':'Devolución Cedoal'},8341:{'detalle':'Cedoal Colombia'},
        8342:{'detalle':'DEVOL. CEDOAL'},8346:{'fecha_movimiento':'2007-07-11','detalle':'Producción','area':'CEDOAL'},8347:{'detalle':'Para la Feria'},8349:{'detalle':'Devolución Feria','area':None},
        8353:{'referencia':'Potosí','area':'CEDOAL'},8354:{'detalle':'Venta Cedoal'},8355:{'detalle':'Ventas Cedoal'},8356:{'detalle':'Cedoal','referencia':'VENTAS','area':None},
        8798:{'area':'CEDOAL'},8802:{'fecha_movimiento':'2012-07-19','area':'CEDOAL'},9785:{'detalle':'FERIA DEL LIBRO'},9786:{'detalle':'Devolución Feria'},
        9788:{'detalle':'Saldo','referencia':'3','estado':'NOTA_DOCUMENTAL'},9789:{'detalle':'Ingresa','referencia':'1','estado':'NOTA_DOCUMENTAL'},
        9790:{'detalle':'Venta','referencia':'2','estado':'NOTA_DOCUMENTAL'},9791:{'detalle':'Saldo','referencia':'2','estado':'NOTA_DOCUMENTAL'}}.items():cambios.setdefault(id,{}).update(fields)
    for id in range(8342,8360):cambios.setdefault(id,{})['orden_fila']=rows[id]['orden_fila']+1
    tecnicas={
        7526:('2008-05-02','HIPOTESIS',None,'El mes de la primera fecha 21-?-08 está repasado, lectura 4/9 no inequívoca. Consulta técnica del 2-5-08 siguiente sin certificar mes por contexto.'),
        7544:('2017-01-26','HIPOTESIS',None,'FIL 17 carece de FECHA. Consulta técnica del antecedente, sin inventar día del año 2017.'),
        8335:('2006-06-26','HIPOTESIS',None,'26-6 sin año; 2006 es solo contexto de consulta anterior a enero de 2007, no año confirmado.'),
        8336:('2006-09-21','HIPOTESIS',None,'21-09 sin año; contexto 2006 exclusivamente técnico.'),
        8337:('2006-10-06','HIPOTESIS',None,'6-10 sin año; contexto 2006 exclusivamente técnico.'),
        8338:('2006-11-09','HIPOTESIS',None,'9-11 sin año; contexto 2006 exclusivamente técnico.'),
        **{id:('2006-11-29','HIPOTESIS',None,'29-11 sin año en dos renglones distintos. Contexto 2006 exclusivamente técnico; no se deduplican las devoluciones.') for id in (8339,8340)},
        8341:('2006-11-29','HIPOTESIS',None,'14-09 sin año después del 29-11. Se conserva lectura parcial y consulta técnica del antecedente.'),
        8344:('2007-01-17','HIPOTESIS',None,'Vice de Cultura sin fecha propia; consulta técnica del antecedente.'),
        8348:('2007-08-08','HIPOTESIS',None,'Ingresa Cbba. tiene FECHA vacía; consulta técnica del antecedente.'),
        8353:('2007-11-15','SECUENCIA_AJUSTADA','2007-11-05','5-11-07 después de 15-11-07. Literal conservada; nota lateral 14-12-07 no se asigna automáticamente.'),
        **{id:('2008-04-21' if id==8357 else '2008-05-02','HIPOTESIS',None,'Movimiento sin fecha propia; consulta técnica del antecedente, no fecha escrita confirmada.') for id in (8357,8359)},
        8788:('2010-08-19','SECUENCIA_AJUSTADA','2010-08-16','16-08-10 aparece después de ingreso 19-08-10. Se conserva literal y consulta técnica del antecedente.'),
        8798:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','La foto escribe 1-08-11, no 10-11-11. Está después de 02-08-11; literal y consulta técnica del antecedente conservadas.'),
        8801:('2012-06-26','SECUENCIA_AJUSTADA','2012-06-25','25-6-12 después de 26-6-12. Se conserva literal y consulta técnica del antecedente.'),
        9786:('2005-08-21','HIPOTESIS',None,'Devolución Feria tiene FECHA vacía; consulta técnica del antecedente, sin copiar 13-10-05 de la siguiente.'),
        **{id:('2005-10-13','HIPOTESIS',None,'Fila del cuadro sin fecha ni cantidades en INGRESOS/SALIDAS; cifras están en REF. Se conserva como nota pendiente de interpretación, sin inventar operaciones.') for id in range(9788,9792)},
    }
    extras={
        7526:{'criterios':['T16'],'motivo':'Mes inicial repasado se conserva como lectura parcial sin elegir por la secuencia.', 'revision':{'fecha_documental_texto':'21-?-08, mes repasado 4/9 no inequívoco.'}},
        7530:{'criterios':['T02'],'motivo':'10 está en SALIDAS, no INGRESOS. Se corrige la columna OCR: saldo 46 a 36.'},
        7543:{'criterios':['T02','T16'],'motivo':'Devolución tiene SALIDA 15 legible y saldo 2 desde 17. Se corrige ingreso OCR y se conserva egreso, sin invertirlo por el nombre.'},
        8335:{'criterios':['T22'],'motivo':'Saldo según inventario 25 es base documental sin cantidad de ingreso.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL','fecha_documental_texto':'26-6, sin año.'}},
        **{id:{'revision':{'fecha_documental_texto':texto}} for id,texto in ((8336,'21-09, sin año.'),(8337,'6-10, sin año.'),(8338,'9-11, sin año.'),(8339,'29-11, sin año.'),(8340,'29-11, sin año.'),(8341,'14-09, sin año.'))},
        8342:{'criterios':['T16'],'motivo':'Antes de esta devolución hay un 6 sin detalle, fecha ni cantidades, omitido por OCR. No acredita recuento físico ni ajuste. Se recupera como nota sin efecto; no se inventa salida 15 para pasar de 21 a 6. Saldo escrito 7 frente a cálculo 22; diferencia -15 persiste hasta cierre escrito 11 frente a cálculo 26.'},
        8349:{'criterios':['T23'],'motivo':'Feria está escrita en ÁREA y describe la devolución. Se conserva en detalle y columna literal, sin crear área Feria.', 'revision':{'columnas_documentales':{'area':'Feria'}}},
        8353:{'criterios':['T16'],'motivo':'Fecha de celda 5-11-07 y nota lateral 14-12-07 conservadas sin sustituirlas automáticamente.', 'revision':{'anotacion_margen_fecha':'14-12-07 junto a devolución; no reemplaza automáticamente fecha de celda.'}},
        8356:{'criterios':['T23'],'motivo':'Ventas está en ÁREA y describe la operación. Se conserva como referencia, con posición documental; no se inventa área Ventas.', 'revision':{'columnas_documentales':{'area':'Ventas'}}},
        8357:{'criterios':['T16'],'motivo':'Texto personal o de proyección cruza ÁREA y no es inequívoco; se conserva literal, sin fusionar personas e instituciones ni crear alias.'},
        9783:{'criterios':['T22'],'motivo':'Saldo según inventario 3 es base documental, no ingreso fabricado.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL'}},
        9785:{'criterios':['T18'],'motivo':'Comillas en DETALLE repiten Feria del libro; salida 1 distinta se conserva.'},
        **{id:{'criterios':['T16'],'motivo':'La cifra está en REF de un cuadro Saldo/Ingresa/Venta/Saldo, con columnas de cantidades vacías. No se acredita que sean nuevas operaciones. Se conserva nota pendiente sin efecto cuantificado y sin aplicar automáticamente T13, cuya confirmación del titular fue para otras cuatro filas específicas.', 'revision':{'tipo_fila':'NOTA_DOCUMENTAL','columnas_documentales':{'referencia':str(n)},'interpretacion_cuadro_pendiente':True,'origen_cantidades':'HIPOTESIS'}} for id,n in ((9788,3),(9789,1),(9790,2),(9791,2))},
        9792:{'criterios':['T22'],'motivo':'Saldo 2 fechado 16-12-09, sin ingreso ni salida. Se conserva base documental; no se declara recuento físico.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL'}},
    }
    plan=construir(version=45,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={134:{'primera_fila':7526,'saldo_base':56,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primera salida 3 y saldo 53: base 56 inferida sin ingreso ficticio.'},
            177:{'primera_fila':8335,'saldo_base':25,'origen_saldo_base':'FOTO','motivo_base':'Base escrita 25 según inventario, sin cantidad de ingreso.'},
            194:{'primera_fila':8787,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 50; base cero inferida sin recuento acreditado.'},
            256:{'primera_fila':9783,'saldo_base':3,'origen_saldo_base':'FOTO','motivo_base':'Base documental escrita 3, sin cantidad de ingreso.'}},
        observaciones=[
            {'articulo_id':134,'observado':True,'excluir_entrenamiento':False,'motivo':'Una fotografía y 19 filas cotejadas. FIL salida 10 y Devolución salida 15 se corrigen desde ingresos OCR. Mes inicial repasado y FIL 17 sin fecha permanecen técnicos; no se elige mes por frecuencia. Base 56 inferida y cierre cero numérico coincidente.'},
            {'articulo_id':177,'observado':True,'excluir_entrenamiento':True,'motivo':'Una foto y 25 filas OCR cotejadas; cifra 6 aislada omitida recuperada como nota documental sin efecto. Tras saldo 21 aparece 6 sin leyenda ni cantidades y luego devolución 1 escribe 7; no acredita recuento o ajuste. Se conserva diferencia -15 sin salida fabricada: cierre escrito 11 frente a cálculo 26, apertura bloqueada y artículo excluido del entrenamiento. Fechas parciales, vacías y fuera de orden identificadas.'},
            {'articulo_id':194,'observado':True,'excluir_entrenamiento':False,'motivo':'Una foto y 26 filas cotejadas. Se recuperan 1-08-11 y 19-7-12 por fotografía, conservando retrocesos como consulta técnica, CEDOAL recuperado. Ingreso inicial escribe 19-08-10; la venta siguiente 16-08-10 se conserva literal. Cierre 1 coincide.'},
            {'articulo_id':256,'observado':True,'excluir_entrenamiento':True,'motivo':'Una foto y 12 filas cotejadas. Bases escritas 3 y 2 conservadas sin ingresos ficticios. Cuadro Saldo 3/Ingresa 1/Venta 2/Saldo 2 tiene cifras en REF y cantidades vacías: se conserva íntegro como notas pendientes de interpretación, sin efecto cuantificado y sin extender T13 específico a otro caso. Cierre 2 coincide condicionalmente; artículo excluido del entrenamiento hasta aclarar interpretación, sin afirmar bloqueo automático.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={134:0,177:26,194:1,256:2},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':8342,'local':-15,'acumulada':-15}],plan['cotejo']
    for e in plan['revisiones']:
        if e['articulo_id']==177 and e['id']>=8342:e['revision']['origen_saldo']='HIPOTESIS'
        if e['id']==8359:e['cambios']['saldo_registrado']=11;e['revision'].update(usar_saldo_esperado=False,origen_saldo='FOTO')
    nota=recuperada(rows,8341,rows[8341]['orden_fila']+1,clave='art177-cifra6-sinleyenda-antes8342-v1',
        detalle='Cifra 6 sin leyenda, fecha ni cantidades',fecha='2006-11-29',saldo=6,tipo='ANULADO',
        motivo='Antes de DEVOL. CEDOAL se ve únicamente saldo 6 en una fila sin fecha, detalle ni cantidades, omitida por OCR. Se conserva como NOTA_DOCUMENTAL sin efecto, no como renglón tachado ni recuento físico. El cambio desde 21 no está explicado; no se inventa una salida 15 ni otra operación.')
    nota['campos']['estado']='NOTA_DOCUMENTAL';nota['campos']['datos_originales']['saldo_registrado']=6
    nota['revision'].update(tipo_fila='NOTA_DOCUMENTAL',criterios=['T09','T16','T23'],saldo_documental=6,origen_saldo='FOTO')
    plan['recuperaciones']=[nota]
    plan['cotejo'].update(movimientos=83,cierres={134:0,177:11,194:1,256:2},cierres_calculados={134:0,177:26,194:1,256:2},pendientes_documentales={8359:['saldo']},
        limites_cierre={177:'Cierre escrito 11 frente a cálculo 26. Cifra 6 intermedia sin leyenda no acredita recuento ni ajuste; se conserva como nota y no se inventa salida 15. Apertura bloqueada y exclusión del entrenamiento.',
            256:'Cierre escrito 2 coincide condicionalmente sin efecto cuantificado del cuadro con cifras en REF. Interpretación pendiente; artículo excluido del entrenamiento, sin extender T13 a otro caso.'})
    return plan

if __name__=='__main__':congelar(generar())
