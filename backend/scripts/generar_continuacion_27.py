"""Trece fotografías completas: Compositores, Estéticas y Fotografía."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(1981,2007),[0,3,1,5,-5,-1,-1,-3,-3,-1,3,-1,-1,-2,1,9,-1,-1,-1,-4,-1,-1,-5,-10,14,-1],
  [85,88,89,94,89,88,87,84,81,None,85,84,83,81,82,91,90,89,88,84,83,82,77,67,81,80]),
 (range(2007,2033),[-5,-2,5,-3,3,-1,-10,8,1,-5,-3,-6,-1,1,-1,-1,-2,2,-10,8,-1,-1,-5,-1,-5,3],
  [75,73,78,75,78,77,67,75,76,71,68,62,61,62,61,60,58,60,50,58,57,56,51,50,45,48]),
 (range(2033,2059),[-1,-10,-1,9,-2,-1,-5,5,-5,3,-1,1,-3,3,-5,5,-10,-1,7,10,-3,-2,-4,3,-1,-2],
  [47,37,36,45,43,42,37,42,37,40,39,40,37,40,35,40,30,29,36,46,43,41,37,40,39,37]),
 (range(2059,2078),[-4,-1,1,1,-3,-1,-3,3,-1,-1,-2,2,-3,-3,2,-2,3,-2,-1],[33,32,33,34,31,30,27,30,29,28,26,28,25,22,24,22,25,23,22]),
 (range(2456,2482),[-1,-5,-2,-1,-1,-3,-1,3,-1,-1,-10,5,-3,1,-2,-1,-3,-2,-1,-1,-1,1,-1,1,-1,-2],
  [317,312,310,309,308,305,304,307,306,305,295,300,297,298,296,295,292,290,289,288,287,288,287,288,287,285]),
 (range(2482,2508),[2,-10,3,-1,-1,-1,-3,-1,-1,1,-1,-10,-1,5,-2,-5,4,-5,1,-1,-1,-1,1,-1,-1,1],
  [287,277,280,279,278,277,274,273,272,273,272,262,261,266,264,259,263,258,259,258,257,256,257,256,255,256]),
 (range(2508,2534),[1,-1,-1,-3,-5,7,-5,-1,5,-10,-1,-1,5,-1,-1,-1,-3,-1,-2,-4,2,-1,-2,-2,-1,1],
  [257,256,255,252,247,254,249,248,253,243,242,241,246,245,244,243,240,239,237,233,235,234,232,230,229,230]),
 (range(2534,2560),[-1,-1,-2,-3,-6,-8,1,-1,-3,-1,-3,-2,-1,-3,-4,-1,-1,-11,-1,-1,2,-4,-2,2,2,-3],
  [229,228,226,223,217,209,210,209,206,205,202,200,199,196,192,191,190,179,178,177,179,175,173,175,177,174]),
 (range(2652,2678),[50,-2,-5,-5,195,-10,-50,-5,-5,-1,-5,-1,-5,-20,-1,-5,-1,-10,-5,-5,-5,-15,-1,-1,-1,-5],
  [50,48,43,38,233,223,173,168,163,162,157,156,151,131,130,125,124,114,109,104,99,84,83,82,81,76]),
 (range(2678,2704),[-50,-25,240,3,-3,-20,-13,42,-3,-3,-1,2,-2,-1,-11,-1,-5,-3,1,-3,-1,-2,-20,-3,-3,-10],
  [26,1,241,244,241,221,208,250,247,244,243,245,243,242,231,230,225,222,223,220,219,217,197,194,191,181]),
 (range(2704,2728),[-2,-1,-2,-1,-3,-2,-1,-5,-2,-4,-2,-1,-1,5,-2,-9,-1,-1,-3,-1,-6,-1,-2,-3],
  [179,178,176,175,172,170,169,164,162,158,156,155,154,159,157,148,147,146,143,142,136,135,133,130]),
 (range(2728,2754),[-2,-1,-1,-3,-2,-1,-1,-1,-1,-1,-1,-5,-1,-2,-1,-5,-1,-1,-1,-25,8,-1,-4,-2,-1,-1],
  [128,127,126,123,121,120,119,118,117,116,115,110,109,107,106,101,100,99,98,73,81,80,76,74,73,72]),
 (range(2754,2769),[-1,-2,1,3,5,-2,-1,-3,-3,-2,-1,-1,-2,-3,-4],[71,69,70,73,78,76,75,72,69,67,66,65,63,60,56]),
]


def generar():
    snapshot='backups/continuacion_hil_27_20261015/articulos_50_56_60_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    for id,r in rows.items():
        if r['area'] in ('Cedroal','Cedoal','CIDOOL','CEDOAL.','CEDOCL','CGODOL','CEDOOL','CEDODL','CEDDAL'):
            cambios[id]={'area':'CEDOAL'};extras[id]={'motivo':'CEDOAL se lee en esta celda de la fotografía. Se corrige la lectura sin crear áreas ni alias.'}
        if r['articulo_id']==60 and r['numero_pagina']==3 and id>=2722:
            cambios.setdefault(id,{})['orden_fila']=r['orden_fila']+2
    for id,fields in {
        1982:{'detalle':'INGRESO POR RECUENTO FISICO'},1984:{'area':None},1992:{'detalle':'RENDICION DIRECTOR'},
        2040:{'detalle':'FIL'},2044:{'detalle':'LETRAS PACEÑAS'},2045:{'detalle':'LARGA NOCHE MUSEOS'},
        2067:{'detalle':'VENTAS - CEDOAL'},2076:{'fecha_movimiento':'2024-10-01'},
        2460:{'referencia':'CBA'},2463:{'fecha_movimiento':'2010-06-11'},2476:{'detalle':'SR. ERIC ALTORFER'},2477:{'detalle':'SR. ERIC ALTORFER'},
        2482:{'fecha_movimiento':'2011-08-02','detalle':'LLALLAGUA'},2505:{'detalle':'LETRAS PACEÑAS'},2507:{'detalle':'LETRAS PACEÑAS'},
        2515:{'detalle':'PATIPIÑA'},2529:{'detalle':'RADIO ALAS AMERICA'},2530:{'detalle':'VENTA CEDOAL'},2535:{'detalle':'FERIA LETRAS PACEÑAS'},
        2540:{'fecha_movimiento':'2015-08-19'},2542:{'referencia':'CONSIG.','area':None},2544:{'detalle':'LARGA NOCHE DE MUSEOS'},
        2547:{'detalle':'VENTAS CEDOAL','referencia':None},2552:{'detalle':'ORURO CASA CULTURA'},2557:{'fecha_movimiento':'2019-12-07'},
        2652:{'referencia':'SAGITARIO'},2655:{'detalle':'VENTAS CEDOAL'},2656:{'referencia':'SAGITARIO'},
        2657:{'detalle':'BIBLIOTECAS - PERIODISTAS','referencia':'DONACION','area':None},2659:{'detalle':'VENTAS - CEDOAL'},
        2677:{'detalle':'PRESENTACION ORURO DONACION'},2682:{'fecha_movimiento':'2015-07-06'},
        2688:{'detalle':'LENA PATIÑO - CONSUL','referencia':'UCRANIA'},2692:{'detalle':'ENVIO GINEBRA + 1 DIRECCION'},
        2694:{'detalle':'LITEXA - CONSIGNACION'},2695:{'detalle':'LA RAYUELA - CONSIGNACION'},
        2706:{'detalle':'VENTAS - CEDOAL'},2720:{'detalle':'SCORPIT - BRESCIA ITALIA'},2727:{'detalle':'VENTA - CEDOAL'},
        2729:{'detalle':'BIBLIOTECA HUANUNI','referencia':'DONA.','area':'CEDOAL'},2732:{'detalle':'VENTAS CEDOAL'},2741:{'detalle':'VENTAS - CEDOAL'},
        2758:{'detalle':'CENTRO PATIÑO'},2765:{'detalle':'VENTAS'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        1981:('2007-12-13','HIPOTESIS',None,'La primera fila no tiene fecha. El 13-12-07 de la siguiente se usa solo para consulta; no se certifica fecha de la base.'),
        1983:('2007-12-13','HIPOTESIS',None,'Devolución Sra. María sin fecha propia: consulta técnica del antecedente.'),
        1984:('2007-12-13','SECUENCIA_AJUSTADA','2007-12-11','11-12-07 aparece después del 13-12-07. Se conserva literal y consulta técnica del antecedente.'),
        1985:('2007-12-13','HIPOTESIS',None,'Bolivia Punto Cultural no tiene fecha en su celda. La nota lateral 14-12-08 no permite atribuirle inequívocamente día/año; consulta técnica del antecedente.'),
        1991:('2008-06-05','HIPOTESIS',None,'Devolución Chile tiene fecha en blanco; se conserva ausencia y consulta técnica del antecedente.'),
        1992:('2008-06-05','SECUENCIA_AJUSTADA','2008-03-17','La foto escribe 17-3-08 después de junio, no 13-07. Se conserva literal y consulta técnica del antecedente.'),
        2025:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08 después del 02-08-11: consulta técnica del antecedente y literal conservada.'),
        2055:('2014-07-25','SECUENCIA_AJUSTADA','2014-07-24','24-07-14 después del 25-07-14: se conserva literal, orden físico y fecha técnica de consulta.'),
        2069:('2017-07-06','HIPOTESIS',None,'FIL no tiene fecha propia; se usa la del antecedente únicamente para consulta.'),
        2077:('2024-10-01','SECUENCIA_AJUSTADA','2024-08-15','15-08-24 está escrito después de 1-10-24. Se conserva el 24 legible en la foto anterior, sin convertirlo en 2021 para cuadrar el orden.'),
        2492:('2012-02-07','HIPOTESIS','2011-02-07','7-2-11 está escrito después de 13-12-11 y antes de mayo de 2012. Se conserva el 11 del papel; el 2012 es solo hipótesis de consulta.'),
        2551:('2016-10-06','HIPOTESIS',None,'FIL 77 tiene fecha en blanco: consulta técnica del antecedente, sin asignarle automáticamente un año distinto por el detalle.'),
        2685:('2015-08-03','HIPOTESIS',None,'Ingreso 42 sin FECHA escrita; consulta técnica del antecedente, no fecha confirmada de recepción.'),
        2701:('2015-12-07','SECUENCIA_AJUSTADA','2015-11-25','25-11-15 aparece después del 07-12-15. Se conserva literal y consulta técnica del antecedente.'),
        2735:('2017-07-06','HIPOTESIS',None,'FIL tiene FECHA en blanco: consulta técnica del antecedente.'),
    }
    extras.update({
        1981:{'criterios':['T22'],'motivo':'Ingreso del otro depósito no consigna cantidad en INGRESOS y tiene saldo 85. Se representa como base documental 85, sin inventar ingreso 85.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL'}},
        1982:{'criterios':['T16'],'motivo':'Ingreso por recuento físico escribe INGRESOS 3 y saldo 88. Se conserva esa entrada 3, sin convertirla en un nuevo conteo total 3.'},
        1984:{'criterios':['T07','T23'],'motivo':'El 5 está escrito en ÁREA; el texto Ingresa devoluciones y el saldo 89 a 94 sustentan ingreso 5. Se conserva la columna documental ÁREA y no se crea un área numérica.', 'revision':{'columna_documental_cantidad':'AREA','interpretacion_cantidad':'INGRESO','cantidad_documental':5}},
        **{id:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'El valor de ÁREA parece código documental junto a ESIP. Se conserva sin inventar una institución con ese número.'} for id in (1987,1988)},
        1990:{'motivo':'El último dígito del saldo está repasado y no es inequívoco entre 80/82. Se conserva la incertidumbre, sin elegir la lectura que haga cuadrar la suma.', 'revision':{'lectura_saldo_parcial':'80/82, último dígito repasado.','candidatos_saldo_documental':[80,82]}},
        1991:{'criterios':['T05'],'motivo':'El saldo escrito se lee 85, no 83. Desde el acumulado independiente 80 más ingreso 3 corresponde 83; la diferencia de dos queda localizada en este tramo de saldo repasado/devolución. No se cambia la cantidad legible para compensarla.'},
        1992:{'motivo':'La fila Rendición Director tiene salida 1 y saldo 84 desde el 85 del papel. Se conserva como salida, sin invertirla por la lectura anterior del texto como devolución.'},
        2021:{'criterios':['T14'],'motivo':'QUIME presenta salida 1 y una marca tachada en INGRESOS. Se elimina el ingreso extra atribuido por OCR, conservando la marca y un solo egreso.', 'revision':{'marcas_documentales':{'ingresos':'Marca tachada sin cantidad adicional legible.'}}},
        2056:{'revision':{'marcas_documentales':{'saldo':'Cifra anterior tachada y lectura final 40.'}}},
        2075:{'criterios':['T07'],'motivo':'DEV. FUN. BCB tiene 3 en SALIDAS, pero saldo 22 a 25. El texto de devolución y la cadena sustentan ingreso 3; se conserva la columna documental SALIDAS y no se inventa otro movimiento.', 'revision':{'columna_documental_cantidad':'SALIDAS','interpretacion_cantidad':'INGRESO','cantidad_documental':3}},
        2466:{'criterios':['T02'],'motivo':'La foto muestra SALIDAS 10, no ingreso: 305 - 10 = 295. Se recupera la columna sin alterar la cantidad.'},
        2476:{'motivo':'Obsequio 1 y posterior devolución 1 del mismo nombre están en renglones distintos con efectos opuestos legibles. Se conservan ambas operaciones, sin deduplicarlas por semejanza.'},
        2542:{'criterios':['T23'],'motivo':'CONSIG. está en REF y ÁREA está vacía. Se recuperan sus columnas sin crear un área llamada consignación.'},
        2547:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'Hay una marca pequeña en ÁREA y REF está en blanco. No es repetición inequívoca suficiente para certificar el área; se elimina el punto desplazado a REF y se conserva la marca como pendiente.', 'revision':{'lectura_area_parcial':'Marca pequeña, posible repetición no inequívoca.'}},
        2657:{'criterios':['T23'],'motivo':'DONACIÓN se extiende por REF/ÁREA y describe el destino de la entrega. Se guarda como referencia con área vacía, conservando las columnas documentales sin inventar un área Donación.', 'revision':{'columnas_documentales_texto':'DONACION entre REF y AREA.'}},
        2659:{'criterios':['T14'],'motivo':'Ventas tiene salida 5 y marca tachada en INGRESOS. Se conserva una sola salida, no una entrada adicional.', 'revision':{'marcas_documentales':{'ingresos':'Marca tachada sin segunda cantidad legible.'}}},
        2682:{'motivo':'La foto escribe 6-7-15, no 7-6. CEDOAL está en REF y VENTAS en ÁREA; se preservan esas columnas literales sin inventar una nueva área llamada Ventas.', 'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True}},
        2692:{'motivo':'Salida 11 documentada con detalle Ginebra + 1 Dirección. Se conserva la cantidad total y la anotación, sin crear una salida adicional 1.'},
        2720:{'criterios':['T02'],'motivo':'La cifra 1 está en SALIDAS, no INGRESOS: 148 - 1 = 147. Se recupera la columna del OCR.'},
        2729:{'criterios':['T23'],'motivo':'El papel intercambia CEDOAL en REF y DONA en ÁREA. Se normalizan referencia DONA y área CEDOAL conservando las columnas escritas, sin crear área Donación.', 'revision':{'columnas_documentales':{'referencia':'CEDOAL','area':'DONA'}}},
    })
    plan=construir(version=27,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(2482,2483),(2506,2507),(2725,2726)],
        bases={50:{'primera_fila':1981,'saldo_base':85,'origen_saldo_base':'FOTO','motivo_base':'Primera fila con saldo escrito 85 sin cantidad de ingreso: base documental, no recepción fabricada.'},
            56:{'primera_fila':2456,'saldo_base':318,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primera salida 1 y saldo 317: base 318 inferida, sin inventar un ingreso o recuento.'},
            60:{'primera_fila':2652,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 50: base cero inferida, sin recuento previo acreditado.'}},
        observaciones=[
            {'articulo_id':50,'observado':True,'excluir_entrenamiento':True,'motivo':'Cuatro fotos y 97 filas cotejadas. Base documental 85 sin ingreso añadido; ingreso 5 escrito en ÁREA y marca tachada de QUIME recuperados. Saldo de María Tapia repasado 80/82 y devolución siguiente con 85 dejan diferencia de dos en ese tramo. Se conserva cierre escrito 22 frente a cálculo condicional 20, con apertura bloqueada y artículo excluido del entrenamiento; sin cambiar cantidades para cuadrar. Las fechas incompletas y el 1-10-24 seguido de 15-08-24 siguen identificados.'},
            {'articulo_id':56,'observado':True,'excluir_entrenamiento':False,'motivo':'Cuatro fotos y 104 filas cotejadas completas. Salida 10 mal leída como ingreso corregida; devolución Llallagua 02-08-11 recuperada. Se conservan obsequio/devolución del mismo nombre como dos operaciones, base 318 inferida, fechas técnicas y una marca de área pendiente. Cierre 174 coincide.'},
            {'articulo_id':60,'observado':True,'excluir_entrenamiento':False,'motivo':'Cinco fotos y 117 filas extraídas cotejadas, además de dos renglones completamente tachados omitidos por OCR recuperados sin efecto. Se corrigen salida 1 mal leída como ingreso, una marca tachada en INGRESOS y columnas de referencia/área. Se mantienen total 11 de Ginebra + 1 Dirección, fechas técnicas y origen de las dos recuperaciones. Cierre 56 coincide sin ajustes.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={50:20,56:174,60:56},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':1991,'local':2,'acumulada':2}],plan['cotejo']
    for e in plan['revisiones']:
        if e['id']==1990:
            e['revision']['motivo']=extras[1990]['motivo']+' Saldo de consulta 80 reconstruido, con lectura documental parcial, no una celda vacía.'
        if e['articulo_id']==50 and e['id']>=1990:
            e['revision']['origen_saldo']='HIPOTESIS'
            e['revision']['motivo']+=' Acumulado condicional al tramo de saldo repasado y diferencia de dos; no acredita existencias físicas.'
        if e['id']==2077:
            e['cambios']['saldo_registrado']=22;e['revision'].update(origen_saldo='FOTO',usar_saldo_esperado=False)
    plan['cotejo'].update(cierres={50:22,56:174,60:56},cierres_calculados={50:20,56:174,60:56},pendientes_documentales={'2077':['saldo']},
        limites_cierre={50:'Saldo repasado 80/82 y siguiente devolución con saldo 85: diferencia persistente de dos. Cierre escrito 22 frente a acumulado condicional 20; pendiente, sin apertura automática.'},movimientos=320,filas_recuperadas_anuladas=2)
    r=rows[2721];foto=next(e for e in plan['revisiones'] if e['id']==2721);recuperaciones=[]
    for i in range(2):
        orden=rows[2722]['orden_fila']+i;detalle=f'Renglón {i+1} de ingreso/donación completamente tachado'
        rev={'criterios':['T09','T14','T23'],'motivo':'Renglón completamente tachado entre Gustavo Buntix y PIEB, omitido por OCR. Se recupera como evidencia anulada; fecha, cantidades y saldo bajo tachadura no se certifican. El saldo 146 es un valor técnico de almacenamiento sin efecto, no lectura del saldo tachado.',
            'tipo_fila':'ANULADO','origen_fecha':'HIPOTESIS','fecha_documental':None,'motivo_fecha':'Fecha bajo tachadura no inequívoca; consulta técnica del antecedente 12-10-2016.',
            'saldo_documental':None,'origen_saldo':'HIPOTESIS','origen_cantidades':'HIPOTESIS','usar_saldo_esperado':False,'cotejo_pagina_completa':True,
            'hallazgos':['HOJA_COMPLETA_COTEJADA','FILA_OMITIDA_RECUPERADA_DESDE_FOTO','FILA_ANULADA_EN_DOCUMENTO_CONSERVADA']}
        campos={'articulo_id':60,'lote_id':r['lote_id'],'ruta_imagen_respaldo':r['ruta_imagen_respaldo'],'numero_pagina':3,'orden_fila':orden,
            'fecha_movimiento':'2016-10-12','fecha_original':None,'detalle':detalle,'referencia':None,'area':None,'ingresos':None,'salidas':None,'saldo_registrado':146,'saldo_calculado':146,
            'fecha_estado':'NO_APLICA_DOCUMENTAL','estado':'ANULADO_DOCUMENTO','nodo_grafo':'Origen no especificado','area_estado':'SIN_AREA_REGISTRADA','referencia_estado':'AUSENTE',
            'requiere_auditoria_nodo':False,'requiere_auditoria_referencia':False,
            'datos_originales':{'fuente':'LECTURA_FOTO_HIL','fecha_documental':None,'detalle':detalle,'ingresos':None,'salidas':None,'saldo_registrado':None,'orden_fila':orden,
                'no_existia_en_extraccion_ocr':True,'limite':'Fila tachada: se conserva sin afirmar cantidades o saldo legibles.'}}
        recuperaciones.append({'clave':f'art60-lote{r["lote_id"]}-p3-tachada-entre2721y2722-{i+1}-v1','fuente':foto['fuente'],'sha256_imagen':foto['sha256_imagen'],'campos':campos,'revision':rev})
    plan['recuperaciones']=recuperaciones
    return plan


if __name__=='__main__':congelar(generar())
