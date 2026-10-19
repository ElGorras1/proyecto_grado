"""Jorge Campero: cotejo con discontinuidad de ámbito conservada como pendiente."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(4711,4737),[10,3,-1,-1,-1,5,-1,-2,272,-5,-1,-3,2,-5,-10,-15,-1,-4,-1,-8,-5,-6,-1,-1,-5,4],
  [10,3,2,1,None,5,4,2,274,269,268,265,267,262,252,237,236,232,231,223,218,212,211,210,205,209]),
 (range(4737,4763),[-3,-1,-10,-2,-10,-100,-5,9,1,-5,-5,-1,1,-5,-1,-3,-1,-1,1,-1,100,100,250,50,-1,-1],
  [206,205,195,193,183,83,78,87,88,83,78,77,78,73,72,69,68,67,68,67,167,267,517,567,566,565]),
 (range(4763,4789),[-2,2,-10,7,-3,1,-4,-2,-1,-10,-10,-3,-75,10,-2,-3,-3,-30,-5,-10,13,-5,-1,1,-1,-2],
  [563,565,555,562,559,560,556,554,553,543,534,531,456,466,464,461,458,428,423,413,426,421,420,421,420,418]),
 (range(4789,4815),[5,-2,-1,2,-2,-1,-1,1,-1,-1,1,1,-10,-5,15,-3,-5,8,-5,-1,-1,-1,5,-1,-1,-10],
  [423,421,420,422,420,419,418,419,418,417,418,419,409,404,419,416,411,419,414,413,412,411,416,415,414,404]),
 (range(4815,4840),[-1,6,-2,-3,-5,-5,-6,2,5,-3,-2,-4,3,-3,-2,-5,-1,-1,4,-1,-1,-2,-1,-3,-1],
  [403,409,407,404,399,394,388,390,395,392,390,386,389,386,384,379,378,377,381,380,379,377,376,373,372]),
 (range(4840,4866),[-1,1,-2,-4,-5,2,-2,-2,-2,-2,-10,-2,-1,-3,-3,-1,-1,1,-2,-4,-3,-1,-2,-3,-1,-2],
  [371,372,370,366,361,363,361,359,357,355,345,343,342,339,336,335,334,335,333,329,326,325,323,320,319,317]),
 (range(4866,4872),[-4,-5,4,-8,1,-5],[313,308,312,304,305,300]),
]


def generar():
    snapshot='backups/continuacion_hil_16_20261015/articulo_81_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={}
    for id,r in rows.items():
        if r['area']=='CEDOCAL':cambios[id]={'area':'CEDOAL'}
    for id,fields in {4729:{'detalle':'C/carta Marien Garten','referencia':'Biblio.'},4730:{'detalle':'C/carta Camp. de lectura','referencia':'SCZ'},
        4735:{'fecha_movimiento':'2010-06-11'},4747:{'fecha_movimiento':'2010-11-22'},4751:{'fecha_movimiento':'2010-12-27'},
        4781:{'fecha_movimiento':'2012-07-24'},4787:{'fecha_movimiento':'2012-09-26'},4792:{'area':'CAP'},4812:{'detalle':'Inaug. Yolanda'},
        4818:{'detalle':'Noira Quiroga'},4826:{'area':'Lucy'},4831:{'detalle':'Cueva Cuentacuento'},4836:{'detalle':'La Paz Lee'},
        4846:{'detalle':'Ventas CID','area':'CID'},4850:{'fecha_movimiento':'2021-10-05'}}.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        **{id:('2012-08-21','SECUENCIA_AJUSTADA',fecha,'Fecha de julio/agosto escrita después del 21-08: consulta técnica con el antecedente y literal conservada.') for id,fecha in [(4781,'2012-07-24'),(4782,'2012-08-05'),(4783,'2012-08-14')]},
        4804:('2013-05-07','HIPOTESIS',None,'Mes manuscrito de lectura 5/6: consulta técnica de mayo por el contexto de la misma actividad; no se certifica el mes del documento.'),
        4838:('2017-05-20','HIPOTESIS',None,'FIL tiene fecha en blanco; consulta técnica del antecedente, sin confirmar día propio.'),
        4857:('2022-10-17','HIPOTESIS',None,'Devolución tiene fecha en blanco: se conserva su ausencia y fecha técnica del antecedente.'),
    }
    extras={
        4711:{'criterios':['T16'],'motivo':'El detalle dice Ingreso al STAND. Su relación con el saldo disponible de la devolución siguiente no está acreditada; no se infiere una venta de 7 ni una salida de 10.','revision':{'alcance_documental':'STAND','interpretacion_ambito':'PENDIENTE','hallazgos':['HOJA_COMPLETA_COTEJADA','AMBITO_STAND_NO_CONCILIADO']}},
        4712:{'criterios':['T16'],'motivo':'Después del ingreso al STAND 10, la devolución ingresa 3 y escribe saldo 3. Un acumulado único daría 13: se conserva la discontinuidad de ámbito, sin declararla un recuento ni inventar una operación compensatoria.','revision':{'interpretacion_ambito':'PENDIENTE','hallazgos':['HOJA_COMPLETA_COTEJADA','AMBITO_STAND_NO_CONCILIADO']}},
        4715:{'revision':{'lectura_saldo_parcial':'Guion en SALDO; no hay cero numérico escrito.'}},
        4732:{'motivo':'Sala Exp. se conserva como lugar literal; no se crea ni se fusiona con un área institucional.'},
        4771:{'criterios':['T02'],'motivo':'Compra Trompo tiene 1 en SALIDAS, no INGRESOS, y el papel baja de 554 a 553.'},
        4773:{'motivo':'543 - salida 10 = 533, pero el papel escribe 534. La diferencia de una unidad continúa en las filas posteriores; no se ajusta la cantidad para cuadrarla.'},
        4787:{'criterios':['T14'],'motivo':'El mes de la fecha está repasado de 10 a 9: se conserva 26-09 como última lectura visible, sin anular el movimiento.'},
        4804:{'revision':{'lectura_fecha_parcial':'7-5/6-13'}},
        4817:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'CEDOAL cruza REF/ÁREA; se conserva su atribución actual en ÁREA con incertidumbre de columna, sin certificarla como resuelta.'},
        4870:{'motivo':'La devolución 1 del 12-08-25 sigue a una salida 8 del mismo día y está en un renglón distinto: ambos se conservan, sin deduplicarlos por compartir fecha.'},
    }
    plan=construir(version=17,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(4747,4748),(4756,4757),(4764,4765),(4775,4776),(4786,4787),(4798,4799),(4839,4840),(4851,4852)],
        bases={81:{'primera_fila':4711,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Base cero solo para explorar un acumulado único. La primera fila dice Ingreso al STAND: no acredita la base disponible general ni un conteo previo.'}},
        observaciones=[{'articulo_id':81,'observado':True,'excluir_entrenamiento':True,
            'motivo':'Siete fotografías y 161 filas cotejadas. Ámbito inicial no conciliado: ingreso al STAND 10 seguido de devolución 3 con saldo 3. Se conservan las cantidades; no se inventa venta 7, salida 10 ni recuento. Un acumulado único da 309 frente al cierre escrito 300, con otra diferencia local de 1 en 2012. Los saldos intermedios incompatibles con el papel son hipótesis. Se conserva cierre escrito 300 con alerta matemática, sin apertura automática; artículo excluido del entrenamiento hasta resolver el ámbito.'}],extras=extras)
    assert plan['cotejo']['cierres']=={81:309}
    assert plan['cotejo']['discrepancias']==[{'id':4712,'local':-10,'acumulada':-10},{'id':4773,'local':1,'acumulada':-9}]
    for e in plan['revisiones']:
        rev=e['revision'];escrito=rev['saldo_documental']
        if escrito is not None and escrito!=e['cambios']['saldo_registrado']:
            rev['origen_saldo']='HIPOTESIS';rev['motivo']+=' Saldo de consulta condicional a un único acumulado: el alcance STAND/general no está conciliado. No acredita existencias.'
            rev['hallazgos']=sorted(set(rev['hallazgos']+['AMBITO_STAND_NO_CONCILIADO']))
        if e['id']==4871:
            # Conservar la duda operativa: no sustituir el cierre escrito por
            # una hipótesis que el inventario podría congelar como apertura.
            e['cambios']['saldo_registrado']=300
            rev.update(origen_saldo='FOTO',usar_saldo_esperado=False)
            rev['motivo']='Cierre escrito 300 conservado. El acumulado único condicional da 309; se mantiene alerta de saldo por ámbito inicial no conciliado y queda bloqueada la apertura automática, sin crear un ajuste.'
    plan['cotejo'].update(cierres={81:300},cierres_calculados={81:309},pendientes_documentales={'4871':['saldo']},
        limite_cierre='300 es el cierre escrito conservado, pendiente de conciliación de ámbito; no es un saldo validado para operar.')
    return plan


if __name__=='__main__':congelar(generar())
