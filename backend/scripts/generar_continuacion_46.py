"""Amplía dos lecturas de texto de Taller 2 conservando sus 63 cotejos."""
from scripts.cotejo_con_anclajes_hil import construir_con_anclajes
from scripts.cotejo_transcripcion_hil import congelar
from scripts.generar_continuacion_43 import HOJAS

def generar():
    plan=construir_con_anclajes(version=46,instantanea='backups/continuacion_hil_46_20261015/articulo_186_revision_43_antes.json',
        anclajes=tuple(range(8529,8592)),hojas=HOJAS,correcciones={8530:{'detalle':'Cedoal Oruro'},8536:{'detalle':'Edgar Arandia'}},
        tecnicas={},grupos_fechas=[],tipos={},
        bases={186:{'primera_fila':8529,'saldo_base':10,'origen_saldo_base':'FOTO','motivo_base':'Base documental escrita 10, sin cantidad de ingreso.'}},
        observaciones=[{'articulo_id':186,'observado':True,'excluir_entrenamiento':False,'motivo':'Se amplían dos lecturas de texto del cotejo 43: Cedoal Oruro, no Cedoal Cerve; y Edgar Arandia, no Edgar Grandia. Se conservan íntegros los 63 anclajes anteriores, todas las cantidades, fechas, saldos, hipótesis y el recuento escrito 3 con diferencia -4. Cierre 12 sin cambios; no se crea persona, área ni alias y no se suman filas al acumulado.'}],
        extras={8530:{'criterios':['T01'],'motivo':'El texto visible se lee Cedoal Oruro. Se corrige el detalle OCR, manteniendo salida 3 y saldo documental vacío.'},
            8536:{'criterios':['T01'],'motivo':'El texto visible se lee Edgar Arandia. Se corrige el detalle OCR sin crear identidad o alias; la salida 1 y la fecha se conservan.'}})
    assert plan['cotejo']['cierres']=={186:12} and plan['cotejo']['nuevos_distintos']==0,plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':8533,'local':-3,'acumulada':-3}]
    assert plan['cotejo']['recuentos_conservados']==[{'id':8534,'previo':7,'escrito':3,'diferencia':-4}]
    return plan

if __name__=='__main__':congelar(generar())
