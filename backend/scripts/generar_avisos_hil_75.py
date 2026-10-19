"""Ocho avisos contrastados con seis fotos; no modifica filas normales."""
from scripts.plan_avisos_hil import construir
from scripts.generar_avisos_hil_71 import fecha
from scripts.cotejo_transcripcion_hil import congelar

CASOS={
7871:({},['T01'],'La fecha propia 14-6-10 es legible y correcta. La devolución anterior 7870 no observada tiene consulta 16-6-10, pero la foto escribe 11-6-10. Se documenta la dependencia y se conserva el aviso sin modificar el vecino ni inventar una fecha técnica para este objetivo.',{'dependencia_fuera_objetivo':{'id':7870,'fecha_vigente':'2010-06-16','fecha_documental_contexto':'2010-06-11','motivo':'El aviso proviene de la lectura del vecino no observado. No se modifica esa fila.'}}),
7890:({'ingresos':7,'salidas':None},['T02'],'FIL DEV del 4-11-13 escribe 7 en INGRESOS, no SALIDAS como OCR. Se restaura la columna escrita, desde saldo 16 a 23, sin modificar las ventas vecinas.',{'columnas_documentales':{'ingresos':7,'salidas':None,'saldo':23}}),
8163:fecha('2011-08-02','2011-08-01','FIL escribe 1-08-11 después de devolución Llallagua 02-08-11. Consulta técnica del antecedente y fecha literal conservada; no se modifica el vecino.'),
8171:({'ingresos':None,'salidas':1},['T02'],'FIC-2019 del 12-8-19 tiene 1 en SALIDAS y saldo 1 desde 2. OCR lo puso en INGRESOS. Se corrige la columna según foto, sin alterar fecha ni saldo.',{'columnas_documentales':{'ingresos':None,'salidas':1,'saldo':1}}),
10867:fecha('2011-08-02','2011-07-12','Ingreso escribe 12-07-11 después de devolución 02-08-11. Se conserva literal y consulta técnica del antecedente, sin cambiar el año por secuencia ni mover operaciones.'),
10869:({'salidas':None},['T19'],'La foto confirma ingreso 6 y saldo 12. SALIDAS tiene una mancha ennegrecida sin cifra legible; no permite certificar el 6 duplicado del OCR como salida real. Se retira esa salida no acreditada; el efecto neto +6 queda explícitamente hipotético y excluido del entrenamiento, sin certificar que la mancha sea cero ni borrar evidencia.',{'origen_cantidades':'HIPOTESIS','columnas_documentales':{'ingresos':6,'salidas':'marca ennegrecida sin cifra legible','saldo':12},'ingreso_documental_confirmado':6,'salida_documental_no_acreditada':True,'hipotesis_efecto_neto':6,'requiere_confirmacion_material':True}),
12210:({'referencia':'Potosi','area':None,'fecha_movimiento':'2007-10-17'},['T01','T09'],'Potosi está escrito en REF, no ÁREA. Se corrige la columna OCR, preservando literal e ingreso 1/saldo 6. FECHA vacía; consulta 17-10-07 conservada sin cambio de valor y marcada como hipótesis, no fecha escrita.',{'origen_fecha':'HIPOTESIS','fecha_documental':None,'motivo_fecha':'FECHA propia vacía; 17-10-07 es consulta técnica del antecedente, no fecha documental.','columnas_documentales':{'referencia':'Potosi','area':None,'fecha':None}}),
12214:({'area':'CEDOAL'},['T01','T23'],'Gestión 2009 del 12-01-09 tiene ÁREA CEDOAL legible, no Cedroal OCR. Se corrige lectura con catálogo existente, salida 2/saldo 2 intactos, sin crear alias.',{'columnas_documentales':{'area':'CEDOAL'}}),
}

if __name__=='__main__':
    congelar(construir(numero=75,snapshot='backups/revision_avisos_hil_20261016/bloque_75/contexto_antes.json',especificaciones=CASOS,pendientes=[7871],limites=['Ocho movimientos observados; seis fotos de contexto, vecinos intactos.','7871 conserva dependencia de fecha del vecino no observado 7870.','10869 conserva cantidad de salida ilegible y efecto neto hipotético, sin certificar cero ni conciliación institucional.']))
