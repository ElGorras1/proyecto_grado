"""Cotejo específico: fila fusionada recuperada sin perder tres decisiones anteriores."""
from copy import deepcopy
import hashlib,json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND,DERIVADOS
from scripts.generar_plan_revision_hil import CAMPOS_BASE,digest
from scripts.generar_continuacion_28 import recuperada
from app.db.session import SessionLocal
from app.services.clasificador_nodos import clasificar_movimiento,_resolver_area_con_catalogo

OTRAS=[
 (range(8813,8822),[15,-10,4,-3,-3,2,-2,-1,-1],[15,5,9,6,3,5,3,2,1]),
 (range(9038,9049),[15,-10,10,-5,10,5,-10,10,-2,-13,-2],[15,5,15,10,20,25,15,25,23,10,8]),
 (range(9771,9783),[0,-2,-1,2,-1,1,-2,0,0,0,0,0],[4,2,1,3,2,3,1,None,None,None,None,None]),
]
POETAS=[
 (range(705,730),[120,2,-1,-3,1,-1,-3,-1,-5,-5,-3,-1,-1,-1,-4,-5,-15,18,-1,-1,-1,-5,4,-1,-1],
  [120,122,121,119,120,None,115,114,109,104,101,100,99,98,94,89,74,92,91,90,89,84,88,87,86]),
 (range(730,756),[-5,-1,-3,3,-1,-10,-5,2,1,-1,-3,-1,-1,1,-1,-2,2,-10,7,-1,-1,-5,-1,-1,-2,-2],
  [81,80,77,80,79,69,64,66,67,66,63,62,61,62,61,59,61,51,58,57,56,51,50,49,47,45]),
 (range(756,782),[1,-5,-5,-10,6,5,-5,-2,-1,-2,-1,1,1,-1,-3,3,-5,-1,4,-5,-3,-1,2,-2,2,-3],
  [46,41,36,26,32,37,32,30,29,27,26,27,28,27,24,27,22,21,25,20,17,16,18,16,18,15]),
 (range(782,790),[-2,-2,1,3,-2,-9,-2,-1],[13,11,12,15,13,4,2,1]),
]

def generar():
    raiz='backups/continuacion_hil_57_20261016/'
    comunes=json.loads((BACKEND/(raiz+'articulos_195_209_255_antes.json')).read_text(encoding='utf-8'))
    cc={r['id']:{'area':'CEDOAL'} for r in comunes if r['area'] in ('CEDOOC','CEDOC')}
    for id,fields in {8813:{'referencia':'CBB','area':None},8820:{'detalle':'VENTA CEDOAL'},9038:{'referencia':'SC','area':None},9046:{'detalle':'VENTAS-CEDOAL'},9047:{'area':'ADM'},9048:{'detalle':'FIL LP'},9775:{'detalle':'Cedoal Feria'},9777:{'detalle':'Cedoal Paraguay'}}.items():cc.setdefault(id,{}).update(fields)
    for id in range(9778,9783):cc.setdefault(id,{})['estado']='NOTA_DOCUMENTAL'
    tech={id:('2005-08-17','HIPOTESIS',None,'Fila sin fecha propia; consulta técnica del antecedente 17-8-05, no fecha documental. Nota marginal 19-12-07 no se asigna automáticamente.') for id in range(9773,9782)}
    extra={
        8813:{'criterios':['T23'],'revision':{'columnas_documentales':{'area':'CBB'}}},9038:{'criterios':['T23'],'revision':{'columnas_documentales':{'area':'SC'}}},
        9048:{'criterios':['T02'],'motivo':'La cifra 2 está en SALIDAS y reduce 10 a 8; se corrige el ingreso OCR, sin inferir por el nombre FIL.'},
        9771:{'criterios':['T22'],'revision':{'tipo_fila':'BASE_DOCUMENTAL'}},
        **{id:{'criterios':['T16','T23'],'motivo':'Cifra en REF de cuadro Saldo inicial/Donación/Venta/Saldo, con cantidades vacías. Se conserva como nota sin efecto acreditado, sin extender T13 confirmado para otro cuadro.', 'revision':{'tipo_fila':'NOTA_DOCUMENTAL','origen_cantidades':'HIPOTESIS','interpretacion_cuadro_pendiente':True,'columnas_documentales':{'referencia':valor}}} for id,valor in ((9778,4),(9779,2),(9780,1),(9781,1))},
        9782:{'criterios':['T16','T23'],'motivo':'Renglón saldo del 16-12-09 no tiene cantidad ni cifra legible en SALDO; se conserva nota sin efecto, no recuento ni saldo 1 confirmado.', 'revision':{'tipo_fila':'NOTA_DOCUMENTAL','origen_cantidades':'HIPOTESIS'}},
    }
    plan=construir(version=57,instantanea=raiz+'articulos_195_209_255_antes.json',hojas=OTRAS,correcciones=cc,tecnicas=tech,grupos_fechas=[],
        bases={195:{'primera_fila':8813,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 15; base previa cero inferida.'},209:{'primera_fila':9038,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 15; base previa cero inferida.'},255:{'primera_fila':9771,'saldo_base':4,'origen_saldo_base':'FOTO','motivo_base':'Base escrita 4 con cantidades vacías; sin ingreso ficticio.'}},
        observaciones=[{'articulo_id':195,'observado':True,'excluir_entrenamiento':False,'motivo':'Foto completa y nueve filas cotejadas. CEDOAL y procedencia CBB conservados sin alias. Cierre 1 coincide.'},
            {'articulo_id':209,'observado':True,'excluir_entrenamiento':False,'motivo':'Foto completa y once filas cotejadas. Última salida 2 corregida desde ingreso OCR; ADM y procedencia SC recuperados por columna. Devolución salida 13 se conserva por columna, no por nombre. Cierre 8 coincide.'},
            {'articulo_id':255,'observado':True,'excluir_entrenamiento':True,'motivo':'Foto completa y doce filas cotejadas. Base escrita 4 sin ingreso, fechas vacías y nota marginal conservadas. Cuatro notas con cifras en REF y renglón saldo sin cifra se mantienen sin efecto acreditado; no se extiende T13 de otro cuadro. Cierre último activo escrito 1 coincide condicionalmente; artículo excluido sin atribuir bloqueo automático solo por exclusión.'}],extras=extra)
    assert plan['cotejo']['discrepancias']==[]
    rows={r['id']:r for r in json.loads((BACKEND/(raiz+'poetas14_antes.json')).read_text(encoding='utf-8'))}
    assert {id for id,r in rows.items() if r['revision_documental']}=={733,746,747}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area']=='Cedoal'}
    for id,fields in {705:{'detalle':'Ingresa del depósito Material','referencia':None,'area':None},710:{'detalle':'Donación CONAMAQ'},718:{'detalle':'C. Interyungueño'},724:{'detalle':'Dona. Min. Rela. Ext.'},731:{'detalle':'C/carta P/TARIJA'},745:{'detalle':'LLALLAGUA'},746:{'detalle':'LLALLAGUA'},757:{'detalle':'FIL'},758:{'detalle':'FIL'},759:{'detalle':'FIL'},760:{'detalle':'FIL'},767:{'detalle':'LETRAS PACEÑAS'},775:{'detalle':'FIL'},776:{'detalle':'FIL'},778:{'detalle':'FIL'},780:{'detalle':'ESCAPARATE','referencia':'DEVOLUCION'},781:{'detalle':'FIL STA. CRUZ'}}.items():cambios.setdefault(id,{}).update(fields)
    for id in range(711,730):cambios.setdefault(id,{})['orden_fila']=rows[id]['orden_fila']+1
    fechas={705:('2008-01-01','HIPOTESIS',None,'FECHA vacía; consulta técnica existente conservada, sin certificar enero ni asignar nota marginal 14-12-07.'),706:('2008-01-01','HIPOTESIS',None,'Devoluciones sin fecha propia; consulta técnica existente, sin asignar automáticamente nota marginal.'),
        708:('2008-08-12','HIPOTESIS',None,'Fecha 12-08-0? con año final repasado 05/08 no inequívoco; consulta técnica existente conservada, no año certificado.'),
        710:('2008-08-17','SECUENCIA_AJUSTADA','2008-05-19','19-5-08 de Donación CONAMAQ aparece después de 17-08-08; literal y consulta técnica conservadas.'),
        **{id:('2008-08-17','SECUENCIA_AJUSTADA',literal,'Fecha escrita retrocede después del 17-08-08; literal y orden físico conservados, consulta técnica del antecedente.') for id,literal in ((711,'2008-05-29'),(712,'2008-07-03'),(713,'2008-07-15'),(714,'2008-08-14'))},
        767:('2013-03-06','SECUENCIA_AJUSTADA','2013-03-05','La foto escribe 5-3-13, no 8-3-13; aparece después del 6-3-13. Literal y consulta técnica conservadas.')}
    assert not set(fechas)&{733,746,747}
    acumulado=papel=0;entries=[];diferencias=[];protegidos={};metas=[];fotos=set()
    with SessionLocal() as db:
        for ids,qs,bs in POETAS:
            for id,q,escrito in zip(ids,qs,bs):
                r=rows[id];previa=deepcopy(r['revision_documental'] or {});acumulado+=q
                delta=0 if escrito is None else escrito-(papel+q);papel=papel+q if escrito is None else escrito
                if delta:diferencias.append({'id':id,'local':delta,'acumulada':escrito-acumulado})
                campos={'ingresos':q if q>0 else None,'salidas':-q if q<0 else None,'saldo_registrado':acumulado,**cambios.get(id,{})}
                rev={'criterios':['T01'],'motivo':'Hoja completa cotejada con vecinos; fuente y extracción inicial conservadas.','hallazgos':['HOJA_COMPLETA_COTEJADA'],'tipo_fila':'MOVIMIENTO','saldo_documental':escrito,'origen_saldo':'HIPOTESIS' if escrito is None else ('FOTO' if escrito==acumulado else 'RECONSTRUIDO'),'origen_fecha':'FOTO','fecha_documental':r['fecha_movimiento'],'usar_saldo_esperado':True,'reconstruir_cadena':True,'cotejo_pagina_completa':True}
                if id==705:rev.update(saldo_base=0,origen_saldo_base='HIPOTESIS',motivo_base='Ingreso y saldo 120 escritos; base anterior cero inferida.',columnas_documentales={'detalle':'Ingresa del','referencia':'depósito','area':'Material'})
                if id==706:rev['anotacion_margen_fecha']='14-12-07 fuera de la celda, no atribuida automáticamente.'
                if id==707:campos.update(area_estado='PENDIENTE_HIL',requiere_auditoria_nodo=True);rev['criterios'].append('T16')
                if id==708:rev.update(fecha_documental_texto='12-08-0?, año final repasado 05/08 no inequívoco.',candidatos_fecha_documental=['2005-08-12','2008-08-12']);rev['motivo']+=' Salida 3 desde 121 escribe 119 frente a cálculo 118: diferencia +1 del papel conservada, sin cambiar 3 a 2.'
                if id==710:rev['motivo']+=' Dos donaciones distintas CONAMAQ y UPEA se habían fusionado. Esta fila conserva CONAMAQ, salida 1 y SALDO vacío; UPEA se recupera aparte, sin duplicar un artículo.'
                if delta:rev.update(diferencia_local_papel=delta);rev['criterios'].append('T05');rev['hallazgos'].append('DESCUADRE_DEL_PAPEL_CONSERVADO')
                if escrito is None:rev['criterios'].append('T08')
                if id in fechas:
                    nueva,origen,literal,motivo=fechas[id];campos['fecha_movimiento']=nueva;rev.update(origen_fecha=origen,fecha_documental=literal,motivo_fecha=motivo);rev['criterios'].append('T09' if origen=='HIPOTESIS' else 'T11')
                if any(campos.get(k,r[k])!=r[k] for k in ('detalle','referencia','area','ingresos','salidas')):
                    clas=clasificar_movimiento(campos.get('detalle',r['detalle']),campos.get('referencia',r['referencia']),campos.get('area',r['area']),campos['ingresos'],campos['salidas'],db);campos.update({k:getattr(clas,k) for k in DERIVADOS})
                    if q>0 and campos['nodo_grafo'].startswith('Salida:'):
                        area=campos.get('area',r['area']);n,e,p=(_resolver_area_con_catalogo(area,db) if area else ('Origen no especificado','SIN_AREA_REGISTRADA',False))
                        campos.update(nodo_grafo=n,area_estado=e,requiere_auditoria_nodo=p)
                if id==707:campos.update(area_estado='PENDIENTE_HIL',requiere_auditoria_nodo=True)
                if previa:
                    # Plan específico: el saldo vigente aprobado se protege, el cálculo independiente revela +1 previo.
                    campos['saldo_registrado']=r['saldo_registrado'];rev.update(previa)
                    rev.update(revision_previa_rectificacion_documental=deepcopy(previa),usar_saldo_esperado=False,reconstruir_cadena=True,cotejo_pagina_completa=True)
                    rev['saldo_documental']=escrito;rev['origen_saldo']='FOTO';rev['diferencia_saldo_documental']=escrito-acumulado
                    rev['criterios']=sorted(set(previa['criterios']+['T05']));rev['hallazgos']=sorted(set(previa.get('hallazgos',[])+['HOJA_COMPLETA_COTEJADA','DESCUADRE_DEL_PAPEL_CONSERVADO']))
                    rev['motivo']=previa['motivo']+' Se amplía cotejo completo y se conserva íntegra esta decisión. La salida 1 UPEA omitida y diferencia +1 anterior dejan acumulado independiente una unidad menor; no se altera cantidad, fecha ni saldo vigente aprobado.'
                    protegidos[str(id)]={'valores':{k:r[k] for k in ('ingresos','salidas','saldo_registrado','fecha_movimiento','estado','orden_fila','orden_pagina_validado')},'revision':deepcopy(previa),'metadatos_rectificables':['diferencia_saldo_documental']}
                    metas.append({'id':id,'metadatos':{'diferencia_saldo_documental':1,'usar_saldo_esperado':False}})
                if id==789:campos['saldo_registrado']=1;rev.update(usar_saldo_esperado=False,origen_saldo='FOTO')
                foto=(BACKEND/r['ruta_imagen_respaldo']).resolve();fotos.add(str(foto))
                entries.append({'id':id,'articulo_id':14,'pagina':f'L{r["lote_id"]:04d}-P{r["numero_pagina"]:02d}','esperado':{k:r[k] for k in CAMPOS_BASE},'esperado_adicional':{**{k:r[k] for k in DERIVADOS},**({'revision_documental':deepcopy(previa)} if previa else {})},'cambios':campos,'revision':rev,'fuente':str(foto),'sha256_imagen':hashlib.sha256(foto.read_bytes()).hexdigest()})
                if id==710:acumulado-=1;papel-=1  # La segunda donación realmente escrita, insertada abajo.
    assert acumulado==0 and papel==1 and diferencias==[{'id':708,'local':1,'acumulada':1}],(acumulado,papel,diferencias)
    upea=recuperada(rows,710,rows[710]['orden_fila']+1,clave='art14-upea-separada-despues710-v1',detalle='Donación UPEA',fecha='2008-08-17',saldo=117,tipo='MOVIMIENTO',motivo='Renglón UPEA con salida 1 y saldo 118, físicamente distinto de CONAMAQ anterior con salida 1 y saldo vacío. OCR había fusionado ambos. Se recupera una sola salida; fecha propia ausente, consulta técnica del contexto. Cálculo 117 conserva diferencia +1 previa del papel.')
    upea['campos'].update(estado='ACTIVO',salidas=1,fecha_estado='ESTIMADA_HIL')
    upea['campos']['datos_originales'].update(detalle='UPEA',salidas=1,saldo_registrado=118)
    upea['revision'].update(tipo_fila='MOVIMIENTO',criterios=['T04','T05','T09','T23'],saldo_documental=118,origen_saldo='RECONSTRUIDO',origen_cantidades='FOTO',usar_saldo_esperado=True)
    plan['revisiones']=entries+plan['revisiones'];plan['recuperaciones']=[upea]
    plan['observaciones_articulos'].insert(0,{'articulo_id':14,'observado':True,'excluir_entrenamiento':True,'motivo':'Cuatro fotos y 85 filas previas cotejadas, más donación UPEA salida 1 fusionada con CONAMAQ recuperada. Salida 3 desde 121 escribe 119, diferencia +1 persistente hasta cierre escrito 1 frente a cálculo 0. Se conservan cantidades, fechas técnicas y saldos vigentes aprobados de 733/746/747 y sus revisiones íntegras; su cálculo independiente muestra la diferencia anterior. No se cambia salida 3 a 2 ni se inventa ingreso compensatorio. Cierre bloqueado y artículo excluido. Fechas iniciales vacías, año repasado y fechas fuera de orden permanecen identificados.'})
    plan['cotejo'].update(fotografias=7,movimientos=118,nuevos_distintos=115,cierres={14:1,195:1,209:8,255:1},cierres_calculados={14:0,195:1,209:8,255:1},cierres_documentales={14:1,195:1,209:8,255:1},discrepancias=diferencias,rectificaciones_previas=protegidos,rectificaciones_documentales=metas,
        pendientes_documentales={733:['saldo'],746:['saldo','fecha'],747:['saldo','fecha'],789:['saldo']},limites_cierre={14:'Cierre escrito 1 frente a cálculo 0. Salida 3 desde 121 escribe 119 y donación UPEA omitida recuperada; se conserva diferencia +1 sin alterar las tres decisiones previas. Apertura bloqueada y artículo excluido del entrenamiento.',255:'Cierre último activo escrito 1 coincide condicionalmente. Cuadro con cifras en REF pendiente, sin extender T13 ni inventar ingresos. Artículo excluido del entrenamiento, sin afirmar bloqueo automático por exclusión.'})
    plan['limites'].append('Plan específico que protege cantidades, fechas y saldos vigentes de tres decisiones anteriores; su revisión íntegra se conserva, y solo se actualiza la diferencia documental derivada del nuevo contexto físico.')
    return plan

if __name__=='__main__':congelar(generar())
