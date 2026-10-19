"""Ocho fotos completas; POLIGENESIS se coteja separado y su artículo vecino queda protegido."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(1566,1592),[30,-2,-5,-1,-10,5,-1,-3,-2,-1,-1,-1,-1,1,-1,-2,2,-3,3,-5,2,-2,3,-1,-1,1],[30,28,23,22,12,17,16,13,11,10,9,8,7,8,7,5,7,4,7,2,4,2,5,4,3,4]),
 (range(1592,1600),[-1,1,-1,1,-1,-1,-1,1],[3,4,3,4,3,2,1,2]),
 (range(6983,7009),[2,20,-1,-2,-1,-1,2,-3,-1,-1,-1,-5,-6,10,-3,3,-1,-5,5,1,-1,1,-1,1,-5,3],[2,22,21,19,18,17,19,16,15,14,13,8,2,12,9,12,11,6,11,12,11,12,11,12,7,10]),
 (range(7009,7016),[-5,5,-8,7,-2,-2,-1],[5,10,2,9,7,5,4]),
 (range(7016,7041),[-10,-1,9,-3,-30,-100,-5,7,-3,-1,-1,3,1,-1,-3,3,-5,-1,5,-10,-1,-2,-20,-10,-5],[201,200,209,206,176,76,71,78,75,74,73,76,77,76,73,76,71,70,75,65,64,62,42,32,27]),
 (range(7041,7046),[-2,-1,-1,1,-2],[25,24,23,24,22]),
 (range(9156,9182),[20,-3,-10,-4,4,-3,-1,-1,1,-1,20,-10,10,-2,2,-5,-5,9,2,-1,-10,20,9,-10,20,8],[20,17,7,3,7,4,3,2,3,2,22,12,22,20,22,17,12,21,23,22,12,32,41,31,51,59]),
 (range(9182,9189),[-1,-2,-41,-1,-2,2,-8],[58,56,15,14,12,14,6]),
]

def generar():
    snapshot='backups/continuacion_hil_62_20261016/articulos_38_101_102_218_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDOA','CDOAL','CEDOCL','CODDOL')}
    for id,fields in {
        1581:{'detalle':'LLALLAGUA'},1582:{'detalle':'LLALLAGUA'},1597:{'detalle':'PATIPIÑA'},
        6988:{'fecha_movimiento':'2008-08-22'},6989:{'fecha_movimiento':'2008-08-26'},6990:{'detalle':'CEDOAL'},7005:{'detalle':'LLALLAGUA'},7006:{'detalle':'LLALLAGUA'},
        7037:{'detalle':'LIB. "AKADEMIA"'},7045:{'detalle':'VENTAS CID','area':'CID'},
        9165:{'detalle':'LLALLAGUA'},9170:{'area':'CEDOAL'},9182:{'area':'Lucy'},9183:{'detalle':'VENTAS-CEDOAL'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        1575:('2010-11-29','SECUENCIA_AJUSTADA','2010-11-17','17-11-10 aparece después de 29-11-10; literal y orden físico conservados, fecha técnica del antecedente.'),
        1583:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11; literal y consulta técnica conservados.'),
        6986:('2008-08-22','SECUENCIA_AJUSTADA','2008-08-14','14-08-08 después de María Tapia del 22-08-08; literal y orden físico conservados.'),
        6987:('2008-08-22','SECUENCIA_AJUSTADA','2008-08-17','17-08-08 después del 22-08-08; literal y consulta técnica del antecedente conservados.'),
        7007:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11; literal y consulta técnica conservados.'),
        7014:('2017-01-14','HIPOTESIS',None,'FIL 17 tiene FECHA vacía. Se conserva consulta técnica existente, sin certificar 14 de enero ni fecha exacta del hecho; 17 solo figura en DETALLE.'),
        7021:('2012-08-21','SECUENCIA_AJUSTADA','2012-07-24','24-7-12 está escrito después del 21-8-12; literal y consulta técnica del antecedente conservados.'),
        9166:('2011-07-18','SECUENCIA_AJUSTADA','2011-07-12','12-07-11 después de 18-07-11; literal y consulta técnica conservados.'),
        9175:('2012-10-04','SECUENCIA_AJUSTADA','2012-06-25','25-6-12 después de 4-10-12; no se cambia junio para ordenar, se conserva literal y consulta técnica.'),
        9185:('2016-12-08','HIPOTESIS',None,'FIL no tiene fecha propia; consulta técnica del antecedente 8-12-16, sin fecha documental certificada.'),
    }
    extras={
        1580:{'criterios':['T14'],'motivo':'Pequeña marca ennegrecida en INGRESOS no acredita cantidad; salida 1 y saldo 7 legibles conservados, sin segunda operación.', 'revision':{'marcas_documentales':{'ingresos':'Marca ennegrecida sin cifra acreditada.'}}},
        1583:{'criterios':['T14'],'motivo':'Cantidad anterior tachada en SALIDAS y corrección 3 legible; se conserva salida 3, sin anular el renglón entero.', 'revision':{'marcas_documentales':{'salidas':'Cifra anterior tachada; 3 final legible.'}}},
        1598:{'criterios':['T16'],'motivo':'Puntos aislados en ÁREA no son comillas inequívocas; no se copia una institución.', 'revision':{'marcas_documentales':{'area':'Puntos aislados, sin atribución inequívoca.'}}},
        6992:{'criterios':['T23'],'motivo':'El Alto completa el nombre Don. Pro Educ. El Alto cruzando DETALLE/REF; se conserva procedencia de columna, sin nueva institución.', 'revision':{'columnas_documentales':{'detalle':'Don. Pro Educ. El','referencia':'Alto'}}},
        6996:{'criterios':['T03'],'motivo':'Ingreso 10 lleva saldo 2 a 12; (1) en SALIDAS es anotación entre paréntesis, no otro egreso. Se aplica el criterio del titular por columna, contexto y saldo conservando la marca.', 'revision':{'origen_cantidades':'INTERPRETACION_HUMANA','marcas_documentales':{'salidas':'(1)'},'hallazgos':['HOJA_COMPLETA_COTEJADA','PARENTESIS_INTERPRETADO']}},
        7000:{'criterios':['T14'],'motivo':'Salida 5 final legible junto a cifra anterior ennegrecida; no se anula toda la fila.', 'revision':{'marcas_documentales':{'salidas':'5 final junto a marca ennegrecida.'}}},
        7014:{'criterios':['T09'],'revision':{'fecha_documental_texto':'FECHA vacía; FIL 17 solo en DETALLE.'}},
        9170:{'criterios':['T18'],'motivo':'Comillas inequívocas en ÁREA repiten CEDOAL de la fila anterior, sin área nueva I I I.'},
        9184:{'criterios':['T02'],'motivo':'DEVOLUCIÓN tiene SALIDA 41 legible y saldo 15 desde 56; se conserva egreso por columna, sin invertirlo por el nombre.'},
    }
    plan=construir(version=62,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={38:{'primera_fila':1566,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 30 explícitos; base previa cero inferida.'},101:{'primera_fila':6983,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 2 explícitos; base previa cero inferida. Segundo ingreso 20 es otra fila real del mismo día.'},102:{'primera_fila':7016,'saldo_base':211,'origen_saldo_base':'HIPOTESIS','motivo_base':'Saldo previo 211 inferido desde salida 10 y primer saldo escrito 201, sin ingreso ficticio ni copiar movimientos del artículo 98.'},218:{'primera_fila':9156,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 20 explícitos; base previa cero inferida.'}},
        observaciones=[
            {'articulo_id':38,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 34 filas cotejadas. Títulos de las dos hojas difieren, pero se mantiene agrupación existente según T20, sin decidir otro artículo. Literal 17-11-10 después de 29-11-10 y 1-08-11 después del 02-08-11 conservan fecha escrita y consulta técnica. Llallagua y Patipiña recuperados por foto; corrección de cantidad 3 y marca ennegrecida no anulan toda una fila. Cierre 2 coincide.'},
            {'articulo_id':101,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 33 filas cotejadas. Dos ingresos 2/20 del mismo día siguen distintos. Devolución ingreso 10/saldo 12 conserva (1) en SALIDAS como anotación, sin egreso adicional. Fechas OCR 22-08-08 y 26-08-08 recuperadas; fechas fuera de orden conservan literal. FIL 17 sin fecha propia identificado; corrección 5 no anula salida. Cierre 4 coincide.'},
            {'articulo_id':102,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 30 filas cotejadas como POLIGENESIS, separado de REV DE HISTORIA POLIGENESIS 1 por confirmación expresa del titular. El artículo 98 y sus 56 filas quedan protegidos íntegros. Base previa 211 inferida sin copiar operaciones; literal 24-7-12 después del 21-8-12 conserva orden físico y fecha técnica. CEDOAL, AKADEMIA y VENTAS CID recuperados por foto, sin crear alias. Cierre 22 coincide.'},
            {'articulo_id':218,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 33 filas cotejadas, manteniendo agrupación y títulos actuales según T20. Fechas 12-07-11 y 25-6-12 fuera de orden conservan literal y consulta técnica. Comillas de ÁREA repiten CEDOAL, Lucy y textos recuperados por foto sin alias. Devolución con salida 41 legible permanece egreso; FIL sin fecha propia identificado. Cierre 6 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['discrepancias']==[] and plan['cotejo']['cierres']=={38:2,101:4,102:22,218:6},plan['cotejo']
    protegido=json.loads((BACKEND/'backups/continuacion_hil_62_20261016/proteccion_articulo_98_antes.json').read_text(encoding='utf-8'))
    assert protegido['nombre_102']=='POLIGENESIS' and protegido['articulo']['nombre']=='REV DE HISTORIA POLIGENESIS 1'
    plan['cotejo']['articulos_protegidos']=[protegido['protegido']]
    return plan

if __name__=='__main__':congelar(generar())
