"""Cotejo de siete fotos: agrupación aprobada y cantidades pendientes conservadas."""
from copy import deepcopy
import hashlib,json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND,DERIVADOS
from scripts.generar_plan_revision_hil import CAMPOS_BASE
from app.db.session import SessionLocal
from app.services.clasificador_nodos import clasificar_movimiento,_resolver_area_con_catalogo

MUJERES=[
 (range(4084,4110),[-1,-1,-1,-1,-3,-8,-2,-5,-5,10,-1,-1,-1,-5,-1,-1,-1,-1,5,-3,-1,-3,-1,2,-1,-10],[71,70,69,68,65,57,55,50,45,55,54,53,52,47,46,45,44,43,48,45,44,41,40,42,41,31]),
 (range(4110,4136),[7,-3,1,-1,-1,-3,-1,-1,-6,-1,1,-1,-2,1,-10,9,-1,-1,-5,-1,3,-10,0,6,-2,1],[38,35,36,35,34,31,30,29,23,22,23,22,20,21,11,20,19,18,13,12,15,5,None,11,9,10]),
 (range(4136,4155),[-5,-3,5,-5,2,-1,-1,8,-3,-2,-3,1,3,-2,1,-2,-1,-1,2],[5,2,7,2,4,3,2,10,7,5,2,3,6,4,5,3,2,1,3]),
]
INDICE=[
 (range(534,560),[86,-5,-3,-5,3,-1,-5,-10,5,-3,-1,-3,-1,-1,-1,1,-1,-2,2,-10,10,-1,-1,-3,-1,1],[86,81,78,73,76,75,70,60,65,62,61,58,57,56,55,56,55,53,55,45,55,54,53,50,49,50]),
 ([560],[1],[1]),
 (range(561,587),[2,-10,-1,10,-2,1,-5,4,-5,-1,-1,1,-1,1,-3,3,-5,5,-5,-1,5,-3,-2,-2,2,3],[52,42,41,51,49,50,45,49,44,43,42,43,42,43,40,43,38,43,38,37,42,39,37,35,37,40]),
 (range(587,590),[-1,-1,2],[39,38,40]),
]

def generar():
    raiz='backups/continuacion_hil_65_20261016/'
    todas=json.loads((BACKEND/(raiz+'articulos_10_74_antes.json')).read_text(encoding='utf-8'))
    mujeres={r['id']:r for r in todas if r['articulo_id']==74}
    cambios={id:{'area':'CEDOAL'} for id,r in mujeres.items() if r['area'] in ('Cedoal','CEDOCAL')}
    for id,fields in {
        4104:{'referencia':'CBA'},4106:{'detalle':'C/carta Obsq.','referencia':'Tocaña'},4113:{'detalle':'ANDINO-AMAZONICO MESOAMERICANO'},4121:{'detalle':'QUIME'},4122:{'detalle':'LLALLAGUA'},4123:{'detalle':'LLALLAGUA'},4126:{'detalle':'YATI KAMA'},4132:{'estado':'NOTA_DOCUMENTAL'},
    }.items():cambios.setdefault(id,{}).update(fields)
    extras={
        4104:{'criterios':['T23'],'motivo':'CBA está en REF, conservada literalmente sin crear alias ni asignar una ciudad.'},
        4106:{'criterios':['T23'],'motivo':'Tocaña está en REF, no en ÁREA; se recupera la columna visible sin alias.', 'revision':{'columnas_documentales':{'referencia':'Tocaña'}}},
        4113:{'criterios':['T23'],'motivo':'Se recupera AMAZONICO del detalle escrito, no AMONICO; sin inferir identidad institucional.'},
        4128:{'criterios':['T16'],'motivo':'Trazo aislado parecido a r en REF se conserva sin expandirlo como comillas por semejanza.', 'revision':{'referencia_documental_ambigua':True,'referencia_documental_texto':'Trazo aislado en REF, parecido a r; no equivale inequívocamente a ditto.'}},
        4132:{'criterios':['T16','T23'],'motivo':'UCB Carmen Pampa lleva fecha, detalle y área entre paréntesis, anotaciones NO a los costados y asteriscos/cruces en SALIDAS y SALDO sin cifra acreditada. Se conserva como nota sin efecto cuantificado, no saldo escrito 5 ni salida ficticia ni anulación de toda la hoja.', 'revision':{'tipo_fila':'NOTA_DOCUMENTAL','origen_cantidades':'HIPOTESIS','efecto_cuantitativo_no_acreditado':True,'marcas_documentales':{'fecha':'(6-6-12)','detalle':'(UCB. CARMEN PAMPA)','referencia':'(DONACION)','area':'(CEDOAL)','salidas':'asterisco/cruz sin cifra','saldo':'asterisco/cruz sin cifra','margen':'NO a ambos lados'}}},
        4134:{'criterios':['T14'],'motivo':'Texto anterior en REF está tachado, pero salida 2 y saldo 9 legibles siguen activos; no se invierte por el detalle de feria.'},
        4154:{'criterios':['T14','T16'],'motivo':'Ingreso 2 y saldo 3 legibles; en SALIDAS hay una marca ennegrecida parecida a 1 atravesada por trazos, sin cancelación ni cifra vigente inequívocas. Se conserva la interpretación previa sin salida cuantificada solo como hipótesis; no se decide por la suma.', 'revision':{'origen_cantidades':'HIPOTESIS','ambito_marca_salidas_pendiente':True,'marcas_documentales':{'salidas':'Marca ennegrecida parecida a 1 atravesada por trazos; cifra vigente no inequívoca.'},'candidatos_salidas_documentales':[None,1]}},
    }
    plan=construir(version=65,instantanea=raiz+'articulo_74_antes.json',hojas=MUJERES,correcciones=cambios,
        tecnicas={4124:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 sigue al 02-08-11; literal, orden físico y consulta técnica del antecedente conservados.')},grupos_fechas=[],
        bases={74:{'primera_fila':4084,'saldo_base':72,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primera salida 1 y saldo 71 escritos permiten inferir 72 previo, sin inventar ingreso.'}},
        observaciones=[{'articulo_id':74,'observado':True,'excluir_entrenamiento':True,'motivo':'Tres fotos completas y 71 filas cotejadas. Base previa 72 inferida, sin ingreso ficticio. UCB Carmen Pampa entre paréntesis, anotaciones NO y cantidades/saldo con cruces se conserva como nota sin efecto cuantificado, no como saldo escrito 5. Último ingreso 2/saldo 3 conserva marca de SALIDAS pendiente; cantidades solo hipotéticas, artículo excluido. Cierre 3 coincide condicionalmente; no atribuir bloqueo automático solo por la exclusión. Llallagua, Quime, columnas CBA/Tocaña y AMAZONICO recuperados por foto sin alias; fecha fuera de orden y trazo de REF conservados.'}],extras=extras)
    assert plan['cotejo']['discrepancias']==[] and plan['cotejo']['cierres']=={74:3}
    rows={r['id']:r for r in todas if r['articulo_id']==10}
    assert {id for id,r in rows.items() if r['revision_documental']}=={560}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CSD00L','CROOTL')}
    for id,fields in {538:{'fecha_movimiento':'2010-06-11'},539:{'detalle':'Fe. libro Oruro'},540:{'referencia':None,'area':'Dirección'},545:{'detalle':'OBSEQUIO PERSONAL','referencia':'ESIP','area':'ADM'},551:{'detalle':'LLALLAGUA'},552:{'detalle':'LLALLAGUA'},563:{'detalle':'UCB. CARMEN PAMPA'},567:{'detalle':'FIL'},574:{'area':'CEDOAL'},583:{'detalle':'LIB. "AKADEMIA"'},587:{'referencia':'DONA'}}.items():cambios.setdefault(id,{}).update(fields)
    fechas={553:('2011-08-02','2011-08-01')}
    fechas.update({id:('2012-10-04',rows[id]['fecha_movimiento']) for id in range(561,570)})
    acumulado=papel=0;entries=[];diferencias=[];protegidos={}
    with SessionLocal() as db:
        for ids,qs,bs in INDICE:
            assert len(ids)==len(qs)==len(bs)
            for id,q,escrito in zip(ids,qs,bs):
                r=rows[id];previa=deepcopy(r['revision_documental'] or {});acumulado+=q
                delta=escrito-(papel+q);papel=escrito
                if delta:diferencias.append({'id':id,'local':delta,'acumulada':escrito-acumulado})
                campos={'ingresos':q if q>0 else None,'salidas':-q if q<0 else None,'saldo_registrado':acumulado,**cambios.get(id,{})}
                rev={'criterios':['T01'],'motivo':'Hoja completa cotejada con vecinos; fotos, extracción inicial y agrupación confirmada por el titular conservadas.','hallazgos':['HOJA_COMPLETA_COTEJADA'],'tipo_fila':'MOVIMIENTO','saldo_documental':escrito,'origen_saldo':'FOTO' if escrito==acumulado else 'RECONSTRUIDO','origen_fecha':'FOTO','fecha_documental':campos.get('fecha_movimiento',r['fecha_movimiento']),'usar_saldo_esperado':True,'reconstruir_cadena':True,'cotejo_pagina_completa':True}
                if id==534:rev.update(saldo_base=0,origen_saldo_base='HIPOTESIS',motivo_base='Ingreso 86 y saldo 86 explícitos; base previa cero inferida, sin recepción adicional.');rev['criterios'].append('T22')
                if delta:rev['diferencia_local_papel']=delta;rev['criterios'].append('T05');rev['hallazgos'].append('DESCUADRE_DEL_PAPEL_CONSERVADO')
                if id in fechas:
                    tecnica,literal=fechas[id];campos['fecha_movimiento']=tecnica;rev.update(origen_fecha='SECUENCIA_AJUSTADA',fecha_documental=literal,motivo_fecha='Fecha propia anterior al antecedente en el orden físico de las hojas agrupadas; literal conservado, fecha técnica solo de consulta. No se reordena la agrupación ni se copia otra fecha como documental.');rev['criterios'].append('T11')
                if id in (540,545,587):rev['criterios'].append('T23');rev['motivo']+=' Texto de REF/ÁREA separado según columna visible, sin crear alias.'
                if id==574:rev['criterios'].append('T12');rev['motivo']+=' Comillas inequívocas en ÁREA repiten CEDOAL de la fila anterior.';rev['columnas_documentales']={'area':'comillas que repiten CEDOAL'}
                if id in (560,561):rev.update(ambito_hoja_pendiente=True);rev['motivo']+=' La página 2 titula EL DIARIO y escribe ingreso 1/saldo 1, mientras la página 3 retoma 50 con ingreso 2/saldo 52. La agrupación confirmada no acredita un saldo único ni un recuento; se muestran ambas cifras y cálculo condicional, sin dividir ni fusionar artículos.'
                if any(campos.get(k,r[k])!=r[k] for k in ('detalle','referencia','area','ingresos','salidas')):
                    c=clasificar_movimiento(campos.get('detalle',r['detalle']),campos.get('referencia',r['referencia']),campos.get('area',r['area']),campos['ingresos'],campos['salidas'],db);campos.update({k:getattr(c,k) for k in DERIVADOS})
                    if q>0 and campos['nodo_grafo'].startswith('Salida:'):
                        area=campos.get('area',r['area']);n,e,p=(_resolver_area_con_catalogo(area,db) if area else ('Origen no especificado','SIN_AREA_REGISTRADA',False));campos.update(nodo_grafo=n,area_estado=e,requiere_auditoria_nodo=p)
                if previa:
                    assert id==560 and q==1 and escrito==1 and acumulado==51
                    nuevos=deepcopy(rev);rev=deepcopy(previa)
                    rev.update({k:v for k,v in nuevos.items() if k not in previa})
                    rev.update(revision_previa_rectificacion_documental=deepcopy(previa),usar_saldo_esperado=False,reconstruir_cadena=True,cotejo_pagina_completa=True,diferencia_saldo_documental=-50,origen_saldo='FOTO')
                    rev['criterios']=sorted(set(previa['criterios']+nuevos['criterios']))
                    rev['hallazgos']=sorted(set(previa.get('hallazgos',[])+nuevos['hallazgos']))
                    rev['motivo']=previa['motivo']+' Se amplía contexto completo, sin alterar esta decisión ni ingreso 1, fecha 4-10-12 y saldo vigente 1. Cálculo independiente 51 y ámbito de hoja EL DIARIO pendiente, sin inventar recuento ni excluir la recepción para cuadrar.'
                    campos['saldo_registrado']=r['saldo_registrado']
                    protegidos[str(id)]={'valores':{k:r[k] for k in ('detalle','referencia','area','ingresos','salidas','saldo_registrado','fecha_movimiento','estado','orden_fila','orden_pagina_validado')},'revision':deepcopy(previa),'metadatos_rectificables':[]}
                if id==589:campos['saldo_registrado']=40;rev.update(usar_saldo_esperado=False,origen_saldo='FOTO')
                foto=(BACKEND/r['ruta_imagen_respaldo']).resolve()
                entries.append({'id':id,'articulo_id':10,'pagina':f'L{r["lote_id"]:04d}-P{r["numero_pagina"]:02d}','esperado':{k:r[k] for k in CAMPOS_BASE},'esperado_adicional':{**{k:r[k] for k in DERIVADOS},**({'revision_documental':deepcopy(previa)} if previa else {})},'cambios':campos,'revision':rev,'fuente':str(foto),'sha256_imagen':hashlib.sha256(foto.read_bytes()).hexdigest()})
    assert acumulado==41 and papel==40 and diferencias==[{'id':560,'local':-50,'acumulada':-50},{'id':561,'local':49,'acumulada':-1}],(acumulado,papel,diferencias)
    assert {e['id'] for e in entries}==set(rows)
    plan['revisiones']=entries+plan['revisiones']
    plan['observaciones_articulos'].insert(0,{'articulo_id':10,'observado':True,'excluir_entrenamiento':True,'motivo':'Cuatro fotos y 56 filas cotejadas; agrupación T20 del titular conservada, sin dividir ni reasociar la hoja EL DIARIO. Anclaje 560 conserva ingreso 1, fecha 4-10-12, saldo vigente 1 y revisión previa íntegra; cálculo independiente 51 revela ámbito pendiente entre hojas. La siguiente foto retoma saldo anterior 50 con ingreso 2/saldo 52; no se inventa recuento para reconciliar. Cierre escrito 40 frente a cálculo condicional 41, exclusión y apertura bloqueada. CEDOAL, columnas ESIP/Dirección, Llallagua y Carmen Pampa recuperados como textos sin alias; literales de fechas que retroceden permanecen identificados.'})
    plan['cotejo'].update(fotografias=7,movimientos=127,nuevos_distintos=126,cierres={10:40,74:3},cierres_calculados={10:41,74:3},cierres_documentales={10:40,74:3},discrepancias=diferencias,rectificaciones_previas=protegidos,rectificaciones_documentales=[{'id':560,'metadatos':{'diferencia_saldo_documental':-50,'usar_saldo_esperado':False,'ambito_hoja_pendiente':True}}],
        pendientes_documentales={**{'560':['saldo'],'589':['saldo']},**{str(id):['fecha'] for id in [553,*range(561,570),4124]}},
        limites_cierre={10:'Cierre escrito 40 frente a cálculo condicional 41; ámbito de la hoja EL DIARIO pendiente con agrupación T20 conservada. No se inventa recuento ni se elimina ingreso 1. Artículo excluido y apertura bloqueada.',74:'Cierre escrito 3 coincide condicionalmente; nota con cruces/NO y marca ennegrecida en SALIDAS final conservadas. Artículo excluido del entrenamiento, sin atribuir bloqueo automático solo por exclusión.'})
    plan['limites'].append('Protección específica de agrupación T20, ingreso, fecha y saldo vigentes de 560; el cálculo independiente conserva las diferencias entre ámbitos sin cambiar el anclaje.')
    return plan

if __name__=='__main__':raise RuntimeError('Plan 65 archivado sin aplicación institucional: conservarlo intacto y usar generador 66.')
