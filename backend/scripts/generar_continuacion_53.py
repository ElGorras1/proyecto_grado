"""Ocho hojas completas: saldos cubiertos, diferencias del papel y columnas visibles."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(2418,2444),[-1,-2,-2,-1,-15,-1,-1,-8,-5,-5,-3,10,-1,-1,-1,-2,-1,-1,-1,-1,2,-3,10,-5,-1,-1],
  [45,43,41,40,25,24,23,15,10,5,2,12,11,10,9,7,6,5,4,3,5,2,12,7,6,5]),
 (range(2444,2451),[1,-1,1,-1,-1,1,-1],[6,5,6,5,4,5,4]),
 (range(3934,3960),[732,-2,-3,-3,-5,-3,-2,-1,-2,-2,-4,-1,-2,-1,-4,-2,-7,-3,-8,-3,-3,-2,-2,-2,-40,-10],
  [None,None,None,None,None,None,None,704,702,700,696,695,693,692,None,686,679,676,668,665,662,660,658,656,616,606]),
 (range(3960,3967),[-2,-4,2,-2,-1,1,-3],[604,600,602,600,599,600,597]),
 (range(10594,10620),[10,-8,20,-10,2,-2,-5,1,-1,-2,50,-10,-10,2,-5,1,-2,-2,-5,2,-3,-1,-10,-10,2,-2],
  [10,2,22,12,14,12,7,8,7,5,55,45,35,37,32,33,31,29,24,26,23,22,12,2,4,2]),
 (range(10620,10623),[1,-1,-1],[3,2,1]),
 (range(11869,11894),[0,-2,-2,1,10,-3,-5,6,-2,2,-2,-2,1,-5,-1,4,-3,3,-3,50,-10,8,-2,-10,10],
  [5,3,1,1,11,None,3,9,7,9,7,5,6,1,0,4,1,4,1,51,41,49,47,37,47]),
 (range(11894,11902),[-1,1,-5,5,-10,8,-30,-4],[46,47,42,47,37,45,15,11]),
]

def generar():
    snapshot='backups/continuacion_hil_53_20261015/articulos_54_70_310_384_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDOCAL','CODDOC','CEDODAL')}
    for id,fields in {
        2425:{'detalle':'Municipios Sucre','referencia':'Sala'},2445:{'detalle':'LLALLAGUA'},2446:{'detalle':'LLALLAGUA'},2449:{'area':'CEDOAL'},
        10600:{'fecha_movimiento':'2007-10-17'},10602:{'detalle':'Donación Emb.','referencia':'Bribun'},10615:{'detalle':'F. libro Oruro'},
        11871:{'detalle':'FERIA DEL LIBRO'},11894:{'detalle':'LLALLAGUA'},11895:{'detalle':'LLALLAGUA'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        2440:('2009-11-20','SECUENCIA_AJUSTADA','2009-06-30','30-6-09 aparece después de 20-11-09; literal conservado sin cambiarlo a 2010. Consulta técnica del antecedente.'),
        2447:('2011-08-02','HIPOTESIS',None,'GALERIA tiene FECHA vacía. Se conserva consulta técnica del antecedente, sin fecha escrita inventada.'),
        3943:('2022-06-01','SECUENCIA_AJUSTADA','2022-05-21','21-5-22 aparece después de 1-6-22; se conserva literal y consulta técnica sin reordenar físicamente.'),
        **{id:('2007-08-08','HIPOTESIS',None,'Ingreso y salida sin fecha propia; consulta técnica del antecedente 8-08-07, no fecha documental confirmada.') for id in (10596,10597)},
        10601:('2007-10-17','HIPOTESIS',None,'Devolución Potosí sin fecha propia; consulta técnica del antecedente 17-10-07, sin asignar automáticamente la nota lateral 19-12-07.'),
        10602:('2007-10-17','SECUENCIA_AJUSTADA','2007-02-08','08-02-07 escrito después de 17-10-07; no se cambia el año por conveniencia. Literal y consulta técnica del antecedente conservadas.'),
        **{id:('2006-08-08','HIPOTESIS',None,'08-06 es fecha parcial sin día completo inequívoco; siguientes filas sin fecha. Se conserva consulta técnica existente de contexto, sin fecha documental completa.') for id in range(11873,11877)},
        11877:('2006-09-06','HIPOTESIS',None,'09-06 es fecha parcial sin año ni día inequívocos; consulta técnica de contexto conservada sin certificar día, mes y año.'),
        11881:('2007-06-15','HIPOTESIS',None,'Devolución sin fecha propia; consulta técnica del antecedente, no fecha escrita confirmada.'),
        11886:('2007-10-17','HIPOTESIS',None,'Devolución Potosí sin fecha propia; nota lateral 19-12-07 conservada sin sustituir la celda vacía.'),
        11890:('2009-07-29','SECUENCIA_AJUSTADA','2009-07-18','18-7-09 aparece después de 29-7-09. Se conserva literal, sin convertir julio en agosto para ordenar.'),
    }
    extras={
        2425:{'criterios':['T23'],'motivo':'(Sala) pertenece a REF y Dirección a ÁREA; se conservan posiciones documentales, sin fusionar el texto con la institución.', 'revision':{'columnas_documentales':{'referencia':'(Sala)','area':'Dirección'}}},
        2449:{'criterios':['T18'],'motivo':'Comillas inequívocas en ÁREA repiten CEDOAL del renglón anterior; no constituyen área HI.'},
        **{id:{'criterios':['T16'],'motivo':'SALDO parcialmente cubierto por una nota adherida; solo se ven dígitos iniciales. No se simula lectura bajo el papel ni se certifica el saldo OCR. El acumulado sigue hipotético.', 'revision':{'saldo_documental_cubierto':True,'saldo_documental_texto':'Cifra parcialmente cubierta por nota adherida.'}} for id in range(3934,3941)},
        3941:{'criterios':['T05','T16'],'motivo':'Primer saldo completo visible 704 frente a acumulado 713 desde ingreso legible 732. La diferencia -9 ya existía al salir de la zona cubierta; no se localiza por inferencia ni se inventa egreso 9.', 'revision':{'tramo_previo_con_saldos_cubiertos':list(range(3934,3941))}},
        3948:{'criterios':['T16'],'motivo':'Cantidad repasada parecida a 4 sobre otro trazo 5; saldo 68? repasado no inequívoco. Se conserva salida vigente 4 solo como hipótesis y saldo documental ausente, sin decidir por la resta.', 'revision':{'origen_cantidades':'HIPOTESIS','candidatos_salidas_documentales':[4,5],'saldo_documental_texto':'68?, cifra final repasada; 680/688 no inequívoco.','candidatos_saldo_documental':[680,688]}},
        3958:{'criterios':['T01'],'motivo':'La fotografía escribe SALIDA 40, no 49. La corrección elimina el ajuste OCR que ocultaba diferencia anterior -9; no se cambia ingreso 732 ni se inventa salida adicional.'},
        10601:{'criterios':['T16'],'revision':{'anotacion_margen_fecha':'19-12-07, fuera de la celda de FECHA.'}},
        10602:{'criterios':['T16','T23'],'motivo':'Emb. está en DETALLE y la atribución siguiente cruza REF. Se conserva lectura OCR Bribun solo incierta, sin identificar embajada por semejanza.', 'clasificacion':{'referencia_estado':'INCIERTA','requiere_auditoria_referencia':True},'revision':{'referencia_documental_ambigua':True,'referencia_documental_texto':'Bri..., resto no inequívoco.','columnas_documentales':{'detalle':'Donación Emb.','referencia':'Bri...'}}},
        10618:{'criterios':['T14'],'motivo':'Trazo de corrección junto al ingreso 2 no es otra operación ni anula el renglón.'},
        10619:{'criterios':['T14'],'motivo':'Cifras anteriores ennegrecidas y correcciones visibles 2 en SALIDAS/SALDO se conservan; no se anula toda la fila.'},
        11869:{'criterios':['T22'],'motivo':'Saldo según inventario 5 es base documental con cantidades vacías, sin recepción ficticia.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL'}},
        11871:{'criterios':['T18'],'motivo':'Comillas claras repiten FERIA DEL LIBRO en DETALLE; permanece la salida 2 distinta con referencia 3-A.'},
        11872:{'criterios':['T05'],'motivo':'Ingreso 1 legible desde saldo 1 vuelve a escribir 1, frente a cálculo 2. Diferencia -1 persiste hasta cierre escrito 11 frente a cálculo 12; no se inventa salida ni recuento.'},
        11873:{'criterios':['T16'],'revision':{'fecha_documental_texto':'08-06, fecha parcial.'}},
        11874:{'criterios':['T08'],'motivo':'SALDO vacío después de salida 3; no se completa con cifra 8 OCR ni con acumulado 9.'},
        **{id:{'criterios':['T14'],'motivo':'Marca de cantidad anterior completamente ennegrecida en SALIDAS, sin cifra adicional inequívoca. Ingreso visible y renglón permanecen activos; una corrección de celda no anula la operación.', 'revision':{'marcas_documentales':{'salidas':'Cifra anterior ennegrecida, no legible como cantidad adicional.'}}} for id in (11876,11878)},
        11877:{'criterios':['T16'],'revision':{'fecha_documental_texto':'09-06, fecha parcial.'}},
        11886:{'criterios':['T16'],'revision':{'anotacion_margen_fecha':'19-12-07, no sustituye fecha vacía.'}},
        11900:{'criterios':['T02'],'motivo':'Devolución contiene SALIDA 30, reduce 45 a 15; no se invierte el sentido por el nombre. La salida 4 siguiente es otra fila, ambas con fecha 8-12-16.'},
    }
    plan=construir(version=53,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={54:{'primera_fila':2418,'saldo_base':46,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primera salida 1 y saldo 45; base previa 46 inferida sin ingreso inventado.'},
            70:{'primera_fila':3934,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Base previa cero solo hipotética desde ingreso 732 y cadena OCR; saldo inicial está parcialmente cubierto, sin certificar su lectura.'},
            310:{'primera_fila':10594,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 10; base previa cero inferida.'},
            384:{'primera_fila':11869,'saldo_base':5,'origen_saldo_base':'FOTO','motivo_base':'Base escrita 5 sin cantidad de recepción.'}},
        observaciones=[
            {'articulo_id':54,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 33 filas cotejadas. Base 46 inferida sin ingreso; 30-6-09 fuera de orden conserva literal y consulta técnica. GALERIA sin fecha permanece técnico. Llallagua, columnas Sala/Dirección y comillas de CEDOAL recuperados de la foto sin alias. Cierre 4 coincide.'},
            {'articulo_id':70,'observado':True,'excluir_entrenamiento':True,'motivo':'Dos fotos completas y 33 filas cotejadas. Ingreso 732 legible; siete saldos iniciales parcialmente cubiertos por adhesivo no se certifican ni reconstruyen como escritos. Primer saldo completo 704 frente a acumulado 713 deja diferencia -9 de origen no localizable dentro del tramo cubierto. Salida 40 extraída como 49 corregida por foto; Mariana Ruiz tiene cantidad 4/5 repasada, vigente 4 solo hipotética. Cierre escrito 597 frente a cálculo condicional 606; exclusión del artículo y apertura bloqueada, sin operación compensatoria.'},
            {'articulo_id':310,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 29 filas cotejadas. Fecha 17-10-07 recuperada; ingreso/salida y devolución sin fechas propias conservan consultas técnicas. 08-02-07 posterior conserva literal, sin cambiar año ni usar nota lateral 19-12-07. Atribución de embajada ilegible se conserva incierta y sin alias. Correcciones visibles 2 y F. libro Oruro recuperados por foto. Cierre 1 coincide.'},
            {'articulo_id':384,'observado':True,'excluir_entrenamiento':True,'motivo':'Dos fotos completas y 33 filas cotejadas. Base escrita 5 sin ingreso ficticio; ingreso 1 vuelve a escribir saldo 1 desde 1, dejando diferencia -1 persistente. Saldo vacío, correcciones de celdas, fechas parciales y nota lateral conservados. Devolución salida 30 y salida 4 siguientes permanecen egresos por columnas visibles. Cierre escrito 11 frente a cálculo 12; artículo excluido y apertura bloqueada, sin ajustar cantidades para cuadrar.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={54:4,70:606,310:1,384:12},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':3941,'local':-9,'acumulada':-9},{'id':11872,'local':-1,'acumulada':-1}],plan['cotejo']
    for e in plan['revisiones']:
        if e['id'] in (3966,11901):e['cambios']['saldo_registrado']={3966:597,11901:11}[e['id']];e['revision'].update(usar_saldo_esperado=False,origen_saldo='FOTO')
    plan['cotejo'].update(cierres={54:4,70:597,310:1,384:11},cierres_calculados={54:4,70:606,310:1,384:12},pendientes_documentales={3966:['saldo'],11901:['saldo']},
        limites_cierre={70:'Cierre escrito 597 frente a cálculo condicional 606. Saldos iniciales parcialmente cubiertos y cantidad repasada 4/5 impiden certificar la cadena. Diferencia -9 visible al terminar la zona cubierta; apertura bloqueada y artículo excluido del entrenamiento.',
            384:'Cierre escrito 11 frente a cálculo 12. Ingreso 1 desde saldo 1 escribe nuevamente 1; diferencia -1 persistente. Apertura bloqueada y artículo excluido del entrenamiento.'})
    return plan

if __name__=='__main__':congelar(generar())
