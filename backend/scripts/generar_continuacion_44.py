"""Nueve fotografías de Jordán y Caillet, con cancelación documental recuperada."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND
from scripts.generar_continuacion_28 import recuperada

HOJAS=[
 (range(82,108),[80,-1,-1,-1,-3,-1,-1,-1,-1,-2,-2,-3,5,-1,-1,-1,-8,-2,-5,-5,8,-3,3,-1,-3,-15],
  [516,515,514,513,510,509,508,507,506,504,502,499,504,503,502,501,493,491,486,481,489,486,489,488,485,470]),
 (range(108,134),[-1,-3,-1,3,-1,-10,5,1,-1,-3,-1,-1,-1,-1,1,-10,8,-1,-1,-1,-2,-1,-5,1,-2,-10],
  [469,466,465,468,467,457,462,463,462,459,458,457,456,455,456,446,454,453,452,451,449,448,443,444,442,432]),
 (range(134,160),[-1,1,-5,-2,2,-5,4,-5,1,2,-1,1,-1,1,-1,-1,-1,-3,3,-5,2,-1,-10,-1,-1,9],
  [431,432,427,425,427,422,426,421,422,424,423,424,423,424,423,422,421,418,421,416,418,417,407,406,405,414]),
 (range(160,186),[-1,-1,1,-3,-1,-2,-2,2,-1,3,-1,-2,-1,-1,-3,-5,-1,1,-2,-1,-1,-2,-1,-2,-1,-2],
  [413,412,413,410,409,407,405,407,406,409,408,406,405,404,401,396,395,396,394,393,392,390,389,387,386,384]),
 (range(186,196),[2,1,2,-2,-5,-2,-2,-15,-10,9],[386,387,389,387,382,380,378,363,353,362]),
 (range(408,434),[0,-1,-21,-3,-2,-20,-1,-50,-5,5,-5,-1,-1,-1,1,-1,-1,-1,-8,-2,-5,-5,-5,12,-4,-3],
  [525,524,503,500,488,468,467,417,412,417,412,411,410,409,410,409,408,407,399,397,392,387,382,394,390,387]),
 (range(434,460),[3,-2,-15,-1,-3,-1,3,-1,-5,3,1,-1,-3,-1,-1,-1,1,-1,-1,1,-10,6,-1,-1,-1,-3],
  [390,388,373,372,369,368,371,370,365,368,369,368,365,364,363,362,363,362,361,362,352,358,357,356,355,352]),
 (range(460,486),[-1,2,-2,-3,3,-3,-5,4,-5,1,1,5,-1,1,-3,3,-5,-1,5,-10,-1,10,10,-3,10,-2],
  [351,353,351,348,351,348,343,347,342,343,344,349,348,349,346,349,344,343,348,338,337,347,357,354,364,362]),
 (range(486,510),[-2,2,-1,-1,3,-2,-1,2,-1,-1,-3,-1,-2,-1,-1,-1,-1,-1,2,1,-3,-2,-16,1],
  [360,362,361,360,363,361,360,362,361,360,357,356,354,353,352,351,350,349,351,352,349,347,331,332]),
]

def generar():
    snapshot='backups/continuacion_hil_44_20261015/articulos_8_3_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDODAL','CEDOC','CEDECL')}
    for id,fields in {85:{'referencia':'ESIP','area':'014-08'},89:{'detalle':'Donación U. Indígena'},99:{'area':'Dirección'},
        106:{'detalle':'F. libro ECUADOR','referencia':'Ventas'},111:{'fecha_movimiento':'2010-06-11','area':'CEDOAL'},113:{'detalle':'FERIA INT. LIBRO'},120:{'detalle':'BIBLIOTECA QUIME'},
        125:{'detalle':'YATI KAMA'},134:{'detalle':'UCB. CARMEN PAMPA'},144:{'detalle':'LETRAS PACEÑAS'},145:{'detalle':'LETRAS PACEÑAS'},
        166:{'fecha_movimiento':'2014-07-29'},168:{'detalle':'UPEA','referencia':'DONACION','area':'DIR'},174:{'fecha_movimiento':'2016-01-11'},
        437:{'fecha_movimiento':'2010-04-08'},445:{'referencia':'OBSEQUIO'},451:{'detalle':'QUIME','referencia':'DONACION'},454:{'detalle':'FIL'},455:{'detalle':'FIL'},
        462:{'detalle':'VENTA - CEDOAL','area':'CEDOAL'},469:{'detalle':'DEVOLUCION - CEDOAL','area':'CEDOAL'},473:{'area':'CEDOAL'},488:{'detalle':'U. COSTA RICA'},
        501:{'detalle':'ORURO CASA DE LA CULTURA','area':'CEDOAL'},503:{'detalle':'VENTA - CID'},509:{'detalle':'DEV. LA RAYUELA'}}.items():cambios.setdefault(id,{}).update(fields)
    for id in range(506,510):cambios.setdefault(id,{})['orden_fila']=rows[id]['orden_fila']+1
    tecnicas={
        82:('2008-01-15','HIPOTESIS',None,'Primera devolución sin fecha propia. Consulta técnica del 15-01-08 siguiente; no fecha documental copiada.'),
        **{id:('2008-05-19','HIPOTESIS',None,'Donación sin fecha propia; consulta técnica del antecedente.') for id in (88,89)},
        136:('2012-06-19','SECUENCIA_AJUSTADA','2012-05-09','9-5-12 aparece después de 19-6-12. Se conserva literal y consulta técnica del antecedente.'),
        151:('2013-05-10','SECUENCIA_AJUSTADA','2013-05-07','7-5-13 aparece después de 10-5-13. Se conserva literal y consulta técnica del antecedente.'),
        179:('2016-09-19','HIPOTESIS',None,'FIL tiene FECHA vacía; consulta técnica del antecedente.'),
        191:('2021-10-05','SECUENCIA_AJUSTADA','2021-10-01','1-10-21 después de 5-10-21; literal conservada y consulta técnica del antecedente.'),
        195:('2025-06-02','HIPOTESIS',None,'DEV. FIL-SCRUZ tiene FECHA en blanco; consulta técnica del antecedente, sin copiar una fecha escrita.'),
        408:('2008-06-01','HIPOTESIS',None,'Solo se escribe 06-2008 sin día. 1 de junio es exclusivamente fecha técnica de consulta, no recepción acreditada ese día.'),
        410:('2008-07-03','SECUENCIA_AJUSTADA','2008-06-19','19-06-08 después de 03-07-08. Se conserva literal y consulta técnica del antecedente.'),
        454:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después del 02-08-11; literal conservada y consulta técnica del antecedente.'),
        466:('2012-08-08','SECUENCIA_AJUSTADA','2012-07-24','24-7-12 está después de 8-8-12. Se conserva literal y consulta técnica del antecedente.'),
        499:('2016-09-19','HIPOTESIS',None,'El día de ARTES 2016 está tachado y el mes repasado. Se conserva la lectura parcial sin certificar 10-10-16 de OCR; consulta técnica del antecedente.'),
        500:('2016-09-19','HIPOTESIS',None,'FIL sin fecha propia después del día tachado de ARTES; consulta técnica de contexto, sin fecha confirmada inventada.'),
    }
    extras={
        82:{'criterios':['T22'],'motivo':'Primer ingreso visible 80 y saldo 516 implican base anterior 436 solo inferida; no se inventa otro ingreso.'},
        85:{'criterios':['T16'],'motivo':'014-08 está en ÁREA y ESIP en REF. Se conserva el código documental con área pendiente, sin crear institución ni alias.', 'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True}},
        89:{'criterios':['T18'],'motivo':'Comillas en DETALLE repiten Donación de la fila previa en esa misma columna.'},
        105:{'criterios':['T03'],'motivo':'SALIDAS contiene (3) como anotación y 1 final legible. Se conserva salida 1 y saldo 488, sin segunda salida 3.', 'revision':{'anotacion_salidas_documental':'(3) junto al 1 final.'}},
        120:{'criterios':['T14'],'motivo':'Hay una marca tachada en INGRESOS junto a salida 1. Se conserva el egreso activo, sin ingreso adicional.', 'revision':{'marcas_documentales':{'ingresos':'Marca completamente tachada.'}}},
        142:{'criterios':['T14'],'motivo':'Ingreso 1 y saldo 422 acompañados de marca pequeña en SALIDAS, sin egreso inequívoco. Se conserva la marca, no una segunda operación.', 'revision':{'marcas_documentales':{'salidas':'Trazo pequeño sin cantidad inequívoca.'}}},
        159:{'criterios':['T14'],'motivo':'Saldo 414 repasado y devolución 9 legible. Se conserva una sola recepción 9 y los trazos previos del saldo.'},
        174:{'criterios':['T16'],'motivo':'CONSIGNACION cruza REF hacia ÁREA y se conserva como referencia; no se inventa área ni persona responsable.', 'revision':{'columnas_documentales':{'referencia':'CONSIGNACION, texto que cruza ÁREA'}}},
        408:{'criterios':['T22'],'motivo':'Ingreso tiene solo saldo 525 y cantidades vacías; se conserva BASE_DOCUMENTAL 525 sin ingreso ficticio.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL','fecha_documental_texto':'06-2008, sin día.'}},
        412:{'criterios':['T05'],'motivo':'Venta tiene SALIDA 2 legible desde 500, pero escribe 488 frente a cálculo 498. Se conserva la cantidad 2 y diferencia -10; no se cambia a 12 para cuadrar. Cierre escrito 332 frente a cálculo 342.'},
        427:{'criterios':['T16'],'motivo':'Se conserva anotación marginal Saldo 389 sin declararla recuento ni usarla para compensar la diferencia aritmética.', 'revision':{'anotacion_margen_saldo':'Saldo 389, al margen de las filas; ámbito no acreditado.'}},
        473:{'criterios':['T18'],'motivo':'Comillas claras en ÁREA repiten CEDOAL del renglón anterior.'},
        499:{'criterios':['T14','T16'],'motivo':'Día tachado y mes repasado de ARTES conservados como fecha parcial, sin anular la salida 1.', 'revision':{'fecha_documental_texto':'Día tachado, ...-10-16 con mes repasado; no inequívoco.'}},
    }
    plan=construir(version=44,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={3:{'primera_fila':82,'saldo_base':436,'origen_saldo_base':'HIPOTESIS','motivo_base':'Ingreso visible 80 y saldo 516: base 436 inferida, sin recepción fabricada.'},
            8:{'primera_fila':408,'saldo_base':525,'origen_saldo_base':'FOTO','motivo_base':'Base documental 525 sin cantidad de ingreso escrita.'}},
        observaciones=[
            {'articulo_id':3,'observado':True,'excluir_entrenamiento':False,'motivo':'Cinco fotografías completas y 114 filas cotejadas. Base 436 inferida antes del ingreso visible 80, sin recepción ficticia. Anotación (3) junto a salida 1 y marcas tachadas no duplican operaciones. Fechas vacías y retrocesos mantienen literal y consulta técnica, 11-6-10, 29-7-14 y 11-1-2016 recuperadas. Código documental de ÁREA conservado pendiente; no se crean alias. Cierre 362 coincide.'},
            {'articulo_id':8,'observado':True,'excluir_entrenamiento':True,'motivo':'Cuatro fotografías y 102 filas OCR cotejadas, con fila totalmente tachada omitida recuperada sin efecto. Base documental 525 sin ingreso añadido y fecha 06-2008 sin día. Venta escribe salida 2 desde 500 y saldo 488 frente a cálculo 498; la diferencia -10 persiste hasta cierre escrito 332 frente a cálculo 342. No se cambia la cantidad a 12 ni se usa nota marginal Saldo 389 como recuento. Apertura bloqueada y artículo excluido del entrenamiento. Fechas fuera de orden, día tachado y celdas vacías conservados.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={3:362,8:342},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':412,'local':-10,'acumulada':-10}],plan['cotejo']
    for e in plan['revisiones']:
        if e['articulo_id']==8 and e['id']>=412:e['revision']['origen_saldo']='HIPOTESIS'
        if e['id']==509:e['cambios']['saldo_registrado']=332;e['revision'].update(usar_saldo_esperado=False,origen_saldo='FOTO')
    plan['recuperaciones']=[recuperada(rows,505,rows[505]['orden_fila']+1,clave='art8-lote-0a62e054-fila-tachada-despues505-v1',
        detalle='Renglón completamente tachado antes de FIL 2021',fecha='2019-12-09',saldo=352,tipo='ANULADO',
        motivo='Después de PLURAL y antes de FIL 2021 hay un renglón tachado en detalle, cantidad y saldo, omitido por OCR. Se conserva anulado sin efecto y sin certificar cifras ocultas. Fecha 09-12-2019 y saldo 352 son almacenamiento técnico de contexto, no lectura de esta fila.')]
    plan['cotejo'].update(movimientos=217,cierres={3:362,8:332},cierres_calculados={3:362,8:342},pendientes_documentales={509:['saldo']},
        limites_cierre={8:'Cierre escrito 332 frente a cálculo 342 por salida 2 desde 500 con saldo escrito 488. Se conserva cantidad legible, sin cambiarla a 12 ni inventar ajuste. Apertura bloqueada y exclusión del entrenamiento.'})
    return plan

if __name__=='__main__':congelar(generar())
