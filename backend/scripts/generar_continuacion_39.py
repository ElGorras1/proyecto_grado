"""Geografía Ecológica y Ecológica 12: cuatro fotos y una fila anulada recuperada."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND
from scripts.generar_continuacion_28 import recuperada

HOJAS=[
 (range(9587,9613),[50,-20,-5,-2,-2,-2,-1,2,-1,-2,-1,-2,-13,-1,1,20,-5,-10,9,-3,1,-1,-1,8,-3,-5],
  [50,None,25,23,21,19,18,20,19,17,16,14,1,0,1,21,16,6,15,12,13,12,11,19,16,11]),
 (range(9613,9631),[-8,-2,4,-2,10,-2,-1,-6,-1,-1,5,-6,5,-3,-2,5,-4,-2],
  [3,1,5,3,13,11,10,4,3,2,7,1,6,3,1,6,2,0]),
 (range(12133,12159),[20,-10,-5,3,-2,-3,50,-10,-10,5,-5,4,-2,-5,4,-3,-1,-10,-10,15,1,-1,-3,1,-5,5],
  [20,10,5,8,6,3,53,43,33,38,33,37,35,30,34,31,30,20,10,25,26,26,22,23,18,23]),
 (range(12159,12175),[-10,3,-3,2,-5,4,2,-10,10,-3,-2,-1,-2,-2,-1,-1],
  [13,16,13,15,10,14,16,6,16,13,11,10,8,6,5,4]),
]

def generar():
    snapshot='backups/continuacion_hil_39_20261015/articulos_397_243_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDOAL.')}
    for id,fields in {9591:{'fecha_movimiento':'2007-10-17','area':'CEDOAL'},9595:{'detalle':'Donación Emb.','referencia':'Brithum','area':None},
        9610:{'referencia':'ECOLOGIA','area':None},12133:{'detalle':'Ingresado SC.'},12137:{'area':'CEDOAL'},12157:{'detalle':'LLALLAGUA'},
        12158:{'detalle':'LLALLAGUA'},12160:{'area':'CEDOAL'},12167:{'fecha_movimiento':'2013-11-04'}}.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        9594:('2007-10-26','HIPOTESIS',None,'Devolución tiene FECHA en blanco. Se conserva nota lateral 18/12/07 sin asignarla automáticamente a la fila; consulta técnica del antecedente.'),
        9596:('2008-02-08','SECUENCIA_AJUSTADA','2008-01-15','15-01-08 está después de 8-2-08. Se conserva literal y consulta técnica del antecedente.'),
        9624:('2015-08-11','SECUENCIA_AJUSTADA','2015-08-03','3-8-15 aparece después de 11-8-15. Se conserva literal y consulta técnica del antecedente.'),
        9629:('2017-07-18','HIPOTESIS',None,'FIL tiene FECHA vacía; consulta técnica del antecedente, sin certificar el día del ingreso anterior.'),
        12134:('2007-08-08','HIPOTESIS',None,'Para la Feria sin fecha propia. Consulta técnica del antecedente, no fecha copiada del papel.'),
        12136:('2007-10-17','HIPOTESIS',None,'Devolución Potosí sin fecha en su celda. Nota lateral 19-12-07 conservada sin asignación automática; consulta técnica del antecedente.'),
        12159:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después del 02-08-11 de la hoja anterior. Se conserva literal y consulta técnica del antecedente.'),
        12171:('2016-09-19','HIPOTESIS',None,'FIL tiene FECHA en blanco. Consulta técnica del antecedente; no se copia 14-8-18 de la fila siguiente.'),
        12173:('2018-08-14','SECUENCIA_AJUSTADA','2018-07-05','5-7-18 está después de 14-8-18 en el papel. Se conserva literal y consulta técnica del antecedente, sin cambiar la gestión por otros artículos.'),
    }
    extras={
        9588:{'criterios':['T08'],'motivo':'SALDO está vacío después de salida 20. El 30 de consulta es hipotético; no cifra escrita.'},
        9594:{'criterios':['T16'],'motivo':'Se conserva nota lateral 18/12/07 junto a la devolución, sin certificar automáticamente su vínculo con la fecha vacía.', 'revision':{'anotacion_margen_fecha':'18/12/07 junto a devolución, vínculo no confirmado.'}},
        9610:{'criterios':['T23'],'motivo':'ECOLOGIA comienza en REF y cruza ÁREA. Se conserva como referencia documental, con área vacía; no se crea institución ni alias Ecología.', 'revision':{'columnas_documentales':{'referencia':'ECOLOGIA, texto que cruza hacia ÁREA'}}},
        9623:{'criterios':['T14'],'motivo':'INGRESO 5 tiene una marca tachada en SALIDAS, extraída como 1. Se conserva solo ingreso 5, saldo 7 desde 2, sin egreso adicional.', 'revision':{'marcas_documentales':{'salidas':'Trazo tachado, sin salida adicional confirmada.'}}},
        12133:{'criterios':['T16'],'motivo':'Ingresado SC. y Para la Feria son dos renglones distintos; no se incluye el segundo detalle en la recepción 20.'},
        12136:{'criterios':['T16'],'motivo':'Nota lateral 19-12-07 conservada, sin sustituir por ella una fecha documental ausente.', 'revision':{'anotacion_margen_fecha':'19-12-07 al lado de devolución, vínculo no confirmado.'}},
        12137:{'criterios':['T18'],'motivo':'Comillas en ÁREA repiten CEDOAL anterior. Se conserva el signo sin crear un área nueva.'},
        12140:{'criterios':['T03'],'motivo':'SALIDAS escribe 10 y en INGRESOS aparece (10) entre paréntesis. Se conserva como anotación, sin segundo ingreso: saldo 53 a 43.', 'revision':{'anotacion_ingresos_documental':'(10)'}},
        12154:{'criterios':['T05'],'motivo':'LUIS OPORTO tiene salida 1 desde 26 y escribe nuevamente 26. Se conservan salida y saldo del papel, frente a cálculo 25. La siguiente salida 3 escribe 22 y compensa el error local +1 con -1, sin entrada ficticia.'},
        12158:{'criterios':['T16'],'motivo':'ÁREA contiene una marca parcial C; se conserva literal sin completar un área solo por frecuencia.'},
        12160:{'criterios':['T18'],'motivo':'Comillas claras en ÁREA repiten CEDOAL de la fila previa.'},
    }
    plan=construir(version=39,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={243:{'primera_fila':9587,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 50: base cero inferida, sin recuento acreditado.'},
            397:{'primera_fila':12133,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 20: base cero inferida, sin recuento acreditado.'}},
        observaciones=[
            {'articulo_id':243,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotografías y 44 filas cotejadas. Saldo inicial de feria vacío, ingreso 5 con marca tachada sin salida adicional, y referencia ECOLOGIA que cruza columnas conservados. Se recupera fecha 17-10-07. Devolución sin fecha y dos retrocesos siguen técnicos; nota lateral se conserva sin asociación automática. Cierre cero numérico coincide, sin ajustes ficticios.'},
            {'articulo_id':397,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotografías y 42 filas OCR cotejadas; se recupera un renglón completamente tachado omitido por OCR, sin efecto. Anotación (10) no se duplica como ingreso. LUIS OPORTO escribe saldo 26 pese a salida 1 desde 26; la salida siguiente 3 vuelve a 22 y compensa +1/-1 del papel. Fechas ausentes y fuera de orden conservadas, 4-11-13 recuperada. Cierre 4 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={243:0,397:4},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':12154,'local':1,'acumulada':1},{'id':12155,'local':-1,'acumulada':0}],plan['cotejo']
    plan['recuperaciones']=[recuperada(rows,12174,rows[12174]['orden_fila']+1,clave='art397-lote-c6dd2fa7-p2-fila-tachada-final-v1',
        detalle='Renglón final completamente tachado',fecha='2020-02-03',saldo=4,tipo='ANULADO',
        motivo='Después de VENTAS CID hay un renglón tachado en fecha, detalle, cantidad y saldo, omitido por OCR. Se recupera como evidencia anulada sin efecto; las cifras ocultas no se certifican. Fecha 03-02-2020 y saldo 4 son almacenamiento técnico de contexto, no lectura de esta fila.')]
    plan['recuperaciones'][0]['campos']['numero_pagina']=2
    plan['cotejo']['movimientos']=87
    return plan

if __name__=='__main__':congelar(generar())
