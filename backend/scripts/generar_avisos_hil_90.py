"""Enmienda 89 no aplicada: precisión de la transcripción documental CAP sin puntos."""
from scripts.generar_avisos_hil_89 import casos
from scripts.plan_enmienda_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar
if __name__=='__main__':
    especificaciones=casos()
    especificaciones[8610][3]['columnas_documentales']['area']='CAP'
    congelar(construir(numero=90,especificaciones=especificaciones,pendientes=[],limites=['Trece observados y seis fotos propias; vecinos exclusivamente de contexto.','Sustituye plan 89 archivado sin ensayo ni aplicación: en 8610 la celda dice CAP, sin añadir puntos a la transcripción documental.','Solo CEDOAL/CAP ya catalogadas; ninguna cantidad, saldo, fecha ni hipótesis cambia.']))
