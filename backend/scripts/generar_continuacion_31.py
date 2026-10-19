"""Trece fotos de Teatro barroco, Cuentos con altura y Cuerpo en los imaginarios."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND
from scripts.generar_continuacion_28 import recuperada

HOJAS=[
 (range(1802,1828),[-1,-1,3,-1,-10,10,-4,-3,-2,-1,-3,-1,-1,-1,1,-1,-1,-2,2,-10,10,-1,-1,-3,-1,1],
  [579,578,581,580,570,580,576,573,571,570,567,566,565,564,565,564,563,561,563,553,563,562,561,558,557,558]),
 (range(1828,1853),[-1,-2,-1,-1,-2,-1,2,-5,5,-5,2,-1,-1,1,-1,-1,-13,1,-7,1,-1,-1,-3,3,-5],
  [557,555,554,553,551,550,552,547,552,547,549,548,547,548,547,546,533,534,527,528,526,525,522,525,520]),
 (range(1853,1879),[-1,4,-10,-1,9,-1,1,-2,-2,2,7,-3,2,-2,-2,2,-2,3,-2,-4,2,-3,-4,-2,-8,-1],
  [519,523,513,512,521,520,521,519,517,519,526,523,525,523,521,523,521,524,522,518,520,517,513,511,503,502]),
 (range(1879,1888),[-1,-4,-1,-1,-5,-1,3,6,-15],[501,497,496,495,490,489,492,498,483]),
 (range(2078,2104),[320,-5,-5,-10,-5,-5,10,-3,-1,-5,-10,-10,2,-1,-1,-3,-1,-1,-1,1,-1,-5,-10,1,-1,-5],
  [320,315,310,300,295,290,300,297,296,291,281,271,273,272,271,268,267,266,265,266,265,260,250,251,250,245]),
 (range(2104,2130),[-1,-1,-3,-1,-1,-3,1,-3,-50,-5,-10,7,-5,5,-3,-1,-1,3,1,-1,-1,1,-1,-1,-3,3],
  [244,243,240,239,238,235,236,233,183,178,168,175,170,175,172,171,170,173,174,173,172,173,172,171,168,171]),
 (range(2130,2156),[-5,-1,5,-10,-1,-5,-1,-3,-5,-2,-14,-20,-50,-1,-3,-5,-10,-2,-12,2,-1,-2,-3,-1,-1,-11],
  [166,165,170,160,159,154,153,150,145,143,129,109,59,58,55,50,40,38,26,28,27,25,22,21,20,9]),
 (range(2156,2167),[-1,-1,-1,-1,5,-2,2,1,-2,-7,3],[8,7,6,5,10,8,10,11,9,2,5]),
 (range(2167,2193),[-105,-1,-1,-1,-2,-5,-50,-1,-1,-1,-1,5,23,-3,-15,-2,-1,-1,-1,-3,-1,3,-1,-1,-10,4],
  [208,207,206,205,203,198,148,147,146,145,144,149,172,169,154,152,151,150,149,146,145,148,147,146,136,140]),
 (range(2193,2219),[-3,-1,-3,-1,-1,1,-4,-1,1,-1,-2,-10,6,-1,-1,-1,-3,-1,-5,-1,-10,-1,8,-5,-2,-2],
  [137,136,133,132,131,132,128,127,128,127,125,115,121,120,119,118,115,114,109,108,98,97,105,100,98,96]),
 (range(2219,2245),[3,-5,-10,10,-5,1,1,-1,-1,-1,-1,-3,3,-5,-1,4,-10,-30,-1,6,25,-1,-1,1,-1,-1],
  [99,94,84,94,89,90,91,90,89,88,87,84,87,82,81,85,75,45,44,50,75,74,73,74,73,72]),
 (range(2245,2270),[5,-3,-1,-2,-2,1,-1,-2,2,-1,-2,-2,-2,2,-1,-1,-1,-4,-1,-2,-2,-1,-1,2,-2],
  [77,74,73,71,69,70,69,67,69,68,66,64,62,64,63,62,61,57,56,54,52,51,50,52,50]),
 (range(2270,2275),[2,1,-2,5,3],[52,53,51,56,59]),
]

def generar():
    snapshot='backups/continuacion_hil_31_20261015/articulos_48_51_52_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    for id,r in rows.items():
        if r['area'] in ('Cedoal','CEDOC','CEDOOL','CSODAL','COORDAL','CDOAL'):
            cambios[id]={'area':'CEDOAL'};extras[id]={'motivo':'La celda se lee CEDOAL en esta fotografía; se corrige lectura sin crear áreas ni alias.'}
        if r['articulo_id']==48 and r['numero_pagina']==2 and id>=1848:cambios.setdefault(id,{})['orden_fila']=r['orden_fila']+1
    for id,fields in {
        1811:{'referencia':'OBSEQUIO'},1813:{'detalle':'Sr. Eric Altorfer'},1817:{'detalle':'QUIME'},1819:{'detalle':'LLALLAGUA'},1820:{'detalle':'LLALLAGUA'},
        1831:{'detalle':'UCB. CARMEN PAMPA'},1847:{'referencia':None,'area':None},
        1874:{'detalle':'Los Amigos Libro - CBBA'},1879:{'fecha_movimiento':'2017-11-13'},
        2082:{'referencia':'Dirección','area':'CEDOAL'},2098:{'detalle':'QUIME'},2099:{'detalle':'LLALLAGUA','fecha_movimiento':'2011-07-18'},
        2107:{'detalle':'COMPA TRONO'},2122:{'fecha_movimiento':'2012-12-05'},2138:{'fecha_movimiento':'2014-07-07'},
        2149:{'detalle':'FERIA STA CRUZ DEVOLUCION'},2156:{'referencia':'DONACION','area':'CEDOAL'},2160:{'area':None},2164:{'detalle':'VENTAS CID'},
        2187:{'detalle':'Donación Tocaña'},2231:{'fecha_movimiento':'2013-05-14'},2232:{'fecha_movimiento':'2013-05-27'},
        2252:{'detalle':'U. COSTA RICA'},2266:{'detalle':'CASA CULTURA ORURO','referencia':'DONA'},2274:{'fecha_movimiento':'2021-10-01'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        1821:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11; literal conservada y consulta técnica del antecedente.'),
        1863:('2014-04-29','SECUENCIA_AJUSTADA','2014-04-11','11-4-14 después del 29-4-14. Se conserva literal y consulta técnica del antecedente.'),
        1877:('2016-09-19','HIPOTESIS',None,'FIL sin fecha propia; consulta técnica del antecedente, sin asignarle otro año por el contexto.'),
        2129:('2013-05-07','HIPOTESIS',None,'Último renglón de esta foto tiene fecha y detalle en blanco, ingreso 3 y saldo 171 repasado. Se conserva el vacío, sin atribuirle automáticamente el evento o fecha de otra hoja.'),
        2148:('2015-07-22','HIPOTESIS',None,'Renglón con salida 12 y saldo 26 sin fecha ni detalle propios; consulta técnica del antecedente, sin inventar destino ni evento.'),
        2199:('2011-04-07','SECUENCIA_AJUSTADA','2011-03-16','16-03-11 después de 07-04-11. Se conserva literal y consulta técnica del antecedente.'),
        2212:('2012-02-07','HIPOTESIS','2011-02-07','La foto escribe 7-2-11 después de octubre de 2011. El 2012 es solo hipótesis de consulta; no se borra el año 11 escrito.'),
        2213:('2012-05-09','HIPOTESIS','2011-05-09','La foto escribe 9-5-11 antes de junio de 2012 y después de octubre de 2011. Se conserva literal; 2012 es hipótesis de contexto para consulta.'),
        2216:('2012-06-19','SECUENCIA_AJUSTADA','2012-05-09','9-5-12 aparece después del 19-6-12. Se conserva literal y consulta técnica del antecedente.'),
        2265:('2017-10-05','HIPOTESIS',None,'FECHA está tachada; no se anula toda la salida 2 con saldo 52. Se conserva la marca y 5-10-17 solo como lectura parcial de contexto para consulta, no fecha documental certificada.'),
    }
    extras.update({
        1817:{'criterios':['T14'],'motivo':'QUIME tiene salida 1 y una marca tachada en INGRESOS; se elimina el ingreso extra de OCR conservando el tachón.', 'revision':{'marcas_documentales':{'ingresos':'Marca tachada, sin cantidad adicional legible.'}}},
        1844:{'motivo':'Gestores teatrales tiene salida 13 legible y la fila siguiente Eduardo Calla salida 7 distinta. Se conservan ambas entregas, sin deduplicar por semejanza.'},
        1847:{'criterios':['T23'],'motivo':'OCR juntó dos renglones físicos. Este renglón GALERIA escribe ingreso 1 y saldo 528; el siguiente, con REF VENTA, escribe salida 1 y saldo 527. Se separan preservando ambos efectos y la extracción original.', 'revision':{'renglon_desdoblado':'Ingreso GALERIA; salida VENTA en renglón físico siguiente recuperado.'}},
        1868:{'criterios':['T14'],'motivo':'La fecha presenta una corrección de trazo. Se conserva la lectura final 20-8-14 y el movimiento ingreso 2, sin anular la fila.', 'revision':{'marcas_documentales':{'fecha':'Trazo anterior corregido en la fecha.'}}},
        2082:{'criterios':['T23'],'motivo':'Dirección está en REF y Cedoal en ÁREA. Se separan sus columnas escritas, sin un área compuesta inventada.', 'revision':{'columnas_documentales':{'referencia':'Dirección','area':'Cedoal'}}},
        **{id:{'criterios':['T02'],'motivo':'La cifra 10 está en SALIDAS, no INGRESOS: disminuye el saldo en 10. Se conserva la cantidad legible y se corrige columna.'} for id in (2088,2089)},
        2098:{'criterios':['T14'],'motivo':'QUIME tiene una sola salida 1 y marca tachada en INGRESOS; se conserva sin segunda entrada.', 'revision':{'marcas_documentales':{'ingresos':'Marca tachada.'}}},
        2112:{'motivo':'MIN. EDUCACION tiene salida 50 legible y saldo 183 repasado; no se reduce la cantidad por ser elevada.', 'revision':{'marcas_documentales':{'saldo':'183 con trazo anterior repasado.'}}},
        2129:{'criterios':['T16'],'motivo':'La hoja deja DETALLE y FECHA vacíos. Ingreso 3 y saldo 171 se conservan; el motivo no se completa por similitud con Larga noche de museos.'},
        2148:{'criterios':['T16'],'motivo':'Salida 12 y saldo 26 legibles, con DETALLE y FECHA vacíos. Se conserva el vacío sin inventar destino FIL o venta por cercanía.'},
        2156:{'criterios':['T23'],'motivo':'El papel separa DONACION en REF y CEDOAL en ÁREA; se recuperan columnas sin confundir referencia e institución.'},
        2160:{'criterios':['T23'],'motivo':'DEV. ENTRE LIBROS tiene 5 en INGRESOS, no un área S. Se recupera ingreso 5 y saldo 10 desde 5.'},
        2167:{'motivo':'La primera foto empieza con salida 105 y saldo 208. Se conserva la cantidad, con base anterior 313 solo inferida; no se inventa recepción inicial 313.'},
        2173:{'motivo':'Obsequio Feria Potosí tiene salida 50 legible y referencia para compradores. Se conserva la entrega y su devolución posterior 23 como operaciones diferentes.'},
        2181:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'El papel parece escribir FUSIP; se conserva literal sin crear equivalencia automática con ESIP por semejanza.'},
        2197:{'motivo':'Obsequio Eric Altorfer 1 y devolución siguiente 1 están en renglones distintos; se conservan ambos sin deduplicación.'},
        2209:{'clasificacion':{'referencia_estado':'PENDIENTE_HIL','requiere_auditoria_referencia':True},'motivo':'REF tiene un trazo vertical aislado. Se conserva como marca pendiente sin convertirlo en una referencia numérica ni comillas ciertas.', 'revision':{'marca_referencia_documental':'Trazo vertical aislado.'}},
        2238:{'motivo':'Hay dos devoluciones FIL el mismo día, de 6 y 25, con saldos 50 y 75. Ambas se conservan; no son duplicados por compartir fecha y texto.'},
        2247:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'Se conserva GALS. como abreviatura documental, sin crear alias automático para un área completa.'},
        2265:{'criterios':['T14'],'motivo':'Solo está tachada la celda FECHA. Se conserva salida 2 y saldo 52 activos, con fecha técnica e imagen de la tachadura.', 'revision':{'marcas_documentales':{'fecha':'Fecha tachada; posible 5-10-17.'}}},
        2274:{'motivo':'La foto escribe 1-10-21, no 10 de enero de 2021. Se recupera el orden día-mes y se conserva ingreso 3.'},
    })
    plan=construir(version=31,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(1843,1844,1845),(1866,1867),(2111,2112,2113,2114,2115)],
        bases={48:{'primera_fila':1802,'saldo_base':580,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primera salida 1 y saldo 579: base 580 inferida, sin inventar un ingreso ni un conteo físico.'},
            51:{'primera_fila':2078,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 320: base cero inferida, sin recuento previo acreditado.'},
            52:{'primera_fila':2167,'saldo_base':313,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primera salida 105 y saldo 208: base 313 inferida, sin ingreso ficticio.'}},
        observaciones=[
            {'articulo_id':48,'observado':True,'excluir_entrenamiento':False,'motivo':'Cuatro fotos y 86 filas OCR cotejadas, con salida 1 recuperada porque OCR unió ingreso GALERIA y venta siguiente en una sola fila. Se conservan ambos renglones físicos y la extracción original. Marca tachada en INGRESOS de Quime no crea entrada; cantidades 13 y 7 y fecha 13-11-17 legibles conservadas. Base 580 inferida, fechas técnicas y correcciones de fecha identificadas. Cierre 483 coincide.'},
            {'articulo_id':51,'observado':True,'excluir_entrenamiento':False,'motivo':'Cuatro fotos y 89 filas cotejadas. Dos salidas 10 extraídas como ingresos corregidas; ingreso 5 de Entre Libros desplazado a área recuperado. Filas con detalle y fecha en blanco mantienen su ausencia, no se atribuyen eventos por semejanza. Salidas 50 y 12 y dos operaciones Quime/Min. Educación se conservan. Cierre 5 coincide.'},
            {'articulo_id':52,'observado':True,'excluir_entrenamiento':False,'motivo':'Cinco fotos y 108 filas cotejadas. Primera salida 105 con base inferida 313 sin ingreso inventado; obsequio 50 y devoluciones 6 y 25 del mismo día se conservan distintos. Fechas de mayo de 2013 y 1-10-21 recuperadas; años 11 fuera de contexto y fecha tachada quedan técnicos. Abreviaturas de áreas y marca aislada de referencia no se convierten en alias. Cierre 59 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={48:484,51:5,52:59},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':1848,'local':-1,'acumulada':-1}],plan['cotejo']
    for e in plan['revisiones']:
        if e['articulo_id']==48 and e['id']>=1848:
            e['cambios']['saldo_registrado']-=1;e['revision']['origen_saldo']='FOTO'
            if e['id']==1848:
                rev=e['revision'];rev.pop('diferencia_local_papel',None)
                rev['criterios']=[c for c in rev['criterios'] if c!='T05'];rev['hallazgos']=[h for h in rev['hallazgos'] if h!='DESCUADRE_DEL_PAPEL_CONSERVADO']
                rev['motivo']+=' Se continúa desde la salida 1 del renglón anterior recuperado, sin error aritmético del papel en este tramo.'
    nueva=recuperada(rows,1847,rows[1848]['orden_fila'],clave='art48-lote-a7775fee-p2-venta1-despues1847-v1',
        detalle='VENTA (detalle documental en blanco)',fecha='2013-03-15',saldo=527,tipo='RECUENTO',
        motivo='El renglón físico siguiente a GALERIA tiene REF VENTA, ÁREA GALERIA, salida 1 y saldo 527. OCR lo había unido al ingreso 1 anterior. Se recupera una sola vez con su evidencia, sin inventar otra operación. FECHA y DETALLE están vacíos; la fecha es técnica y el detalle de consulta describe la referencia escrita.')
    nueva['campos'].update(numero_pagina=2,salidas=1,referencia='VENTA',area='GALERIA')
    from app.db.session import SessionLocal
    from app.services.clasificador_nodos import clasificar_movimiento
    from scripts.cotejo_transcripcion_hil import DERIVADOS
    with SessionLocal() as db:
        clasificacion=clasificar_movimiento(nueva['campos']['detalle'],'VENTA','GALERIA',None,1,db)
        nueva['campos'].update({k:getattr(clasificacion,k) for k in DERIVADOS})
    nueva['revision'].update(tipo_fila='MOVIMIENTO',criterios=['T09','T23'],detalle_documental=None,origen_cantidades='FOTO')
    nueva['campos']['datos_originales'].update(salidas=1,referencia='VENTA',area='GALERIA',detalle=None,limite='Fila unida por OCR al renglón anterior; cantidad y saldo leídos de la foto, fecha y detalle ausentes.')
    plan['recuperaciones']=[nueva]
    plan['cotejo'].update(movimientos=284,cierres={48:483,51:5,52:59},discrepancias=[])
    return plan

if __name__=='__main__':congelar(generar())
