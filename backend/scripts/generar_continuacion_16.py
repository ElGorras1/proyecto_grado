"""Juan Carlos Orihuela: siete fotografías completas cotejadas."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(4872,4898),[200,-8,4,-117,-1,-1,1,-1,-1,25,-2,-1,-1,-10,-40,38,-10,-1,-3,-1,-8,-1,-5,-1,-15,17],
  [200,192,196,79,78,77,78,77,76,101,99,98,97,87,47,85,75,74,71,70,62,61,56,55,40,57]),
 (range(4898,4924),[-1,-1,-1,-1,-1,-3,3,-5,-10,-2,-1,-8,-5,-1,3,-3,-1,-10,-3,-4,1,1,-1,100,100,300],
  [56,55,54,53,52,49,52,47,37,35,34,26,21,20,23,20,19,9,6,2,3,4,3,103,203,503]),
 (range(4924,4950),[-2,2,-3,-2,2,-1,-10,-10,-75,8,-2,-3,-3,-1,-30,-5,-10,13,-5,-1,1,-1,-2,3,-2,2],
  [501,503,500,498,500,499,489,479,404,412,410,407,404,403,373,368,358,371,366,365,366,365,363,366,364,366]),
 (range(4950,4976),[-2,-1,-1,1,5,-1,-1,1,-1,1,-10,-5,-1,13,-3,-5,6,-5,-1,-1,-1,5,-1,-1,-10,5],
  [364,363,362,363,368,367,366,367,366,367,357,352,351,364,361,356,362,357,356,355,354,359,358,357,347,352]),
 (range(4976,5001),[-2,-1,-3,-5,3,-5,-4,-1,5,-3,-1,-6,1,-3,-2,-5,-1,-1,4,-1,-1,-1,-2,-2,-4],
  [350,349,346,341,344,339,335,334,339,336,335,329,330,327,325,320,319,318,322,321,320,319,317,315,311]),
 (range(5001,5027),[-1,-1,-3,-2,-3,-5,3,-2,-5,-2,-3,-2,-2,-1,-1,1,-2,-1,-1,-9,-3,-3,-2,-2,-3,-2],
  [310,309,306,304,301,296,299,297,292,290,287,285,283,282,281,282,280,279,278,269,266,263,261,259,256,254]),
 (range(5027,5038),[-2,-5,-3,-4,-20,-5,2,-5,5,-8,-5],[252,247,244,240,220,215,217,212,217,209,204]),
]


def generar():
    snapshot='backups/continuacion_hil_16_20261015/articulo_82_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={}
    for id,r in rows.items():
        if r['area'] in ('Cedozel','CEDOC','EDOSAL'):cambios[id]={'area':'CEDOAL'}
    for id,fields in {4902:{'referencia':'Ventas','area':None},4903:{'referencia':'Ventas','area':'Cedoal'},
        4908:{'referencia':'Bibliot.','area':'Dirección'},4909:{'referencia':'SCZ','area':'CAP'},4910:{'referencia':'Ventas','area':'Cedoal'},
        4932:{'fecha_movimiento':'2012-05-22'},4947:{'detalle':'Devolucion'},4973:{'detalle':'Jesus te ama'},4978:{'detalle':'Noira Quiroga'},
        4992:{'detalle':'Cueva Cuentacuento'},4993:{'detalle':'Biblio - Uncia'},4997:{'fecha_movimiento':'2017-04-06'},
        5004:{'detalle':'OBSQ.','referencia':'OBSQ'},5007:{'area':'CID'}}.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        4901:('2009-09-02','SECUENCIA_AJUSTADA','2009-08-21','21-08-09 después del 02-09: consulta técnica del antecedente, con literal conservada.'),
        **{id:('2012-08-21','SECUENCIA_AJUSTADA',fecha,'Fecha de julio/agosto escrita después del 21-08: consulta técnica del antecedente, sin certificar otra fecha real.') for id,fecha in [(4939,'2012-07-24'),(4940,'2012-08-05'),(4941,'2012-08-14')]},
        5000:('2017-05-20','HIPOTESIS',None,'FIL tiene fecha en blanco; consulta con el antecedente, sin acreditar fecha propia.'),
        5016:('2022-10-17','HIPOTESIS',None,'Devolución con fecha en blanco: fecha técnica del antecedente y ausencia documental conservada.'),
    }
    extras={
        4875:{'motivo':'Salida 117 visible y consistente: 196 - 117 = 79. La cantidad elevada se conserva.'},
        4887:{'criterios':['T03'],'motivo':'La devolución tiene INGRESOS 38 y (38) en SALIDAS. El paréntesis conserva una marca de rectificación, sin segunda salida: 47 + 38 = 85.','revision':{'marcas_documentales':{'salidas':'(38)'}}},
        4902:{'criterios':['T23'],'motivo':'Ventas está en REF de esta foto y ÁREA está en blanco; no se atribuye al área de otra hoja parecida.'},
        4903:{'criterios':['T23'],'motivo':'REF contiene Ventas y ÁREA Cedoal; se recuperan las columnas.'},
        4908:{'criterios':['T23'],'motivo':'Bibliot. está en REF y Dirección en ÁREA; no se agrupan como un área compuesta.'},
        4909:{'criterios':['T23'],'motivo':'SCZ está en REF y CAP en ÁREA.'},
        4910:{'criterios':['T23'],'motivo':'Ventas está en REF y Cedoal en ÁREA.'},
        4915:{'revision':{'anotacion_documental':'Fecha 14-06 tachada/repasada y corrección 22 al margen: se conserva la lectura final 22-06 en la misma fila, sin crear otro movimiento.'}},
        4940:{'revision':{'anotacion_documental':'El acercamiento confirma 358 repasado en SALDO. La cadena 368 - 10 = 358 y el ingreso siguiente 13 = 371 son consistentes.'}},
        4976:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'CEDOAL cruza REF/ÁREA. Se conserva la atribución en REF con incertidumbre explícita, sin afirmar un área resuelta o ausente.'},
        4994:{'criterios':['T14'],'motivo':'La devolución tiene ingreso 4; el 4 en SALIDAS está tachado. Se conserva la celda cancelada sin reducir otra vez el saldo y sin anular el movimiento.','revision':{'marcas_documentales':{'salidas':'4 tachado'}}},
        5018:{'criterios':['T02','T14'],'motivo':'El acercamiento permite leer salida 1 y saldo final 279 sobre una rectificación blanca. Se conserva la última lectura visible, no el texto cubierto: 280 - 1 = 279.','revision':{'anotacion_documental':'Correcciones blancas presentes en la foto; el 1 final está legible y el 9 de 279 está escrito sobre la corrección. No se reconstruye el texto anterior tapado.'}},
    }
    for id in cambios:
        if cambios[id].get('area')=='CEDOAL':extras.setdefault(id,{})['motivo']=extras.get(id,{}).get('motivo','')+' Lectura literal de ÁREA recuperada desde la foto; no se crean áreas ni alias.'
    plan=construir(version=16,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(4932,4933),(4944,4945),(4956,4957),(5001,5002),(5019,5020)],
        bases={82:{'primera_fila':4872,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 200: base cero inferida, sin acreditar recuento previo.'}},
        observaciones=[{'articulo_id':82,'observado':True,'excluir_entrenamiento':False,
            'motivo':'Siete fotografías y 166 filas cotejadas. Cierre 204 coincide con el papel. Devoluciones 38 y 4 conservan sus marcas entre paréntesis/tachadas sin doble efecto; FIL es salida 1 y saldo 279 rectificados en la foto. Fechas técnicas y atribución REF/ÁREA pendiente siguen identificadas.'}],extras=extras)
    assert plan['cotejo']['cierres']=={82:204} and plan['cotejo']['discrepancias']==[]
    return plan


if __name__=='__main__':congelar(generar())
