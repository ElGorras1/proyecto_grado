"""Taller 2: tres fotografías y recuento físico escrito conservado."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(8529,8553),[0,-3,-2,3,-1,0,-1,-1,-1,1,3,-2,1,-1,-1,48,-3,2,-1,-1,-1,-8,-5,-5],
  [10,None,5,8,4,3,2,None,0,1,4,2,3,2,1,49,46,48,47,46,45,37,32,27]),
 (range(8553,8579),[10,-1,-1,-1,-2,-5,5,-5,-2,-4,-3,3,-1,-10,8,1,-1,-1,-1,1,-2,2,-10,6,-2,1],
  [37,36,35,34,32,27,32,27,25,21,18,21,20,10,18,19,18,17,16,17,15,17,7,13,11,12]),
 (range(8579,8592),[10,-5,5,2,-10,8,-1,-1,-1,-2,-2,-2,-1],[22,17,22,24,14,22,21,20,19,17,15,13,12]),
]

def generar():
    snapshot='backups/continuacion_hil_43_20261015/articulo_186_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDCAL')}
    for id,fields in {8529:{'referencia':None},8540:{'referencia':None,'area':'CEDOAL'},8541:{'fecha_movimiento':'2007-11-05','referencia':None,'area':'CEDOAL'},
        8542:{'detalle':'Pro. Culto Bunker'},8543:{'referencia':None,'area':'CEDOAL'},8547:{'referencia':None,'area':'CEDOAL'},
        8548:{'referencia':None,'area':'CEDOAL'},8549:{'detalle':'C. Inter Yungueña','referencia':None,'area':'CEDOAL'},
        8550:{'detalle':'Municipios Sucre','referencia':'Sala','area':'Dirección'},8551:{'referencia':None,'area':'CEDOAL'},8552:{'referencia':None,'area':'CEDOAL'},
        8558:{'detalle':'Feria de libro Potosí','referencia':'Ventas','area':'CEDOAL'},8569:{'detalle':'CBA TARIJA','referencia':'OBSEQUIO'},
        8573:{'detalle':'LLALLAGUA'},8574:{'detalle':'LLALLAGUA'},8585:{'fecha_movimiento':'2014-07-29'}}.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        8529:('2006-06-26','HIPOTESIS',None,'26-6 sin año. Contexto 2006 anterior a enero de 2007 solo para consulta; no gestión 2010 confirmada.'),
        8530:('2006-10-06','HIPOTESIS',None,'6-10 sin año. Consulta técnica 2006 por contexto, sin certificar año.'),
        8531:('2006-10-11','HIPOTESIS',None,'11-10 sin año. Consulta técnica 2006 por contexto, sin certificar año.'),
        8532:('2006-11-29','HIPOTESIS',None,'29-11 sin año. Consulta técnica 2006 por contexto, sin certificar año.'),
        8533:('2006-11-29','HIPOTESIS',None,'14-09 sin año después del 29-11 sin año. Se conserva texto parcial y consulta técnica del antecedente.'),
        8534:('2006-11-29','HIPOTESIS',None,'Según recuento físico no tiene fecha propia; consulta técnica del antecedente sin inventar fecha de conteo.'),
        **{id:('2007-01-17','HIPOTESIS',None,'Vice de Cultura o devolución sin fecha propia; consulta técnica del antecedente.') for id in (8537,8538)},
        8575:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11. Se conserva literal y consulta técnica del antecedente.'),
        8580:('2012-07-30','SECUENCIA_AJUSTADA','2012-07-24','24-7-12 después de 30-7-12. Se conserva literal y consulta técnica del antecedente.'),
        8588:('2016-10-10','HIPOTESIS',None,'FIL 17 tiene fecha vacía; consulta técnica del antecedente, sin fabricar día del año 2017.'),
    }
    extras={
        8529:{'criterios':['T22'],'motivo':'Saldo según inventario 10 solo es base documental; no se añade un ingreso 10.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL','fecha_documental_texto':'26-6, sin año.'}},
        8530:{'revision':{'fecha_documental_texto':'6-10, sin año.'}},8531:{'revision':{'fecha_documental_texto':'11-10, sin año.'}},8532:{'revision':{'fecha_documental_texto':'29-11, sin año.'}},
        8533:{'criterios':['T05'],'motivo':'Cedoal Colombia escribe salida 1 desde saldo 8, pero saldo tenue 4. Se conservan cantidad 1 y lectura 4 frente a cálculo 7; no se cambia la cantidad a 4 para cuadrar.', 'revision':{'fecha_documental_texto':'14-09, sin año.'}},
        8534:{'criterios':['T15'],'motivo':'El papel dice Según recuento físico y saldo 3, sin cantidades. El recuento reemplaza la base de consulta 7 y conserva diferencia -4; no se fabrica salida 4 ni se declara conteo actual.', 'revision':{'tipo_fila':'RECUENTO','diferencia_con_cadena_previa':-4,'saldo_anterior_cadena':7}},
        8541:{'criterios':['T01','T16'],'motivo':'La fecha de la celda es 5-11-07, no 15-11-07. Se conserva además anotación lateral 19-12-07 sin sustituirla automáticamente por la fecha de la celda.', 'revision':{'anotacion_margen_fecha':'19-12-07 junto al saldo, no sustituye automáticamente la fecha de la celda.'}},
        8550:{'criterios':['T23'],'motivo':'Sala está en REF y Dirección en ÁREA. Se recuperan ambas columnas sin atribuir responsable personal.'},
        8558:{'criterios':['T23'],'motivo':'Ventas está en REF y CEDOAL en ÁREA; el OCR había desplazado el texto entre detalle y referencia. Se recuperan las columnas visibles.'},
        8585:{'criterios':['T01'],'motivo':'La foto escribe 29-7-14, no 9-7-14. Salida 1 y saldo 21 conservados.'},
    }
    plan=construir(version=43,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={186:{'primera_fila':8529,'saldo_base':10,'origen_saldo_base':'FOTO','motivo_base':'Base documental escrita 10, sin cantidad de ingreso.'}},
        observaciones=[{'articulo_id':186,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos completas y 63 filas cotejadas. Base documental 10 sin ingreso ficticio. Cedoal Colombia escribe salida 1 con saldo 4 desde 8, diferencia local -3 conservada. Recuento físico escrito 3 después de cálculo 7 restablece la base con diferencia -4, sin fabricar operación ni conteo actual. Fechas parciales sin año y celdas vacías siguen técnicas; 5-11-07 y 29-7-14 corregidas. Columnas de referencias y áreas recuperadas, cierre 12 coincide siguiendo el recuento.'}],extras=extras)
    assert plan['cotejo']['cierres']=={186:16},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':8533,'local':-3,'acumulada':-3},{'id':8534,'local':-1,'acumulada':-4}],plan['cotejo']
    for e in plan['revisiones']:
        if e['id']>=8534:
            e['cambios']['saldo_registrado']-=4;escrito=e['revision']['saldo_documental'];calc=e['cambios']['saldo_registrado']
            e['revision']['origen_saldo']='HIPOTESIS' if escrito is None else ('FOTO' if escrito==calc else 'RECONSTRUIDO')
        if e['id']==8534:
            e['revision'].pop('diferencia_local_papel',None)
            e['revision']['hallazgos']=[h for h in e['revision']['hallazgos'] if h!='DESCUADRE_DEL_PAPEL_CONSERVADO']
    plan['cotejo'].update(cierres={186:12},discrepancias=[{'id':8533,'local':-3,'acumulada':-3}],
        recuentos_documentales=[{'id':8534,'previo':7,'escrito':3,'diferencia':-4}])
    return plan

if __name__=='__main__':congelar(generar())
