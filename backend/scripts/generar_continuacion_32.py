"""Tres hojas con avisos: Arquitectura CD, Catálogo Goliero y Boletín 16."""
from scripts.cotejo_transcripcion_hil import construir,congelar

HOJAS=[
 (range(970,996),[0,2,5,-5,2,-1,-1,-1,1,-1,-1,-1,-7,-3,-1,-5,5,-5,-3,-5,-1,-1,-1,-2,-2,-5],
  [232,234,239,234,236,235,234,233,234,None,None,231,224,221,220,215,220,215,212,207,206,205,204,202,200,195]),
 (range(8316,8335),[15,-15,6,-3,20,-5,3,1,-10,10,-5,-5,-4,-2,-2,4,-7,-1,3],
  [15,0,6,3,23,18,21,22,12,22,17,12,8,6,4,8,1,0,3]),
 (range(8770,8787),[2,-2,2,-2,15,-3,-3,2,-5,-6,8,1,-10,5,-2,-1,-2],[4,2,4,2,17,14,11,13,8,2,10,11,1,6,4,3,1]),
]

def generar():
    tecnicas={
        970:('2007-12-11','HIPOTESIS',None,'Base documental sin fecha propia; el 11-12-07 de la tercera fila se usa solo para consulta, no como fecha escrita de la base.'),
        971:('2007-12-11','HIPOTESIS',None,'Primera devolución sin fecha propia; consulta técnica de contexto, sin certificar fecha escrita.'),
        974:('2007-12-11','HIPOTESIS',None,'Devolución 2 tiene FECHA en blanco; consulta técnica del antecedente, no la fecha posterior 29-01-08.'),
        980:('2008-05-19','HIPOTESIS',None,'UPEA tiene FECHA en blanco; consulta técnica del antecedente.'),
        981:('2008-05-19','HIPOTESIS',None,'U. Andagoya tiene FECHA en blanco; consulta técnica del antecedente.'),
        982:('2008-05-19','SECUENCIA_AJUSTADA','2008-03-18','18-03-08 está después de 19-05-08; se conserva literal y consulta técnica del antecedente.'),
        983:('2008-05-19','SECUENCIA_AJUSTADA','2008-03-12','12-03-08 está después de 19-05-08; se conserva literal y consulta técnica del antecedente.'),
        8320:('2011-09-20','SECUENCIA_AJUSTADA','2011-07-30','La foto escribe 30-7-11 después del 20-9-11. Se conserva el año y día escritos; consulta técnica del antecedente, sin certificar otro año.'),
        8321:('2011-09-20','SECUENCIA_AJUSTADA','2011-07-24','24-7-11 después de septiembre de 2011. Se conserva literal y consulta técnica del antecedente, sin reconstruir una gestión confirmada.'),
        8322:('2011-09-20','SECUENCIA_AJUSTADA','2011-08-14','14-8-11 después de septiembre de 2011. Se conserva literal y consulta técnica del antecedente.'),
        8330:('2016-10-10','HIPOTESIS',None,'FIL 17 carece de fecha escrita. El año del detalle no acredita fecha del movimiento; consulta técnica del antecedente.'),
        8331:('2016-10-10','HIPOTESIS',None,'INGRESO 4 sin fecha propia; consulta técnica del antecedente, no fecha de una recepción nueva confirmada.'),
        8334:('2021-10-01','SECUENCIA_AJUSTADA','2021-08-01','1-8-21 está después de 1-10-21. Se conserva literal y consulta técnica del antecedente.'),
        8773:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11: literal conservada y consulta técnica del antecedente.'),
        8782:('2012-10-04','SECUENCIA_AJUSTADA','2012-10-02','La foto escribe 2-10-12, no 24-10-12, después de 4-10-12. Se conserva literal y consulta técnica del antecedente.'),
        8785:('2016-09-19','HIPOTESIS',None,'FIL 17 sin fecha propia; consulta técnica del antecedente, sin inventar fecha del año 2017.'),
    }
    cambios={972:{'fecha_movimiento':'2007-12-11'},973:{'fecha_movimiento':'2007-12-11'},979:{'detalle':'Donación Caranavi'},
        984:{'fecha_movimiento':'2008-07-03','area':'CEDOAL'},987:{'area':'CEDOAL'},988:{'area':'CEDOAL'},
        **{id:{'area':'CEDOAL'} for id in (990,991,992,995,8317,8319,8321,8323,8329,8330,8770,8771,8773,8775,8776,8777,8778,8779,8781,8782,8785)},
        8771:{'area':'CEDOAL','detalle':'LLALLAGUA'},8772:{'detalle':'LLALLAGUA'},8775:{'detalle':'VENTAS CEDOAL'},
        8786:{'fecha_movimiento':'2019-07-05','detalle':'VENTA CID','area':'CID'}}
    extras={
        970:{'criterios':['T22'],'motivo':'Ingresa del depósito Materiales tiene solo saldo 232 y cantidades vacías. Se conserva base documental sin ingreso 232 ficticio.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL'}},
        971:{'motivo':'La cifra de INGRESOS se lee 2 y el saldo 234, con trazo repasado. Se conserva la lectura y no se genera una segunda devolución.'},
        **{id:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'Se conserva el código documental en ÁREA junto a ESIP. No se crea institución ni alias con ese número.'} for id in (976,977,983)},
        979:{'motivo':'Caranavi y UPEA tienen SALDO vacío; sus acumulados de consulta 233 y 232 son hipótesis, no cifras escritas.'},
        988:{'criterios':['T18'],'motivo':'Comillas claras en ÁREA repiten CEDOAL del renglón anterior; no se crea área de comillas.'},
        8317:{'motivo':'Se conserva el cero numérico escrito después de la salida total 15. No es celda vacía ni un guion.'},
        8325:{'criterios':['T01'],'motivo':'La devolución FIL escribe INGRESOS 10, no 16: saldo escrito 22 desde 12. La fotografía confirma los dígitos, sin elegir cantidad solo por la resta.'},
        8331:{'criterios':['T14'],'motivo':'INGRESO escribe 4 y saldo 8 desde 4; la marca pequeña en SALIDAS no es egreso 1. Se conserva la marca y una sola entrada 4.', 'revision':{'marcas_documentales':{'salidas':'Trazo pequeño, sin egreso adicional legible.'}}},
        8770:{'motivo':'Primera fila ingreso 2 y saldo 4: base anterior 2 solo inferida, sin inventar otra entrada ni un recuento.'},
        8786:{'motivo':'La foto escribe 5-7-19, no 7 de mayo, y VENTA CID con área CID. Se recupera el orden día-mes y la lectura de la última letra.'},
    }
    plan=construir(version=32,instantanea='backups/continuacion_hil_32_20261015/articulos_25_176_193_antes.json',hojas=HOJAS,
        correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[(987,988)],
        bases={25:{'primera_fila':970,'saldo_base':232,'origen_saldo_base':'FOTO','motivo_base':'Base documental 232 sin cantidad de ingreso escrita.'},
            176:{'primera_fila':8316,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 15: base cero inferida sin recuento previo.'},
            193:{'primera_fila':8770,'saldo_base':2,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso 2 y saldo 4: base 2 inferida sin operación fabricada.'}},
        observaciones=[
            {'articulo_id':25,'observado':True,'excluir_entrenamiento':False,'motivo':'Hoja completa y 26 filas cotejadas. Base 232 documental sin ingreso ficticio, dos saldos vacíos conservados, fechas ausentes y fuera de orden identificadas. Se recupera 11-12-07 y 03-07-08, conservando códigos documentales en área sin crear instituciones. Cierre 195 coincide.'},
            {'articulo_id':176,'observado':True,'excluir_entrenamiento':False,'motivo':'Hoja completa y 19 filas cotejadas. Ingreso 10 mal leído como 16 corregido por foto; la marca junto a ingreso 4 no es una salida 1. Fechas de 2011 fuera de orden y FIL 17 sin fecha conservan literal y consulta técnica, sin inventar gestión confirmada. Ceros escritos y cierre 3 preservados.'},
            {'articulo_id':193,'observado':True,'excluir_entrenamiento':False,'motivo':'Hoja completa y 17 filas cotejadas. LLALLAGUA y CEDOAL recuperados de la foto; 2-10-12 y 5-7-19 corregidos conservando fechas técnicas cuando hay retroceso. FIL 17 tiene fecha vacía y no se inventa gestión. Base previa 2 inferida; cierre 1 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={25:195,176:3,193:1},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[],plan['cotejo']
    return plan

if __name__=='__main__':congelar(generar())
