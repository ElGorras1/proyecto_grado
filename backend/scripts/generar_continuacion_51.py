"""Ocho fotos con contexto: Chaco, Memoria IV, Ecológica 29 y Ecología 16."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND
from scripts.generar_continuacion_28 import recuperada

HOJAS=[
 (range(300,326),[320,-50,-11,-5,-10,-1,-15,-20,-2,-1,-1,-5,-1,-3,-5,-1,-19,-40,-5,-5,-1,-1,4,1,-1,-1],
  [320,270,259,254,244,243,228,208,206,205,204,199,198,195,190,189,170,130,125,120,119,118,122,123,122,121]),
 (range(326,352),[-1,-8,-2,-5,-5,-5,9,-8,-3,3,-3,-2,-1,-1,-3,-1,3,-1,-5,-10,3,-3,1,-1,-3,-1],
  [120,112,110,105,100,95,104,96,93,96,93,91,90,89,86,85,88,87,82,72,75,72,73,72,69,68]),
 (range(352,378),[-3,-1,-1,-1,-1,-1,1,-1,-2,-10,6,-1,-1,-1,-5,-1,-5,-1,-10,-1,8,-2,-1,-5,-15,14],
  [65,64,63,62,61,60,61,60,58,48,54,53,52,51,46,45,40,39,29,28,36,34,33,28,13,27]),
 (range(378,404),[-3,-5,1,2,-3,-1,-1,3,1,1,-1,-2,-3,3,-5,2,-1,-10,-1,-1,4,-4,1,1,-3,1],
  [24,19,20,22,19,18,17,20,21,22,21,19,16,19,14,16,15,5,4,3,7,3,4,5,2,3]),
 (range(404,408),[-2,-1,1,-1],[1,None,1,0]),
 (range(8447,8458),[15,-10,8,20,-5,3,-3,1,-10,8,-1],[15,5,13,33,28,31,28,29,19,27,26]),
 (range(9711,9726),[0,1,-2,-1,5,-1,-2,0,5,-2,-1,-1,-1,-1,-3],[3,4,2,1,6,None,3,3,8,6,5,4,4,3,0]),
 (range(11937,11957),[-2,-1,1,-1,10,-3,-5,4,-2,2,-2,-2,2,-1,-3,-1,1,4,-2,2],
  [3,2,3,2,12,None,4,8,6,8,6,4,6,5,2,1,2,6,4,6]),
]

def generar():
    snapshot='backups/continuacion_hil_51_20261015/articulos_7_184_247_386_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDIOC','Cedocd','Cdocd')}
    for id,fields in {
        304:{'detalle':'Ventas Cedoal'},327:{'detalle':'Municipios Sucre','referencia':'Sala'},333:{'referencia':'Ventas','area':None},360:{'detalle':'LLALLAGUA'},
        394:{'referencia':'DONACION','area':None},401:{'fecha_movimiento':'2014-04-17'},406:{'area':'CEDOAL'},
        8447:{'area':None,'referencia':'CBB'},8453:{'detalle':'VENTAS-CEDOAL'},8457:{'orden_fila':rows[8457]['orden_fila']+1},
        9711:{'detalle':'SALDO SEGÚN INVENTARIO'},9714:{'detalle':'FERIA DEL LIBRO'},
        11938:{'detalle':'FERIA DEL LIBRO'},11939:{'detalle':'ENVÍO DE STA. CRUZ'},11941:{'detalle':'Ingresa Santa Cruz'},11947:{'detalle':'Cedoal - Ventas'},11956:{'fecha_movimiento':'2019-12-30'},
    }.items():cambios.setdefault(id,{}).update(fields)
    for id in range(11937,11957):cambios.setdefault(id,{})['orden_fila']=rows[id]['orden_fila']+1
    tecnicas={
        **{id:('2008-08-19','SECUENCIA_AJUSTADA',literal,'Fecha escrita retrocede dentro de la primera hoja; se conserva literal y consulta técnica 19-08-08, sin reordenar filas físicas.') for id,literal in ((311,'2008-08-14'),(312,'2008-08-15'),(313,'2008-08-16'),(315,'2008-08-14'),(316,'2008-07-29'))},
        375:('2012-08-02','SECUENCIA_AJUSTADA','2012-07-24','24-7-12 aparece después de 2-8-12. Literal y consulta técnica conservadas.'),
        8451:('2012-07-30','SECUENCIA_AJUSTADA','2012-07-24','24-7-12 aparece después del ingreso 30-7-12. Literal y consulta técnica conservadas.'),
        **{id:('2005-10-13','HIPOTESIS',None,'Fila sin fecha propia; consulta técnica del antecedente 13-10-05. La nota lateral 19-12-07 se conserva sin asignación automática.') for id in (9716,9717,9718)},
        9720:('2016-09-07','HIPOTESIS',None,'FIL carece de fecha propia; consulta técnica del antecedente, sin afirmar que ocurrió ese día.'),
        11940:('2005-10-13','HIPOTESIS',None,'Feria Cedoal sin fecha propia; consulta técnica del antecedente.'),
        **{id:('2006-08-01','HIPOTESIS',None,'08-06 es fecha parcial no inequívoca; las siguientes filas tienen FECHA vacía. Consulta técnica de contexto, sin certificar día, mes y año completos.') for id in range(11941,11945)},
        11945:('2006-10-09','HIPOTESIS',None,'09-10 sin año explícito; gestión 2006 solo técnica por contexto previo a 29-11-06, no año documental confirmado.'),
        11949:('2007-06-15','HIPOTESIS',None,'Devolución carece de fecha propia; consulta técnica del antecedente. Nota lateral 14-12-07 no sustituye fecha vacía.'),
        11950:('2007-06-15','SECUENCIA_AJUSTADA','2007-02-08','8-2-07 aparece después de 15-6-07. Se conserva literal y consulta técnica del antecedente.'),
    }
    extras={
        304:{'criterios':['T18'],'motivo':'Comillas inequívocas repiten Cedoal dentro de DETALLE, sin crear otra venta ni modificar salida 10.'},
        327:{'criterios':['T23'],'motivo':'Sala está escrita en REF entre paréntesis; se separa de DETALLE y se conserva Dirección como ÁREA.', 'revision':{'columnas_documentales':{'referencia':'(Sala)','area':'Dirección'}}},
        333:{'criterios':['T23'],'motivo':'Ventas escrito en ÁREA describe la operación. Se conserva como referencia con su posición literal, sin crear área Ventas.', 'revision':{'columnas_documentales':{'area':'Ventas'}}},
        359:{'criterios':['T14'],'motivo':'Marca ennegrecida en INGRESOS no acredita cifra adicional; salida 1 visible conservada sin anular la fila.', 'revision':{'marcas_documentales':{'ingresos':'Trazo ennegrecido sin cifra inequívoca.'}}},
        372:{'criterios':['T16'],'motivo':'Ingreso 8 legible junto a marca muy ennegrecida parecida a 8 en SALIDAS. No se puede certificar si fue anulada o si expresa otro egreso. Se conserva ingreso 8 vigente solo como hipótesis, sin resolver por saldo 36 ni inventar operación adicional; artículo excluido del entrenamiento.', 'revision':{'origen_cantidades':'HIPOTESIS','efecto_cuantitativo_no_acreditado':True,'columnas_documentales':{'ingresos':8,'salidas':'Marca ennegrecida parecida a 8; cancelación o efecto no inequívocos.'},'candidatos_salidas_documentales':[None,8]}},
        394:{'criterios':['T23'],'motivo':'DONACION en ÁREA describe la operación y se conserva como referencia, con posición literal, sin crear área Donación.', 'revision':{'columnas_documentales':{'area':'DONACION'}}},
        401:{'motivo':'La fotografía escribe 17-4-14, no 27-4-14.'},
        403:{'criterios':['T02'],'motivo':'El papel dice INGRESO, escribe 1 en SALIDAS y aumenta saldo 2 a 3. Se interpreta como ingreso 1 por detalle explícito y contexto documental, conservando la columna original equivocada; no se añade una segunda operación.', 'revision':{'columnas_documentales':{'ingresos':None,'salidas':1},'columna_reinterpretada':True}},
        405:{'criterios':['T08'],'motivo':'SALDO es guion, no cero numérico escrito. El acumulado cero solo se usa como hipótesis de continuidad.', 'revision':{'saldo_documental_texto':'Guion.'}},
        407:{'criterios':['T16'],'motivo':'COOR-DIR es atribución compuesta literal; no se divide entre instituciones ni crea alias.'},
        8447:{'criterios':['T23'],'motivo':'CBB en ÁREA es procedencia literal del ingreso; se conserva como referencia y posición documental, sin crear nueva área abreviada.', 'revision':{'columnas_documentales':{'area':'CBB'}}},
        8448:{'criterios':['T16'],'motivo':'Marca redondeada muy oscura en INGRESOS sin cifra adicional inequívoca; se conserva salida 10 y la evidencia.', 'revision':{'marcas_documentales':{'ingresos':'Marca redondeada oscura; no cero certificado ni ingreso adicional.'}}},
        8457:{'criterios':['T23','T16'],'motivo':'El 2 de INGRESOS pertenece a un renglón anterior sin detalle, fecha ni saldo; OCR lo unió a FIL-2015. Se separa como nota con efecto pendiente, no como ingreso confirmado de esta salida 1. El cierre 26 queda condicional y el artículo excluido.'},
        9711:{'criterios':['T22'],'motivo':'Saldo según inventario 3 es base documental sin ingreso ficticio.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL'}},
        9714:{'criterios':['T18'],'motivo':'Comillas inequívocas repiten FERIA DEL LIBRO; salida 1 distinta conservada.'},
        9716:{'criterios':['T08'],'motivo':'SALDO vacío después de salida 1; cálculo 5 solo hipotético, no saldo 6 escrito.'},
        9718:{'criterios':['T16'],'motivo':'Devolución tiene guiones en INGRESOS y saldo 3; no hay cantidad numérica acreditada. Se conserva sin efecto cuantificado solo para consulta condicional.', 'revision':{'origen_cantidades':'HIPOTESIS','efecto_cuantitativo_no_acreditado':True,'columnas_documentales':{'ingresos':'Guiones'},'anotacion_margen_fecha':'19-12-07, sin asignar automáticamente.'}},
        9723:{'criterios':['T05'],'motivo':'Salida 1 desde saldo 4 escribe 4 como corrección visible junto a trazo anterior. Diferencia +1 del papel persiste hasta cierre escrito cero frente a cálculo condicional -1; no se inventa ingreso 1 ni se cambia la última salida 3.'},
        11938:{'criterios':['T18'],'motivo':'Comillas inequívocas repiten FERIA DEL LIBRO sin duplicar operaciones.'},
        11941:{'criterios':['T16'],'revision':{'fecha_documental_texto':'08-06, fecha parcial no inequívoca.'}},
        11942:{'criterios':['T08'],'motivo':'SALDO vacío tras salida 3; cálculo 9 hipotético, no saldo 12 escrito.'},
        11945:{'criterios':['T16'],'revision':{'fecha_documental_texto':'09-10, sin año.'}},
        11949:{'criterios':['T16'],'revision':{'anotacion_margen_fecha':'14-12-07 al margen, sin sustituir fecha vacía.'}},
        11955:{'criterios':['T16'],'motivo':'La atribución literal CIO se conserva sin resolverla como CID por frecuencia ni crear alias.'},
        11956:{'motivo':'La foto escribe 30-12-19, no 20-12-19.'},
    }
    plan=construir(version=51,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={7:{'primera_fila':300,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 320; base anterior cero inferida, no recuento.'},
            184:{'primera_fila':8447,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 15; base anterior cero inferida.'},
            247:{'primera_fila':9711,'saldo_base':3,'origen_saldo_base':'FOTO','motivo_base':'Base documental escrita 3 sin ingreso ficticio.'},
            386:{'primera_fila':11937,'saldo_base':5,'origen_saldo_base':'FOTO','motivo_base':'Recepción inicial escrita 5 omitida que se recupera una sola vez.'}},
        observaciones=[
            {'articulo_id':7,'observado':True,'excluir_entrenamiento':True,'motivo':'Cinco fotos en dos lotes y 108 filas cotejadas. INGRESO 1 colocado en SALIDAS por el papel se interpreta como recepción con columna literal conservada, sin duplicar. Marca ennegrecida parecida a 8 junto al ingreso 8 no permite certificar su cancelación: cantidad vigente solo hipotética y artículo excluido. Fechas fuera de orden y guion de saldo preservados. Cierre cero condicional, sin afirmar bloqueo automático por exclusión.'},
            {'articulo_id':184,'observado':True,'excluir_entrenamiento':True,'motivo':'Una foto y 11 filas OCR cotejadas, más cifra 2 en INGRESOS de un renglón separado sin fecha, detalle ni saldo, recuperada como nota con efecto pendiente. Se elimina su unión OCR con FIL-2015, cuya salida 1 es distinta. No se declara ingreso 2 confirmado ni se aplica T13 de otro caso. Cierre 26 condicional, artículo excluido; no se atribuye bloqueo automático solo por exclusión.'},
            {'articulo_id':247,'observado':True,'excluir_entrenamiento':True,'motivo':'Una foto y 15 filas cotejadas. Base escrita 3 sin ingreso ficticio, saldo vacío tras Sopocachi y guiones de Devolución con cantidad no acreditada conservados. Salida 1 escribe saldo 4 repetido y deja diferencia +1 persistente: cierre escrito cero frente a cálculo condicional -1. Apertura bloqueada y artículo excluido; no se inventa recepción ni se cambia salida 3.'},
            {'articulo_id':386,'observado':True,'excluir_entrenamiento':False,'motivo':'Una foto y 20 filas OCR cotejadas, más ingreso 5 y saldo 5 iniciales omitidos recuperados desde foto, sin fecha ni detalle inventados. Saldo vacío después de salida 3, fechas parciales, devolución sin fecha y nota lateral conservados. La fecha escrita 8-2-07 fuera de orden permanece literal con consulta técnica; último ingreso 30-12-19 recuperado. Cierre 6 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={7:0,184:26,247:-1,386:6},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':9723,'local':1,'acumulada':1}],plan['cotejo']
    for e in plan['revisiones']:
        if e['id']==11937:
            for k in ('saldo_base','origen_saldo_base','motivo_base'):e['revision'].pop(k,None)
        if e['id']==9725:e['cambios']['saldo_registrado']=0;e['revision'].update(usar_saldo_esperado=False,origen_saldo='FOTO')
    nota=recuperada(rows,8456,rows[8456]['orden_fila']+1,clave='art184-cifra2-antes8457-v1',detalle='Cifra 2 en INGRESOS sin fecha, detalle ni saldo',fecha='2013-11-04',saldo=27,tipo='NOTA_DOCUMENTAL',
        motivo='Cifra 2 en INGRESOS de un renglón separado sin fecha, detalle ni saldo, entre devolución 8 y FIL-2015. OCR la unió al último movimiento. Se conserva como nota con efecto cuantitativo pendiente, sin certificar recepción ni aplicar T13 de otro artículo. Saldo 27 es contexto técnico, no cifra escrita en este renglón.')
    nota['campos'].update(estado='NOTA_DOCUMENTAL',referencia='2 en INGRESOS; efecto pendiente')
    nota['campos']['datos_originales'].update(detalle=None,ingresos=2,saldo_registrado=None)
    nota['revision'].update(criterios=['T09','T16','T23'],tipo_fila='NOTA_DOCUMENTAL',saldo_documental=None,origen_saldo='HIPOTESIS',origen_cantidades='HIPOTESIS',columnas_documentales={'ingresos':2},efecto_cuantitativo_no_acreditado=True)
    ingreso=recuperada(rows,11937,1,clave='art386-ingreso5-inicial-antes11937-v1',detalle='Ingreso 5 sin fecha ni detalle documental',fecha='2005-08-17',saldo=5,tipo='MOVIMIENTO',
        motivo='Primera fila con INGRESOS 5 y SALDO 5, fecha y detalle vacíos, omitida por OCR. Se recupera una sola recepción histórica sin recuento ni apertura operativa; fecha posterior solo técnica.')
    ingreso['campos'].update(estado='ACTIVO',ingresos=5,fecha_estado='ESTIMADA_HIL')
    ingreso['campos']['datos_originales'].update(detalle=None,ingresos=5,saldo_registrado=5)
    ingreso['revision'].update(criterios=['T09','T23'],tipo_fila='MOVIMIENTO',detalle_documental=None,saldo_documental=5,origen_saldo='FOTO',origen_cantidades='FOTO',saldo_base=0,origen_saldo_base='HIPOTESIS',motivo_base='Base anterior cero inferida desde recepción y saldo 5, sin recuento acreditado.')
    plan['recuperaciones']=[nota,ingreso]
    plan['cotejo'].update(movimientos=156,cierres={7:0,184:26,247:0,386:6},cierres_calculados={7:0,184:26,247:-1,386:6},pendientes_documentales={9725:['saldo']},
        limites_cierre={7:'Cierre escrito 0 coincide condicionalmente. Marca ennegrecida junto a ingreso 8 mantiene incertidumbre de cantidad; artículo excluido del entrenamiento, sin afirmar bloqueo automático por exclusión.',
            184:'Cierre escrito 26 coincide condicionalmente sin efecto cuantificado de la cifra 2 aislada. No se certifica recepción; artículo excluido del entrenamiento, sin afirmar bloqueo automático por exclusión.',
            247:'Cierre escrito 0 frente a cálculo condicional -1. Salida 1 con saldo 4 repetido dejó diferencia +1; guiones de devolución sin cantidad acreditada. Apertura bloqueada y artículo excluido del entrenamiento.'})
    return plan

if __name__=='__main__':congelar(generar())
