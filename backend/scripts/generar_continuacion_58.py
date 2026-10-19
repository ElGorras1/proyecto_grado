"""Borrador 58 descartado en ensayo; solo antecedente del plan vigente 59.

El plan congelado original permanece intacto en planes_no_aplicados.
La función se conserva para reproducir el generador 59, sin regenerar el 58.
"""
import json
from scripts.cotejo_transcripcion_hil import BACKEND,congelar
from scripts.cotejo_con_anclajes_hil import construir_con_anclajes
from scripts.generar_continuacion_28 import recuperada

HOJAS=[
 (range(1748,1764),[48,-6,-1,-1,-2,-1,-1,-1,-1,-1,-1,-2,-2,-2,-2,2],[48,42,41,40,38,37,36,35,34,33,32,30,28,26,24,26]),
 (range(7711,7737),[10,-1,-1,-1,-1,-1,-2,0,-2,2,20,-5,2,-1,-1,-1,-1,-1,-1,-2,-1,43,-1,-8,-5,-5],[10,None,None,7,6,5,3,None,1,3,23,18,20,19,18,None,None,15,14,12,11,54,53,45,40,35]),
 (range(8116,8129),[3,-3,2,-2,2,-1,2,-1,-1,1,1,-2,-1],[3,None,2,None,2,1,3,2,1,2,3,1,0]),
 (range(8944,8959),[35,-5,-10,15,-11,-1,-3,-12,-3,10,-14,5,-6,2,-2],[35,30,20,35,24,23,20,8,5,15,1,6,None,2,0]),
 (range(9425,9441),[10,-2,-2,-2,-3,-1,5,-5,5,-2,5,-1,-4,-1,5,-4],[10,8,6,4,1,0,5,0,None,3,8,7,3,2,7,3]),
 (range(11441,11458),[20,20,-10,10,-10,20,10,-2,-2,-41,-2,-2,2,-1,-1,-1,-3],[20,40,30,40,30,50,60,58,56,15,13,11,13,12,11,10,7]),
]

def generar():
    snapshot='backups/continuacion_hil_58_20261016/articulos_45_140_157_201_231_357_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    anclajes=[7712,7713,7714,7715,7716,7717,7722,7724,7726,7727]
    cambios={id:{'area':'CEDOAL'} for id in (1755,1757,7720,7724,7729,7735,7736,9427,9428,9429)}
    for id,fields in {
        7718:{'detalle':None,'estado':'NOTA_DOCUMENTAL'},7726:{'detalle':'Donación CONAMAQ'},7727:{'detalle':'Donación UPEA'},
        8127:{'detalle':'VENTAS CID'},8944:{'referencia':'CBBA.','area':None},8945:{'detalle':'LILIANA DE LA QUINTANA'},
        8949:{'detalle':'BIBLIO. CDP.','referencia':'CDP','area':'CDP'},
        9425:{'fecha_movimiento':'2016-02-18'},9426:{'fecha_movimiento':'2016-09-19'},9428:{'detalle':'VENTAS-CEDOAL'},
    }.items():cambios.setdefault(id,{}).update(fields)
    for id in range(9431,9441):cambios.setdefault(id,{})['orden_fila']=rows[id]['orden_fila']+1
    tecnicas={
        **{id:('2015-12-08','SECUENCIA_AJUSTADA','2015-08-22','22-8-15 está escrito después del 8-12-15. Literal y orden físico conservados; consulta técnica del antecedente, no fecha certificada.') for id in (1750,1751)},
        1753:('2016-09-19','HIPOTESIS',None,'CDP sin fecha propia; consulta técnica del antecedente, no fecha escrita.'),
        1755:('2016-11-24','HIPOTESIS',None,'FIL sin fecha propia después de Obsequio C. Educación; consulta técnica del antecedente.'),
        1763:('2022-09-07','HIPOTESIS',None,'Devolución final sin fecha propia; consulta técnica del antecedente, sin certificar fecha de retorno.'),
        7718:('2007-05-29','SECUENCIA_AJUSTADA','2007-04-19','19-04-07 es lo único escrito en el renglón. No hay detalle, cantidad ni saldo; consulta técnica del contexto, conservando literal y nota sin efecto.'),
        7719:('2007-06-10','HIPOTESIS',None,'La foto escribe 10/06/07 con el mes manuscrito no inequívoco 04/06; se conserva consulta técnica existente, sin certificar el mes por la secuencia.'),
        7728:('2008-05-19','FOTO','2008-05-19','Comillas inequívocas en FECHA repiten 19-05-08 de la donación anterior, sin otra operación.'),
        8117:('2013-10-08','SECUENCIA_AJUSTADA','2013-10-02','2-10-13 sigue al ingreso 8-10-13; literal conservado, consulta técnica del antecedente.'),
        8118:('2013-10-08','HIPOTESIS',None,'Ingreso 2 tiene FECHA vacía; consulta técnica del contexto, no 2-10-13 confirmado.'),
        8121:('2015-08-07','SECUENCIA_AJUSTADA','2015-08-03','3-8-15 aparece después de 7-8-15; conservar literal, sin mover las cantidades.'),
        8125:('2019-07-05','SECUENCIA_AJUSTADA','2018-07-23','23-7-18 está escrito después de 5-7-19; conservar el año 2018 literal, sin cambiarlo a 2019 para ordenar.'),
        8954:('2015-08-11','SECUENCIA_AJUSTADA','2015-08-03','3-8-15 aparece después de 11-8-15; conservar literal y consulta técnica del antecedente.'),
        9429:('2017-06-12','HIPOTESIS',None,'FIL con salida 3 tiene FECHA vacía; consulta técnica del antecedente, sin asignar 2019 por la fila siguiente.'),
        9433:('2021-10-01','SECUENCIA_AJUSTADA','2021-02-07','7-2-21 está escrito después de 1-10-21; conservar 2021 literal, sin convertirlo en 2022 para ordenar.'),
        11443:('2013-04-22','SECUENCIA_AJUSTADA','2013-04-18','18-4-13 aparece después de 22-4-13. Consulta técnica del antecedente, literal y filas conservados.'),
        11450:('2015-12-08','HIPOTESIS',None,'Año de 8-12-1? muy repasado, 15/16 no inequívoco. Consulta técnica existente conservada, sin certificarlo por secuencia.'),
        11451:('2015-12-08','HIPOTESIS',None,'FIL tiene FECHA vacía; consulta técnica del antecedente cuya gestión permanece incierta.'),
    }
    extras={
        1763:{'criterios':['T07'],'motivo':'DEVOLUCIÓN escribe 2 en SALIDAS pero saldo sube de 24 a 26. Se conserva la interpretación de ingreso 2 y la columna escrita, sin añadir otra operación.', 'revision':{'columnas_documentales':{'salidas':2}}},
        7718:{'criterios':['T16','T23'],'motivo':'Renglón con solo 19-04-07 en FECHA; DETALLE y cantidades vacíos. Devolución y saldo 3 OCR no aparecen escritos. Se conserva nota sin efecto, sin inventar recepción ni recuento.', 'revision':{'tipo_fila':'NOTA_DOCUMENTAL','origen_cantidades':'HIPOTESIS'}},
        7719:{'criterios':['T16'],'revision':{'fecha_documental_texto':'10/0?/07; mes 04/06 manuscrito no inequívoco.','candidatos_fecha_documental':['2007-04-10','2007-06-10']}},
        7724:{'criterios':['T16'],'motivo':'Nota marginal 13/12/07 se conserva sin sustituir la fecha técnica anterior ya aprobada.', 'revision':{'anotacion_margen_fecha':'13/12/07 al costado, no asignada automáticamente.'}},
        7725:{'criterios':['T02'],'motivo':'Dev. Julio Berker tiene SALIDA 1 y saldo 18 desde 19; se conserva egreso por columna y contexto, sin invertir por el nombre.'},
        7728:{'criterios':['T18']},
        **{id:{'criterios':['T08'],'motivo':'SALDO tiene guion, sin cifra numérica; cero es solo cálculo técnico, no lectura de un cero escrito.', 'revision':{'marcas_documentales':{'saldo':'—'}}} for id in (8117,8119,8956)},
        8944:{'criterios':['T23'],'motivo':'CBBA. ocupa ÁREA como procedencia del ingreso, conservada en referencia sin crear institución ni alias.', 'revision':{'columnas_documentales':{'area':'CBBA.'}}},
        8945:{'criterios':['T23'],'motivo':'DE LA QUINTANA continúa el nombre que cruza DETALLE/REF; se conserva como texto, sin nueva área.'},
        8953:{'criterios':['T16'],'motivo':'Punto aislado en ÁREA conservado pendiente; no se interpreta como comilla ni se copia una institución.', 'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True}},
        9428:{'criterios':['T18'],'motivo':'Comillas inequívocas en ÁREA repiten CEDOAL escrito arriba; lectura de la celda, sin crear alias.'},
        9433:{'criterios':['T19'],'motivo':'Saldo final del renglón tiene forma 5/6 no inequívoca en el acercamiento. Se conserva ausente documental y cálculo 5 hipotético; no se elige una lectura por la siguiente resta.', 'revision':{'saldo_documental_texto':'5/6 no inequívoco.','candidatos_saldo_documental':[5,6]}},
        11450:{'criterios':['T02','T14','T19'],'motivo':'41 está en SALIDAS y saldo 15 es legible; se corrige ingreso 41 y saldo 45 del OCR, sin convertir Devolución en recepción por su nombre. Año repasado no se certifica.', 'revision':{'fecha_documental_texto':'8-12-1?, último dígito repasado 15/16 no inequívoco.','candidatos_fecha_documental':['2015-12-08','2016-12-08']}},
    }
    bases={aid:{'primera_fila':id,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':f'Primer ingreso y saldo {saldo} explícitos; base previa cero inferida, sin recepción adicional.'} for aid,id,saldo in ((45,1748,48),(140,7711,10),(157,8116,3),(201,8944,35),(231,9425,10),(357,11441,20))}
    observaciones=[
        {'articulo_id':45,'observado':True,'excluir_entrenamiento':False,'motivo':'Foto completa y dieciséis filas cotejadas. Dos 22-8-15 posteriores a 8-12-15 conservan literal y consulta técnica. CDP/FIL/Devolución sin fecha propia marcados. Devolución 2 escrita en SALIDAS se interpreta como recepción por saldo 24 a 26, conservando columna. Cierre 26 coincide.'},
        {'articulo_id':140,'observado':True,'excluir_entrenamiento':False,'motivo':'Foto completa y veintiséis filas cotejadas, conservando diez revisiones anteriores íntegras. Renglón 19-04-07 con detalle y cantidades vacíos queda nota sin efecto, sin Devolución ficticia. Mes de curso permanece incierto. CONAMAQ y UPEA recuperados como textos; comillas de fecha y nota marginal preservadas. Cierre 35 coincide.'},
        {'articulo_id':157,'observado':True,'excluir_entrenamiento':False,'motivo':'Foto completa y trece filas cotejadas. Guiones de saldo se conservan como marcas, con cálculo cero técnico. Literales 2-10-13, 3-8-15 y 23-7-18 fuera de orden permanecen visibles; ingreso sin fecha conserva consulta técnica. Cierre cero coincide.'},
        {'articulo_id':201,'observado':True,'excluir_entrenamiento':False,'motivo':'Foto completa y quince filas cotejadas. CDP y nombre que cruza columnas leídos desde foto; procedencia CBBA. conservada sin alias, punto aislado pendiente. Saldo guion y 3-8-15 fuera de orden mantienen hipótesis y literal. Cierre cero coincide.'},
        {'articulo_id':231,'observado':True,'excluir_entrenamiento':True,'motivo':'Foto completa y dieciséis filas OCR cotejadas, más fila totalmente tachada omitida recuperada sin efecto. Fechas iniciales 18-2-16 y 19-9-16 recuperadas; FIL sin fecha propio y 7-2-21 fuera de orden identificados. CEDOAL y comillas recuperados por foto, sin alias. Saldo parcial 5/6 incierto se conserva como hipótesis 5, no elegido por aritmética. Cierre escrito 3 coincide condicionalmente; artículo excluido sin atribuir bloqueo automático por esa exclusión.'},
        {'articulo_id':357,'observado':True,'excluir_entrenamiento':False,'motivo':'Foto completa y diecisiete filas cotejadas. Devolución con SALIDA 41 y saldo 15 legibles corrige ingreso 41/saldo 45 OCR. Año repasado 15/16 no certificado y FIL sin fecha permanecen técnicos. 18-4-13 después de 22-4-13 conserva literal. Cierre 7 coincide.'},
    ]
    plan=construir_con_anclajes(version=58,instantanea=snapshot,anclajes=anclajes,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],bases=bases,tipos={7718:'NOTA_DOCUMENTAL'},observaciones=observaciones,extras=extras)
    assert plan['cotejo']['discrepancias']==[] and plan['cotejo']['cierres']=={45:26,140:35,157:0,201:0,231:3,357:7},plan['cotejo']
    anulada=recuperada(rows,9430,rows[9430]['orden_fila']+1,clave='art231-ingreso-tachado-despues9430-v1',detalle='Ingreso completamente tachado antes de 10-9-21',fecha='2019-08-12',saldo=0,tipo='ANULADO',motivo='Renglón con FECHA, DETALLE, INGRESOS y SALDO completamente tachados entre FIL-2019 y el ingreso 10-9-21. Se recupera como ANULADO_DOCUMENTO sin efecto, sin certificar cifras ocultas. Fecha y saldo técnicos del antecedente, no lectura de lo tachado.')
    anulada['revision']['marcas_documentales']={'fecha':'Completamente tachada.','ingresos':'Cifra ennegrecida no inequívoca.','saldo':'Cifra ennegrecida no inequívoca.'}
    plan['recuperaciones']=[anulada]
    plan['cotejo'].update(movimientos=104,nuevos_distintos=94,limites_cierre={231:'Cierre escrito 3 coincide solo condicionalmente; saldo parcial 5/6 incierto. Exclusión de entrenamiento sin afirmar bloqueo automático.'})
    return plan

if __name__=='__main__':
    raise RuntimeError('El plan 58 está descartado. Conservar su evidencia; el plan vigente es 59.')
