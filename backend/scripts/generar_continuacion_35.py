"""Cinco fotos completas: Música Chapaca CD y Festival 30 años CD, con incertidumbres explícitas."""
from scripts.cotejo_transcripcion_hil import construir,congelar

HOJAS=[
 (range(7445,7471),[10,-1,-2,3,-6,-3,-1,-1,2,26,0,-2,-3,-1,-3,2,29,-1,-1,-1,-5,-15,19,-2,-2,-5],
  [10,None,7,10,None,None,0,-1,1,27,None,25,22,21,18,20,49,48,47,46,41,26,45,43,41,36]),
 (range(7471,7496),[-3,2,-1,-10,8,1,-1,-1,1,-2,2,-10,9,-2,1,20,-5,3,3,-5,4,-2,-2,-2,-2],
  [33,35,34,24,32,33,32,31,32,30,32,22,31,29,30,50,45,48,51,46,50,48,46,44,42]),
 (range(7496,7501),[-2,-1,-1,3,-1],[40,39,38,41,40]),
 (range(8841,8867),[-3,-1,20,-5,5,-1,-1,-2,-1,-1,-5,-15,-2,19,-2,-2,-3,3,-1,-6,-10,10,-3,1,-1,-1],
  [14,13,33,28,33,32,31,29,28,27,22,7,5,24,22,20,17,20,19,None,3,13,10,11,10,9]),
 (range(8867,8886),[1,-1,1,-9,6,-2,2,10,-5,4,-1,-10,9,-1,-1,-4,-3,-2,-2],[10,9,10,1,7,5,7,17,12,16,15,5,14,13,12,8,5,3,1]),
]

def generar():
    # La instantánea y acercamientos se tomaron antes de reservar el número
    # 34 para la rectificación específica de Arquitectura.
    snapshot='backups/continuacion_hil_34_20261015/articulos_132_198_antes.json'
    import json
    from scripts.cotejo_transcripcion_hil import BACKEND
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDOC','GDOAL','CPOAL')}
    cambios.update({7446:{'detalle':'Donación Diario'},7447:{'detalle':'Donación Canciller'},
        7458:{'detalle':'Donación Caranavi'},7477:{'referencia':'OBSEQUIO'},7491:{'fecha_movimiento':'2013-11-04'},
        7497:{'fecha_movimiento':'2019-07-05','detalle':'VENTA CID','area':'CID'},7498:{'detalle':'ADM'},
        8856:{'detalle':'Feria libro ECUADOR','referencia':'VENTAS'},8857:{'detalle':'Feria libro U. Católica','referencia':'VENTAS','area':'CEDOAL'},
        8865:{'area':'GALERIA'},8877:{'detalle':'VENTAS CEDOAL','area':'CEDOAL'}})
    tecnicas={
        7445:('2007-03-29','HIPOTESIS',None,'Primera fecha escribe 29-03 sin año. 2007 es solo contexto anterior al 11-07-07 explícito, no una gestión confirmada ni el 2003 atribuido por OCR.'),
        7446:('2007-03-29','HIPOTESIS',None,'Donación Diario sin fecha propia; consulta técnica de la fecha parcial anterior.'),
        7447:('2007-03-29','HIPOTESIS',None,'Comillas en DETALLE repiten Donación, sin fecha propia; consulta técnica del antecedente.'),
        7453:('2007-11-15','SECUENCIA_AJUSTADA','2007-11-05','La foto escribe 5-11-07 después del 15-11-07. Se conserva literal y consulta técnica del antecedente.'),
        7455:('2007-12-13','SECUENCIA_AJUSTADA','2007-11-05','Devolución 5-11-07 después de 13-12-07, sin cantidades ni saldo escritos. Se conserva literal y consulta técnica, sin inventar una cantidad.'),
        7482:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11. Se conserva literal y consulta técnica del antecedente.'),
        7494:('2015-08-03','HIPOTESIS',None,'FIL 17 no tiene fecha escrita; consulta técnica del antecedente, sin convertir el 17 del detalle en fecha confirmada.'),
        8841:('2008-07-03','HIPOTESIS',None,'Primera fila sin fecha. Se usa 03-07-08 de la siguiente solo como contexto de consulta, no 1 de enero confirmado.'),
        8870:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11. Se conserva literal y consulta técnica del antecedente.'),
        8882:('2014-07-29','HIPOTESIS',None,'FIL 17 tiene FECHA en blanco. Se conserva ausencia y consulta técnica del antecedente, sin inventar 14 de agosto de 2017.'),
    }
    extras={
        7445:{'motivo':'Ingreso 10 y saldo 10 legibles; fecha 29-03 sin año. Se conserva el límite, sin certificar un año inferido.'},
        7446:{'motivo':'DETALLE se lee Donación Diario, con SALDO vacío. El 9 es solo cálculo hipotético.'},
        7447:{'criterios':['T18'],'motivo':'Comillas en DETALLE repiten Donación, seguida de Canciller; no se convierte en otro nombre por similitud.'},
        7449:{'criterios':['T16'],'motivo':'Aunque dice Devolución, hay SALIDA 6 escrita y SALDO vacío. Se conserva la columna literal y cálculo 4 hipotético, sin invertirla por el nombre.'},
        7450:{'motivo':'Venta Potosí escribe SALIDA 3 con SALDO vacío: se conserva 1 solo como cálculo hipotético.'},
        7451:{'criterios':['T05'],'motivo':'La celda principal escribe cero numérico entre guiones, con anotación 2 al margen. Se conservan ambos, sin reemplazar el cero por el número marginal. La siguiente salida 1 escribe -1 y luego ingreso 2 escribe 1.', 'revision':{'anotacion_margen_saldo':'2, fuera de la celda junto al cero escrito.'}},
        7452:{'motivo':'La foto escribe saldo -1, no positivo 1. Se conserva el negativo histórico y la devolución siguiente 2 que escribe 1, sin ingreso ficticio para evitarlo.'},
        7453:{'motivo':'Ingreso 2 escribe saldo 1 desde -1. El OCR había registrado 3; se recupera la lectura del papel sin cambiar cantidad.'},
        7455:{'criterios':['T16','T19'],'motivo':'La fila Devolución tiene FECHA 5-11-07, INGRESOS, SALIDAS y SALDO vacíos. No se inventa cantidad ni se anula por parecido con otra devolución; su efecto permanece indeterminado. La consulta continúa sin efecto cuantificado solo como hipótesis.', 'revision':{'origen_cantidades':'HIPOTESIS','cantidad_documental_ausente':True,'efecto_cuantitativo_no_acreditado':True}},
        7497:{'motivo':'La foto escribe 5-7-19, VENTA CID y área CID; se recuperan día-mes y lectura de la última letra.'},
        8841:{'criterios':['T16'],'motivo':'Devolución Donación Chile tiene SALIDA 3 y saldo 14. Se conserva el egreso consistente con base previa inferida 17; el nombre no basta para convertirlo en ingreso.'},
        8860:{'criterios':['T19'],'motivo':'Cantidad y saldo están repasados; la cantidad no es inequívoca entre 5/6. Se usa salida 6 solo como hipótesis de continuidad, apoyada por la extracción previa y el siguiente saldo 3 después de salida 10, sin certificarla por cuadrar.', 'revision':{'origen_cantidades':'HIPOTESIS','lectura_cantidad_parcial':'5/6, cifra repasada.','candidatos_cantidad_documental':[5,6],'lectura_saldo_parcial':'13/14, cifra repasada.','candidatos_saldo_documental':[13,14]}},
        **{id:{'criterios':['T02'],'motivo':'La foto escribe la cantidad en SALIDAS, no INGRESOS. Se conserva el egreso 4/3 y su saldo decreciente.'} for id in (8882,8883)},
    }
    plan=construir(version=35,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(7486,7487),(8853,8854),(8874,8875)],
        bases={132:{'primera_fila':7445,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 10; base cero inferida, sin recuento previo acreditado.'},
            198:{'primera_fila':8841,'saldo_base':17,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primera salida 3 y saldo 14; base 17 inferida, sin inventar una entrada.'}},
        observaciones=[
            {'articulo_id':132,'observado':True,'excluir_entrenamiento':True,'motivo':'Tres fotos y 56 filas cotejadas. Fechas parciales sin año, cero entre guiones, negativo histórico -1 y posterior saldo 1 conservados; no se inventan ingresos. Renglón Devolución sin cantidad ni saldo tiene efecto indeterminado y se mantiene sin cantidad fabricada. La reconstrucción desde ahí es condicional; cierre escrito 40 coincide con consulta sin efecto cuantificado para esa fila, pero no resuelve su incertidumbre. Artículo excluido del entrenamiento hasta aclarar; no se crea apertura ni se afirma bloqueo automático por la exclusión.'},
            {'articulo_id':198,'observado':True,'excluir_entrenamiento':True,'motivo':'Dos fotos y 45 filas cotejadas conservando el título y agrupación confirmados por el titular, aunque los encabezados de las hojas difieren. Salidas 4 y 3 extraídas como ingresos corregidas. Primera fila sin fecha y FIL 17 sin fecha quedan técnicos. Cantidad repasada de FIL se usa solo como salida hipotética 6, lectura 5/6 y saldo 13/14; no se certifica por suma. Cierre escrito 1 coincide condicionalmente; artículo excluido del entrenamiento hasta aclarar, sin afirmar bloqueo automático de apertura.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={132:40,198:1} and not plan['cotejo']['discrepancias'],plan['cotejo']
    for e in plan['revisiones']:
        if (e['articulo_id']==132 and e['id']>=7455) or (e['articulo_id']==198 and e['id']>=8860):
            e['revision']['origen_saldo']='HIPOTESIS'
        if e['id'] in (7500,8885):e['revision']['origen_saldo']='FOTO'
        if e['id']==8860:e['revision']['motivo']=extras[8860]['motivo']+' El saldo escrito queda como lectura parcial, no como celda vacía.'
    plan['cotejo']['limites_cierre']={132:'Cierre escrito 40 con reconstrucción condicional: una devolución no consigna cantidad ni saldo y su efecto no está acreditado. Artículo excluido del entrenamiento hasta aclarar.',
        198:'Cierre escrito 1 con reconstrucción condicionada a salida hipotética 6 de una cifra repasada 5/6. Artículo excluido del entrenamiento hasta aclarar.'}
    return plan

if __name__=='__main__':congelar(generar())
