"""Iporre, Historia Poligénesis 1 y Taller 1: once fotos completas."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(2779,2804),[367,-1,-2,-1,-1,-3,-16,-14,-1,10,-1,-1,-2,1,-10,-10,8,2,-1,-1,-1,-3,-5,-1,-1],
  [367,366,364,363,362,359,343,329,328,338,337,336,334,335,325,315,323,325,324,323,322,319,314,313,312]),
 (range(2804,2830),[-1,-1,-1,-5,-1,-3,-1,-1,-3,-3,-5,-20,14,-3,-5,3,-1,-1,1,-1,-1,-1,-1,-3,1,-5],
  [311,310,309,304,303,300,299,298,295,292,287,267,281,278,273,276,275,274,275,274,273,272,271,268,269,264]),
 (range(2830,2855),[-2,4,-10,-1,-1,4,-1,-1,1,-5,-1,-2,-22,4,-2,-1,4,-1,-3,-2,-1,-17,2,-3,-1],
  [262,266,256,255,254,258,257,256,257,252,251,249,227,231,229,228,232,231,228,226,225,208,210,207,206]),
 (range(2855,2881),[-3,1,-4,-2,-1,-2,-1,-2,-2,-1,-2,-1,-6,-10,-1,-5,-5,-2,-5,1,6,3,-5,-2,-4,-2],
  [203,204,200,198,197,195,194,192,190,189,187,186,180,170,169,164,159,157,152,153,159,162,157,155,151,149]),
 (range(2881,2888),[-2,-3,-6,-2,-2,-5,-20],[147,144,138,136,134,129,109]),
 (range(6724,6750),[280,-5,-5,-15,-5,14,-5,-1,-10,-40,29,-4,-1,-3,-1,-1,-5,5,-10,5,-1,-1,-5,-1,-2,-1],
  [280,275,270,255,250,264,259,258,248,208,237,233,232,229,228,227,222,227,217,222,221,220,215,214,212,211]),
 (range(6750,6775),[-10,-1,9,-3,-30,-100,-5,7,-3,-1,-1,3,1,-1,-3,3,-5,-1,5,-10,-1,-2,-20,-10,-5],
  [201,200,209,206,176,76,71,78,75,74,73,76,77,76,73,76,71,70,75,65,64,62,42,32,27]),
 (range(6775,6780),[-2,-1,-1,1,-2],[25,24,23,24,22]),
 # El recuento 3 omitido por OCR se intercala después de 8462 mediante
 # recuperación documental. La reconstrucción específica posterior lo usa.
 (range(8458,8481),[0,-3,-2,3,-1,-1,-1,2,-3,20,-5,6,-2,-2,-1,-1,-1,1,-1,-1,-1,-1,-1],
  [10,None,5,8,7,2,1,3,0,20,15,None,19,17,16,15,14,15,14,None,None,11,10]),
 (range(8481,8507),[-1,-3,41,-3,2,-1,-1,-1,-8,-5,-5,8,-1,-1,-1,-2,-5,5,-5,-4,-3,3,-1,-5,1,1],
  [9,6,47,44,46,45,44,43,35,30,25,33,32,31,30,28,23,28,23,19,16,19,18,13,14,15]),
 (range(8507,8529),[-1,-1,-1,1,-2,2,-8,4,-2,1,10,-5,5,2,-10,7,-2,-2,-1,-2,-3,-2],
  [14,13,12,13,11,13,5,9,7,8,18,13,18,20,10,17,15,13,12,10,7,5]),
]


def recuperada(rows,id,orden,*,clave,detalle,fecha,saldo,tipo,motivo):
    import hashlib
    r=rows[id];foto=(BACKEND/r['ruta_imagen_respaldo']).resolve();activa=tipo=='RECUENTO'
    rev={'criterios':['T09','T15' if activa else 'T14','T23'],'motivo':motivo,'tipo_fila':tipo,
        'origen_fecha':'HIPOTESIS','fecha_documental':None,'motivo_fecha':'La fila carece de fecha inequívoca; se usa una fecha técnica de contexto para consulta, no una fecha documental.',
        'saldo_documental':saldo if activa else None,'origen_saldo':'FOTO' if activa else 'HIPOTESIS','usar_saldo_esperado':False,'reconstruir_cadena':True,
        'cotejo_pagina_completa':True,'hallazgos':['HOJA_COMPLETA_COTEJADA','FILA_OMITIDA_RECUPERADA_DESDE_FOTO']}
    if not activa:rev['origen_cantidades']='HIPOTESIS'
    campos={'articulo_id':r['articulo_id'],'lote_id':r['lote_id'],'ruta_imagen_respaldo':r['ruta_imagen_respaldo'],'numero_pagina':1,'orden_fila':orden,
        'fecha_movimiento':fecha,'fecha_original':None,'detalle':detalle,'referencia':None,'area':None,'ingresos':None,'salidas':None,
        'saldo_registrado':saldo,'saldo_calculado':saldo,'fecha_estado':'ESTIMADA_HIL' if activa else 'NO_APLICA_DOCUMENTAL',
        'estado':'ACTIVO' if activa else 'ANULADO_DOCUMENTO','nodo_grafo':'Origen no especificado','area_estado':'SIN_AREA_REGISTRADA','referencia_estado':'AUSENTE',
        'requiere_auditoria_nodo':False,'requiere_auditoria_referencia':False,
        'datos_originales':{'fuente':'LECTURA_FOTO_HIL','fecha_documental':None,'detalle':detalle,'ingresos':None,'salidas':None,'saldo_registrado':saldo if activa else None,
            'orden_fila':orden,'no_existia_en_extraccion_ocr':True,'limite':'Recuperación desde fotografía existente; no es una transacción nueva ni una extracción OCR.'}}
    return {'clave':clave,'fuente':str(foto),'sha256_imagen':hashlib.sha256(foto.read_bytes()).hexdigest(),'campos':campos,'revision':rev}


def generar():
    snapshot='backups/continuacion_hil_28_20261015/articulos_62_98_185_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    for id,r in rows.items():
        if r['area'] in ('CDOAL','CEDOCAL','GSDOAL','GEDOAL','CEDOSL','Cedral','Cedoal'):
            cambios[id]={'area':'CEDOAL'};extras[id]={'motivo':'La celda se lee CEDOAL en esta foto, sin crear áreas ni alias.'}
        if (r['articulo_id']==62 and r['numero_pagina']==1 and id>=2788) or (r['articulo_id']==185 and r['numero_pagina']==1 and id>=8463):
            cambios.setdefault(id,{})['orden_fila']=r['orden_fila']+1
    for id,fields in {
        2790:{'area':'GALERIA'},2791:{'detalle':'LLALLAGUA'},2792:{'detalle':'LLALLAGUA'},2799:{'detalle':'BIBLIOT. ORURO'},
        2806:{'detalle':'APAC - PALCA'},2807:{'referencia':'CONSIG.'},2808:{'fecha_movimiento':'2011-11-25'},
        2809:{'detalle':'VENTAS - CEDOAL'},2811:{'detalle':'UCB. CARMEN PAMPA'},2814:{'detalle':'FIL'},2815:{'detalle':'FIL'},2816:{'detalle':'FIL'},
        2817:{'detalle':'VENTAS CEDOAL'},2824:{'detalle':'VENTAS CEDOAL'},2843:{'area':None},2846:{'area':None},
        2855:{'referencia':'CONSIG.','area':None},2858:{'detalle':'VENTAS'},2859:{'detalle':'VENTAS CEDOAL'},2860:{'detalle':'LA PAZ LEE'},
        2861:{'area':None},2862:{'area':None},2863:{'detalle':'FIL'},2864:{'detalle':'FIL'},2865:{'detalle':'VENTAS CEDOAL'},
        2866:{'detalle':'ORURO CASA CULTURA','referencia':'DONACION'},2867:{'detalle':'VENTAS CEDOAL'},2869:{'area':None},2871:{'area':None},
        2887:{'detalle':'FIL - CBBA. FRANCISCO'},6728:{'detalle':'DONACION TOCAÑA'},6731:{'detalle':'FERIA LIBRO ORURO'},
        6779:{'detalle':'VENTAS CID','area':'CID'},
        8459:{'detalle':'CEDOAL - ORURO'},8460:{'detalle':'CEDOAL - SUCRE'},8461:{'detalle':'DEVOLUCION CEDOAL'},8462:{'detalle':'CEDOAL - COLOMBIA'},
        8463:{'detalle':'COBOCE'},8470:{'detalle':'PARA EL CEDOAL'},8474:{'area':'Potosi'},
        8507:{'referencia':'OBSEQUIO','area':'GALERIA'},8511:{'detalle':'LLALLAGUA'},8512:{'detalle':'LLALLAGUA'},8515:{'detalle':'FL. POTOSI'},8516:{'detalle':'FL. POTOSI'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        2793:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11; literal conservada y consulta técnica del antecedente.'),
        2863:('2017-07-06','HIPOTESIS',None,'FIL sin fecha propia; consulta técnica del antecedente.'),
        2864:('2017-07-06','HIPOTESIS',None,'Segundo FIL también sin fecha propia; no se anula ni duplica por semejanza, se conserva salida 1 y saldo 189.'),
        2876:('2020-02-20','HIPOTESIS',None,'DEV. FUN. BCB no tiene fecha escrita. Se usa el antecedente 20-02-20 solo para consulta, sin copiar una fecha de otro artículo.'),
        6742:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11; literal conservada y consulta técnica.'),
        6755:('2012-08-21','SECUENCIA_AJUSTADA','2012-07-24','24-07-12 después de 21-08-12. Se conserva literal y consulta técnica del antecedente, sin alterar la salida 100.'),
        8458:('2006-06-26','HIPOTESIS',None,'La base escribe 26-6 sin año. La gestión 2006 es solo contexto previo a enero de 2007, no fecha completa confirmada.'),
        8459:('2006-10-06','HIPOTESIS',None,'6-10 sin año escrito; se conserva esa lectura parcial y gestión técnica 2006.'),
        8460:('2006-10-11','HIPOTESIS',None,'11-10 sin año escrito; gestión 2006 solo para consulta.'),
        8461:('2006-11-29','HIPOTESIS',None,'29-11 sin año escrito; gestión 2006 solo para consulta.'),
        8462:('2006-11-29','HIPOTESIS',None,'14-09 sin año escrito, colocado después de 29-11. Se conserva parcial y consulta técnica del antecedente.'),
        8464:('2007-01-17','HIPOTESIS',None,'Edgar Grandica tiene fecha en blanco; consulta del antecedente 17-01-07, sin copiar la fecha de la siguiente recepción.'),
        8467:('2007-08-08','HIPOTESIS',None,'Marca de repetición pequeña en FECHA: se conserva y se usa 08-08-07 como consulta técnica, no fecha documental completa.'),
        8475:('2007-11-13','SECUENCIA_AJUSTADA','2007-11-05','5-11-07 después del 13-11-07. Se conserva literal y consulta técnica del antecedente, sin atribuirle automáticamente la nota lateral 19-12-07.'),
        8478:('2008-05-19','HIPOTESIS',None,'UPEA no tiene fecha propia; consulta técnica del antecedente.'),
        8479:('2008-05-19','HIPOTESIS',None,'U. Técnica no tiene fecha propia; consulta técnica del antecedente.'),
        8513:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11; literal conservada y consulta técnica.'),
        8518:('2012-07-30','SECUENCIA_AJUSTADA','2012-07-24','24-07-12 después del ingreso 30-07-12; consulta técnica del antecedente.'),
        8526:('2016-10-10','HIPOTESIS',None,'FIL 77 no tiene fecha propia; consulta técnica del antecedente, sin inventar un año por el detalle.'),
    }
    extras.update({
        **{id:{'criterios':['T23'],'motivo':'La cifra 4 está en INGRESOS, no ÁREA: se recupera la columna sin crear un área numérica.'} for id in (2843,2846)},
        2796:{'motivo':'L. Zeballos tiene ingreso 2 y la siguiente fila salida 1, ambas legibles. Se conservan como operaciones distintas y no se deduplican por nombre y fecha.'},
        2836:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'CEDOAL cruza REF/ÁREA; se conserva la atribución literal sin certificar su columna.'},
        2842:{'motivo':'FIL escribe salida 22 legible desde 249, saldo 227. No se reduce a 2 por parecer una cantidad elevada.'},
        2851:{'motivo':'FIL-2015 escribe salida 17, saldo 208 desde 225. Se conserva la cifra legible.'},
        2855:{'criterios':['T23'],'motivo':'El papel escribe CBA en REF y CONSIG en ÁREA. Se normaliza la consignación como referencia, manteniendo CBBA en el detalle y las columnas escritas en metadatos, sin crear área Consignación.', 'revision':{'columnas_documentales':{'referencia':'CBA','area':'CONSIG'}}},
        **{id:{'motivo':'ÁREA contiene un punto aislado, no comillas inequívocas. Se conserva la marca sin convertirla en un área ni repetir automáticamente otra institución.', 'revision':{'marca_area_documental':'Punto aislado'}} for id in (2861,2862,2869,2871)},
        6732:{'criterios':['T02'],'motivo':'La cifra 10 está en SALIDAS: 258 - 10 = 248. Se corrige el ingreso atribuido por OCR.'},
        6755:{'motivo':'Salida 100 y referencia DONACIÓN son legibles: desde 176 deja 76. No se cambia la cantidad por su magnitud ni se fusiona este artículo con POLIGENESIS.'},
        **{id:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'El área se conserva literalmente como C+C; no se crea una equivalencia automática con CTC por semejanza.'} for id in (6758,6761)},
        8458:{'criterios':['T22'],'motivo':'Saldo según inventario 10 es una base documental escrita, sin ingreso 10 inventado.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL','lectura_fecha_parcial':'26-6; año ausente.'}},
        8459:{'motivo':'La celda SALDO está vacía; se conserva el 7 como cálculo hipotético, no como cifra escrita.'},
        8466:{'motivo':'La celda muestra un cero entre guiones. Se conserva 0 numérico, distinto de una celda con solo guion.'},
        8469:{'criterios':['T01','T19'],'motivo':'Ingreso y saldo están muy repasados: la extracción propuso 9/24, pero la siguiente salida 2 deja 19. Se usa ingreso 6 como hipótesis de continuidad desde 15; no se certifica la cantidad ni el saldo repasado como hechos.',
            'revision':{'origen_cantidades':'HIPOTESIS','lectura_cantidad_parcial':'Cifra repasada; hipótesis 6 frente a 9 de la extracción.','lectura_saldo_parcial':'21/24, cifra final repasada.','candidatos_saldo_documental':[21,24]}},
        8476:{'criterios':['T14'],'motivo':'La salida final se lee 1, con una marca anterior repasada. Se conserva una sola salida y saldo 14.', 'revision':{'marcas_documentales':{'salidas':'1 y trazo anterior repasado.'}}},
        8477:{'motivo':'Donación Caranavi tiene SALDO en blanco, no el 14 repetido por OCR. Se conserva el cálculo hipotético 13.'},
        8478:{'motivo':'UPEA tiene SALDO en blanco, no el 13 repetido por OCR. Se conserva el cálculo hipotético 12.'},
    })
    plan=construir(version=28,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[(2826,2827)],
        bases={62:{'primera_fila':2779,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 367: base cero inferida, sin recuento previo acreditado.'},
            98:{'primera_fila':6724,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 280: base cero inferida, sin recuento previo acreditado.'},
            185:{'primera_fila':8458,'saldo_base':10,'origen_saldo_base':'FOTO','motivo_base':'Base documental 10 escrita, sin cantidad de ingreso inventada.'}},
        observaciones=[
            {'articulo_id':62,'observado':True,'excluir_entrenamiento':False,'motivo':'Cinco fotos cotejadas con 109 filas OCR y una fila totalmente tachada recuperada sin efecto. Se recuperan dos ingresos 4 desplazados a ÁREA y se conservan salidas legibles 22 y 17, puntos de área y fechas vacías. Cierre 109 coincide sin ajustes.'},
            {'articulo_id':98,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos y 56 filas cotejadas, manteniendo este artículo separado de POLIGENESIS por instrucción expresa. Salida 10 mal leída como ingreso corregida; salida 100 por donación y salida 30 legibles conservadas. Fecha fuera de orden y código C+C pendientes identificados. Cierre 22 coincide.'},
            {'articulo_id':185,'observado':True,'excluir_entrenamiento':True,'motivo':'Tres fotos cotejadas con 71 filas OCR y recuento documental omitido recuperado. Base 10 y recuento físico escrito 3, con diferencia -4 frente a 7, se conservan sin salida ficticia. Cantidad de devolución repasada se interpreta solo como hipótesis 6, con saldo escrito dudoso 21/24; artículo excluido del entrenamiento hasta aclarar. Cierre escrito 5 coincide con esa reconstrucción condicional, sin certificar la cantidad intermedia.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={62:109,98:22,185:9},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':8463,'local':-4,'acumulada':-4}],plan['cotejo']
    # El recuento realmente fotografiado se inserta antes de 8463. Se aplica
    # su base 3, sin una salida 4 de compensación y sin borrar la diferencia.
    for e in plan['revisiones']:
        if e['articulo_id']!=185:continue
        if e['id']>=8463:e['cambios']['saldo_registrado']-=4
        rev=e['revision'];escrito=rev['saldo_documental'];calc=e['cambios']['saldo_registrado']
        rev['origen_saldo']='HIPOTESIS' if escrito is None else ('FOTO' if escrito==calc else 'RECONSTRUIDO')
        if e['id']==8463:
            rev.pop('diferencia_local_papel',None);rev['criterios']=[c for c in rev['criterios'] if c!='T05']
            rev['hallazgos']=[h for h in rev['hallazgos'] if h!='DESCUADRE_DEL_PAPEL_CONSERVADO']
            rev['motivo']+=' Se sigue desde el recuento 3 escrito en el renglón recuperado anterior; su diferencia -4 se conserva en ese recuento, no como salida ficticia.'
        if e['id']==8469:rev['motivo']=extras[8469]['motivo']+' El saldo se conserva como lectura parcial, no como celda vacía.'
    plan['recuperaciones']=[
        recuperada(rows,2787,rows[2788]['orden_fila'],clave='art62-lote64-p1-feria-tachada-entre2787y2788-v1',
            detalle='FERIA UCB (renglón completamente tachado)',fecha='2011-04-28',saldo=328,tipo='ANULADO',
            motivo='Renglón de Feria UCB completamente tachado en fecha, texto, columnas y saldo, omitido por OCR. Se recupera solo como evidencia anulada. Fecha y cantidades no se certifican; saldo 328 es almacenamiento técnico sin efecto, no lectura del saldo tachado.'),
        recuperada(rows,8462,rows[8463]['orden_fila'],clave='art185-lote200-p1-recuento3-entre8462y8463-v1',
            detalle='SEGUN RECUENTO FISICO',fecha='2007-01-01',saldo=3,tipo='RECUENTO',
            motivo='La foto escribe Según recuento físico y saldo 3 después del saldo 7. Se recupera la fila omitida y se sigue desde 3, conservando diferencia -4. La fecha no está escrita y queda técnica; no se inventa una salida 4 ni un conteo actual.'),
    ]
    protegido=json.loads((BACKEND/'backups/continuacion_hil_28_20261015/poligenesis_antes.json').read_text(encoding='utf-8'))
    plan['cotejo'].update(movimientos=238,cierres={62:109,98:22,185:5},cierres_documentales={62:109,98:22,185:5},discrepancias=[],
        recuentos_recuperados=[{'clave':plan['recuperaciones'][1]['clave'],'previo':7,'escrito':3,'diferencia':-4}],
        articulos_protegidos=[p for p in protegido if p['id']!=98],
        limites_cierre={185:'El cierre escrito 5 coincide con una reconstrucción condicionada al ingreso hipotético 6 de una devolución repasada. No certifica esa cantidad intermedia; artículo excluido del entrenamiento hasta aclarar.'})
    return plan


if __name__=='__main__':congelar(generar())
