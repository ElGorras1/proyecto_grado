"""Ocho fotos completas: diferencia del papel, cancelación omitida y fechas literales."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND
from scripts.generar_continuacion_28 import recuperada

HOJAS=[
 (range(666,692),[10,-5,-3,7,-2,-2,-2,15,-1,-3,-1,1,-1,-2,2,-8,7,-3,-3,1,-5,4,-5,2,5,-1],
  [10,5,2,9,7,5,3,18,17,14,13,14,13,11,13,6,13,10,7,8,3,7,2,4,9,8]),
 (range(692,705),[1,-3,3,-5,5,-5,5,-3,-2,1,3,-1,-1],[9,6,9,4,9,4,9,6,4,5,8,7,6]),
 (range(7737,7763),[5,-1,-1,-1,-5,-1,-1,-1,5,-1,-3,3,-1,-10,5,1,-1,-1,1,-1,-10,8,-2,20,-5,3],
  [40,39,38,37,32,31,30,29,34,33,30,33,32,22,27,28,27,26,27,26,16,24,22,42,37,40]),
 (range(7763,7776),[1,-10,9,-2,1,-12,-8,-2,-1,-1,-2,-1,-1],[41,31,40,38,39,27,19,17,16,15,13,12,11]),
 (range(8054,8079),[20,-5,-10,7,-3,1,-8,20,-15,-5,3,-2,-1,-1,10,-10,5,-5,5,-1,5,-7,-1,-2,6],
  [20,15,5,12,9,10,2,22,7,2,5,3,2,1,11,1,6,1,6,5,10,3,2,0,6]),
 (range(8079,8088),[3,3,-4,-4,3,-4,-3,15,-6],[9,12,8,4,7,3,0,15,9]),
 (range(8667,8693),[50,-8,-5,-15,16,-1,-1,-1,-5,-1,-1,-1,2,-5,-4,-3,3,-3,-1,-3,-10,-1,1,-1,15,-3],
  [50,42,37,22,38,37,36,35,30,29,28,27,29,24,20,17,20,17,16,13,3,2,3,2,17,14]),
 (range(8693,8702),[1,-5,-8,9,4,-1,-10,3,-3],[15,10,2,11,15,14,4,7,4]),
]

def generar():
    snapshot='backups/continuacion_hil_54_20261015/articulos_13_141_155_190_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CDOAL','CODOL','CEDOSL','EDOAL','CEDOC')}
    for id,fields in {
        673:{'detalle':'INGRESO','referencia':'CBBA'},674:{'area':'GALERIA'},677:{'fecha_movimiento':'2011-05-18'},678:{'detalle':'QUIÑE','referencia':'OBSEQUIO'},
        679:{'detalle':'LLALLAGUA','referencia':'VENTAS'},680:{'detalle':'LLALLAGUA'},691:{'detalle':'LETRAS PACEÑAS'},692:{'detalle':'LETRAS PACEÑAS'},693:{'detalle':'LARGA NOCHE MUSEOS'},694:{'detalle':'LARGA NOCHE MUSEOS'},
        7756:{'detalle':'LLALLAGUA'},7760:{'referencia':'CBBA','area':None},8081:{'detalle':'FIL'},
        8668:{'referencia':'Sala'},8674:{'detalle':'Dona. J.E.B.'},8677:{'detalle':'Donación CEFOI'},8690:{'area':'GALERIA'},8691:{'referencia':'CBB','area':None},8698:{'detalle':'VENTA - CEDOAL'},8699:{'fecha_movimiento':'2013-10-02'},8700:{'fecha_movimiento':'2013-11-04'},
    }.items():cambios.setdefault(id,{}).update(fields)
    for id in (7774,7775):cambios.setdefault(id,{})['orden_fila']=rows[id]['orden_fila']+1
    tecnicas={
        681:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 aparece después de 02-08-11; fecha literal y consulta técnica conservadas, sin reordenar físicamente.'),
        687:('2012-07-24','SECUENCIA_AJUSTADA','2012-07-14','14-7-12 aparece después de 24-7-12. Se conserva literal, sin cambiar julio a agosto por otra hoja parecida.'),
        690:('2012-10-04','HIPOTESIS',None,'FL CBBA. DEV tiene FECHA vacía; consulta técnica del antecedente sin inventar fecha escrita.'),
        7761:('2012-07-30','SECUENCIA_AJUSTADA','2012-07-24','24-7-12 aparece después de 30-7-12; literal y consulta técnica conservadas.'),
        7770:('2016-09-19','HIPOTESIS',None,'FIL 17 tiene FECHA vacía. Se conserva consulta técnica del antecedente, sin inventar día ni confirmar gestión 2017.'),
        8055:('2012-07-30','SECUENCIA_AJUSTADA','2012-07-24','24-7-12 aparece después de 30-7-12. Literal y consulta técnica del antecedente conservadas.'),
        8060:('2012-10-04','SECUENCIA_AJUSTADA','2012-10-02','2-10-12 aparece después de 4-10-12. Se conserva literal, sin cambiar el año para ordenar.'),
        8068:('2014-07-17','HIPOTESIS',None,'INGRESO 10 tiene FECHA vacía; consulta técnica del antecedente 17-7-14, no fecha documental confirmada.'),
        **{id:('2017-02-22','HIPOTESIS',None,'INGRESO y FIL carecen de fecha propia; consulta técnica del antecedente 22-2-17, sin fecha documental inventada.') for id in (8074,8075)},
        8076:('2017-02-22','SECUENCIA_AJUSTADA','2012-12-19','19-12-12 literal aparece después de 22-2-17. No se cambia a 2017 por contexto; consulta técnica del antecedente y fecha escrita conservadas.'),
        8697:('2012-10-14','HIPOTESIS',None,'Día de devolución está repasado, 4/14 no inequívoco. Se conserva consulta técnica existente sin elegir por frecuencia de otras hojas.'),
    }
    extras={
        673:{'criterios':['T23'],'motivo':'Cbba pertenece a REF y no a ÁREA ni solo a DETALLE; se conserva posición documental sin crear institución abreviada.', 'revision':{'columnas_documentales':{'detalle':'INGRESO','referencia':'cbba'}}},
        674:{'criterios':['T01'],'motivo':'ÁREA visible GALERIA, no SALIDA; no se crea área con nombre de operación.'},
        677:{'criterios':['T01'],'motivo':'La fotografía escribe 18-05-11 y no 18-04-11.'},
        681:{'criterios':['T05'],'motivo':'SALIDA 8 visible desde saldo 13 escribe saldo 6, frente a cálculo 5. Diferencia +1 persiste hasta cierre escrito 6 frente a cálculo 5; no se cambia el 8 a 7 para cuadrar.'},
        7760:{'criterios':['T23'],'motivo':'CBBA está en ÁREA como procedencia de recepción. Se conserva en referencia y columna documental, sin crear nueva área abreviada.', 'revision':{'columnas_documentales':{'area':'CBBA'}}},
        7772:{'criterios':['T16'],'motivo':'Atribución abreviada final CID/CIO no inequívoca; lectura vigente CID conservada como pendiente, sin identificar institución ni crear alias.', 'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'revision':{'atribucion_documental_ambigua':True,'candidatos_area_documental':['CID','CIO']}},
        8078:{'criterios':['T14','T16'],'motivo':'INGRESO 6 y saldo 6 legibles con cifra anterior ennegrecida en SALIDAS. No se cuenta una operación oculta ni se anula la recepción. Atribución CID/CIO no inequívoca, vigente CIO conservada pendiente sin alias.', 'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'revision':{'marcas_documentales':{'salidas':'Cifra anterior ennegrecida, sin cantidad adicional inequívoca.'},'atribucion_documental_ambigua':True,'candidatos_area_documental':['CID','CIO']}},
        8668:{'criterios':['T23'],'motivo':'Sala está en REF y Dirección en ÁREA; se corrige Salz sin fusionar ni crear instituciones.'},
        8686:{'criterios':['T14'],'motivo':'Salida 3 legible junto a marca anterior ennegrecida y saldo 13 repasado; se conserva una sola salida activa, sin cancelar el renglón.', 'revision':{'marcas_documentales':{'salidas':'3 visible junto a trazo anterior ennegrecido.','saldo':'13 con cifra final repasada.'}}},
        8691:{'criterios':['T23'],'motivo':'CBB en ÁREA identifica procedencia literal de recepción; se conserva en REF y con posición documental, sin crear institución nueva.', 'revision':{'columnas_documentales':{'area':'CBB.'}}},
        8697:{'criterios':['T16'],'revision':{'fecha_documental_texto':'?4-10-12, día repasado 4/14 no inequívoco.','candidatos_fecha_documental':['2012-10-04','2012-10-14']}},
        8699:{'criterios':['T01'],'motivo':'La foto escribe 2-10-13, no 2-02-13.'},8700:{'criterios':['T01'],'motivo':'La foto escribe 4-11-13, no 4-01-13.'},
    }
    plan=construir(version=54,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={13:{'primera_fila':666,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 10; base anterior cero inferida sin recuento.'},
            141:{'primera_fila':7737,'saldo_base':35,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso 5 y saldo 40; base anterior 35 solo inferida, sin recepción ficticia.'},
            155:{'primera_fila':8054,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 20; base anterior cero inferida.'},
            190:{'primera_fila':8667,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 50; base anterior cero inferida.'}},
        observaciones=[
            {'articulo_id':13,'observado':True,'excluir_entrenamiento':True,'motivo':'Dos fotos completas y 39 filas cotejadas. Salida 8 desde saldo 13 escribe 6 frente a cálculo 5, diferencia +1 persistente hasta cierre escrito 6 frente a cálculo 5. No se cambia la cantidad a 7. Fecha 18-05-11, GALERIA y Llallagua recuperados, fechas fuera de orden conservadas y devolución sin fecha sigue técnica. Apertura bloqueada y artículo excluido del entrenamiento.'},
            {'articulo_id':141,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos y 39 filas OCR cotejadas, más ingreso completamente tachado omitido recuperado sin efecto, conservando números y fecha ocultos sin certificar. Base 35 inferida, procedencia CBBA y fecha 24-7-12 fuera de orden identificadas. FIL 17 sin fecha permanece técnico; abreviación CID/CIO no se resuelve por similitud. Cierre 11 coincide.'},
            {'articulo_id':155,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 34 filas cotejadas. Ingreso 10, ingreso 5 y FIL 7 sin fecha propia conservan consulta técnica. 24-7-12, 2-10-12 y 19-12-12 fuera de orden conservan literales, sin cambiar años para ordenar. Ingreso 6 y saldo 6 con celda opuesta ennegrecida siguen activos; atribución CID/CIO queda pendiente. Cierre 9 coincide.'},
            {'articulo_id':190,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 35 filas cotejadas. Sala/Dirección separados por columna, GALERIA y procedencia CBB recuperados sin alias. Salida 3 con corrección de celda sigue activa. Fechas 2-10-13 y 4-11-13 recuperadas del OCR; día de devolución 4/14 repasado permanece hipotético sin escoger por otras hojas. Cierre 4 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={13:5,141:11,155:9,190:4},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':681,'local':1,'acumulada':1}],plan['cotejo']
    for e in plan['revisiones']:
        if e['id']==704:e['cambios']['saldo_registrado']=6;e['revision'].update(usar_saldo_esperado=False,origen_saldo='FOTO')
    anulada=recuperada(rows,7773,rows[7773]['orden_fila']+1,clave='art141-ingreso-tachado-despues7773-v1',detalle='Ingreso completamente tachado antes de FIL 2021',fecha='2019-08-12',saldo=13,tipo='ANULADO',
        motivo='Entre FIL-2019 y FIL-2021 hay un renglón de INGRESO completamente tachado en fecha, detalle, cantidad y saldo, omitido por OCR. Se conserva ANULADO_DOCUMENTO sin efecto, sin certificar cifras ni fecha cubiertas; fecha y saldo vigentes solo de almacenamiento técnico del antecedente.')
    anulada['campos']['numero_pagina']=2
    anulada['revision'].update(fecha_documental_texto='Fecha completamente tachada; no inequívoca.',marcas_documentales={'detalle':'INGRESO tachado.','ingresos':'Cifra completamente tachada.','saldo':'Cifra completamente tachada.'})
    plan['recuperaciones']=[anulada]
    plan['cotejo'].update(movimientos=148,cierres={13:6,141:11,155:9,190:4},cierres_calculados={13:5,141:11,155:9,190:4},pendientes_documentales={704:['saldo']},
        limites_cierre={13:'Cierre escrito 6 frente a cálculo 5. Salida 8 desde saldo 13 escribe 6, diferencia +1 persistente. Apertura bloqueada y artículo excluido del entrenamiento; no se reduce la salida ni se inventa operación.'})
    return plan

if __name__=='__main__':congelar(generar())
