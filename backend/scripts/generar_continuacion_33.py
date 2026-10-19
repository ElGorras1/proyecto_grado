"""Seis fotos completas: Tambor mayor, Ecológica 52 y Árbol de los cuentos 2."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(7379,7404),[0,-1,-5,5,-1,0,6,-1,-1,-1,-1,10,-1,-2,-3,3,-3,5,-2,-5,-1,-10,-1,2,-1],
  [33,32,27,32,31,28,34,33,None,31,30,40,None,None,34,37,34,39,37,32,31,21,20,22,21]),
 (range(7404,7421),[-2,-3,-3,-1,10,-5,-5,-3,-2,1,-1,-2,-1,-1,2,-2,-1],[19,16,13,12,22,17,12,9,7,8,7,5,4,3,5,3,2]),
 (range(10811,10837),[10,40,-10,-10,3,-5,1,-2,-5,3,-3,-1,-10,-8,5,-3,-1,-2,1,15,-5,5,-3,1,0,-10],
  [10,50,40,30,33,28,29,27,22,25,22,21,11,3,8,5,4,2,3,18,13,18,15,16,None,6]),
 (range(10837,10847),[8,-1,-5,-1,5,-2,-1,-2,2,-2],[14,13,8,7,12,10,9,7,9,7]),
 (range(11560,11586),[20,30,-5,-10,-10,20,-5,4,-2,-5,4,-1,-10,-10,10,-4,1,-3,-1,-1,1,-1,1,-10,9,-2],
  [20,50,45,35,25,45,40,44,42,37,41,40,30,20,30,26,27,24,23,22,23,22,23,13,22,20]),
 (range(11586,11604),[-5,-5,7,5,-10,20,7,-10,9,-2,-21,-2,-5,2,-2,-2,-2,-1],[15,10,17,22,12,32,39,29,38,36,15,13,8,10,8,6,4,3]),
]

def generar():
    snapshot='backups/continuacion_hil_33_20261015/articulos_128_318_368_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    for id,r in rows.items():
        if r['area'] in ('Cedoal','GDOAL','CDOAL','GDOOAL','GEDOAL'):
            cambios[id]={'area':'CEDOAL'};extras[id]={'motivo':'La foto se lee CEDOAL en esta celda; se corrige lectura sin crear áreas ni alias.'}
    for id,fields in {
        7392:{'detalle':'Donación Canciller'},7393:{'fecha_movimiento':'2007-06-15'},
        7396:{'fecha_movimiento':'2007-08-29','detalle':'Devolución Feria','area':None},7407:{'detalle':'Donación Caranavi'},7408:{'area':None},
        **{id:{'detalle':'Feria Libro'} for id in (7410,7411,7412)},
        10831:{'fecha_movimiento':'2011-08-12','area':'CEDOAL'},10832:{'area':'CEDOAL'},10835:{'estado':'ANULADO_DOCUMENTO'},
        10837:{'fecha_movimiento':'2013-11-04'},10841:{'area':None},10845:{'area':None},
        11573:{'detalle':'FERIA INT. LIBRO','area':'CEDOAL'},11576:{'detalle':'FERIA ORURO'},
        11581:{'detalle':'LLALLAGUA','area':'CEDOAL'},11582:{'detalle':'LLALLAGUA'},11594:{'fecha_movimiento':'2013-11-04'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        7379:('2006-06-26','HIPOTESIS',None,'La base escribe 26-6 sin año. Se conserva la lectura parcial; 2006 es contexto previo a enero de 2007, no fecha completa confirmada.'),
        7380:('2006-09-21','HIPOTESIS',None,'21-09 sin año: 2006 es solo gestión técnica de contexto.'),
        7381:('2006-10-06','HIPOTESIS',None,'6-10 sin año: 2006 es solo gestión técnica de contexto.'),
        7382:('2006-11-29','HIPOTESIS',None,'29-11 sin año: 2006 es solo gestión técnica de contexto.'),
        7383:('2006-11-29','HIPOTESIS',None,'14-09 sin año está después de 29-11. Se conserva lectura parcial y consulta técnica del antecedente, sin confirmar el año.'),
        7384:('2006-11-29','HIPOTESIS',None,'Recuento físico 28 no tiene fecha escrita. Se conserva ausencia y consulta técnica del antecedente, sin inventar 1 de diciembre.'),
        7388:('2007-01-17','HIPOTESIS',None,'Vice de Cultura sin fecha propia; consulta técnica del antecedente.'),
        7390:('2007-02-15','HIPOTESIS',None,'La foto escribe 29-02-02, fecha imposible para 2002 y sin base para sustituirla por 28 de febrero de 2007. Se conserva texto literal y consulta técnica del antecedente 15-02-07.'),
        7391:('2007-02-15','HIPOTESIS',None,'Donación Italo tiene FECHA en blanco; consulta técnica del antecedente, cuya fecha imposible no se certifica.'),
        7392:('2007-02-15','HIPOTESIS',None,'Donación Canciller tiene FECHA en blanco; consulta técnica sin atribuir fecha o institución por semejanza.'),
        7394:('2007-06-15','SECUENCIA_AJUSTADA','2007-01-11','11-01-07 aparece después de 15-06-07. Se conserva literal y consulta técnica del antecedente.'),
        7395:('2007-06-15','SECUENCIA_AJUSTADA','2007-01-18','18-01-07 aparece después de 15-06-07. Se conserva literal y consulta técnica del antecedente.'),
        7400:('2007-11-13','SECUENCIA_AJUSTADA','2007-08-01','01-08-07 después de 13-11-07. Se conserva literal y consulta técnica del antecedente.'),
        7402:('2007-11-15','SECUENCIA_AJUSTADA','2007-11-05','5-11-07 después de 15-11-07. Se conserva literal y consulta técnica del antecedente.'),
        10835:('2012-07-19','HIPOTESIS',None,'Fecha y renglón tachados. Se conserva la extracción original y una fecha técnica sin efecto operativo, no fecha documental confirmada.'),
        10843:('2016-12-08','HIPOTESIS',None,'FIL no tiene fecha propia; consulta técnica del antecedente.'),
        11583:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11; literal conservada y consulta técnica del antecedente.'),
        11597:('2016-12-08','HIPOTESIS',None,'FIL no tiene fecha propia; consulta técnica del antecedente.'),
    }
    extras.update({
        7379:{'criterios':['T22'],'motivo':'Saldo según inventario 33 es base documental, sin cantidad de ingreso. No se inventa recepción 33.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL','lectura_fecha_parcial':'26-6, año ausente.'}},
        7384:{'criterios':['T15'],'motivo':'La foto escribe Recuento físico y saldo 28 después de 31. Se toma base 28 conservando diferencia -3, sin salida ficticia ni conteo actual.', 'revision':{'tipo_fila':'RECUENTO','usar_saldo_esperado':False}},
        7387:{'motivo':'Edgar Grandic tiene saldo vacío, no 32 escrito. Se conserva 32 como cálculo hipotético.'},
        7390:{'criterios':['T09'],'motivo':'El texto de FECHA se conserva exactamente como 29-02-02 y se identifica como fecha imposible. No se lo convierte en una fecha válida confirmada.', 'revision':{'fecha_texto_documental':'29-02-02','fecha_documental_imposible':True}},
        7391:{'motivo':'Donación Italo tiene SALDO vacío; 39 es cálculo hipotético, no cifra escrita.'},
        7392:{'criterios':['T18'],'motivo':'La comilla en DETALLE repite Donación, seguida de Canciller; no completa fecha ni saldo ausentes.'},
        7396:{'criterios':['T23'],'motivo':'FERIA está en ÁREA y describe la devolución, no una institución confirmada. Se conserva en detalle y columna literal sin crear área Feria.', 'revision':{'columnas_documentales':{'area':'Feria'}}},
        7408:{'criterios':['T23'],'motivo':'El 10 es INGRESOS, no un área numérica; una sola recepción 10 desde 12 a 22.'},
        **{id:{'criterios':['T18'],'motivo':'Comillas inequívocas en DETALLE repiten Feria Libro en la misma columna. Se conserva la marca sin crear otro evento.'} for id in (7410,7411,7412)},
        **{id:{'criterios':['T02'],'motivo':'La cantidad está en SALIDAS, no INGRESOS: la fotografía muestra el egreso y el saldo decreciente. Se conserva cifra legible.'} for id in (10823,10824)},
        10831:{'criterios':['T14'],'motivo':'SALIDAS tiene 10 tachado y lectura final 5, saldo 13. Se conserva la corrección visible, no dos egresos; la fecha se lee 12-08-11.', 'revision':{'marcas_documentales':{'salidas':'10 tachado y cifra final 5.','saldo':'Cifra anterior tachada y lectura final 13.'}}},
        10832:{'criterios':['T18'],'motivo':'Comillas claras en ÁREA repiten CEDOAL del renglón anterior; se conserva la marca documental.'},
        10835:{'criterios':['T14'],'motivo':'La fila FIL está tachada en fecha, detalle, área, salida y saldo. Se conserva anulada sin efecto; no se certifican las cifras ocultas. La extracción original atribuía salida 8 y saldo 8.'},
        **{id:{'criterios':['T23'],'motivo':'La cifra está en INGRESOS y ÁREA vacía. Se conserva una sola recepción, sin área numérica inventada.'} for id in (10841,10845)},
        10842:{'criterios':['T16'],'motivo':'Aunque el detalle dice Devolución, la foto escribe SALIDA 2 y saldo 10 desde 12. Se conserva el egreso consistente, sin invertirlo automáticamente.'},
        11589:{'criterios':['T01'],'motivo':'La foto escribe INGRESOS 5, no 6. Se recupera el dígito legible y saldo 22 desde 17, sin elegir cifra únicamente por la suma.'},
        11596:{'criterios':['T16'],'motivo':'Devolución tiene SALIDA 21 legible y saldo 15 desde 36. Se conserva el egreso, sin convertir toda devolución en ingreso ni reducir la cantidad por magnitud.'},
    })
    plan=construir(version=33,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={128:{'primera_fila':7379,'saldo_base':33,'origen_saldo_base':'FOTO','motivo_base':'Base documental escrita 33, sin cantidad de ingreso inventada.'},
            318:{'primera_fila':10811,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 10: base cero inferida, sin recuento previo acreditado.'},
            368:{'primera_fila':11560,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 20: base cero inferida, sin recuento previo acreditado.'}},
        observaciones=[
            {'articulo_id':128,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 42 filas cotejadas. Base escrita 33 y recuento físico 28 después de 31 se conservan sin salida ficticia, diferencia -3. Fechas parciales sin año, fecha imposible 29-02-02, celdas vacías y retrocesos siguen identificados; no se fabrica fecha confirmada. Ingreso 10 desplazado a área recuperado; cierre 2 coincide siguiendo el recuento.'},
            {'articulo_id':318,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos y 36 filas cotejadas. Dos salidas extraídas como ingresos corregidas. Fila FIL completamente tachada queda anulada sin efecto; salida 10 corregida a 5 en otra fila no anula su movimiento. Ingresos 5 y 2 sin áreas numéricas, fecha 12-08-11 y 4-11-13 recuperadas. Devolución 2 consistente como salida se conserva. Cierre 7 coincide.'},
            {'articulo_id':368,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos y 44 filas cotejadas. Devolución 5 extraída como 6 corregida visualmente; fecha 4-11-13 recuperada. Devolución con salida 21 legible y saldo 15 se conserva como egreso consistente, no se invierte por su nombre. Áreas CEDOAL y LLALLAGUA corregidas por foto, fechas técnicas identificadas; cierre 3 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={128:5,318:7,368:3},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':7384,'local':-3,'acumulada':-3}],plan['cotejo']
    for e in plan['revisiones']:
        if e['articulo_id']==128 and e['id']>=7384:
            e['cambios']['saldo_registrado']-=3;rev=e['revision'];escrito=rev['saldo_documental'];calc=e['cambios']['saldo_registrado']
            rev['origen_saldo']='HIPOTESIS' if escrito is None else ('FOTO' if escrito==calc else 'RECONSTRUIDO')
            if e['id']==7384:
                rev.pop('diferencia_local_papel',None);rev['hallazgos']=[h for h in rev['hallazgos'] if h!='DESCUADRE_DEL_PAPEL_CONSERVADO']
        if e['id']==10835:
            e['cambios'].update(salidas=rows[10835]['salidas'],saldo_registrado=rows[10835]['saldo_registrado'])
            e['revision'].update(tipo_fila='ANULADO',saldo_documental=None,origen_saldo='HIPOTESIS',origen_cantidades='HIPOTESIS',usar_saldo_esperado=False,
                marcas_documentales={'fila':'Tachaduras en fecha, detalle, área, salida y saldo; cifras ocultas no certificadas.'})
    plan['cotejo'].update(cierres={128:2,318:7,368:3},discrepancias=[],
        recuentos_documentales=[{'id':7384,'previo':31,'escrito':28,'diferencia':-3}],filas_anuladas_preexistentes=[10835])
    return plan

if __name__=='__main__':congelar(generar())
