"""Murciélagos de Bolivia: tres fotos, dos anclajes y una celda cubierta."""
import json
from scripts.cotejo_con_anclajes_hil import construir_con_anclajes
from scripts.cotejo_transcripcion_hil import congelar,BACKEND

HOJAS=[
 (range(9651,9677),[5,-2,-2,2,-1,-1,40,-5,-7,11,-2,-2,-3,1,-1,-5,3,1,-3,-1,1,-1,1,-8,5,-1],
  [5,3,1,3,2,1,41,36,29,40,38,36,33,34,33,28,31,32,29,28,29,28,29,21,26,25]),
 (range(9677,9702),[1,-5,-2,6,-2,-2,-3,1,-2,-2,-1,-3,-10,-1,10,-3,-2,4,3,-4,-5,-2,-1,5,10],
  [None,21,19,25,23,21,18,19,17,15,14,11,1,0,10,7,5,9,12,8,3,1,0,5,15]),
 (range(9702,9705),[-5,1,-6],[10,11,5]),
]

def generar():
    snapshot='backups/continuacion_hil_40_20261015/articulo_245_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area']=='Cedoal'}
    for id,fields in {9655:{'detalle':'Donación Emb.','referencia':'Britan.','area':None},9671:{'fecha_movimiento':'2011-05-18'},
        9672:{'detalle':'LLALLAGUA'},9673:{'detalle':'LLALLAGUA'},9698:{'detalle':'VENTAS - ESIP'},9699:{'detalle':'VENTAS - ESIP'}}.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        9654:('2007-10-16','HIPOTESIS',None,'La devolución o producción Potosí tiene FECHA vacía. Nota marginal 19-12-07 conservada sin asignación automática; consulta técnica del antecedente.'),
        9655:('2007-10-16','SECUENCIA_AJUSTADA','2007-02-08','La foto escribe 8-02-07 después de octubre de 2007. Se conserva la fecha literal sin cambiar el año a 2008 para ordenar; consulta técnica del antecedente.'),
        9674:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11. Se conserva literal y consulta técnica del antecedente.'),
        9691:('2019-07-05','SECUENCIA_AJUSTADA','2018-07-31','31-7-18 está escrito después de 5-7-19. Se conserva literal y consulta técnica del antecedente, sin certificar cambio de año.'),
    }
    extras={
        9654:{'criterios':['T16'],'motivo':'Nota lateral 19-12-07 junto a saldo 3 conservada; no reemplaza automáticamente la fecha vacía de la fila.', 'revision':{'anotacion_margen_fecha':'19-12-07 junto al saldo, vínculo no confirmado.'}},
        9657:{'motivo':'Se conserva íntegramente la revisión anterior: ingreso 40 y saldo 41 visibles, sin volver a OCR 10/11.'},
        9658:{'motivo':'Se conserva íntegramente la revisión anterior: salida 5 y saldo 36, sin volver a OCR 6.'},
        9671:{'criterios':['T01'],'motivo':'La fecha visible es 18-5-11, no 28-5-11; ingreso 1 y saldo 29 se conservan.'},
        9676:{'criterios':['T16'],'motivo':'La celda de ÁREA termina en un trazo no inequívoco. Se conserva CEDOD de la extracción sin completarlo por frecuencia ni crear alias.', 'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True}},
        9677:{'criterios':['T08','T19'],'motivo':'Una nota adherida cubre la celda SALDO de la primera fila de la segunda fotografía. El ingreso 1 es visible y el acumulado 26 es hipótesis; no se certifica el 1 de saldo atribuido por OCR ni se simula lectura bajo el papel.', 'revision':{'saldo_documental_cubierto':True,'obstaculo_documental':'Nota adherida cubre SALDO en la fotografía original.'}},
        9690:{'motivo':'VENTA CID escribe un cero numérico como saldo tras la salida 1. Se conserva el cero confirmado.'},
        9691:{'motivo':'El ingreso 10 escribe saldo 10 desde cero; la fecha fuera de orden se conserva literal y como consulta técnica, sin cambiar cantidad.'},
    }
    plan=construir_con_anclajes(version=40,instantanea=snapshot,anclajes=(9657,9658),hojas=HOJAS,correcciones=cambios,
        tecnicas=tecnicas,grupos_fechas=[],tipos={},
        bases={245:{'primera_fila':9651,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 5: base cero inferida, sin recuento acreditado.'}},
        observaciones=[{'articulo_id':245,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotografías y 54 filas cotejadas, 52 nuevas y dos revisiones anteriores conservadas: ingreso 40/saldo 41 y salida 5/saldo 36. Saldo de primera fila de la segunda foto está cubierto por una nota adherida: se conserva ausencia y cálculo hipotético 26, sin certificar el 1 OCR. Se recupera 18-5-11; 8-02-07 y 31-7-18 fuera de orden mantienen literal y consulta técnica. No se completan áreas parciales ni se asignan notas marginales automáticamente. Cierre 5 coincide.'}],extras=extras)
    assert plan['cotejo']['cierres']=={245:5} and not plan['cotejo']['discrepancias'],plan['cotejo']
    assert plan['cotejo']['nuevos_distintos']==52
    return plan

if __name__=='__main__':congelar(generar())
