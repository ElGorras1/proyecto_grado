"""Ocho hojas completas de cuatro artículos, con todas sus filas vecinas."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(8702,8728),[50,-8,-5,-15,17,-1,-1,-1,-5,-1,-1,-1,2,-5,-4,-3,3,-3,-1,-3,-10,-2,2,1,-1,-1],
  [50,42,37,22,39,38,37,36,31,30,29,28,30,25,21,18,21,18,17,14,4,2,4,5,4,3]),
 (range(8728,8744),[-1,1,-2,2,-2,15,-3,2,10,-5,-8,8,2,-10,-6,-3],[2,3,1,3,1,16,13,15,25,20,12,20,22,12,6,3]),
 (range(9272,9298),[50,-5,-5,-10,-10,18,-3,-2,-3,20,-10,-10,6,-4,-3,-1,1,-1,1,-10,9,-1,-2,1,-5,-15],
  [50,45,40,30,20,38,35,33,30,50,40,30,36,32,29,28,29,28,29,19,28,27,25,26,21,6]),
 (range(9298,9316),[-2,4,-3,20,-10,4,-10,20,5,-2,-2,-10,-2,-2,-3,-2,-2,2],
  [4,8,5,25,15,19,9,29,34,32,30,20,18,16,13,11,9,11]),
 (range(9535,9560),[35,-3,-1,-2,-3,1,-5,-10,-8,2,-1,-1,5,-3,-4,-2,20,-1,-5,-2,-2,-2,-8,5,-5],
  [35,32,31,29,26,27,22,12,4,6,5,4,9,6,2,0,20,19,14,12,10,8,None,5,0]),
 (range(9560,9576),[5,-5,10,-6,-4,4,-4,5,-2,-3,5,10,-5,-1,-5,-4],[5,0,10,4,0,4,0,5,3,0,5,15,10,9,4,0]),
 (range(11283,11309),[20,-10,-8,1,-3,50,-10,-11,6,-5,3,-1,-2,-5,2,-3,-1,-10,-10,15,1,-1,-3,2,-5,5],
  [20,10,2,3,0,50,40,29,35,30,33,32,30,25,27,24,23,13,3,18,19,18,15,17,12,17]),
 (range(11309,11326),[-10,7,-3,2,-5,1,-1,-6,6,-2,4,-2,-1,-1,1,2,-1],[7,14,11,13,8,9,8,2,8,6,10,8,7,6,7,9,8]),
]

def generar():
    snapshot='backups/continuacion_hil_55_20261015/articulos_191_223_240_348_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDIOL','CEDDVAL','CEDOCAL','CEDOAL.')}
    for id,fields in {
        8714:{'detalle':'Devolu. F. libro','referencia':'Potosí'},8715:{'detalle':'Feria del ECUADOR','referencia':'Ventas'},8722:{'detalle':'FERIA INTER. LIBRO'},8727:{'detalle':'LUIS OPORTO'},
        8730:{'detalle':'LLALLAGUA'},8731:{'detalle':'LLALLAGUA'},8733:{'referencia':'CBB','area':None},8736:{'referencia':'CBBA','area':None},
        9289:{'detalle':'LLALLAGUA'},9290:{'detalle':'LLALLAGUA'},9292:{'fecha_movimiento':'2011-08-17'},9293:{'fecha_movimiento':'2011-08-22'},9295:{'area':'CEDOAL'},9310:{'area':'Lucy'},
        9536:{'detalle':'VENTAS CEDOAL'},9537:{'detalle':'VENTAS CEDOAL'},9539:{'detalle':'VENTAS CEDOAL'},9540:{'area':'CEDOAL'},9545:{'detalle':'CEDOAL VENTAS'},9546:{'detalle':'CEDOAL'},9547:{'referencia':'ECOLOGIA','area':None},9552:{'detalle':'VENTAS - CEDOAL'},9554:{'detalle':'VENTAS CEDOAL'},9555:{'detalle':'VENTAS CEDOAL'},9556:{'detalle':'VENTAS - CEDOAL'},
        11307:{'detalle':'LLALLAGUA'},11308:{'detalle':'LLALLAGUA'},11310:{'area':'CEDOAL'},11315:{'detalle':'CEDOAL-VENTAS'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        8732:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 aparece después de 02-08-11. Se conserva literal y consulta técnica sin reordenar filas.'),
        8737:('2012-07-30','SECUENCIA_AJUSTADA','2012-07-24','24-7-12 aparece después de 30-7-12. Se conserva literal y consulta técnica del antecedente.'),
        9291:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 aparece después de 02-08-11. Se conserva literal y consulta técnica del antecedente.'),
        9302:('2013-04-22','SECUENCIA_AJUSTADA','2013-04-18','18-4-13 aparece después de 22-4-13. Se conserva literal y consulta técnica del antecedente.'),
        9313:('2016-09-19','HIPOTESIS',None,'FIL sin fecha propia después de FIL-2016; se conserva consulta técnica del antecedente, sin certificar día ni inventar gestión 2017.'),
        9537:('2012-01-26','SECUENCIA_AJUSTADA','2011-12-22','22-12-11 aparece después de 26-1-12. Se conserva literal y consulta técnica sin modificar el año escrito.'),
        9539:('2012-06-26','SECUENCIA_AJUSTADA','2012-06-25','25-6-12 aparece después de 26-6-12. Literal y consulta técnica conservadas.'),
        9561:('2017-07-18','HIPOTESIS',None,'FIL sin fecha propia después del ingreso 18-7-17; consulta técnica del antecedente, no fecha escrita confirmada.'),
        9564:('2019-08-12','SECUENCIA_AJUSTADA','2018-08-14','14-8-18 aparece después de FIL-2019 del 12-8-19. Se conserva fecha literal y consulta técnica, sin reordenar hojas ni cambiar el año.'),
        11284:('2007-08-08','HIPOTESIS',None,'Para la Feria tiene FECHA vacía. Consulta técnica del antecedente 8-08-07, no fecha documental confirmada.'),
        11309:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 al comenzar segunda hoja aparece después de 02-08-11 al terminar primera. Se conserva orden físico y literal, con consulta técnica.'),
        11321:('2016-09-19','HIPOTESIS',None,'FIL tiene FECHA vacía; consulta técnica del antecedente, sin fecha escrita inventada.'),
    }
    extras={
        8703:{'criterios':['T16','T23'],'motivo':'La abreviación C/carta o C/conta en REF no es inequívoca; vigente C/conta conservada como incierta. Dirección en ÁREA permanece separada, sin crear instituciones por el texto de la solicitud.', 'clasificacion':{'referencia_estado':'INCIERTA','requiere_auditoria_referencia':True},'revision':{'referencia_documental_ambigua':True,'candidatos_referencia_documental':['C/carta','C/conta']}},
        8714:{'criterios':['T23'],'motivo':'Potosí está en REF; se recupera su posición sin deducir identidad ni fusionar referencias.'},
        8715:{'criterios':['T23'],'motivo':'Ventas está en REF y CAP en ÁREA; se conserva la separación de columnas.'},
        8721:{'criterios':['T14'],'motivo':'Salida 3 y saldo 14 finales visibles junto a trazos ennegrecidos anteriores; se conserva una sola salida, sin anular el renglón.'},
        **{id:{'criterios':['T23'],'motivo':'La abreviación de procedencia de recepción está en ÁREA. Se conserva como referencia y posición documental, sin crear nueva institución abreviada.', 'revision':{'columnas_documentales':{'area':rows[id]['area']}}} for id in (8733,8736)},
        9281:{'criterios':['T23'],'motivo':'SCZ aparece en ÁREA como procedencia de la recepción. Ya se conserva en REF; se registra la posición documental sin nueva área abreviada.', 'revision':{'columnas_documentales':{'area':'SCZ'}}},
        9292:{'criterios':['T01'],'motivo':'La foto escribe 17-08-11, no 13-08-11.'},9293:{'criterios':['T01'],'motivo':'La foto escribe 22-8-11, no 22-3-11.'},
        **{id:{'criterios':['T18'],'motivo':'Comillas inequívocas en ÁREA repiten CEDOAL en la misma columna; no se crea un área de comillas.'} for id in (9295,9540,11310)},
        9310:{'criterios':['T01'],'motivo':'La foto escribe Lucy en ÁREA, no Lic.; se conserva texto sin crear identidad ni alias.'},
        9547:{'criterios':['T23'],'motivo':'ECOLOGÍA comienza en REF y cruza hacia ÁREA como procedencia literal del ingreso. Se conserva en REF y su posición documental, sin crear un área nueva.', 'revision':{'columnas_documentales':{'referencia':'ECOLOGIA, texto que cruza ÁREA'}}},
        9550:{'criterios':['T14'],'motivo':'Salida 2 y cero numérico finales repasados legibles se conservan activos; una corrección de celda no anula el renglón.'},
        9557:{'criterios':['T08'],'motivo':'SALDO es guion, no cero numérico escrito. Acumulado cero solo hipotético, sin completar la celda.', 'revision':{'saldo_documental_texto':'Guion.'}},
        9562:{'criterios':['T14'],'motivo':'INGRESOS 10 y saldo 10 legibles junto a marca angular no numérica en SALIDAS; no se cuenta una segunda operación.', 'revision':{'marcas_documentales':{'salidas':'Trazo angular parecido a L, sin cifra numérica inequívoca.'}}},
        11290:{'criterios':['T16'],'motivo':'SALIDA 11 legible se conserva, sin convertirla a 10 por semejanza con otros artículos.'},
        11306:{'criterios':['T14'],'motivo':'Ingreso 2 y saldo 17 finales visibles junto a trazos anteriores ennegrecidos se conservan; no hay otra operación ni anulación de la fila.'},
    }
    plan=construir(version=55,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={191:{'primera_fila':8702,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 50; base anterior cero inferida.'},
            223:{'primera_fila':9272,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 50; base anterior cero inferida.'},
            240:{'primera_fila':9535,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 35; base anterior cero inferida.'},
            348:{'primera_fila':11283,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 20; base anterior cero inferida.'}},
        observaciones=[
            {'articulo_id':191,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 42 filas cotejadas. Columnas Potosí/REF y Ventas/CAP recuperadas, Llallagua y Luis Oporto cotejados sin alias. Procedencias CBB/CBBA conservadas con su posición original. Correcciones de celda no anulan salida 3; fechas 1-08-11 y 24-7-12 fuera de orden mantienen literal y consulta técnica. Cierre 3 coincide.'},
            {'articulo_id':223,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 44 filas cotejadas. Fechas 17-08-11 y 22-8-11 recuperadas por foto; 1-08-11 y 18-4-13 fuera de orden mantienen literal y consulta técnica. SCZ como procedencia y comillas CEDOAL conservadas por columnas; Lucy recuperado sin asociar identidad. FIL sin fecha sigue técnico. Cierre 11 coincide.'},
            {'articulo_id':240,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 41 filas cotejadas. CEDOAL y comillas recuperados, ECOLOGÍA cruza REF/ÁREA sin nueva institución. Fechas 22-12-11 y 25-6-12 fuera de orden mantienen literal; FIL sin fecha y 14-8-18 posterior a FIL-2019 conservan consulta técnica sin cambiar años. Guion de saldo no es cero documental; marca angular junto a ingreso 10 no se cuenta como operación. Cierre cero numérico coincide.'},
            {'articulo_id':348,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 43 filas cotejadas. Salida 11 legible y correcciones 2/17 se conservan sin modificar por otros artículos ni anular filas. Llallagua y comillas CEDOAL recuperados; fecha inicial vacía, 1-08-11 fuera de orden al cambiar de hoja y FIL sin fecha permanecen identificados. Cierre 8 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={191:3,223:11,240:0,348:8} and plan['cotejo']['discrepancias']==[],plan['cotejo']
    return plan

if __name__=='__main__':congelar(generar())
