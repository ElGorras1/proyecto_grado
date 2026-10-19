"""Dieciséis avisos contrastados con ocho fotos, sin cambios de contexto."""
from scripts.plan_avisos_hil import construir
from scripts.generar_avisos_hil_71 import fecha
from scripts.cotejo_transcripcion_hil import congelar

CASOS={
236:({},['T11'],'Literal 19-7-12 escrito después de 26-8-12. Subir únicamente este objetivo a agosto volvería anterior el ingreso vecino 237 del 30-7-12. Se conserva el aviso y la dependencia, sin corregir la fecha del vecino ni asumir que agosto significa junio.',{'dependencia_fuera_objetivo':{'ids':[235,237],'fecha_documental_anterior':'2012-08-26','fecha_documental_siguiente':'2012-07-30','motivo':'Ajuste conjunto requeriría fechas de vecinos no observados; no aplicado.'}}),
238:fecha('2012-07-30','2012-07-24','Literal 24-7-12 después del ingreso 30-7-12. Se conserva la fecha escrita y consulta técnica del antecedente, sin cambiar ingreso ni devolución vecinos.'),
7272:({'referencia':'SC','area':None},['T17','T23'],'SC del ingreso es procedencia; se conserva como referencia literal sin expandir ni crear área. La revisión previa del saldo 14 de 7274 se conserva íntegra.',{'columnas_documentales':{'area':'SC'},'procedencia_documental':'SC'}),
7279:fecha('2012-07-30','2012-07-24','24-7-12 está escrito después del ingreso 30-7-12. Consulta técnica del antecedente, literal conservado, sin modificar filas vecinas.'),
7811:fecha('2015-08-07','2015-08-03','FIL-2015 escribe 3-8-15 después del ingreso 7-8-15. Se conserva literal y fecha técnica del antecedente, sin certificar una fecha distinta del hecho.'),
7829:fecha('2022-08-09','2022-07-11','VENTAS ESIP escribe 11-7-22 después de 9-8-22. Se conserva literal y consulta técnica del antecedente, sin inventar mes por secuencia.'),
9058:({'referencia':'TORRICO LASERNA STA. CRUZ','area':None},['T17','T23'],'TORRICO LASERNA en REF y STA. CRUZ en ÁREA acompañan el ingreso como procedencia. Se conservan literalmente en referencia, sin crear área institucional.',{'columnas_documentales':{'referencia':'TORRICO LASERNA','area':'STA. CRUZ'},'procedencia_documental':'STA. CRUZ'}),
9067:fecha('2011-08-02','2011-08-01','1-08-11 está escrito después de la devolución de Llallagua 02-08-11. Consulta técnica del antecedente y fecha literal conservada, sin mover operaciones.'),
9127:fecha('2011-08-02','2011-08-01','1-08-11 sigue físicamente a devolución 02-08-11. Se conserva literal y consulta técnica del antecedente; cantidades y saldos quedan intactos.'),
9130:fecha('2012-06-26','2012-06-25','Venta CEDOAL escribe 25-6-12 después de FL. Potosí 26-6-12. Se conserva el literal y fecha técnica del antecedente, sin modificar la venta por su posición.'),
9332:({'referencia':'SC','area':None},['T17','T23'],'SC figura en ÁREA del ingreso como procedencia. Referencia literal conservada sin expansión geográfica ni alta de un área.',{'columnas_documentales':{'area':'SC'},'procedencia_documental':'SC'}),
9343:fecha('2013-04-22','2013-04-18','Feria Infantil escribe 18-4-13 después de ingreso 22-4-13. Consulta técnica del antecedente, literal conservado; no se modifica la fecha vecina ni se inventa otra operación.'),
10633:({'referencia':'SCZ','area':None},['T01','T23'],'La foto coloca SCZ en REF, con ÁREA vacía. Se corrige la columna extraída por OCR, preservando sigla sin expandirla ni crear área.',{'columnas_documentales':{'referencia':'SCZ','area':None}}),
10653:fecha('2011-08-02','2011-08-01','1-08-11 de FIL sigue a devolución de Llallagua 02-08-11. Consulta técnica del antecedente y literal conservado, sin editar otros movimientos de la hoja.'),
12024:({'detalle':'LLALLAGUA','area':'CEDOAL'},['T01','T23'],'La foto escribe LLALLAGUA y ÁREA CEDOAL, no LLOLLEIUD ni CEDCOL del OCR. Se corrige exclusivamente el aviso con catálogo existente, conservando salida 1/saldo 23 y la fila de devolución siguiente intacta.',{'columnas_documentales':{'detalle':'LLALLAGUA','area':'CEDOAL'}}),
12026:fecha('2011-08-02','2011-08-01','FIL escribe 1-08-11 después de devolución 02-08-11. Se conserva literal y consulta técnica del antecedente; no se modifica la devolución vecina.'),
}

if __name__=='__main__':
    congelar(construir(numero=72,snapshot='backups/revision_avisos_hil_20261016/bloque_72/contexto_antes.json',especificaciones=CASOS,pendientes=[236],limites=['Solo dieciséis avisos HIL y ocho fotografías como evidencia y contexto.','236 mantiene dependencia cronológica de vecinos normales; no modificar esos vecinos.','Preservar íntegra revisión previa de 7274 y todas las filas fuera de objetivos.']))
