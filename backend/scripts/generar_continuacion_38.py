"""Seis fotografías completas con columnas desplazadas, notas y límites del papel."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(590,615),[-1,-1,0,59,-3,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-3,-3,3,-20,-2,-5,-3,-1,-2],
  [None,6,None,65,None,None,None,None,None,None,None,None,None,None,None,None,None,45,48,28,26,21,18,17,15]),
 (range(615,627),[-1,-5,3,-1,-1,-1,-1,1,-2,-1,-5,1],[14,9,12,11,None,None,8,9,7,6,1,2]),
 (range(7688,7711),[-3,2,-1,-10,10,1,-1,1,-10,10,-1,20,1,-10,10,-2,2,-2,-1,-1,-1,-1,-1],
  [16,18,17,7,17,18,17,18,8,18,17,37,38,28,38,36,38,36,35,34,33,32,31]),
 (range(7776,7802),[-1,-1,20,-4,-5,-5,-6,-1,1,-1,15,-15,2,-1,20,-5,-10,5,-3,1,-9,-1,10,-10,20,-3],
  [4,3,23,19,14,9,3,2,3,2,17,2,4,3,23,18,8,13,10,11,2,1,11,1,20,17]),
 (range(7802,7810),[-14,7,-10,0,10,15,-15,-10],[3,10,None,None,10,25,10,0]),
 (range(11798,11817),[10,-4,20,-10,9,-10,20,9,-2,-2,-25,-1,-2,2,-1,-2,-3,-1,-1],
  [10,6,26,16,25,15,35,44,42,40,15,14,12,14,13,11,8,7,6]),
]

def generar():
    snapshot='backups/continuacion_hil_38_20261015/articulos_379_139_142_11_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CDD00L')}
    for id,fields in {592:{'estado':'NOTA_DOCUMENTAL'},606:{'fecha_movimiento':'2007-04-27'},620:{'area':'CEDOAL'},621:{'area':'CEDOAL'},
        7689:{'fecha_movimiento':'2010-06-11','area':'CEDOAL'},7694:{'fecha_movimiento':'2011-07-18','detalle':'LLALLAGUA'},7695:{'detalle':'LLALLAGUA'},
        7698:{'area':'GALERIA'},7778:{'area':None},7789:{'detalle':'VENTAS'},7802:{'fecha_movimiento':'2016-09-19'},
        11800:{'area':None},11804:{'area':None},11805:{'area':None,'referencia':'DEV'},11811:{'area':None},11813:{'detalle':'VENTAS - ESIP'}}.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        **{id:('2007-01-17','HIPOTESIS',None,'FECHA en blanco; consulta técnica del 17-01-07 anterior, sin copiar una fecha documental inexistente.') for id in (591,592,593,594)},
        **{id:('2007-03-29','HIPOTESIS',None,'Nombre o donación sin fecha propia; consulta técnica del 29-03-07 anterior, sin certificar el día real.') for id in range(597,606)},
        610:('2007-08-01','SECUENCIA_AJUSTADA','2007-04-18','18-04-07 aparece después de 1-08-07. Se conserva literal y consulta técnica del antecedente.'),
        611:('2007-08-01','SECUENCIA_AJUSTADA','2007-07-11','11-07-07 aparece después de 1-08-07. Se conserva literal y consulta técnica del antecedente.'),
        616:('2007-11-02','SECUENCIA_AJUSTADA','2007-10-16','16-10-07 después de 2-11-07 al empezar la segunda hoja. Se conserva literal y consulta técnica del antecedente.'),
        **{id:('2008-05-19','HIPOTESIS',None,'FECHA vacía en donación o devolución por error; consulta técnica del antecedente, sin inventar fecha escrita.') for id in (620,621,622)},
        7696:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después del 02-08-11; literal conservada y consulta técnica del antecedente.'),
        7701:('2012-10-04','SECUENCIA_AJUSTADA','2012-10-02','2-10-12 está después de 4-10-12. Se conserva literal y consulta técnica del antecedente.'),
        7707:('2016-09-19','HIPOTESIS',None,'FIL 17 carece de FECHA; consulta técnica del antecedente, sin deducir un día a partir del detalle.'),
        7790:('2011-09-20','HIPOTESIS',None,'INGRESO 20 sin fecha propia; consulta técnica del antecedente.'),
        7799:('2015-08-14','SECUENCIA_AJUSTADA','2015-08-03','3-8-15 aparece después del 14-8-15. Se conserva literal y consulta técnica del antecedente.'),
        7800:('2015-08-14','HIPOTESIS',None,'INGRESO 20 sin fecha propia. Consulta técnica del contexto anterior; no se inventa día ni recuento.'),
        **{id:('2016-09-19','HIPOTESIS',None,'INGRESO o FIL sin fecha propia después de 19-9-16; consulta técnica del antecedente, no gestión 2019 confirmada.') for id in (7803,7804)},
        11801:('2013-04-22','SECUENCIA_AJUSTADA','2013-04-18','18-4-13 está después de 22-4-13. Se conserva literal y consulta técnica del antecedente.'),
        11809:('2016-12-08','HIPOTESIS',None,'FIL tiene FECHA en blanco; consulta técnica del antecedente, sin inventar gestión del detalle.'),
    }
    extras={
        590:{'criterios':['T22'],'motivo':'Antes de Edgar Arandia hay una cifra muy tenue sin fecha ni detalle, lectura no inequívoca 8/9. Se documenta sin certificarla como recuento ni añadir ingreso: base 8 únicamente inferida desde dos salidas 1 y el posterior ingreso 59 con saldo 65.', 'revision':{'anotacion_base_previa':'Cifra tenue 8/9 en primera línea de SALDO, no inequívoca.'}},
        592:{'criterios':['T16'],'motivo':'Se adjunta el saldo de el continúa en el siguiente renglón Otro Depósito. Esta línea sin cantidad es nota documental sin efecto; el ingreso 59 solo se registra en la fila siguiente.', 'revision':{'tipo_fila':'NOTA_DOCUMENTAL','saldo_documental':None,'origen_saldo':'HIPOTESIS'}},
        593:{'motivo':'Ingreso 59 y saldo 65 son legibles. Se conserva la nota de la línea precedente y un solo ingreso; no se duplica el texto como operación.'},
        **{id:{'criterios':['T18'],'motivo':'Comillas inequívocas en ÁREA repiten CEDOAL del renglón anterior; se conserva la marca sin crear un área nueva.'} for id in (620,621)},
        618:{'criterios':['T01'],'motivo':'La salida 1 desde 12 escribe saldo 11 tenue, no 13. Se conserva esa lectura y los saldos vacíos de las dos filas siguientes.'},
        622:{'motivo':'Error U Indígena registra ingreso 1 y saldo 9; se conserva como devolución escrita, sin anularla por el término Error.'},
        7689:{'criterios':['T01'],'motivo':'La foto escribe 11-6-10, no 30-6-10. Se corrige el día por la escritura visible.'},
        7694:{'criterios':['T01'],'motivo':'La fecha se lee 18-07-11 y LLALLAGUA; no 18-08-2010. Se conserva el trazo repasado y la lectura de año, sin trasplantar otra fecha.'},
        7778:{'criterios':['T23'],'motivo':'20 está en INGRESOS y Cbba. en REF, con ÁREA vacía. Se recupera la cantidad sin crear área numérica.'},
        7798:{'criterios':['T14'],'motivo':'INGRESO 10 tiene una marca tachada en SALIDAS. Se conserva solo el ingreso activo 10, saldo 11, y el tachón como evidencia.', 'revision':{'marcas_documentales':{'salidas':'Trazo completamente tachado, sin segunda cantidad confirmada.'}}},
        7800:{'criterios':['T05'],'motivo':'INGRESO 20 tiene saldo escrito 20 desde 1: el cálculo independiente es 21. No se cambia la cantidad a 19 ni se declara recuento para cuadrar; diferencia -1 persiste hasta cierre escrito 0 frente a cálculo condicional 1.'},
        7804:{'criterios':['T08'],'motivo':'SALDO contiene un guion, no cero numérico. Se conserva como ausente; la consulta acumulada es hipotética.'},
        7805:{'criterios':['T16','T19'],'motivo':'FIL-2019 con fecha 12-8-19 no tiene cantidad ni saldo escritos. No se inventa salida 1 para compensar el descuadre anterior: efecto cuantitativo indeterminado, continuidad sin efecto cuantificado solo hipotética.', 'revision':{'origen_cantidades':'HIPOTESIS','cantidad_documental_ausente':True,'efecto_cuantitativo_no_acreditado':True}},
        **{id:{'criterios':['T23'],'motivo':'La cifra está en INGRESOS y ÁREA vacía. Se recupera la columna y se elimina el área numérica atribuida por OCR.'} for id in (11800,11804,11811)},
        11805:{'criterios':['T23'],'motivo':'9 está en INGRESOS y DEV en ÁREA. Se conserva la posición documental de DEV y se guarda como referencia; no se crea área 9 ni área Devolución.', 'revision':{'columnas_documentales':{'area':'DEV','ingresos':9}}},
        11808:{'criterios':['T02','T16'],'motivo':'Aunque el detalle dice Devolución, la cantidad 25 está en SALIDAS y el saldo disminuye 40 a 15. Se corrige el ingreso OCR a salida 25; no se invierte automáticamente por el nombre.'},
    }
    plan=construir(version=38,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={11:{'primera_fila':590,'saldo_base':8,'origen_saldo_base':'HIPOTESIS','motivo_base':'Base 8 inferida desde ingreso 59, saldo 65 y dos salidas 1 previas; cifra tenue inicial no se certifica.'},
            139:{'primera_fila':7688,'saldo_base':19,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primera salida 3 y saldo 16: base 19 inferida, sin ingreso ficticio.'},
            142:{'primera_fila':7776,'saldo_base':5,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primera salida 1 y saldo 4: base 5 inferida, sin ingreso ficticio.'},
            379:{'primera_fila':11798,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 10: base cero inferida, sin recuento acreditado.'}},
        observaciones=[
            {'articulo_id':11,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotografías y 37 filas cotejadas. Nota sin cantidades separada del ingreso 59 de Otro Depósito, sin duplicarlo. Base inicial tenue no certificada; consulta desde base 8 inferida, con saldo 65 posterior legible. Saldos vacíos conservados, 11 tenue corregido frente a 13 OCR y fechas ausentes o fuera de orden identificadas. Comillas repiten CEDOAL y devolución por Error U Indígena mantiene ingreso 1. Cierre 2 coincide.'},
            {'articulo_id':139,'observado':True,'excluir_entrenamiento':False,'motivo':'Fotografía y 23 filas cotejadas. Se recuperan 11-6-10, LLALLAGUA 18-07-11 y GALERIA. Fechas literales fuera de orden permanecen documentadas con consulta técnica; FIL 17 sin fecha no se fecha por el detalle. Base previa 19 inferida, cierre 31 coincide.'},
            {'articulo_id':142,'observado':True,'excluir_entrenamiento':True,'motivo':'Dos fotografías y 34 filas cotejadas. Ingreso 20 desplazado a ÁREA recuperado; FECHA 19-9-16 corregida frente a 2019. Ingreso 20 desde saldo 1 escribe 20, pero cálculo 21: diferencia -1 persistente. FIL-2019 sin cantidad ni saldo tiene efecto indeterminado; no se inventa una salida para cuadrar. Cierre escrito 0 frente a cálculo condicional 1, apertura bloqueada y artículo excluido del entrenamiento.'},
            {'articulo_id':379,'observado':True,'excluir_entrenamiento':False,'motivo':'Fotografía completa y 19 filas cotejadas. Ingresos 20, 20, 9 y 2 desplazados a ÁREA recuperados; DEV se conserva como referencia y con sus columnas documentales. Devolución 25 está escrita como salida y reduce 40 a 15; se respeta ese egreso. Fecha fuera de orden y FIL sin fecha permanecen técnicos. Cierre 6 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={11:2,139:31,142:1,379:6},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':7800,'local':-1,'acumulada':-1}],plan['cotejo']
    for e in plan['revisiones']:
        if e['articulo_id']==142 and e['id']>=7800:e['revision']['origen_saldo']='HIPOTESIS'
        if e['id']==7809:e['cambios']['saldo_registrado']=0;e['revision'].update(usar_saldo_esperado=False,origen_saldo='FOTO')
    plan['cotejo'].update(cierres={11:2,139:31,142:0,379:6},cierres_calculados={11:2,139:31,142:1,379:6},pendientes_documentales={7809:['saldo']},
        limites_cierre={142:'Cierre escrito 0 frente a cálculo condicional 1. Ingreso 20 desde 1 escribe 20 y FIL-2019 no tiene cantidad ni saldo: no se inventa salida compensatoria. Apertura bloqueada y exclusión del entrenamiento.'})
    return plan

if __name__=='__main__':congelar(generar())
