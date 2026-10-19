"""Siete fotografías completas de Moraima Ibáñez DVD y Quipus."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(1612,1638),[100,-1,-1,-1,-20,-1,1,-2,-3,3,-1,-3,-1,3,-1,-10,10,-3,1,-1,-3,-1,1,-1,-2,2],
  [100,99,98,97,77,76,77,75,72,75,74,71,70,73,72,62,72,69,70,69,66,65,66,65,63,65]),
 (range(1638,1664),[-10,10,-3,3,-1,-1,-5,5,-5,-1,3,-1,-1,1,-1,1,-1,1,-1,-3,3,-5,-1,5,-1,-5],
  [55,65,62,65,64,63,58,63,58,57,60,59,58,59,58,59,58,59,58,55,58,53,52,57,56,51]),
 (range(1664,1681),[-1,5,-1,1,-2,2,-3,-1,-2,-2,2,3,-2,-1,-4,2,1],
  [50,55,54,55,53,55,52,51,49,47,49,52,50,49,45,47,48]),
 (range(6172,6198),[265,-1,-4,3,-4,1,1,-1,-20,-1,-1,-5,3,-1,-1,-1,-5,5,-3,-15,-5,-3,-1,-1,-1,3],
  [265,264,260,263,259,260,261,260,240,239,238,233,236,235,234,233,228,233,230,215,210,207,206,205,204,207]),
 (range(6198,6224),[-1,-10,10,-1,-3,-1,-1,-4,-1,-1,1,-1,-2,2,-10,10,-1,-1,-3,-1,-1,1,-1,-3,-10,-3],
  [206,196,206,205,202,201,200,196,195,194,195,194,192,194,184,194,193,192,189,189,188,189,188,185,175,172]),
 (range(6224,6250),[-1,10,-2,2,-5,5,-5,7,-1,-1,1,-1,-13,1,-7,-3,3,-5,5,-1,-10,-1,10,-2,-2,2],
  [171,181,179,181,176,181,176,183,182,181,182,181,168,169,162,159,162,157,162,161,151,150,160,158,156,158]),
 (range(6250,6271),[6,-1,-3,-1,-2,-2,2,1,-2,-2,2,1,-1,-4,-1,-2,-1,-4,-2,2,-2],
  [164,163,160,159,157,155,157,158,156,154,156,157,156,152,151,149,148,144,142,144,142]),
]

def generar():
    snapshot='backups/continuacion_hil_36_20261015/articulos_42_92_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDOC','CEDOCAL')}
    cambios.update({1625:{'fecha_movimiento':'2010-06-11','area':'CEDOAL'},1648:{'detalle':'DEVOLUCIÓN','area':'CEDOAL'},
        1653:{'area':'CEDOAL'},1662:{'detalle':'DONACIÓN UTO','referencia':'DONA','area':'CEDOAL'},1664:{'detalle':'UPEA','area':'CEDOAL'},
        1668:{'detalle':'VENTAS - CEDOAL ACTIV.','area':'CEDOAL'},1671:{'detalle':'VENTAS - CEDOAL','area':'CEDOAL'},
        6176:{'detalle':'Ginebra'},6200:{'fecha_movimiento':'2010-09-03'},6201:{'fecha_movimiento':'2010-12-27'},6202:{'area':'ADM'},
        6210:{'detalle':'LLALLAGUA'},6211:{'detalle':'LLALLAGUA'},6253:{'detalle':'VENTAS - CEDOAL'}})
    tecnicas={
        1638:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11: se conserva literal y consulta técnica del antecedente.'),
        1676:('2014-11-27','HIPOTESIS',None,'FIL no tiene fecha escrita. La consulta técnica conserva el antecedente, sin inventar gestión del detalle.'),
        6205:('2011-04-07','SECUENCIA_AJUSTADA','2011-03-16','16-03-11 está escrito después de 07-04-11. Se conserva literal y consulta técnica del antecedente.'),
        6212:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11: se conserva literal y consulta técnica del antecedente.'),
        6225:('2012-06-06','SECUENCIA_AJUSTADA','2012-05-19','19-5-12 aparece después de 6-6-12. Se conserva literal y consulta técnica del antecedente.'),
        6237:('2013-03-12','SECUENCIA_AJUSTADA','2013-03-05','5-3-13 aparece después del 12-3-13. Se conserva literal y consulta técnica del antecedente.'),
        6250:('2014-04-29','SECUENCIA_AJUSTADA','2014-04-11','11-4-14 está después de 29-4-14 al comenzar la cuarta hoja. Se conserva literal y consulta técnica del antecedente.'),
        6265:('2016-05-28','HIPOTESIS',None,'FIL tiene FECHA en blanco. Se usa la fecha anterior solo para consulta; no es fecha escrita.'),
    }
    extras={
        1653:{'criterios':['T18'],'motivo':'Comillas en ÁREA repiten el CEDOAL anterior; no se crea un área llamada comillas.'},
        1662:{'criterios':['T23'],'motivo':'La foto escribe CEDOAL en REF y DONA en ÁREA. Se conservan las columnas documentales y se ordenan semánticamente referencia DONA y área CEDOAL; no se crea un área Donación.', 'revision':{'columnas_documentales':{'referencia':'CEDOAL','area':'DONA'}}},
        1663:{'criterios':['T14'],'motivo':'FIL tiene cantidad anterior tachada y salida final 5 visible, saldo corregido a 51. Se conserva la corrección sin anular la fila.', 'revision':{'marcas_documentales':{'salidas':'Cifra anterior tachada, 5 final visible.','saldo':'Cifra anterior tachada, 51 final visible.'}}},
        1664:{'criterios':['T14'],'motivo':'UPEA está tachado y reescrito en DETALLE, sin anulación de cantidad ni saldo: se conserva una salida 1.'},
        1680:{'criterios':['T19'],'motivo':'INGRESO y saldo están repasados. La cifra de ingreso no es inequívoca entre 1/8; se conserva ingreso 1 solo como hipótesis de consulta, sin certificarlo porque 47+1=48. Cierre escrito final 48 se mantiene y la incertidumbre exige exclusión del artículo.', 'revision':{'origen_cantidades':'HIPOTESIS','candidatos_cantidad_documental':[1,8],'marcas_documentales':{'ingresos':'Cifra repasada, lectura no inequívoca.','saldo':'48 con trazos anteriores repasados.'}}},
        6202:{'criterios':['T01'],'motivo':'ÁREA se lee ADM, no DDH; se corrige por la fotografía sin crear alias.'},
        6212:{'criterios':['T02'],'motivo':'La foto escribe salida 10 en SALIDAS, no ingreso: saldo 194 a 184. Se corrige la columna OCR.'},
        6217:{'criterios':['T05'],'motivo':'APAC-PALCA tiene salida 1 legible desde 189 y vuelve a escribir 189. Se conserva la salida y el saldo del papel; cálculo independiente 188. La diferencia +1 persiste hasta cierre escrito 142 frente a cálculo 141, sin ingreso compensatorio ficticio.'},
        6251:{'criterios':['T16'],'motivo':'La palabra de REF cruza hacia ÁREA. Se conserva el texto y área vacía, sin crear una institución por una lectura no inequívoca.'},
        6259:{'motivo':'LUCY está escrito como ÁREA y se conserva literal; este cotejo no crea áreas ni alias por nombres personales.'},
        6261:{'motivo':'ENTREGA-DIR tiene INGRESO 1 y saldo creciente 157. Se conserva la columna escrita, sin invertirla por el nombre del detalle.'},
    }
    plan=construir(version=36,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={42:{'primera_fila':1612,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 100; base cero inferida, sin recuento acreditado.'},
            92:{'primera_fila':6172,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 265; base cero inferida, sin recuento acreditado.'}},
        observaciones=[
            {'articulo_id':42,'observado':True,'excluir_entrenamiento':True,'motivo':'Tres fotografías y 69 filas cotejadas. CEDOAL recuperado, columnas REF/ÁREA intercambiadas en donación UTO preservadas en metadatos. Cantidad tachada de FIL corregida en el papel no anula la fila. FIL sin fecha permanece técnico. Último ingreso repasado 1/8 se mantiene como ingreso hipotético 1: cierre escrito 48 coincide condicionalmente, sin certificar la cifra ni crear apertura. Artículo excluido del entrenamiento hasta aclarar.'},
            {'articulo_id':92,'observado':True,'excluir_entrenamiento':True,'motivo':'Cuatro fotografías y 99 filas cotejadas. Salida FIL 10 extraída como ingreso y fecha 03-09-10 corregidas. APAC-PALCA escribe salida 1 desde 189, pero saldo 189; el cálculo es 188 y la diferencia +1 persiste. Cierre escrito 142 frente a cálculo 141, apertura bloqueada y exclusión del entrenamiento. Fechas literales fuera de orden y FIL sin fecha conservan marca técnica. No se inventan ajustes.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={42:48,92:141},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':6217,'local':1,'acumulada':1}],plan['cotejo']
    for e in plan['revisiones']:
        if e['articulo_id']==92 and e['id']>=6217:e['revision']['origen_saldo']='HIPOTESIS'
        if e['id']==1680:e['revision']['origen_saldo']='FOTO'
        if e['id']==6270:e['cambios']['saldo_registrado']=142;e['revision'].update(usar_saldo_esperado=False,origen_saldo='FOTO')
    plan['cotejo'].update(cierres={42:48,92:142},cierres_calculados={42:48,92:141},pendientes_documentales={6270:['saldo']},
        limites_cierre={42:'Cierre escrito 48 coincide condicionalmente con ingreso hipotético 1 de una cifra repasada 1/8. Artículo excluido del entrenamiento hasta aclarar.',
            92:'Cierre escrito 142 frente a cálculo 141 por salida 1 de APAC-PALCA que no se resta en el papel. Pendiente de conciliación; apertura bloqueada y artículo excluido del entrenamiento.'})
    return plan

if __name__=='__main__':congelar(generar())
