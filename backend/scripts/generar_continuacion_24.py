"""Seis fotos de Teatro contemporáneo y Festival XIV, con catorce anclajes."""
import json
from scripts.cotejo_con_anclajes_hil import construir_con_anclajes
from scripts.cotejo_transcripcion_hil import congelar,BACKEND

ANCLAJES=(*range(4025,4036),7294,7296,7297)
HOJAS=[
 (range(3986,4012),[328,-80,-50,-50,-5,-8,66,-2,-3,-1,2,-5,-15,7,-5,1,-1,-1,5,-5,-1,1,-1,-3,3,-5],
  [328,248,198,148,143,135,201,199,196,195,197,192,177,184,179,180,179,178,183,178,177,178,177,174,177,172]),
 (range(4012,4037),[-1,5,-1,-1,-10,10,-1,-2,-2,2,-5,-2,-2,2,5,-3,-1,-1,3,-8,-5,-4,-1,5,-2],
  [171,176,175,174,164,174,173,171,169,171,166,164,162,164,169,166,165,164,167,159,154,150,149,154,152]),
 (range(4037,4045),[3,-1,-4,-1,-1,1,-2,-1],[155,154,150,149,148,149,147,146]),
 (range(7289,7313),[0,-1,-3,3,-1,0,-1,-1,-1,10,-1,-2,-5,20,-5,-1,-5,-1,-1,-1,2,-1,-2,-3],
  [23,22,19,22,21,3,2,None,0,10,9,7,2,22,17,16,11,10,9,8,10,9,7,4]),
 (range(7313,7339),[-3,50,1,-1,-2,-3,-1,-1,-5,-10,10,-2,-2,-2,-3,2,-3,-1,-5,-5,0,1,-3,-1,1,-1],
  [1,51,52,51,49,46,45,44,39,29,39,37,35,33,30,32,29,28,23,18,18,19,16,15,16,15]),
 (range(7339,7361),[1,-10,8,-3,-2,20,-5,3,-5,3,-2,-1,-2,-2,-2,-5,-1,-1,-2,3,-1,-3],
  [16,6,14,11,9,29,24,27,22,25,23,22,20,18,16,11,10,9,7,10,9,6]),
]


def generar():
    snapshot='backups/continuacion_hil_24_20261015/articulos_72_120_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    for id,r in rows.items():
        if r['area'] in ('CEDODAL','CEDOC','CEDOC.','CEDDAL','Cedoal','Cedral','CEDRAL','CSDOAL','CSDOD'):
            cambios[id]={'area':'CEDOAL'}
            extras[id]={'motivo':'La celda de la foto se lee CEDOAL. Se corrige la lectura sin crear áreas o alias, conservando las decisiones previas de cantidad.'}
    for id,fields in {
        3990:{'detalle':'MASCARETRO, PASGUIDO,...'},3994:{'detalle':'VENTAS CEDOAL'},3999:{'area':None},
        4001:{'detalle':'DEVOLUCION'},4004:{'area':None},4010:{'area':None},4012:{'detalle':'PATIPIÑA'},
        4019:{'detalle':'TANTANIAN - FARACE'},4020:{'detalle':'VENTA CEDOAL'},
        4030:{'detalle':'FERIA STA CRUZ - DEVOLUCION','referencia':None},4031:{'detalle':'VENTAS - CEDOAL'},
        4037:{'detalle':'DEVOLUCION - CEDOAL'},
        7290:{'detalle':'PARA COLOMBIA'},7293:{'detalle':'CEDOAL COLOMBIA'},
        7313:{'detalle':'CEDOAL'},7316:{'detalle':'CEDOAL'},7318:{'detalle':'VENTAS CEDOAL'},
        7319:{'referencia':'EL ALTO'},7327:{'referencia':'VENTA'},7333:{'ingresos':0},
        7338:{'detalle':'LLALLAGUA'},7339:{'detalle':'LLALLAGUA'},
        7351:{'detalle':'VENTAS - CEDOAL'},7352:{'detalle':'VENTAS - CEDOAL'},7355:{'detalle':'VENTA - CID','area':'CID'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        7289:('2006-06-26','HIPOTESIS',None,'La base escribe 26-6 sin año. Se mantiene 2006 solo como año de consulta anterior a la fecha explícita de enero de 2007; no se certifica la gestión documental.'),
        7290:('2006-09-21','HIPOTESIS',None,'21-9 sin año escrito. La gestión 2006 queda como hipótesis de consulta, no como fecha confirmada.'),
        7291:('2006-10-06','HIPOTESIS',None,'6-10 sin año escrito; gestión 2006 solo de consulta.'),
        7292:('2006-11-29','HIPOTESIS',None,'29-11 sin año escrito; gestión 2006 solo de consulta.'),
        7293:('2006-11-29','HIPOTESIS',None,'14-09 sin año escrito, colocado después del 29-11. Se conserva esa lectura parcial y se usa el antecedente solo para consulta.'),
        7299:('2007-03-29','HIPOTESIS',None,'Donación sin fecha propia; consulta técnica del antecedente, sin convertir la cercanía en fecha documental.'),
        7300:('2007-04-19','HIPOTESIS',None,'19-04 sin año; gestión 2007 inferida por contexto, no fecha completa confirmada.'),
        7302:('2007-08-08','HIPOTESIS',None,'Ingreso Cbba sin fecha escrita; consulta técnica del antecedente.'),
        7308:('2007-11-15','SECUENCIA_AJUSTADA','2007-08-14','14-08-07 después del 15-11-07. Se conserva la literal, el orden físico y una consulta técnica del antecedente.'),
        7309:('2007-11-15','SECUENCIA_AJUSTADA','2007-11-05','5-11-07 después del 15-11-07. La anotación lateral 19-12-07 no permite sustituir con certeza esta fecha.'),
        7313:('2008-04-21','HIPOTESIS','2007-04-21','La hoja escribe 21-04-07 después de marzo de 2008. El año 2008 se usa solo como hipótesis de consulta; se conserva el 07 escrito.'),
        7345:('2012-07-30','SECUENCIA_AJUSTADA','2012-07-24','24-07-12 aparece después del ingreso 30-07-12. Consulta técnica del antecedente y literal conservada.'),
        7353:('2016-11-07','HIPOTESIS',None,'FIL tiene FECHA en blanco; el antecedente 07-11-16 se usa solo para consulta.'),
    }
    extras.update({
        **{id:{'criterios':['T23'],'motivo':'La devolución tiene ÁREA en blanco: se elimina el CEDODAL que el OCR había repetido, sin atribuir automáticamente un destino.'} for id in (3999,4004,4010)},
        4018:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'CEDOAL cruza REF/ÁREA. Se conserva la atribución actual marcada como pendiente, sin certificar su columna.'},
        4030:{'criterios':['T23'],'motivo':'DEVOLUCIÓN es una palabra del detalle que se extendió a REF. Se reúne el texto sin cambiar el ingreso 3 ya revisado ni crear una nueva referencia.'},
        **{id:{'motivo':'Se vuelve a cotejar la operación y sus vecinas en la foto completa; las cantidades, dirección y saldo de la corrección anterior se mantienen.'} for id in range(4025,4036) if id!=4030},
        7289:{'criterios':['T22'],'motivo':'Saldo según inventario 23 es una base documental escrita, sin ingreso 23 añadido y sin declarar un nuevo conteo físico.',
            'revision':{'lectura_fecha_parcial':'26-6; año no escrito.'}},
        7290:{'revision':{'lectura_fecha_parcial':'21-9; año no escrito.'}},7291:{'revision':{'lectura_fecha_parcial':'6-10; año no escrito.'}},
        7292:{'revision':{'lectura_fecha_parcial':'29-11; año no escrito.'}},7293:{'revision':{'lectura_fecha_parcial':'14-09; año no escrito.'}},
        7294:{'motivo':'La fotografía completa confirma el texto Según recuento físico y el saldo 3. Se conserva la discrepancia -18 y la fecha hipotética de la revisión anterior, sin inventar una salida 18.'},
        7296:{'motivo':'Se confirma SALIDAS 1, saldo en blanco y fecha ausente. Se conserva íntegra la reconstrucción anterior, sin afirmar un saldo escrito.'},
        7297:{'motivo':'La última celda muestra un cero precedido por un guion; no es solo un guion vacío. Se mantiene saldo documental 0 y la fecha hipotética anterior.'},
        7300:{'revision':{'lectura_fecha_parcial':'19-04; año no escrito.'}},
        7310:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'035-08 está escrito en la columna ÁREA, pero parece código documental junto a ESIP. Se conserva y marca pendiente; no se inventa una institución con ese número.'},
        7333:{'motivo':'La devolución de Feria Int. Libro escribe ingreso 0 y saldo 18. Se conserva el cero documental sin fabricar una cantidad positiva.'},
    })
    plan=construir_con_anclajes(version=24,instantanea=snapshot,anclajes=ANCLAJES,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(3993,3994),(4019,4020),(7339,7340)],
        bases={72:{'primera_fila':3986,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso 328 y saldo 328: base cero inferida, sin acreditar recuento previo.'},
            120:{'primera_fila':7289,'saldo_base':23,'origen_saldo_base':'FOTO','motivo_base':'Saldo según inventario 23 escrito: base documental, sin ingreso inventado.'}},
        tipos={7289:'BASE_DOCUMENTAL',7294:'RECUENTO'},observaciones=[
            {'articulo_id':72,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos y 59 filas cotejadas completas, ampliando 11 correcciones previas sin sustituir cantidades, saldos ni fechas. Se conserva cada revisión anterior íntegra y sus huellas. Se recuperan áreas realmente vacías y CEDOAL, manteniendo una atribución entre REF/ÁREA pendiente. Cierre 146 coincide sin ajustes.'},
            {'articulo_id':120,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos y 72 filas cotejadas completas, conservando tres revisiones previas y sus motivos. Base escrita 23 sin ingreso ficticio y recuento físico documental 3 con discrepancia -18 retenida. Fechas sin año, vacías o fuera de secuencia continúan técnicas y excluidas del entrenamiento. Ingreso cero, saldo ausente y código 035-08 preservados; cierre 6 coincide después del recuento documentado.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={72:146,120:6} and not plan['cotejo']['discrepancias'],plan['cotejo']
    assert plan['cotejo']['recuentos_conservados']==[{'id':7294,'previo':21,'escrito':3,'diferencia':-18}]
    assert plan['cotejo']['nuevos_distintos']==117 and len(plan['cotejo']['anclajes_previos'])==14
    return plan


if __name__=='__main__':congelar(generar())
