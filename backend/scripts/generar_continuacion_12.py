"""Cotejo de 239 filas en diez fotos de Los caminos de la escultura."""
import hashlib,json
from pathlib import Path
from app.db.session import SessionLocal
from app.services.clasificador_nodos import clasificar_movimiento,_resolver_area_con_catalogo
from scripts.generar_plan_revision_hil import CAMPOS_BASE,DEST,digest

BACKEND=Path(__file__).resolve().parents[1]
HOJAS=[
 (range(6485,6511),[200,-30,-13,-10,-60,-1,-30,-5,50,-50,-14,-6,750,-44,-5,-10,-5,-10,-1,1,-1,-1,-10,-5,-4,-20],
  [200,170,157,147,87,86,56,51,101,51,37,31,781,737,732,722,717,707,706,707,706,705,695,690,686,666]),
 (range(6511,6538),[-5,-10,-1,-1,-31,-1,-1,-1,-1,-5,-1,-1,-1,-5,-1,-1,-25,-25,-1,-1,-1,-5,5,-3,-3,-1,-25],
  [661,651,650,649,618,617,616,615,614,609,608,607,606,601,600,599,574,549,548,547,546,541,546,543,540,539,514]),
 (range(6538,6564),[-1,-5,-1,-5,-10,-2,10,15,-2,-30,3,26,-8,-3,-1,-1,-1,-10,-15,-6,-3,-1,-1,-10,-10,-3],
  [513,508,507,502,492,490,500,515,513,483,486,512,504,501,500,499,498,488,473,467,464,463,462,452,442,439]),
 (range(6564,6590),[-4,-6,-2,2,-1,3,-10,-1,1,-10,-5,10,-1,-1,-5,-1,-1,-1,-5,1,-1,4,-2,-1,-1,-4],
  [435,429,427,429,428,431,421,420,421,411,406,416,415,414,409,408,407,406,401,402,401,405,403,402,401,397]),
 (range(6590,6616),[-1,-1,-1,9,-3,-2,2,-3,-3,2,-5,2,-1,-2,-1,-1,-1,1,5,-1,-1,-1,1,1,8,-1],
  [396,395,394,403,400,398,400,397,394,396,391,393,392,390,389,388,387,388,393,392,391,390,391,392,400,399]),
 (range(6616,6642),[-1,-1,-1,-6,-3,3,-5,-1,5,-1,-1,-5,-1,-1,5,-1,1,1,-2,5,-3,-5,-2,-2,-4,1],
  [398,397,396,390,387,390,385,384,389,388,387,382,381,380,385,384,385,386,384,389,386,381,379,377,373,374]),
 (range(6642,6668),[-1,-2,-2,-2,-3,-1,-1,3,-1,-2,-2,-1,-2,2,-3,-2,1,-1,-1,-3,-1,-5,-1,3,-2,-1],
  [373,371,369,367,364,363,362,365,364,362,360,359,357,359,356,354,355,354,353,360,349,344,343,346,244,243]),
 (range(6668,6694),[-1,-3,5,-1,-1,-1,-1,-3,-6,-1,-2,-3,-1,-1,-1,-1,-1,-1,1,-1,-1,-1,-1,-1,-1,-4],
  [242,239,244,243,242,241,240,237,231,330,328,325,324,323,322,321,320,319,320,319,318,317,316,315,314,310]),
 (range(6694,6720),[-1,-1,-2,2,4,14,-2,-1,-2,-2,-2,-1,-2,-1,2,-2,-2,-4,-1,-1,-1,-1,-2,-1,-2,1],
  [309,308,306,308,312,326,324,323,321,319,317,316,314,313,315,313,311,307,306,305,304,303,301,300,298,299]),
 (range(6720,6724),[6,-1,-1,-5],[305,304,303,298]),
]
FECHAS_FOTO={6524:'2010-04-21',6551:'2010-09-15',6569:'2011-05-27',6604:'2012-10-06',6656:'2015-06-14',6663:'2016-05-23',6692:'2018-08-15'}
PARES=[(6568,6569),(6572,6573),(6611,6612),(6637,6638),(6639,6640),(6641,6642),(6709,6710)]
TECNICAS={
 **{id:('2010-03-31','SECUENCIA_AJUSTADA','2010-03-29','29-03-10 después de varios renglones del 31-03; consulta técnica con el antecedente y literal conservada.') for id in (6513,6514)},
 6551:('2010-10-21','SECUENCIA_AJUSTADA','2010-09-15','15-09-10 escrito después del 21-10, confirmado en el recorte de la fecha. Consulta técnica del antecedente.'),
 6564:('2011-04-11','SECUENCIA_AJUSTADA','2011-03-16','16-03-11 escrito después del 11-04. La cadena de cantidades confirma el orden de hojas; consulta técnica del antecedente.'),
 6588:('2012-02-28','SECUENCIA_AJUSTADA','2011-12-09','09-12-11 después de febrero de 2012. Se conserva el literal; no se inventa el día real del obsequio.'),
 6589:('2012-02-28','SECUENCIA_AJUSTADA','2012-01-06','06-01-12 después de febrero de 2012. Consulta técnica del antecedente, sin mover la cantidad a otra fila.'),
 6594:('2012-05-22','SECUENCIA_AJUSTADA','2012-05-09','09-05-12 intercalado después del 22-05: fecha técnica del antecedente.'),
 6598:('2012-08-08','SECUENCIA_AJUSTADA','2012-07-24','24-07-12 intercalado después del 08-08: fecha técnica del antecedente.'),
 6604:('2012-10-29','SECUENCIA_AJUSTADA','2012-10-06','06-10-12 después del 29-10. El OCR decía 16-10; se conserva el 6 leído y la consulta se ajusta técnicamente.'),
 6616:('2013-03-28','SECUENCIA_AJUSTADA','2012-12-16','16-12-12 después del 28-03-13. Cantidades y resto de la hoja encadenan 399 a 398: no se reordena toda la hoja para corregir dos fechas.'),
 6617:('2013-03-28','SECUENCIA_AJUSTADA','2012-12-14','14-12-12 en el segundo renglón de la misma hoja. Fecha técnica del contexto de marzo de 2013 y literal conservada.'),
 6656:('2015-08-14','SECUENCIA_AJUSTADA','2015-06-14','14-06-15 después de agosto: fecha técnica del antecedente, sin certificar una fecha de junio en esta posición.'),
 6683:('2017-08-11','HIPOTESIS',None,'FIL tiene fecha en blanco; consulta con el antecedente, sin acreditar el día.'),
 6695:('2019-07-05','SECUENCIA_AJUSTADA','2018-12-11','11-12-18 después de julio de 2019. Fecha técnica del antecedente y literal conservada; no se deduce otro año real.'),
 6699:('2021-08-15','HIPOTESIS',None,'Ingreso de Centros Patiño / Fund. BCB sin fecha. Consulta técnica de la fecha vecina siguiente; no se acredita su día ni año reales.'),
 6700:('2021-08-15','HIPOTESIS',None,'15-8?-21 repasado: se conserva 15 de agosto como hipótesis técnica y la lectura parcial en metadatos.'),
 6708:('2023-06-16','HIPOTESIS',None,'Devolución con fecha en blanco. Las dos filas siguientes escriben 19 y 16 de junio de 2023; consulta técnica con el 16 tras ordenar sus fechas de consulta, sin confirmar fecha propia.'),
}


def generar():
    rows=json.loads((BACKEND/'backups/continuacion_hil_11_20261015/articulo_96_antes.json').read_text(encoding='utf-8'))
    rows={r['id']:r for r in rows};assert len(rows)==239 and not any(r['revision_documental'] for r in rows.values())
    literal={id:r['fecha_movimiento'] for id,r in rows.items()};literal.update(FECHAS_FOTO)
    fechas=dict(TECNICAS)
    for par in PARES:
        for id,nueva in zip(par,sorted(literal[id] for id in par)):
            if nueva!=literal[id]:fechas[id]=(nueva,'SECUENCIA_AJUSTADA',literal[id],'Fechas contiguas permutadas solo para consulta según T10/T11 tras cotejar cantidades; se conserva la fecha escrita de cada renglón.')
    calc=papel=0;entries=[];hashes={};diferencias=[]
    with SessionLocal() as db:
        for ids,qs,saldos in HOJAS:
            assert len(ids)==len(qs)==len(saldos)
            for id,q,escrito in zip(ids,qs,saldos):
                r=rows[id];calc+=q;delta=escrito-(papel+q);papel=escrito
                cambios={'ingresos':q if q>0 else None,'salidas':-q if q<0 else None,'saldo_registrado':calc}
                rev={'criterios':['T01'],'motivo':'Diez hojas completas cotejadas: cantidades, saldos y fechas con contexto de las filas previas y siguientes. Se conserva el documento y la extracción original.',
                    'tipo_fila':'MOVIMIENTO','saldo_documental':escrito,'origen_saldo':'FOTO' if calc==escrito else 'RECONSTRUIDO',
                    'origen_fecha':'FOTO','fecha_documental':literal[id],'usar_saldo_esperado':True,'reconstruir_cadena':True,
                    'cotejo_pagina_completa':True,'hallazgos':['HOJA_COMPLETA_COTEJADA']}
                if delta:
                    rev['criterios'].append('T05');rev['diferencia_local_papel']=delta
                    rev['hallazgos'].append('DESCUADRE_DEL_PAPEL_CONSERVADO');diferencias.append({'id':id,'local':delta,'acumulada':escrito-calc})
                if id==6485:
                    rev.update(saldo_base=0,origen_saldo_base='HIPOTESIS',motivo_base='Primer ingreso 200 igual al saldo 200: base previa cero inferida; no acredita un conteo anterior.')
                    rev['criterios'].append('T22')
                if id in (6589,6637,6647,6648):
                    rev['criterios'].append('T02');rev['motivo']+=' La cifra está en SALIDAS, no en INGRESOS. Se corrige la columna sin cambiar el valor visible.'
                if id==6662:rev['motivo']+=' Usuario del año: la foto muestra salida 1, no 4. El saldo 349 sigue al esperado 350 de la salida anterior.'
                if id==6661:rev['motivo']+=' 353 - 3 = 350; el papel escribe 360. La fila siguiente de salida 1 vuelve a 349; se conservan ambos errores locales, sin inventar operaciones.'
                if id==6666:rev['motivo']+=' 346 - 2 = 344; el papel escribe 244. Se reconstruye la cadena independiente conservando el salto de centena del documento.'
                if id==6677:
                    rev['criterios'].append('T04');rev['motivo']+=' El saldo repasado visible es 330, no 230; vuelve a coincidir con la cadena independiente tras el error de centena. No es un ingreso ni un nuevo recuento.'
                    rev['anotacion_documental']='Saldo 330 repasado; la corrección coincide con las cantidades acumuladas, sin reinicio ficticio del inventario.'
                if id==6544:rev['anotacion_margen']='Signo de interrogación junto al ingreso 10 de Sucre Casa de la Cultura: se conserva; no equivale a una anulación expresa.'
                if id==6720:rev['motivo']+=' La devolución 6 es un renglón propio, con saldo 305 después del ingreso 1 y saldo 299 de la hoja anterior. Se conservan ambos registros del mismo día.'
                if r['area'] in ('C.DOC.','CDOASC','CEDDAL','CDD0C','CDD0C.','CDD0','CEDOOL'):
                    cambios['area']='CEDO.' if id in (6680,6683) else 'CEDOAL'
                    rev['motivo']+=' Se recupera la lectura literal de ÁREA desde la foto, sin crear áreas ni agrupar instituciones por similitud.'
                if id==6696:
                    cambios['area']='CEDOAL';rev['criterios'].append('T18');rev['motivo']+=' La comilla de ÁREA repite CEDOAL de la fila anterior, no un área llamada dos puntos.'
                if id in FECHAS_FOTO:cambios['fecha_movimiento']=FECHAS_FOTO[id]
                if id in fechas:
                    nueva,origen,fecha,motivo=fechas[id];cambios['fecha_movimiento']=nueva
                    rev.update(origen_fecha=origen,fecha_documental=fecha,motivo_fecha=motivo)
                    rev['criterios'].append('T09' if origen=='HIPOTESIS' else 'T11')
                if id==6700:
                    rev['lectura_fecha_parcial']='15-8?-21, repasada'
                    rev['anotacion_documental']='CBBA tachado y sustituido por STA CRUZ en el detalle. Se corrige el destino de la feria; no se anula la salida 2.'
                    rev['criterios'].append('T14')
                if any(cambios.get(k,r[k])!=r[k] for k in ('detalle','area','referencia','ingresos','salidas')):
                    clas=clasificar_movimiento(r['detalle'],r['referencia'],cambios.get('area',r['area']),cambios['ingresos'],cambios['salidas'],db)
                    d={k:getattr(clas,k) for k in ('nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia')}
                    if q>0 and d['nodo_grafo'].startswith('Salida:'):
                        area=cambios.get('area',r['area']);n,e,p=(_resolver_area_con_catalogo(area,db) if area else ('Origen no especificado','SIN_AREA_REGISTRADA',False))
                        d.update(nodo_grafo=n,area_estado=e,requiere_auditoria_nodo=p)
                    cambios.update(d)
                if id==6626:
                    cambios.update(referencia_estado='INCIERTA',requiere_auditoria_referencia=True)
                    rev['motivo']+=' El punto aislado en REF no acredita documento ni una comilla inequívoca de repetición: se conserva como referencia incierta.'
                rev['criterios']=sorted(set(rev['criterios']))
                foto=(BACKEND/r['ruta_imagen_respaldo']).resolve();hashes.setdefault(str(foto),hashlib.sha256(foto.read_bytes()).hexdigest())
                entries.append({'id':id,'articulo_id':96,'pagina':f"L{r['lote_id']:04d}-P{r['numero_pagina']:02d}",
                    'esperado':{k:r[k] for k in CAMPOS_BASE},'esperado_adicional':{k:r[k] for k in ('nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia')},
                    'cambios':cambios,'revision':rev,'fuente':str(foto),'sha256_imagen':hashes[str(foto)]})
    assert len(hashes)==10 and calc==papel==298,(calc,papel)
    assert diferencias==[{'id':6661,'local':10,'acumulada':10},{'id':6662,'local':-10,'acumulada':0},{'id':6666,'local':-100,'acumulada':-100},{'id':6677,'local':100,'acumulada':0}],diferencias
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    return {'version':12,'criterio_sha256':digest(policy),'revisiones':entries,'sin_reasociaciones_ni_borrados':True,
        'autorizacion_adicional':'El usuario delegó las decisiones de interpretación en base a sus 23 criterios previos.',
        'observaciones_articulos':[{'articulo_id':96,'observado':True,'excluir_entrenamiento':False,
            'motivo':'Diez fotografías y 239 filas cotejadas. Cierre 298 coincide con el papel tras corregir columnas y salida 1 de Usuario del año. Errores de centena y decena del papel preservados con su corrección posterior; ninguna operación ficticia. Fechas técnicas y una referencia incierta siguen identificadas.'}],
        'cotejo':{'fotografias':10,'movimientos':239,'cierres':{96:298},'cierres_documentales':{96:298},'discrepancias':diferencias},
        'limites':['La coincidencia del cierre no borra errores intermedios ni confirma fechas hipotéticas.','No se crean áreas ni alias ni se fusionan instituciones.','El saldo documental no certifica existencias físicas.']}


if __name__=='__main__':
    path=DEST/'plan_continuacion_12.json'
    if path.exists():raise RuntimeError('Conservar el plan congelado; cambios posteriores requieren otro lote.')
    plan=generar();path.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'plan':str(path),'sha256':digest(json.loads(path.read_text(encoding='utf-8'))),'cotejo':plan['cotejo']},ensure_ascii=False))
