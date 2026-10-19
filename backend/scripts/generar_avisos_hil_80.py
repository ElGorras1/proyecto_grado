"""Once fechas observadas y una base ausente; vecinos intactos."""
from scripts.plan_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar
from scripts.generar_avisos_hil_71 import fecha

CASOS={
199:fecha('2015-07-20','2015-07-11','Reposición de demasía 11-7-15 está escrita después de venta 20-7-15. Se conserva fecha literal y consulta técnica 20-7-15 del antecedente; cantidades y vecinos intactos.'),
640:fecha('2012-08-24','2012-08-14','Devolución FIL 14-8-12 aparece después de FIL 24-8-12 en la misma hoja. Se conserva literal y fecha técnica del antecedente, sin cambiar ninguna fila vecina.'),
921:fecha('2013-03-06','2013-03-05','Devolución Letras Paceñas 5-3-13 aparece después de venta 6-3-13. Se conserva literal y consulta técnica del antecedente.'),
7047:fecha('2019-07-25','2019-07-05','Venta 5-7-19 está escrita después de ingreso 25-7-19. Se conserva literal y fecha técnica del antecedente; no se modifica área ni otro renglón.'),
7060:fecha('2019-07-25','2019-07-05','La foto propia escribe venta 5-7-19 después de ingreso 25-7-19. Se conserva literal y consulta técnica del antecedente; no se deduce por similitud con otro artículo.'),
7362:fecha('2021-09-13','2021-08-01','Ingreso 1-8-21 aparece físicamente después de ingreso 13-9-21. Se conserva fecha escrita y consulta técnica del antecedente, sin certificar otra fecha del hecho.'),
8243:fecha('2015-08-07','2015-08-03','FIL 2015 del 3-8-15 aparece después del ingreso 7-8-15. Se conserva literal y consulta técnica del antecedente.'),
8250:fecha('2015-08-07','2015-08-03','La foto propia escribe FIL 3-8-15 después de ingreso 7-8-15. Se conserva literal y consulta técnica 7-8-15.'),
8299:fecha('2016-08-24','2016-08-19','FIL 2016 del 19-8-16 está escrito después de ingreso 24-8-16. Se conserva el mes 8 literal y consulta técnica del antecedente.'),
8361:fecha('2019-07-23','2019-07-05','Venta 5-7-19 está entre ingresos 23-7-19 y 25-7-19. Se conserva literal y consulta técnica 23-7-19, sin modificar los ingresos vecinos.'),
8392:({},['T22'],'La primera fila visible es salida 10/saldo 8 del 04-08-10, sin apertura escrita ni página anterior del artículo. Se conserva la operación y se representa base anterior 18 inferida como 8+10, exclusivamente hipotética; no se crea ingreso ni recuento físico.',{'saldo_base':18,'origen_saldo_base':'HIPOTESIS','base_no_es_ingreso':True,'motivo_saldo_base':'Primera operación visible: saldo 8 más salida 10; base no documentada, hipótesis excluida del entrenamiento.'}),
8445:fecha('2019-07-05','2018-07-23','Ingreso escribe 23-7-18 después de venta 5-7-19. Se conserva el año documental 2018 y consulta técnica 5-7-19. La siguiente fila sin fecha documental permanece intacta; no se certifica 2019 como año real del ingreso.'),
}

if __name__=='__main__':
    congelar(construir(numero=80,snapshot='backups/revision_avisos_hil_20261016/bloque_80/contexto_antes.json',especificaciones=CASOS,pendientes=[],limites=['Solo doce avisos HIL; fotografías completas vistas y vecinos intactos.','Fechas técnicas de consulta no sustituyen fechas originales ni certifican la fecha del hecho.','8392 conserva base anterior 18 hipotética; no es ingreso ni dato certificado para entrenamiento.']))
