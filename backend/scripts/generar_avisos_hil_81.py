"""Diez observados: fechas y diferencia aritmética documentada."""
from scripts.plan_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar
from scripts.generar_avisos_hil_71 import fecha

CASOS={
9197:fecha('2013-04-22','2013-04-18','Feria infantil 18-4-13 aparece después de recepción 22-4-13. Se conserva fecha literal y consulta técnica del antecedente, con salida 10 y saldo 18 intactos.'),
9330:fecha('2019-07-05','2018-08-14','La foto escribe FIL 2018 del 14-8-18 después de venta 5-7-19. Se conserva año 2018 literal y consulta técnica del antecedente; no se inventa el año real del hecho.'),
9939:fecha('2023-08-09','2023-08-08','La foto propia escribe FIL 8-8-23 después de ingreso 9-8-23. Se conserva literal y consulta técnica 9-8-23.'),
9950:fecha('2023-08-09','2023-08-08','La fotografía de Ecológica 92 confirma FIL 8-8-23 tras ingreso 9-8-23. Se conserva literal y consulta técnica del antecedente.'),
9960:fecha('2023-08-09','2023-08-08','En Ecológica 93 la foto propia confirma FIL 8-8-23 después de ingreso 9-8-23. Se conserva literal y fecha técnica 9-8-23.'),
9986:fecha('2024-08-15','2024-08-12','La fecha escrita de FIL-25 es 12-8-24, después de FIL-24 del 15-8-24. Se conserva 2024 documental y consulta técnica 15-8-24; el texto FIL-25 no acredita fecha 2025.'),
10006:({'fecha_movimiento':'2022-05-18'},['T09'],'La fila de ingreso 2/saldo 2 carece de fecha escrita. Consulta vigente 18-5-22 es hipotética. El vecino anterior 10005 escribe 3-6-22 y el siguiente 10007 escribe 21-5-22: ajustar solo este objetivo a junio crearía retroceso en vecino normal. Se marca fecha ausente como hipótesis y se conserva dependencia cronológica, sin cambiar vecinos ni atribuir fecha documental.',{'origen_fecha':'HIPOTESIS','fecha_documental':None,'motivo_fecha':'FECHA vacía y vecinos con fechas incompatibles; consulta hipotética, no fecha certificada.','dependencia_fuera_objetivo':{'id':10007,'fecha_documental_contexto':'2022-05-21','anterior_id':10005,'fecha_anterior_contexto':'2022-06-03','motivo':'Resolver toda la secuencia exigiría tratamiento de vecinos no observados; intactos.'}}),
10226:({},['T05'],'La foto confirma salida 3/saldo 6, tras saldo 7. El resultado local sería 4: diferencia +2 del papel que continúa en los saldos siguientes. Se conserva la evidencia, la cantidad y el aviso aritmético; no se cambia salida a 1 ni se inventa recepción 2 para cuadrar.',{'columnas_documentales':{'salidas':3,'saldo':6},'descuadre_del_papel_conservado':True,'diferencia_local_papel':2,'saldo_calculado_local':4,'requiere_confirmacion_material':True}),
10243:fecha('2024-08-15','2024-07-31','La segunda recepción está fechada 31-7-24 después de FIL-24 del 15-8-24. Se conserva fecha escrita y consulta técnica del antecedente; no se fusiona con la primera recepción ni se considera duplicada por parecerse.'),
10249:fecha('2024-11-08','2024-08-12','La foto escribe FIL-25 del 12-8-24 después de venta 8-11-24. Se conserva 2024 documental y consulta técnica 8-11-24; no se infiere 2025 como fecha real.'),
}

if __name__=='__main__':
    congelar(construir(numero=81,snapshot='backups/revision_avisos_hil_20261016/bloque_81/contexto_antes.json',especificaciones=CASOS,pendientes=[10006,10226],limites=['Diez observados; fotos propias completas y vecinos exclusivamente como contexto.','10006 conserva dependencia temporal con vecinos fuera del objetivo y fecha ausente marcada como hipótesis.','10226 conserva diferencia +2 del papel; sin operación compensatoria ni cambio a vecinos.']))
