"""Últimos nueve avisos sin cotejo de la cola inicial: fechas escritas fuera de orden."""
from scripts.plan_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar
from scripts.generar_avisos_hil_71 import fecha
CASOS={
11066:fecha('2016-12-08','2016-10-10','La foto de Ecológica 61 escribe venta 10-10-16 después de devolución 8-12-16. Se conserva fecha literal y consulta técnica del antecedente, con salida 2 y saldo 8 intactos.'),
11192:fecha('2016-12-08','2016-10-10','La foto de Ecológica 72 escribe venta 10-10-16 después de devolución 8-12-16. Se conserva literal y consulta técnica del antecedente; no se invierte la devolución por su nombre.'),
11223:fecha('2016-12-08','2016-10-10','La foto propia de Ecológica 75 confirma venta 10-10-16 tras devolución 8-12-16. Se conserva literal y consulta técnica del antecedente; siguiente ingreso julio 2017 intacto.'),
11329:fecha('2019-08-12','2018-08-14','Ecológica 81 escribe FIL 2018 del 14-8-18 después de FIL 2019 del 12-8-19. Se conserva año documental 2018 y consulta técnica 12-8-19, sin certificar año real distinto.'),
11339:fecha('2019-08-12','2018-08-14','La foto de Ecológica 82 confirma FIL 2018 del 14-8-18 tras FIL 2019 del 12-8-19. Se conserva literal y consulta técnica 12-8-19; cantidades y vecinos intactos.'),
11350:fecha('2019-08-12','2018-08-14','La foto de Ecológica 83 confirma FIL 2018 del 14-8-18 después de FIL 2019 del 12-8-19. Se conserva año literal y consulta técnica del antecedente, sin reinterpretar fechas de otras filas.'),
11358:fecha('2019-08-12','2018-08-14','La foto de Ecológica 84 escribe FIL 2018 del 14-8-18 después de FIL 2019 del 12-8-19. Se conserva literal y fecha técnica del antecedente, sin modificar vecinos.'),
11459:fecha('2013-04-22','2013-04-18','Árbol 11 escribe Feria infantil 18-4-13 tras ingreso 22-4-13. Se conserva literal y consulta técnica del antecedente; salida 10 y saldo 20 permanecen.'),
11635:fecha('2021-09-10','2021-08-03','Árbol 22 escribe ingreso 3-8-21 tras ingreso 10-9-21. Se conserva literal y consulta técnica 10-9-21; ingreso 10 y saldo 13 intactos.'),
}
if __name__=='__main__':
    congelar(construir(numero=83,snapshot='backups/revision_avisos_hil_20261016/bloque_82/contexto_antes.json',especificaciones=CASOS,pendientes=[],limites=['Solo nueve movimientos observados; cada foto propia completa vista y vecinos intactos.','Las fechas técnicas de consulta no sustituyen las fechas literales ni acreditan fechas reales.']))
