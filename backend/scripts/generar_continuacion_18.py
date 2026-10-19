"""Paisaje sin fronteras: tres fotografías, base documental sin ingreso inventado."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(5214,5240),[0,-1,-1,-2,-1,-20,-24,-3,-34,-12,-1,-3,-2,-1,-1,-4,-5,2,-30,-1,-1,-2,-1,-2,-1,-3],
  [223,222,221,219,218,198,174,171,137,125,124,121,119,118,117,113,108,110,80,79,78,76,75,73,72,69]),
 (range(5240,5266),[-5,-1,-1,-1,-20,1,-1,-3,-3,-2,5,-1,-1,1,-1,-1,-1,-1,-10,-4,3,-1,-1,-3,3,2],
  [64,63,62,61,41,42,41,38,35,33,38,37,36,37,36,35,34,33,23,19,22,21,20,17,20,22]),
 (range(5266,5277),[-1,-1,2,-18,9,-1,-1,-1,-2,-4,6],[21,20,22,4,13,12,11,10,8,4,10]),
]


def generar():
    snapshot='backups/continuacion_hil_18_20261015/articulo_84_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    # Son números de documento escritos en ÁREA, no nombres de áreas. Su
    # posición física se conserva expresamente en la revisión y en el original.
    for id in (5218,5219,5224,5226,5227,5229,5236,5237,5238):
        r=rows[id];area='ESIP' if id in (5218,5219,5224,5236,5237,5238) else None
        cambios[id]={'referencia':r['area'],'area':area}
        extras[id]={'criterios':['T17','T23'],'motivo':'El papel usa ÁREA para un código de documento. Se representa el código en REF y ESIP como área solo donde ESIP está escrito en esa misma fila; si falta, no se atribuye una institución.',
            'revision':{'columnas_documentales':{'referencia':r['referencia'],'area':r['area']},'normalizacion_columnas':'CODIGO_DOCUMENTAL_EN_REF'}}
    for id,r in rows.items():
        if r['area'] in ('Cedral','CDOAL','CEDASC','CEDDAL'):
            cambios.setdefault(id,{})['area']='CEDOAL'
            extras.setdefault(id,{}).update(motivo='Lectura literal CEDOAL recuperada en la fotografía, sin crear áreas ni alias.')
    cambios.update({5220:{'detalle':'Cedoal. Taller de S. Pellicc.'},5222:{'detalle':'Cedoal Bibliotecas Unicas'},
        5234:{'detalle':'Donacion Coroico','area':'Cedoal'},5244:{'area':'CAP'},
        5245:{'referencia':'022/08'},5273:{'detalle':'BIBLIO - UNCIA','area':'CEDOAL'}})
    tecnicas={
        5214:('2007-08-01','HIPOTESIS',None,'Primera fila sin fecha: consulta técnica del primer renglón fechado, no una fecha acreditada del saldo inicial.'),
        5230:('2007-12-06','SECUENCIA_AJUSTADA','2007-10-16','16-10-07 escrito después del 06-12: consulta técnica del antecedente, sin certificar otra fecha.'),
        5231:('2007-12-06','HIPOTESIS',None,'Fecha de la devolución en blanco. La fecha al margen de una firma no acredita inequívocamente el día del movimiento; consulta técnica del antecedente.'),
        5232:('2008-01-15','HIPOTESIS',None,'Día manuscrito 00/06 de marzo de lectura dudosa, antes del 15-01. Se usa fecha técnica del renglón siguiente y se conserva lectura parcial.'),
        5236:('2008-02-11','SECUENCIA_AJUSTADA','2008-01-12','La foto escribe 12-01-08 después de 11-02-08; la extracción decía febrero. Se conserva enero como literal y febrero solo como fecha de consulta del antecedente.'),
        5245:('2008-05-29','SECUENCIA_AJUSTADA','2008-03-13','13-03-08 está escrito después del 29-05-08; se conserva la literal y una consulta técnica del antecedente.'),
    }
    extras.update({
        5214:{'criterios':['T16'],'motivo':'Hay saldo 223 y ningún número en INGRESOS o SALIDAS. Se conserva como base documental inicial sin inventar un ingreso de 223 ni un recuento físico.',
            'clasificacion':{'nodo_grafo':'Origen no especificado','area_estado':'SIN_AREA_REGISTRADA','requiere_auditoria_nodo':False},
            'revision':{'tipo_fila':'BASE_DOCUMENTAL','cantidades_documentales':{'ingresos':None,'salidas':None}}},
        5231:{'revision':{'anotacion_documental':'Fecha al margen junto a firma; no se asocia como fecha confirmada del renglón.'}},
        5232:{'revision':{'lectura_fecha_parcial':'00/06-03-08'}},
        5234:{'criterios':['T18'],'motivo':'Las comillas de ÁREA repiten Cedoal de la misma columna anterior; no se trata como un área llamada comillas.'},
        5235:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'Abreviatura de área AR/AB no inequívoca; se conserva la lectura original y la duda, sin asignarla por semejanza.'},
        5245:{'criterios':['T23'],'motivo':'022/08 es un código de documento escrito en ÁREA; se representa en REF conservando su posición física y sin inferir un área.',
            'revision':{'columnas_documentales':{'referencia':None,'area':'022/08'}}},
        5271:{'criterios':['T02','T14','T19'],'motivo':'Expo tiene una cifra en SALIDAS repasada/tachada y saldo final 12 corregido. Desde 13, la salida 1 es hipótesis por continuidad; no es un ingreso 15 ni se anula toda la fila. La abreviatura de ÁREA continúa pendiente.',
            'revision':{'origen_cantidades':'HIPOTESIS','marcas_documentales':{'salidas':'1 y cifra siguiente repasada/tachada','saldo':'valor tachado, final 12'},'lectura_area_parcial':'G?E'},
            'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True}},
    })
    plan=construir(version=18,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={84:{'primera_fila':5214,'saldo_base':223,'origen_saldo_base':'FOTO','motivo_base':'223 es el saldo inicial escrito sin cantidad de ingreso: base documental, no alta ni conteo físico inventado.'}},
        observaciones=[{'articulo_id':84,'observado':True,'excluir_entrenamiento':False,
            'motivo':'Tres fotografías y 63 filas cotejadas. Base escrita 223 sin cantidad de ingreso: se conserva sin fabricar una entrada. Cierre 10 coincide con el papel bajo la salida 1 hipotética de Expo, que está tachada/repasada y queda excluida del entrenamiento. Fechas técnicas, dos abreviaturas de área pendientes y columnas documentales originales conservadas.'}],extras=extras)
    assert plan['cotejo']['cierres']=={84:10} and plan['cotejo']['discrepancias']==[]
    return plan


if __name__=='__main__':congelar(generar())
