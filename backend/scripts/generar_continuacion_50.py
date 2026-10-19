"""Nueve fotos completas con un anclaje previo protegido de Los primeros 30."""
import json
from scripts.cotejo_con_anclajes_hil import construir_con_anclajes
from scripts.cotejo_transcripcion_hil import congelar,BACKEND

HOJAS=[
 (range(790,816),[33,-1,-1,-5,-1,-1,1,-1,-2,2,-10,10,-1,-1,-3,-1,2,-1,-1,-10,-1,10,-2,-1,2,-5],
  [33,32,31,26,25,24,25,24,22,24,14,24,23,22,19,18,20,19,18,8,7,17,15,14,None,11]),
 (range(816,842),[5,-5,-1,1,-1,-1,1,-1,-1,1,-1,2,-1,-3,3,-5,-1,5,-1,-5,4,-2,2,-3,-1,-1],
  [16,11,10,11,10,9,10,9,8,9,8,10,9,6,9,4,3,8,7,2,6,4,6,3,2,1]),
 (range(842,846),[1,3,-1,-2],[2,5,4,2]),
 (range(7162,7188),[0,2,-1,-1,-1,-3,-1,-2,29,-2,1,1,-2,-1,-1,-1,-2,-5,-15,19,-1,-1,-1,-5,-1,-1],
  [26,28,27,26,25,22,21,19,48,46,47,48,46,45,44,43,41,36,21,40,39,38,37,32,31,30]),
 (range(7188,7214),[-1,5,-3,-2,-4,-3,3,-1,-10,7,1,-1,-3,-1,-1,1,-1,-1,1,-10,8,1,-2,1,20,-5],
  [29,34,31,29,25,22,25,24,14,21,22,21,18,17,16,17,16,15,16,6,14,15,13,14,34,29]),
 (range(7214,7228),[-7,10,3,-5,3,-2,2,-1,-1,-2,-2,-2,-1,3],[22,32,35,30,33,31,33,32,31,29,27,25,24,27]),
 (range(12222,12248),[-2,-3,3,-2,-5,50,-5,-10,-10,21,-3,-3,-2,-3,2,-3,-1,-10,0,1,-1,-3,-1,1,-1,1],
  [13,10,13,11,6,56,51,41,31,52,49,46,44,41,43,40,39,29,29,30,29,26,25,26,25,26]),
 (range(12248,12272),[-10,8,-3,3,-5,-10,11,1,-10,7,-1,-2,-2,-2,-1,-1,-2,-3,-1,-1,-2,5,-3,-1],
  [16,24,21,24,19,9,20,21,11,18,17,15,13,11,10,9,7,4,3,2,0,5,2,1]),
 (range(12272,12277),[5,-2,-2,5,-4],[6,4,2,7,3]),
]

def generar():
    snapshot='backups/continuacion_hil_50_20261015/articulos_15_115_395_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CEDOC','CDOAL','CEDOOC','CEDOOL','CEDOCAL')}
    for id,fields in {
        798:{'detalle':'LLALLAGUA'},799:{'detalle':'LLALLAGUA'},813:{'fecha_movimiento':'2012-07-18'},831:{'fecha_movimiento':'2013-05-27'},836:{'fecha_movimiento':'2013-11-04'},
        845:{'detalle':'VENTAS-CEDOAL'},7162:{'detalle':'Ingresa del depósito Materiales','area':None},7165:{'detalle':'Donación Caranavi'},
        7183:{'detalle':'Donac. Mi. Rela. Ext.'},7199:{'fecha_movimiento':'2010-11-16'},7200:{'detalle':'PARA VENTA CEDOAL'},7205:{'detalle':'LLALLAGUA'},7206:{'detalle':'LLALLAGUA'},7223:{'detalle':'VENTAS-CEDOAL'},
        12222:{'detalle':'Para el Cedoal'},12240:{'ingresos':0},12243:{'detalle':'PARA VENTA'},12246:{'detalle':'LLALLAGUA'},12247:{'detalle':'LLALLAGUA'},12251:{'area':'CEDOAL'},
        12258:{'detalle':'VENTAS-CEDOAL'},12260:{'detalle':'VENTAS-CEDOAL'},12264:{'detalle':'VENTAS-CEDOAL'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        800:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','La foto escribe 1-08-11, no 11-08-11; está después del 02-08-11. Literal y consulta técnica del antecedente conservadas.'),
        810:('2012-06-09','SECUENCIA_AJUSTADA','2012-06-06','6-6-12 después de 9-6-12; se conserva literal y consulta técnica del antecedente.'),
        811:('2012-06-09','SECUENCIA_AJUSTADA','2012-05-19','19-5-12 después de 9-6-12; literal y consulta técnica conservadas, sin cambiar año.'),
        825:('2013-03-06','SECUENCIA_AJUSTADA','2013-03-05','5-3-13 después de 6-3-13; literal conservada y consulta técnica.'),
        832:('2013-06-03','FOTO','2013-06-03','Después de recuperar 27-5-13 de la fila anterior, 3-6-13 conserva su fecha escrita.'),
        **{id:('2007-12-18','HIPOTESIS',None,'FECHA vacía; nota lateral 18/12/07 conservada como anotación, sin asignarla automáticamente a la celda. Consulta técnica de contexto, no fecha escrita confirmada.') for id in (7162,7163)},
        7207:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11. Se conserva literal y consulta técnica del antecedente.'),
        7213:('2012-07-30','SECUENCIA_AJUSTADA','2012-07-24','24-7-12 después del ingreso fechado 30-7-12; literal y consulta técnica conservadas.'),
        7217:('2013-10-02','HIPOTESIS',None,'El año de 2-10-1? está repasado; no se certifica la cifra oculta por secuencia. Consulta 2013-10-02 solo técnica, con lectura parcial conservada.'),
        7222:('2015-08-03','HIPOTESIS',None,'FIL 17 carece de fecha propia. Se conserva consulta técnica del antecedente, sin inventar fecha de 2017.'),
        12224:('2007-10-17','HIPOTESIS',None,'Devolución Potosí carece de fecha propia; anotación lateral 18/12/07 no se asigna automáticamente. Consulta técnica del antecedente.'),
        12248:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11; literal y consulta técnica del antecedente conservadas.'),
        12265:('2017-06-12','HIPOTESIS',None,'FIL carece de fecha propia; consulta técnica del antecedente, sin inventar día de 2017.'),
    }
    extras={
        800:{'motivo':'La fecha visible es 1-08-11; la salida 10 y el saldo 14 se conservan.'},
        813:{'motivo':'La foto escribe 18-7-12, no 19-7-12.'},
        814:{'criterios':['T16'],'motivo':'Ingreso 2 legible en columna INGRESOS. Saldo está repasado, 12/16 no inequívoco; no se elige el dígito por la suma. Cálculo 16 solo hipotético y lectura parcial conservada.', 'revision':{'saldo_documental_texto':'1?, repasado 12/16 no inequívoco.','candidatos_saldo_documental':[12,16]}},
        815:{'criterios':['T01'],'motivo':'La foto escribe SALIDA 5, no 1. Se recupera la columna visible y saldo escrito 11, sin usar la resta como única prueba.'},
        831:{'motivo':'La foto escribe 27-5-13, no 27-6-13.'},836:{'motivo':'La fecha es 4-11-13, no 14-11-13.'},
        7162:{'criterios':['T22','T23'],'motivo':'La frase Ingresa del depósito Materiales cruza DETALLE/ÁREA, con cantidades vacías y saldo 26. Base documental, sin recepción ficticia 26 ni nueva área Materiales.', 'revision':{'columnas_documentales':{'area':'Materiales'}}},
        7163:{'criterios':['T16'],'revision':{'anotacion_margen_fecha':'18/12/07 junto a devolución; no fecha de celda confirmada.'}},
        7164:{'criterios':['T16'],'motivo':'Texto personal no inequívoco se conserva sin asociarlo a otra identidad ni crear alias.'},
        7173:{'criterios':['T16'],'motivo':'Hay dos ingresos 1 en renglones distintos del mismo día, con saldos 47 y 48; no se deduplican por parecido.'},
        7199:{'motivo':'La foto escribe 16-11-10 y no 16-10-10.'},
        7200:{'criterios':['T14'],'motivo':'PARA VENTA corrige COLECCIÓN tachado solo en DETALLE. La fila y su salida 3 siguen activas; no se anula por una palabra tachada.'},
        7217:{'criterios':['T16'],'revision':{'fecha_documental_texto':'2-10-1?, año repasado no inequívoco.'}},
        12224:{'criterios':['T16'],'revision':{'anotacion_margen_fecha':'18/12/07 junto a devolución; no sustituye automáticamente la fecha vacía.'}},
        12240:{'criterios':['T16'],'motivo':'INGRESOS contiene cero numérico escrito y saldo 29 repetido; se conserva 0, distinto de una celda vacía o guion.'},
        12251:{'criterios':['T18'],'motivo':'Comillas inequívocas en ÁREA repiten CEDOAL, sin crear un área de comillas.'},
        12272:{'motivo':'La foto confirma ingreso 5 y saldo 6 con FECHA vacía. Se conserva íntegramente la revisión anterior y su fecha técnica 2023-01-01, sin convertirla en fecha escrita.'},
        12274:{'criterios':['T14'],'motivo':'Salida 2 visible sobre adhesivo y saldo vigente 2 legible a la derecha de otro adhesivo. No se afirma lectura de cifras cubiertas ni se anula la fila; se conserva la corrección visible.', 'revision':{'marcas_documentales':{'salidas':'Adhesivo con cifra nueva 2 legible.','saldo':'Adhesivo cubre parte izquierda; cifra nueva 2 legible a la derecha. No se certifica lo cubierto.'}}},
    }
    plan=construir_con_anclajes(version=50,instantanea=snapshot,anclajes=(12272,),hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],tipos={7162:'BASE_DOCUMENTAL'},
        bases={15:{'primera_fila':790,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 33, base anterior cero inferida sin recuento.'},
            115:{'primera_fila':7162,'saldo_base':26,'origen_saldo_base':'FOTO','motivo_base':'Base escrita 26 con cantidades vacías, sin ingreso ficticio.'},
            395:{'primera_fila':12222,'saldo_base':15,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primera salida 2 y saldo 13; base anterior 15 inferida, no recepción inventada.'}},
        observaciones=[
            {'articulo_id':15,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos completas y 56 filas cotejadas. Salida 5 extraída como 1 recuperada por columna visible. Saldo previo repasado 12/16 queda incierto, cálculo 16 solo hipotético, sin elegir por suma. Fechas 1-08-11, 18-7-12, 27-5-13 y 4-11-13 recuperadas; retrocesos conservados. Cierre 2 coincide.'},
            {'articulo_id':115,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos y 66 filas cotejadas. Base escrita 26 sin ingreso ficticio y Materiales sin nueva institución; nota lateral 18/12/07 no asignada automáticamente a fechas vacías. Palabra COLECCIÓN tachada no anula salida 3. Dos ingresos 1 del mismo día permanecen distintos. Fecha 16-11-10 recuperada; año repasado y FIL 17 sin fecha permanecen técnicos. Cierre 27 coincide.'},
            {'articulo_id':395,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos y 55 filas cotejadas, conservando íntegro el anclaje 12272 con ingreso 5/saldo 6 y fecha técnica sin certificación documental. Cero numérico en INGRESOS preservado, comillas en ÁREA resueltas por posición visible y FIL sin fecha identificado. Adhesivos conservados con correcciones visibles 2, sin afirmar lectura de lo cubierto. Base 15 inferida; cierre 3 coincide.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={15:2,115:27,395:3} and plan['cotejo']['discrepancias']==[],plan['cotejo']
    assert plan['cotejo']['nuevos_distintos']==176 and len(plan['cotejo']['anclajes_previos'])==1
    return plan

if __name__=='__main__':congelar(generar())
