"""Tres fechas observadas que solo tenían orden de hojas cotejado."""
from scripts.plan_enmienda_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar
from scripts.generar_avisos_hil_71 import fecha
CASOS={
20:fecha('2011-08-02','2011-08-01','La foto completa escribe FIL 1-8-11 después de devolución Llallagua 02-08-11. Se conserva la fecha literal y se ajusta solo la consulta del objetivo al antecedente. Se mantiene íntegra la revisión previa del orden de hojas y ningún vecino cambia.'),
32:fecha('2012-06-19','2012-05-09','La foto 3 inicia con Lewy Libros 9-5-12/salida 2/saldo 380, continuando saldo 382 de la foto 2 terminada 19-6-12. Se conserva literal y consulta técnica 19-6-12, sin alterar el orden de hojas ya validado ni mover filas.'),
36:fecha('2012-08-08','2012-07-24','FIL escribe 24-7-12 después de La Rayuela 8-8-12. Se conserva literal y consulta técnica del antecedente 8-8-12; devolución posterior 14-8-12 intacta. Se conserva revisión previa del orden de hojas.'),
}
if __name__=='__main__':
    congelar(construir(numero=84,especificaciones=CASOS,pendientes=[],limites=['Tres avisos vigentes de la cola inicial, no tres objetivos nuevos de histórico completo.','Revisión previa de orden de hojas conservada íntegra; ninguna fila vecina cambia.','Fechas técnicas excluidas del entrenamiento; fechas originales y literales intactas.']))
