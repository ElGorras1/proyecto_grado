"""Cotejo completo de Solo Agnes, preservando los anclajes T06 y T10."""
import json
from scripts.cotejo_con_anclajes_hil import construir_con_anclajes
from scripts.cotejo_transcripcion_hil import congelar,BACKEND

HOJAS=[
 (range(1410,1436),[79,-2,-10,-3,-5,-3,-2,-1,-1,-1,1,-1,-2,-5,-15,18,-3,-1,-3,3,-1,-10,6,-3,1,-1],
  [79,77,67,64,59,56,54,53,52,51,52,51,49,44,29,47,44,43,40,43,42,32,38,35,36,35]),
 (range(1436,1462),[-3,-1,-1,1,-1,-2,2,-10,8,-1,-1,-3,-1,3,-1,-5,4,-5,-1,1,-1,-1,1,-2,-1,1],
  [32,31,30,31,30,28,30,20,28,27,26,23,22,25,24,19,23,18,17,18,17,16,17,15,14,15]),
 (range(1462,1488),[-1,1,-1,-3,3,-5,-1,-1,2,-5,-1,5,-1,1,-2,2,-3,3,-2,-2,2,-1,3,-1,-1,-1],
  [14,15,14,11,14,9,8,7,9,4,3,8,7,8,6,8,5,8,6,4,6,5,8,7,6,5]),
 (range(1488,1493),[-1,-2,2,1,-1],[4,2,4,5,4]),
]

def generar():
    snapshot='backups/continuacion_hil_37_20261015/articulo_35_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDOOL')}
    for id,fields in {1427:{'referencia':'CBA','area':'Dirección','detalle':'C/carta p/Tarija'},1435:{'area':'GALERIA'},1440:{'detalle':'QUIME'},
        1441:{'detalle':'LLALLAGUA'},1442:{'detalle':'LLALLAGUA'},1448:{'detalle':'APAC - PALCA'},1467:{'fecha_movimiento':'2013-05-27'},
        1469:{'detalle':'CEDOAL'},1474:{'detalle':'VENTAS - DIR'},1475:{'fecha_movimiento':'2013-12-11','referencia':'DEV'},
        1476:{'detalle':'VENTAS - CEDOAL ACTIV.','area':'CEDOAL'},1479:{'area':'ADM'},1487:{'fecha_movimiento':'2017-10-05','detalle':'ORURO CASA CULTURA','area':'CEDOAL'},
        1492:{'detalle':'VENTAS CID','area':'CID'}}.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        1410:('2008-08-07','HIPOTESIS',None,'Ingreso inicial sin fecha escrita. Se usa 07-08-08 de la siguiente fila solo como consulta, sin inventar 1 de agosto confirmado.'),
        1443:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11. Se conserva literal y consulta técnica del antecedente.'),
        1486:('2015-10-02','SECUENCIA_AJUSTADA','2015-07-07','7-7-15 aparece después de 2-10-15. Se conserva literal y consulta técnica del antecedente, sin certificar otro mes.'),
    }
    extras={
        1427:{'criterios':['T23'],'motivo':'CBA figura en REF y Dirección en ÁREA; el OCR había puesto CBA en ÁREA. Se recuperan las columnas visibles, sin crear una entidad nueva.'},
        1440:{'criterios':['T14'],'motivo':'EQUIPOS está tachado y QUIME permanece como detalle final. La salida 1 y saldo 30 siguen activos; no se anula todo el renglón.'},
        1449:{'criterios':['T06'],'motivo':'Se conserva expresamente la confirmación del titular: saldo 25, no la lectura previa 26, junto a ingreso 3 y posterior salida 1 que escribe 24.'},
        1455:{'motivo':'Se conserva íntegra la corrección previa de fecha a 4-10-12, sin volver a la lectura OCR 14-10-12.'},
        1467:{'criterios':['T01'],'motivo':'La foto escribe 27-5-13, no 27-6-13; la salida 5 y saldo 9 se conservan.'},
        1475:{'criterios':['T01'],'motivo':'La foto escribe 11-12-13, no 1-12-13. Se conserva devolución ingreso 1 y saldo 8.'},
        1487:{'criterios':['T01'],'motivo':'La última fecha de la tercera hoja se lee 5-10-17 y el detalle ORURO CASA CULTURA. Se corrige año 2015 de OCR por la fotografía, sin usar otras hojas para inventarlo.'},
        1492:{'criterios':['T01'],'motivo':'Se lee VENTAS CID y CID en ÁREA, no C10 ni C1O; se recuperan las letras por la fotografía.'},
    }
    plan=construir_con_anclajes(version=37,instantanea=snapshot,anclajes=(1449,1455),hojas=HOJAS,correcciones=cambios,
        tecnicas=tecnicas,grupos_fechas=[],tipos={},
        bases={35:{'primera_fila':1410,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 79; base cero inferida, sin recuento acreditado.'}},
        observaciones=[{'articulo_id':35,'observado':True,'excluir_entrenamiento':False,'motivo':'Cuatro fotografías completas y 83 filas cotejadas, 81 nuevas y dos anclajes anteriores conservados íntegramente. T06 mantiene saldo 25 confirmado por el titular y T10 mantiene fecha 4-10-12. Se recuperan CEDOAL, REF/ÁREA CBA/Dirección, GALERIA, ADM y CID por foto. Fechas 27-5-13, 11-12-13 y 5-10-17 corregidas; fecha inicial vacía y dos retrocesos siguen técnicos. El cierre 4 coincide sin movimientos inventados.'}],extras=extras)
    assert plan['cotejo']['cierres']=={35:4} and not plan['cotejo']['discrepancias'],plan['cotejo']
    assert plan['cotejo']['nuevos_distintos']==81
    return plan

if __name__=='__main__':congelar(generar())
