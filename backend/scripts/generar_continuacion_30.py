"""Ocho fotos completas de artículos con avisos: Homenaje, Pienso y Pariti."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(1700,1726),[37,-1,-5,5,-5,-1,-1,-4,-1,5,-1,-1,-1,1,-1,2,-1,-1,-3,3,-5,-1,4,-1,-1,-1],
  [37,36,31,36,31,30,29,25,24,29,28,27,26,27,26,28,27,26,23,26,21,20,24,23,22,21]),
 (range(1726,1748),[-5,4,-1,1,-2,2,-2,-3,-2,-2,2,-1,3,-1,-1,-3,-1,-2,-4,2,1,-2],
  [16,20,19,20,18,20,18,15,13,11,13,12,15,14,13,10,9,7,3,5,6,4]),
 (range(3805,3831),[315,-5,-6,-1,-11,-1,-2,-1,-2,-6,-2,-1,-1,-5,-1,-1,-3,-4,-2,-2,-4,-1,-1,-2,-2,-2],
  [315,310,304,303,292,291,289,288,286,280,278,277,276,271,270,269,266,262,260,258,254,253,252,250,248,246]),
 (range(3831,3857),[-15,-2,-4,-2,-4,-1,-1,-2,-1,-2,-1,-7,-2,-1,-1,-2,-5,500,-50,-364,14,-11,-3,-5,-6,-1],
  [231,229,225,223,219,218,217,215,214,212,211,204,202,201,200,198,193,693,643,273,287,276,273,268,262,261]),
 (range(3857,3878),[-4,-2,-1,-2,-2,-2,-1,2,-2,-3,-2,-3,-1,-2,-2,-4,2,-2,-1,1,-2],
  [257,255,254,252,250,248,247,249,247,244,242,239,238,236,234,230,232,230,229,230,228]),
 (range(7909,7935),[106,194,-10,4,-3,-7,-5,-1,-1,-2,-1,-1,-1,-1,1,-1,-5,-5,-3,-5,8,0,-2,-1,-1,-1],
  [106,300,290,294,291,284,279,278,277,275,274,273,272,271,272,271,266,261,258,253,261,260,258,257,256,255]),
 (range(7935,7961),[-8,-2,-5,-5,-10,-5,15,-3,2,-3,-5,-3,3,-1,-5,-5,-10,6,-1,-1,-1,1,-1,-2,2,-10],
  [247,245,240,235,225,220,235,232,234,231,226,223,226,225,220,215,205,211,210,209,208,209,208,206,208,198]),
 (range(7961,7984),[10,-1,-2,-5,1,-1,-10,5,-2,-5,-9,-7,-2,-2,-3,-6,-3,-2,-2,-3,3,-4,-1],
  [208,207,205,200,201,200,190,195,193,188,179,172,170,168,165,159,156,154,152,149,152,148,147]),
]

def generar():
    snapshot='backups/continuacion_hil_30_20261015/articulos_44_68_147_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    for id,r in rows.items():
        if r['area'] in ('CEDOCAL','DOCAL','CEDOC','CEDOCL','Cedoal'):
            cambios[id]={'area':'CEDOAL'};extras[id]={'motivo':'La celda se lee CEDOAL en la foto; se recupera lectura sin crear áreas ni alias.'}
    for id,fields in {
        1710:{'detalle':'LETRAS PACEÑAS'},1711:{'detalle':'VENTA CEDOAL'},1713:{'detalle':'LETRAS PACEÑAS','fecha_movimiento':'2013-03-05'},
        1717:{'fecha_movimiento':'2013-06-10'},1723:{'detalle':'DAVID MONDACA'},1730:{'detalle':'VENTAS CEDOAL'},1732:{'detalle':'VENTAS CEDOAL'},
        1741:{'fecha_movimiento':'2016-01-01','detalle':'LOS AMIGOS LIBRO - CBBA','referencia':'CONSIG.','area':None},
        3828:{'detalle':'Bibli - CASAS DIST'},3829:{'detalle':'VENTAS PERSONAL ESIP'},3838:{'area':None},
        3848:{'area':None},3850:{'detalle':'Solicitud libros'},3869:{'detalle':'FILEJA'},
        7912:{'detalle':'Devolución Feria','area':None},7930:{'referencia':'CARTA'},
        7942:{'referencia':'VENTAS'},7944:{'referencia':'VENTAS'},7946:{'referencia':'VENTAS'},7953:{'referencia':'OBSEQUIO'},
        7961:{'area':None},7974:{'detalle':'VENTAS CEDOAL'},7978:{'area':None},7981:{'area':None},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        1718:('2013-06-10','SECUENCIA_AJUSTADA','2013-05-07','7-5-13 está después de EXPO RAUL LARA 10-6-13. Se conserva literal y consulta técnica del antecedente, sin cambiar el mes de EXPO.'),
        1719:('2013-06-10','SECUENCIA_AJUSTADA','2013-05-14','14-5-13 después de la exposición 10-6-13; literal conservada y consulta técnica del antecedente.'),
        1720:('2013-06-10','SECUENCIA_AJUSTADA','2013-05-27','27-5-13 después de la exposición 10-6-13; literal conservada y consulta técnica del antecedente.'),
        1721:('2013-06-10','SECUENCIA_AJUSTADA','2013-06-03','3-6-13 después de la exposición 10-6-13; literal conservada y consulta técnica del antecedente.'),
        1723:('2013-07-11','HIPOTESIS',None,'David Mondaca no tiene fecha propia; consulta técnica del antecedente, no fecha documental.'),
        1732:('2014-04-29','SECUENCIA_AJUSTADA','2014-04-08','8-4-14 está después del 29-4-14; se conserva literal y consulta técnica del antecedente.'),
        1743:('2017-07-06','HIPOTESIS',None,'FIL tiene fecha en blanco; consulta técnica del antecedente.'),
        3823:('2016-09-19','SECUENCIA_AJUSTADA','2016-07-02','2-7-16 está después de 19-9-16. Se conserva fecha escrita y consulta técnica del antecedente.'),
        3831:('2017-05-10','HIPOTESIS','2010-05-10','El papel escribe 10-5-10 después de abril de 2017. El 2017 solo se propone como consulta de contexto; el año 10 del papel no se oculta ni se certifica corregido.'),
        3835:('2017-07-06','HIPOTESIS',None,'FIL tiene fecha en blanco; consulta técnica del antecedente.'),
        3864:('2022-10-17','HIPOTESIS',None,'Devolución no tiene fecha propia; consulta técnica del antecedente.'),
        7910:('2007-07-11','HIPOTESIS',None,'Segunda recepción 194 sin fecha propia; consulta técnica de la primera recepción, no fecha escrita confirmada.'),
        7911:('2007-07-11','HIPOTESIS',None,'Feria del Libro sin fecha propia; consulta técnica del antecedente.'),
        7921:('2008-05-19','HIPOTESIS',None,'UPEA repite Donación en DETALLE pero no tiene fecha propia; consulta técnica del antecedente.'),
        7922:('2008-05-19','HIPOTESIS',None,'U. Indígena repite Donación en DETALLE pero no tiene fecha propia; consulta técnica del antecedente.'),
        7923:('2008-05-19','SECUENCIA_AJUSTADA','2008-03-11','11-3-08 está después del 19-5-08; se conserva literal y consulta técnica del antecedente.'),
        7930:('2008-08-26','SECUENCIA_AJUSTADA','2008-07-01','Recuento físico según carta lleva 01-07-08 después de 26-08-08. Se conserva fecha literal y consulta técnica; no se inventa fecha de conteo actual.'),
        7960:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 después de 02-08-11; consulta técnica del antecedente y literal conservada.'),
        7975:('2017-06-12','HIPOTESIS',None,'FIL 17 sin fecha propia; consulta técnica del antecedente, sin atribuirle una fecha de otro artículo.'),
    }
    extras.update({
        1707:{'motivo':'Los dos DOSSIER del 14-11-12 son filas distintas con salidas 1 y 4 y saldos 29 y 25. Se conservan ambas sin deduplicación.'},
        1717:{'motivo':'La foto escribe 10-6-13 para Expo Raúl Lara, no mayo. Se corrige el mes y se identifican las fechas de mayo que aparecen después.'},
        1741:{'criterios':['T23'],'motivo':'CBA está en REF y CONSIG en ÁREA; se normaliza consignación como referencia y CBBA en detalle, conservando columnas literales sin crear área Consignación.', 'revision':{'columnas_documentales':{'referencia':'CBA','area':'CONSIG'}}},
        3838:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'En ÁREA hay una marca C aislada, no institución completa ni comillas claras. Se conserva la marca pendiente, sin crear área C ni equivalencia automática.', 'revision':{'marca_area_documental':'C / trazo aislado.'}},
        3848:{'criterios':['T23'],'motivo':'INGRESO 500 y saldo 693 están legibles; ÁREA está vacía, no SOD. No se reduce la cantidad por magnitud.'},
        3850:{'criterios':['T05'],'motivo':'Solicitud libros tiene salida 364 legible y saldo escrito 273 desde 643. El cálculo es 279; la diferencia -6 persiste. Se conserva 364 sin aumentarla a 370 para cuadrar.'},
        7912:{'criterios':['T23'],'motivo':'FERIA está en ÁREA y describe la devolución; se conserva en detalle y columna literal, sin crear área Feria.', 'revision':{'columnas_documentales':{'area':'FERIA'}}},
        7921:{'criterios':['T18'],'motivo':'Comillas en DETALLE repiten Donación; no completan una FECHA vacía.'},
        7922:{'criterios':['T18'],'motivo':'Comillas en DETALLE repiten Donación; no completan una FECHA vacía.'},
        7930:{'criterios':['T15'],'motivo':'La fila escribe Recuento físico según carta y saldo 260 después de 261. Se toma la base documental 260 conservando diferencia -1, sin salida ficticia ni conteo nuevo.', 'revision':{'tipo_fila':'RECUENTO','usar_saldo_esperado':False}},
        7935:{'motivo':'DIRECCIÓN se extiende de ÁREA hacia la columna vecina, sin cantidad de ingreso adicional. Se conserva salida 8 y su texto.', 'revision':{'columnas_documentales_texto':'DIRECCION cruza el borde de AREA/INGRESOS.'}},
        7936:{'motivo':'DIRECCIÓN se extiende de ÁREA hacia la columna vecina, sin cantidad de ingreso adicional. Se conserva salida 2 y su texto.', 'revision':{'columnas_documentales_texto':'DIRECCION cruza el borde de AREA/INGRESOS.'}},
        7961:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'La pequeña marca vertical de ÁREA no acredita un área llamada 1 ni repetición inequívoca. Se conserva como marca pendiente.', 'revision':{'marca_area_documental':'Trazo vertical pequeño.'}},
        7978:{'criterios':['T14'],'motivo':'ADM tiene salida 2 y saldo 154; marca tachada anterior en INGRESOS sin segunda cantidad legible. Se conserva una sola salida y el tachón, sin área R.', 'revision':{'marcas_documentales':{'ingresos':'Marca anterior tachada; no es una entrada adicional.'}}},
        7981:{'criterios':['T23'],'motivo':'El 3 está en INGRESOS, no ÁREA. Se conserva una sola entrada 3 sin área numérica.'},
    })
    plan=construir(version=30,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(1700,1701),(1712,1713)],
        bases={44:{'primera_fila':1700,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 37: base cero inferida, sin recuento anterior acreditado.'},
            68:{'primera_fila':3805,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 315: base cero inferida, sin recuento anterior acreditado.'},
            147:{'primera_fila':7909,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 106: base cero inferida, sin recuento anterior acreditado.'}},
        observaciones=[
            {'articulo_id':44,'observado':True,'excluir_entrenamiento':False,'motivo':'Dos fotos completas y 48 filas cotejadas. Dos salidas Dossier del mismo día se conservan distintas; Expo Raúl Lara es 10-6-13 y fechas posteriores fuera de orden conservan literal y consulta técnica. Consignación en columna de área normalizada con evidencia y FIL sin fecha identificado. Cierre 4 coincide.'},
            {'articulo_id':68,'observado':True,'excluir_entrenamiento':True,'motivo':'Tres fotos y 73 filas cotejadas. Ingreso 500 y salida 364 legibles conservados; 643 menos 364 corresponde a 279 pero el papel escribe 273. Diferencia -6 persistente: cierre escrito 228 frente a acumulado condicional 234. Se bloquea apertura y excluye artículo del entrenamiento, sin cambiar 364 a 370. Fecha 10-5-10 conserva literal y 2017 es solo hipótesis; marca C de área y fechas ausentes mantienen incertidumbre.'},
            {'articulo_id':147,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos y 75 filas cotejadas. Recuento físico según carta escrito 260 después de 261 se conserva como nueva base documental con diferencia -1, sin movimiento compensatorio ni conteo actual. Fechas ausentes y fuera de orden, trazos de área, tachón de ADM y entrada 3 se distinguen. Cierre 147 coincide siguiendo el recuento.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={44:4,68:234,147:148},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':3850,'local':-6,'acumulada':-6},{'id':7930,'local':-1,'acumulada':-1}],plan['cotejo']
    for e in plan['revisiones']:
        if e['articulo_id']==147 and e['id']>=7930:
            e['cambios']['saldo_registrado']-=1;rev=e['revision'];escrito=rev['saldo_documental'];calc=e['cambios']['saldo_registrado']
            rev['origen_saldo']='HIPOTESIS' if escrito is None else ('FOTO' if escrito==calc else 'RECONSTRUIDO')
            if e['id']==7930:
                rev.pop('diferencia_local_papel',None);rev['hallazgos']=[h for h in rev['hallazgos'] if h!='DESCUADRE_DEL_PAPEL_CONSERVADO']
        if e['articulo_id']==68 and e['id']>=3850:e['revision']['origen_saldo']='HIPOTESIS'
        if e['id']==3877:e['cambios']['saldo_registrado']=228;e['revision'].update(usar_saldo_esperado=False,origen_saldo='FOTO')
    plan['cotejo'].update(cierres={44:4,68:228,147:147},cierres_calculados={44:4,68:234,147:147},
        discrepancias=[{'id':3850,'local':-6,'acumulada':-6}],pendientes_documentales={3877:['saldo']},
        recuentos_documentales=[{'id':7930,'previo':261,'escrito':260,'diferencia':-1}],
        limites_cierre={68:'La salida 364 escrita deja cálculo 279 desde 643, mientras el papel indica 273. Cierre escrito 228 frente a cálculo 234; artículo excluido del entrenamiento y apertura bloqueada, sin aumentar la salida para cuadrar.'})
    return plan

if __name__=='__main__':congelar(generar())
