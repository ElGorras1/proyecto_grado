"""Cinco fotos completas con cancelación expresa y cierre discrepante conservado."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(2621,2646),[300,-31,-1,-1,-3,-9,-6,-1,-2,-1,-5,-1,-6,-4,-2,-10,-2,-1,-1,-2,-2,1,-1,-10,-1],[300,269,268,267,264,255,249,248,246,245,240,239,233,231,229,219,217,216,215,213,211,212,211,201,200]),
 (range(7835,7861),[-3,-1,-1,-1,-3,1,-1,10,-5,-5,10,-5,5,-1,-1,-3,-5,-2,1,-1,10,-3,-5,-2,1,-2],[10,9,8,7,4,5,4,14,9,4,14,9,14,13,12,9,4,2,3,2,12,9,4,2,3,1]),
 (range(8088,8113),[-10,10,1,-1,1,-1,1,-10,10,-1,-2,1,-5,5,1,-10,10,-1,-2,2,-3,-4,-2,-1,-1],[19,29,30,29,30,29,30,20,30,29,27,28,23,28,29,19,29,28,26,28,25,21,19,18,17]),
 (range(8113,8116),[-1,-1,-1],[16,15,14]),
 (range(10992,11015),[10,-1,-3,-3,2,-3,3,15,-15,9,-3,-3,3,-5,3,4,-10,9,-3,0,-2,2,-2],[10,9,6,3,5,2,5,20,5,14,11,8,11,6,9,13,3,12,9,None,7,9,7]),
]

def generar():
    snapshot='backups/continuacion_hil_61_20261016/articulos_58_144_156_325_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDOOL')}
    for id,fields in {
        2628:{'area':None},2631:{'area':None},2633:{'fecha_movimiento':'2016-11-11'},
        7840:{'area':'ESIP'},7855:{'referencia':'Cbba','area':None},
        8108:{'area':'Lucy'},8113:{'detalle':'Ventas CID','area':'CID'},8114:{'detalle':'FIL'},
        10992:{'fecha_movimiento':'2010-07-20'},10994:{'detalle':'PARA VENTA'},10997:{'detalle':'LLALLAGUA'},10998:{'detalle':'LLALLAGUA'},11011:{'estado':'ANULADO_DOCUMENTO'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        2636:('2017-07-06','HIPOTESIS',None,'FIL tiene FECHA vacía; consulta técnica del antecedente, no fecha escrita.'),
        **{id:('2008-05-19','HIPOTESIS',None,'Donación sin fecha propia; consulta técnica del antecedente 19-5-08, no fecha documental certificada.') for id in (7837,7838)},
        7840:('2008-05-29','HIPOTESIS',None,'Devolución sin fecha propia; consulta técnica del antecedente 29-5-08.'),
        7856:('2010-06-30','SECUENCIA_AJUSTADA','2010-02-21','La foto escribe 21-02-10 después de 30-6-10. Se conserva literal y consulta técnica del antecedente, sin mover las operaciones.'),
        8095:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 aparece después de 02-08-11; literal y consulta técnica conservados.'),
        8110:('2016-09-19','HIPOTESIS',None,'FIL 17 tiene FECHA vacía; consulta técnica del antecedente, sin certificar 1-1-2016 ni fabricar día de 2017.'),
        10999:('2011-08-02','SECUENCIA_AJUSTADA','2011-07-12','12-07-11 aparece después de 02-08-11; literal y orden físico conservados.'),
        11011:('2014-07-29','HIPOTESIS',None,'Fecha completamente tachada; contexto técnico del antecedente, no lectura de lo oculto.'),
        **{id:('2014-07-29','HIPOTESIS',None,'FECHA vacía después del renglón tachado; consulta técnica del último antecedente legible, no fecha del hecho.') for id in (11012,11013)},
    }
    extras={
        **{id:{'criterios':['T14'],'motivo':'ÁREA contiene una palabra completamente tachada. Se conserva esa celda ausente, sin anular la salida legible ni crear área GEP/LEG.', 'revision':{'columnas_documentales':{'area':'Palabra completamente tachada, sin lectura inequívoca.'}}} for id in (2628,2631)},
        2630:{'criterios':['T14'],'motivo':'Pequeña marca en INGRESOS no aporta cantidad acreditada; salida 1 legible y saldo 245 conservados, sin ingreso adicional.', 'revision':{'marcas_documentales':{'ingresos':'Pequeña marca sin cifra acreditada.'}}},
        2633:{'criterios':['T01'],'motivo':'La foto escribe 11-11-16, no 14-11-16.'},
        2634:{'criterios':['T05'],'motivo':'Salida 4 legible desde 233 escribe saldo 231 frente a cálculo 229. Diferencia +2 persiste hasta cierre, sin cambiar cantidad 4 a 2.'},
        2636:{'criterios':['T19'],'motivo':'Cantidad de FIL tiene primer dígito estilizado 10/40 no inequívoco en acercamiento. Se conserva vigente 10 solo hipotético; no se decide por el saldo 219 ni se certifica el egreso. Cálculo condicional 198 sería 168 con salida 40.', 'revision':{'origen_cantidades':'HIPOTESIS','candidatos_salidas_documentales':[10,40],'cantidad_documental_texto':'10/40, primer dígito no inequívoco.'}},
        7855:{'criterios':['T23'],'motivo':'Cbba está en REF, no ÁREA; columnas conservadas desde foto sin crear institución ni alias.', 'revision':{'columnas_documentales':{'referencia':'Cbba','area':None}}},
        8097:{'criterios':['T16'],'motivo':'Texto de ÁREA junto a Alonzo Francesa no es inequívoco. Se conserva literal OCR BOLSRID como pendiente, sin inventar institución por semejanza.', 'revision':{'atribucion_documental_ambigua':True}, 'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True}},
        8103:{'criterios':['T14'],'motivo':'Año 13 repasado legible; se conserva 2-10-13 y salida 10, sin anular el renglón por corrección de una celda.'},
        11011:{'criterios':['T14'],'motivo':'Fila completa tachada en fecha, detalle, ingreso y saldo. Se conserva ANULADO_DOCUMENTO sin efecto; no se suman ingreso 5 ni saldo 14 OCR ocultos por tachadura.', 'revision':{'tipo_fila':'ANULADO','origen_cantidades':'HIPOTESIS','marcas_documentales':{'fecha':'Completamente tachada.','detalle':'Completamente tachado.','ingresos':'Cifra completamente tachada.','saldo':'Cifra completamente tachada.'}}},
        11012:{'criterios':['T16'],'motivo':'Referencia tiene trazo pequeño abierto 0/C no inequívoco. Se conserva lectura vigente 0 como incierta, sin nueva referencia ni alias.', 'revision':{'referencia_documental_ambigua':True,'candidatos_referencia_documental':['0','C']}, 'clasificacion':{'referencia_estado':'INCIERTA','requiere_auditoria_referencia':True}},
        11013:{'criterios':['T14'],'motivo':'Ingreso 2 y saldo final 9 legibles junto a cifra anterior ennegrecida. Se conserva fila activa, sin anularla por la corrección del saldo.'},
    }
    plan=construir(version=61,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={58:{'primera_fila':2621,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Ingreso y saldo 300 explícitos; base previa cero inferida.'},144:{'primera_fila':7835,'saldo_base':13,'origen_saldo_base':'HIPOTESIS','motivo_base':'Saldo previo 13 inferido desde salida 3 y primer saldo escrito 10, sin nueva recepción.'},156:{'primera_fila':8088,'saldo_base':29,'origen_saldo_base':'HIPOTESIS','motivo_base':'Saldo previo 29 inferido desde salida 10 y primer saldo escrito 19, sin nueva recepción.'},325:{'primera_fila':10992,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Ingreso y saldo 10 explícitos; base previa cero inferida.'}},
        observaciones=[
            {'articulo_id':58,'observado':True,'excluir_entrenamiento':True,'motivo':'Foto completa y veinticinco filas cotejadas. Salida 4 desde 233 escribe 231 frente a cálculo 229, diferencia +2 persistente. Cantidad de FIL 10/40 incierta, vigente 10 solo hipotética; no se elige por la suma. Cierre escrito 200 frente a cálculo condicional 198 (168 si salida 40), artículo excluido y apertura bloqueada. Áreas tachadas conservadas sin anular salidas; fecha 11-11-16 recuperada, FIL sin fecha identificado.'},
            {'articulo_id':144,'observado':True,'excluir_entrenamiento':False,'motivo':'Foto completa y veintiséis filas cotejadas. Base anterior 13 inferida sin ingreso inventado; dos donaciones y devolución sin fecha propia marcadas. Literal 21-02-10 posterior a 30-6-10 conserva fecha escrita y consulta técnica. Cbba en REF y ESIP recuperados por columna, sin alias. Cierre 1 coincide.'},
            {'articulo_id':156,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y veintiocho filas cotejadas. Base anterior 29 inferida sin ingreso ficticio; 1-08-11 posterior al 02-08-11 y FIL 17 sin fecha identificados. Área no inequívoca junto a Alonzo Francesa queda pendiente, sin institución inventada. Lucy, Ventas CID y FIL recuperados por foto, sin alias. Cierre 14 coincide.'},
            {'articulo_id':325,'observado':True,'excluir_entrenamiento':False,'motivo':'Foto completa y veintitrés filas cotejadas. Ingreso completamente tachado se conserva anulado sin efecto y sin certificar cifras ocultas, corrigiendo la falsa recepción 5 OCR. Última devolución 2 con saldo corregido 9 permanece activa. Primera fecha 20-07-10 recuperada y 12-07-11 fuera de orden conserva literal. Dos FIL sin fecha siguen técnicos; referencia 0/C incierta. Cierre 7 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={58:198,144:1,156:14,325:7} and plan['cotejo']['discrepancias']==[{'id':2634,'local':2,'acumulada':2}],plan['cotejo']
    cierre=next(e for e in plan['revisiones'] if e['id']==2645)
    cierre['cambios']['saldo_registrado']=200
    cierre['revision'].update(usar_saldo_esperado=False,origen_saldo='FOTO')
    plan['cotejo'].update(cierres={58:200,144:1,156:14,325:7},cierres_calculados={58:198,144:1,156:14,325:7},pendientes_documentales={2645:['saldo']},limites_cierre={58:'Cierre escrito 200 frente a cálculo condicional 198; salida FIL 10/40 incierta. Si fuera 40 el cálculo sería 168. Exclusión del artículo y apertura bloqueada, sin modificar cantidades para cuadrar.'})
    return plan

if __name__=='__main__':congelar(generar())
