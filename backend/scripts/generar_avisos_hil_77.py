"""Diez avisos de fecha, contrastados uno por uno con diez fotografías."""
from scripts.plan_avisos_hil import construir
from scripts.generar_avisos_hil_71 import fecha
from scripts.cotejo_transcripcion_hil import congelar

CASOS={
7114:fecha('2011-08-02','2011-08-01','1-08-11 está escrito después de devolución Llallagua 02-08-11. Se conserva literal y consulta técnica del antecedente, sin cambiar filas vecinas.'),
7136:fecha('2012-07-30','2012-07-24','FIL escribe 24-7-12 después del ingreso 30-7-12. Se conserva literal y consulta técnica del antecedente, sin modificar ingreso ni devolución.'),
9444:fecha('2015-09-17','2015-08-10','REG-FIL escribe 10-8-15 después de venta 17-9-15. Se conserva la fecha documental y consulta técnica del antecedente; ingreso 3/saldo 40 intactos.'),
10582:fecha('2011-08-02','2011-08-01','La foto de Ecológica 44 escribe 1-08-11 después de devolución 02-08-11. Consulta técnica del antecedente, literal conservado y vecinos intactos.'),
10691:fecha('2011-08-02','2011-08-01','La foto de Ecológica 48 escribe 1-08-11 después de devolución 02-08-11. Consulta técnica del antecedente, literal conservado, sin modificar la devolución vecina.'),
10759:fecha('2011-08-02','2011-08-01','La foto de Ecológica 50 escribe 1-08-11 después de devolución 02-08-11. Consulta técnica del antecedente, fecha literal conservada y cantidades intactas.'),
10795:fecha('2011-08-02','2011-08-01','La foto de Ecológica 51 escribe 1-08-11 después de devolución 02-08-11. Consulta técnica del antecedente y fecha literal conservada; ninguna fila vecina se modifica.'),
10921:({},['T09','T11'],'La fecha propia 26-6-12 es legible. El antecedente 10920 tiene consulta 17-8-12, aunque en la foto solo escribe 17-08 sin año, dentro del tramo posterior al ingreso 12-07-11. Resolver el año técnico del vecino no observado excede los objetivos. Se conserva aviso y dependencia, sin inventar otro año documental ni modificarlo.',{'dependencia_fuera_objetivo':{'id':10920,'fecha_vigente':'2012-08-17','fecha_documental_contexto':'17-08, sin año','motivo':'Año de consulta del vecino no observado requiere tratamiento específico; no aplicado.'}}),
11022:fecha('2011-08-02','2011-07-12','La foto escribe ingreso 12-07-11 después de devolución 02-08-11. Se conserva literal y consulta técnica del antecedente, sin reordenar físicamente las filas.'),
12049:fecha('2011-08-02','2011-08-01','La foto de Revista 22 escribe FIL 1-08-11 después de devolución 02-08-11. Consulta técnica del antecedente y literal conservado, sin cambiar cantidades ni filas vecinas.'),
}

if __name__=='__main__':
    congelar(construir(numero=77,snapshot='backups/revision_avisos_hil_20261016/bloque_77/contexto_antes.json',especificaciones=CASOS,pendientes=[10921],limites=['Solo diez avisos, cada uno contrastado con su propia foto.','Fechas de consulta técnicas identificadas, sin certificar fechas del hecho por secuencia.','10921 conserva dependencia de año no escrito del vecino 10920, que permanece intacto.']))
