"""Cuatro fotos completas de Ecología 15 y 18, incluida una recepción omitida."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND
from scripts.generar_continuacion_28 import recuperada

HOJAS=[
 (range(11902,11926),[-2,-1,1,-1,10,-3,-5,3,-2,2,-2,-2,2,-1,-4,50,-10,8,-2,-3,-1,0,-1,1],
  [3,2,3,2,12,None,4,7,5,7,5,3,5,4,0,50,40,48,46,43,42,42,41,42]),
 (range(11926,11937),[-10,8,-5,4,1,-10,10,-1,-24,-2,2],[32,40,35,39,40,30,40,39,15,13,15]),
 (range(11970,11996),[0,10,-3,-5,4,-2,2,-2,-2,2,-5,4,-3,1,-1,-2,-2,50,-10,8,-2,-10,10,-3,-1,-1],
  [5,15,None,7,11,9,11,9,7,9,4,8,5,6,5,3,1,51,41,49,47,37,47,44,43,42]),
 (range(11996,12007),[1,-10,9,-5,4,3,-10,9,-1,-1,-26],[43,33,42,37,41,44,34,43,42,41,15]),
]

def generar():
    snapshot='backups/continuacion_hil_47_20261015/articulos_385_388_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','Cedcal','CEDCAL','ODCAL','CEDOC')}
    for id,fields in {
        11902:{'fecha_movimiento':'2005-08-17'},11903:{'detalle':'FERIA DEL LIBRO'},11904:{'detalle':'Envío de S. Cruz'},
        11905:{'detalle':'Para la Feria Cedoal'},11906:{'detalle':'Ingresa Sta. Cruz'},11907:{'detalle':'Salida para Feria'},11908:{'detalle':'Salida para Feria'},
        11913:{'detalle':'Oruro'},11915:{'fecha_movimiento':'2007-07-18'},11920:{'referencia':'Ventas','area':'CAP'},
        11924:{'detalle':'LLALLAGUA'},11925:{'detalle':'LLALLAGUA'},11928:{'area':'CEDOAL'},
        11970:{'detalle':'Saldo según inventario, último ingreso','referencia':None,'area':None},
        11975:{'detalle':'Cedoal - Oruro'},11976:{'detalle':'Devolución Cedoal Oruro'},11977:{'detalle':'Cedoal - Ventas'},
        11981:{'detalle':'Devolución Feria','area':None},11993:{'detalle':'PARA VENTA'},11995:{'detalle':'LLALLAGUA'},11996:{'detalle':'LLALLAGUA'},
    }.items():cambios.setdefault(id,{}).update(fields)
    for id in range(11902,11926):cambios.setdefault(id,{})['orden_fila']=rows[id]['orden_fila']+1
    tecnicas={
        11905:('2005-10-18','HIPOTESIS',None,'Para la Feria Cedoal tiene FECHA vacía; consulta técnica del antecedente.'),
        **{id:('2006-08-01','HIPOTESIS',None,'La celda inicial escribe únicamente 08-06, sin fecha completa inequívoca. Las filas posteriores no tienen fecha propia. Consulta 2006-08-01 exclusivamente técnica, sin certificar día, mes y año de cada movimiento.') for id in range(11906,11910)},
        11910:('2006-08-01','HIPOTESIS',None,'09-?-06 tiene mes trazado no inequívoco. Se conserva lectura parcial y consulta técnica del antecedente, sin certificar el mes OCR.'),
        11914:('2007-06-15','HIPOTESIS',None,'Devolución Cedoal carece de fecha propia; consulta técnica de Oruro anterior.'),
        11926:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 aparece después de 02-08-11; literal conservada y consulta técnica del antecedente.'),
        11928:('2011-08-17','SECUENCIA_AJUSTADA','2011-07-24','La fotografía escribe 24-7-11 después de 17-08-11. Se conserva el año 11, sin cambiarlo a 2012 para ordenar.'),
        11970:('2006-08-01','HIPOTESIS',None,'Base sin fecha escrita. Consulta técnica del contexto parcial de la siguiente recepción, no 1 de enero documental.'),
        **{id:('2006-08-01','HIPOTESIS',None,'8-06 es fecha parcial sin día, mes y año completos inequívocos; las siguientes filas tienen fecha vacía. Consulta 2006-08-01 solo técnica, sin certificarla como fecha escrita.') for id in range(11971,11975)},
        11976:('2006-10-06','HIPOTESIS',None,'Devolución Cedoal Oruro no tiene fecha propia; consulta técnica del antecedente.'),
        11978:('2007-06-16','HIPOTESIS',None,'El día de 15/16-06-07 está repasado y no es inequívoco. Se conserva lectura parcial y consulta 2007-06-16 solo técnica, sin certificar el día OCR.'),
        11979:('2007-06-16','HIPOTESIS',None,'Devolución sin fecha propia; consulta técnica del antecedente cuyo día está repasado.'),
        11983:('2007-10-17','HIPOTESIS',None,'Devolución Potosí tiene FECHA vacía y nota lateral 14-12-07, que se conserva sin asignarla automáticamente a la celda.'),
        11984:('2008-02-02','HIPOTESIS',None,'Día de donación repasado 2/8 no inequívoco; mes 02 y año 08 conservados como texto. Consulta 2008-02-02 solo técnica, no fecha documental completa.'),
        11997:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','La fotografía escribe 1-08-11, no 11-08-11; está después de 02-08-11. Literal y consulta técnica del antecedente conservadas.'),
    }
    extras={
        11903:{'criterios':['T18'],'motivo':'Comillas inequívocas en DETALLE repiten FERIA DEL LIBRO, manteniendo salida 1 distinta.'},
        **{id:{'revision':{'fecha_documental_texto':'08-06, fecha parcial; no fecha completa.'}} for id in (11906,11971)},
        11907:{'criterios':['T08'],'motivo':'SALDO está vacío después de la salida 3. Se conserva ausencia documental; cálculo 9 solo hipotético.'},
        11910:{'criterios':['T16'],'motivo':'Mes de fecha y texto de destino no inequívocos; no se completan por frecuencia ni por semejanza.', 'revision':{'fecha_documental_texto':'09-?-06, mes trazado no inequívoco.'}},
        11915:{'motivo':'La fecha visible es 18-07-07, no 18-04-07. Se conserva salida 1 y saldo 4.'},
        11920:{'criterios':['T23'],'motivo':'Ventas está en REF y CAP en ÁREA. Se recuperan columnas sin crear área Ventas CAP.', 'revision':{'columnas_documentales':{'referencia':'Ventas','area':'CAP'}}},
        11923:{'criterios':['T16'],'motivo':'FERIA UCB con REF DEV. tiene guiones en INGRESOS y SALIDAS y saldo escrito 42 repetido. No hay cantidad numérica acreditada. Se conserva sin efecto cuantificado solo para continuidad condicional, sin inventar devolución ni certificar cero como cantidad.', 'revision':{'origen_cantidades':'HIPOTESIS','efecto_cuantitativo_no_acreditado':True,'columnas_documentales':{'ingresos':'Guion','salidas':'Guion'}}},
        11934:{'criterios':['T02'],'motivo':'Devolución escribe 24 en SALIDAS, saldo 39 a 15. Se conserva egreso legible; no se invierte por su nombre.'},
        11970:{'criterios':['T22','T23'],'motivo':'Saldo según inventario, último ingreso cruza DETALLE/REF/ÁREA y tiene cantidades vacías. Es base documental 5, no recepción 5 ni área Ingreso.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL','columnas_documentales':{'referencia':'Último','area':'Ingreso'}}},
        11972:{'criterios':['T08'],'motivo':'La salida 3 carece de saldo escrito; acumulado 12 solo hipotético, sin llenar la fuente.'},
        11978:{'criterios':['T16'],'revision':{'fecha_documental_texto':'15/16-06-07, día repasado no inequívoco.'}},
        11981:{'criterios':['T23'],'motivo':'Feria en ÁREA describe la devolución y se conserva en detalle con posición literal, sin crear institución Feria.', 'revision':{'columnas_documentales':{'area':'Feria'}}},
        11983:{'criterios':['T16'],'revision':{'anotacion_margen_fecha':'14-12-07 junto a devolución, sin asignación automática a la celda.'}},
        11984:{'criterios':['T16'],'revision':{'fecha_documental_texto':'?-02-08, día repasado 2/8 no inequívoco.'}},
        12006:{'criterios':['T02'],'motivo':'Devolución escribe 26 en SALIDAS y reduce 41 a 15. Se conserva egreso por columna visible, sin invertirlo por el nombre.'},
    }
    plan=construir(version=47,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={385:{'primera_fila':11902,'saldo_base':5,'origen_saldo_base':'FOTO','motivo_base':'Ingreso 5 y saldo 5 visibles en fila anterior omitida, que se recupera por separado una sola vez.'},
            388:{'primera_fila':11970,'saldo_base':5,'origen_saldo_base':'FOTO','motivo_base':'Base escrita según inventario 5 sin cantidad de ingreso.'}},
        observaciones=[
            {'articulo_id':385,'observado':True,'excluir_entrenamiento':True,'motivo':'Dos fotos y 35 filas OCR cotejadas; recepción inicial 5 y saldo 5 sin fecha ni detalle omitida por OCR recuperada una sola vez. No es recuento ni inventario actual. Guiones sin cantidad numérica en FERIA UCB DEV. quedan con efecto no acreditado, sin inventar devolución ni cantidad cero confirmada; artículo excluido del entrenamiento. Fechas parciales y fuera de orden conservadas; 24-7-11 no se convierte en 2012. Devolución salida 24 legible conservada. Cierre 15 coincide condicionalmente, sin afirmar bloqueo automático por exclusión.'},
            {'articulo_id':388,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 37 filas cotejadas. Base documental 5 sin ingreso ficticio, saldo vacío tras salida 3, fechas parciales o repasadas y devolución sin fecha identificadas. La nota marginal 14-12-07 no sustituye fecha vacía. CEDOAL y LLALLAGUA recuperados de lectura OCR sin crear alias; 1-08-11 literal conservado. Devolución salida 26 legible; cierre 15 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={385:15,388:15} and plan['cotejo']['discrepancias']==[],plan['cotejo']
    # La recepción recuperada inicia la cadena. No se conserva una segunda base en la venta siguiente.
    for e in plan['revisiones']:
        if e['id']==11902:
            for k in ('saldo_base','origen_saldo_base','motivo_base'):e['revision'].pop(k,None)
    nueva=recuperada(rows,11902,1,clave='art385-ingreso5-inicial-antes11902-v1',detalle='Ingreso 5 sin fecha ni detalle documental',fecha='2005-08-17',saldo=5,tipo='MOVIMIENTO',
        motivo='La primera fila de la foto escribe INGRESOS 5 y SALDO 5, con fecha y detalle vacíos; fue omitida por OCR. Se recupera una sola recepción documentada, sin inventar fecha, responsable, recuento o inventario operativo. La primera fecha posterior se usa solo para consulta.')
    nueva['campos'].update(estado='ACTIVO',ingresos=5,fecha_estado='ESTIMADA_HIL')
    nueva['campos']['datos_originales'].update(detalle=None,ingresos=5,saldo_registrado=5)
    nueva['revision'].update(criterios=['T09','T23'],tipo_fila='MOVIMIENTO',detalle_documental=None,saldo_documental=5,origen_saldo='FOTO',origen_cantidades='FOTO',
        saldo_base=0,origen_saldo_base='HIPOTESIS',motivo_base='Base anterior cero inferida desde ingreso y saldo 5; no recuento acreditado.')
    plan['recuperaciones']=[nueva]
    plan['cotejo'].update(movimientos=73,limites_cierre={385:'Cierre escrito 15 coincide condicionalmente. FERIA UCB DEV. tiene guiones sin cantidad numérica acreditada; no se inventa devolución. Artículo excluido del entrenamiento, sin atribuir bloqueo automático por esa exclusión.'})
    return plan

if __name__=='__main__':congelar(generar())
