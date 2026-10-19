"""Dieciséis avisos; vecinos consultados sin modificar ni declarar cotejados."""
from scripts.plan_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar

def fecha(tecnica,literal,motivo):
    return ({'fecha_movimiento':tecnica},['T11'],motivo,{'origen_fecha':'SECUENCIA_AJUSTADA','fecha_documental':literal,'motivo_fecha':motivo})

CASOS={
11071:({'referencia':'SC.','area':None},['T17','T23'],'SC. en ÁREA del ingreso describe procedencia; se conserva como referencia literal, sin expandir sigla ni crear área.',{'columnas_documentales':{'area':'SC.'},'procedencia_documental':'SC.'}),
11082:({'detalle':'VENTAS CID','area':'CID'},['T01','T23'],'La foto escribe VENTAS CID y ÁREA CID, no VENTOS CCO ni CLD del OCR. Cantidad y saldo se conservan; clasificación por catálogo existente.',{'columnas_documentales':{'detalle':'VENTAS CID','area':'CID'}}),
11102:({'referencia':'ECOLOGIA'},['T01','T17'],'REF dice ECOLOGIA, no EcoCobia. ÁREA Difuci se conserva literal con catalogación pendiente; no se expande a una dependencia institucional inventada.',{'lectura_resuelta_catalogacion_pendiente':True,'columnas_documentales':{'referencia':'ECOLOGIA','area':'Difuci'}}),
11112:({},['T11'],'El papel escribe 10-10-16 después de 8-12-16. El FIL siguiente 11113 carece de fecha escrita y tiene consulta 10-10-16. Ajustar solo este objetivo a diciembre crearía un retroceso en ese vecino no observado: se conserva el aviso y se documenta la dependencia, sin modificarlo ni certificar otra fecha del hecho.',{'dependencia_fuera_objetivo':{'id':11113,'fecha_vigente':'2016-10-10','fecha_documental_contexto':None,'motivo':'La fecha técnica conjunta requeriría tratar un vecino no observado. No aplicado.'}}),
11117:({'referencia':'ECOLOGIA'},['T01','T17'],'REF ECOLOGIA y ÁREA DIFUSI son lecturas de la foto. Se conserva el área abreviada y la catalogación pendiente, sin crear alias ni inferir una unidad institucional.',{'lectura_resuelta_catalogacion_pendiente':True,'columnas_documentales':{'referencia':'ECOLOGIA','area':'DIFUSI'}}),
11119:({'referencia':'ECOLOGIA STA CRUZ','area':None},['T17','T23'],'REF ECOLOGIA y ÁREA STA CRUZ del ingreso describen procedencia. Se conservan juntos en referencia literal, sin crear área institucional.',{'columnas_documentales':{'referencia':'ECOLOGIA','area':'STA CRUZ'},'procedencia_documental':'STA CRUZ'}),
11827:fecha('2007-04-25','2006-11-29','Literal 29-11-06 posterior físicamente a 25-4-07. Se conserva el año escrito y se usa fecha técnica del antecedente para consulta; la nota marginal no se asigna como fecha de esta operación.'),
11830:({'estado':'NOTA_DOCUMENTAL','nodo_grafo':'Nota documental','area_estado':'NO_APLICA','requiere_auditoria_nodo':False},['T13'],'Saldo 2 del 16-12-09 repite el saldo anterior, con guiones y sin cantidades. Nota sin efecto cuantitativo ni área operativa, no ingreso ni recuento físico. No se extiende la excepción T13 de cuatro ingresos.',{'tipo_fila':'NOTA_DOCUMENTAL','columnas_documentales':{'ingresos':'guion','salidas':'guion','saldo':2}}),
7424:({'referencia':'CBB.','area':None},['T17','T23'],'CBB. es procedencia escrita en ÁREA del ingreso. Se conserva literalmente en referencia, sin expandir la sigla ni crear área.',{'columnas_documentales':{'area':'CBB.'},'procedencia_documental':'CBB.'}),
7429:fecha('2012-07-30','2012-07-24','24-7-12 está escrito después del ingreso 30-7-12. Se conserva literal y consulta técnica del antecedente; no se cambia ninguna fila vecina.'),
11084:({},['T17'],'ÁREA del ingreso presenta texto superpuesto; no se certifica CSDOSS del OCR ni una lectura CEDOAL o ECOLOGIA por parecido. REF ECOLOGIA y recepción 10/saldo 10 son legibles. Se conserva el aviso de área con evidencia y lectura incierta.',{'lectura_area':'INCIERTA','columnas_documentales':{'referencia':'ECOLOGIA','area':'texto superpuesto no inequívoco'},'requiere_confirmacion_lectura':True}),
11086:({'referencia':'ECOLOGIA ST. CRUZ','area':None},['T17','T23'],'ST. CRUZ en ÁREA del ingreso indica procedencia junto a REF ECOLOGIA. Se conservan como referencia literal sin expandir ni crear área.',{'columnas_documentales':{'referencia':'ECOLOGIA','area':'ST. CRUZ'},'procedencia_documental':'ST. CRUZ'}),
1684:fecha('2014-05-19','2014-04-10','La foto escribe 10-4-14 después de 19-5-14. Se conserva literal y fecha técnica del antecedente, sin modificar la fecha original ni movimientos vecinos.'),
1685:({'salidas':1},['T01'],'La salida escrita es 1, igual al trazo 1 de la fila anterior, y no 4 como extrajo el OCR. Se corrige por lectura de la fotografía: saldo 27 a 26. El 4 claramente escrito en la siguiente fila permanece intacto.',{'columnas_documentales':{'salidas':1,'saldo':26}}),
9099:fecha('2016-12-08','2016-10-10','10-10-16 está escrito después de 8-12-16. Se conserva literal y consulta técnica del antecedente, sin convertir la devolución previa en ingreso por su nombre.'),
9111:fecha('2024-08-15','2024-08-12','La foto escribe 12-8-24 aunque el detalle dice FIL-25. Se conserva 2024 literal y consulta técnica 15-8-24 del antecedente, sin inventar año 2025.'),
}

if __name__=='__main__':
    congelar(construir(numero=71,snapshot='backups/revision_avisos_hil_20261016/bloque_71/contexto_antes.json',especificaciones=CASOS,pendientes=[11084,11102,11112,11117],limites=['Solo dieciséis avisos HIL; contexto de ocho fotos sin cambios en filas normales.','11112 depende de fecha técnica del vecino 11113 no observado, que se conserva intacto.','DIFUCI/DIFUSI mantienen catalogación pendiente; área superpuesta 11084 no resuelta por semejanza.']))
