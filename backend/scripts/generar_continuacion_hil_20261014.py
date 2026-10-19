"""Cotejo manual de nueve fotografías: cantidades, saldos, marcas y fechas concretas.

Las matrices se transcribieron de la foto completa y sus ampliaciones. No se
generan correcciones por parecido ni se recalifica automáticamente todo el archivo.
"""
import hashlib
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex
from app.services.revision_documental import snapshot_revision
from scripts.generar_plan_revision_hil import CAMPOS_BASE, DEST, digest

BACKEND=Path(__file__).resolve().parents[1]

# Primer ID, efecto de cada renglón, lectura de SALDO, criterio de cotejo.
HOJAS=[
 (255,[500,-45,-56,-10,-3,-10,-15,-47,-120,-20,-10,-1,-2,-7,-1,-20,-40,-4,-1,-1,-1,-7,-2,-3,-5,-3],
  [500,455,399,389,386,376,361,314,194,174,164,163,161,154,153,133,73,69,68,67,66,62,60,57,52,49],'T05'),
 (281,[15,-6,-1,109,-20,-3,-3,-6,-4,-2,-2,-11,-3,-3,-4,-3,-4,2,-2],
  [64,58,57,166,146,143,140,134,130,128,126,115,112,109,105,102,98,100,98],'T05'),
 (5038,[483,-1,-8,-1,-5,-1,-50,-15,18,-1,-1,-1,-1,-136,-3,3,-5,-10,-15,-1,-4,-1,-8,-5,-1,-1],
  [483,482,474,473,468,467,417,402,420,419,418,417,416,280,277,280,275,265,250,249,245,244,236,231,230,229],'T01'),
 (5064,[4,-3,-1,-10,-2,-100,-10,-1,-5,9,1,-5,-5,-1,1,-5,-1,-3,-1,1,-1,100,100,300,-1,-1],
  [233,230,229,219,217,117,107,106,101,110,111,106,101,100,101,96,95,92,91,92,91,191,291,591,590,589],'T02'),
 (5090,[-2,2,-10,7,-3,1,-2,2,-1,-10,-10,-3,-75,-5,10,-2,-3,-10,-3,-1,-30,-5,-10,14,-5,-1],
  [587,589,579,586,583,584,582,584,593,583,573,570,495,490,500,498,495,485,482,481,451,446,436,450,435,434],'T04'),
 (5116,[1,-2,-2,1,5,-1,-2,-1,2,-2,-1,-1,1,5,-1,-1,1,-10,-5,-1,12,-3,-5,8,-5,-1],
  [435,433,431,432,437,436,434,433,435,433,432,431,432,437,436,435,436,426,421,420,432,429,424,432,427,426],'T04'),
 (5142,[-1,-2,5,-1,-1,-1,-10,7,-2,-1,-3,-5,-5,-2,1,-1,5,-1,-12,-30,-20,-10,-10,-5,-3],
  [425,423,428,427,427,426,416,423,421,420,417,412,407,405,406,405,410,409,398,368,348,338,328,323,320],'T05'),
 (5167,[-2,-5,-1,8,-1,4,-1,6,-1,-1,-2,-1,-1,-2,9,-1,-2,-5,-1,-2,-2,-1,-3,-1,-2,-2],
  [318,313,312,320,319,323,322,328,327,326,324,323,321,319,328,327,325,320,319,317,315,314,311,310,308,306],'T05'),
 (5193,[-1,-1,9,-2,-2,-3,-2,-2,-2,-3,-2,-3,-5,-3,-4,-40,2,-5,5,-8,-5],
  [305,304,313,311,309,306,304,302,300,297,295,292,287,284,280,240,242,237,242,234,229],'T23'),
]

# Correcciones legibles de día/mes. El valor literal se guarda además del original OCR.
FECHAS_FOTO={5068:'2010-07-28',5072:'2010-09-08',5170:'2016-06-09',5179:'2017-10-05',5197:'2023-09-08'}
# Permutaciones autorizadas cuando la cadena de cantidades ya fue cotejada.
GRUPOS_FECHAS=[(286,287),(5048,5049),(5072,5073),(5076,5077),(5084,5085),
               (5091,5092),(5102,5103,5104),(5119,5120,5121),(5131,5132),(5179,5180),(5187,5188)]
# Son fechas técnicas, no conclusiones sobre cuándo ocurrió el hecho.
FECHAS_TECNICAS={
 263:('2019-01-11','SECUENCIA_AJUSTADA','2019-05-28','Fecha escrita de mayo antes de las filas de enero; para consulta se usa la fecha de la fila siguiente, conservando la escrita.'),
 296:('2024-05-24','HIPOTESIS',None,'Fecha en blanco; se conserva como hipótesis la fecha del antecedente, sin certificar el día del envío.'),
 5111:('2012-08-21','SECUENCIA_AJUSTADA','2012-07-24','Fecha escrita anterior al tramo de agosto. Se usa técnicamente la fecha del antecedente para consulta.'),
 5112:('2012-08-21','SECUENCIA_AJUSTADA','2012-08-05','Fecha escrita anterior al antecedente; ajuste de consulta con fuente literal preservada.'),
 5113:('2012-08-21','SECUENCIA_AJUSTADA','2012-08-14','Fecha escrita anterior al antecedente del tramo; ajuste técnico, sin alterar la anotación de saldo.'),
 5117:('2012-10-02','HIPOTESIS',None,'Fecha repasada, lectura 26-9?-12, extraída como 26-10-12. Se usa 02-10-12 entre las filas vecinas; la lectura no se confirma.'),
 5178:('2017-04-20','HIPOTESIS',None,'Fecha ausente en la fila FIL; se asigna técnicamente la del antecedente, con marca de hipótesis.'),
 5195:('2022-10-17','HIPOTESIS',None,'Fecha ausente en la devolución; se usa para consulta la del antecedente de octubre.'),
 5196:('2022-10-17','SECUENCIA_AJUSTADA','2022-02-07','El papel dice 7-2-22 después de octubre de 2022. Se conserva ese año literal; no se cambia a 2023 por suposición.'),
}


def generar():
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    ids=[start+i for start,q,s,_ in HOJAS for i in range(len(q))]
    with SessionLocal() as db:
        rows={m.id:snapshot_revision(m) for m in db.query(MovimientoKardex).filter(MovimientoKardex.id.in_(ids)).all()}
    assert len(rows)==len(ids)==221
    assert all(r['fecha_original'] and r['datos_originales'] for r in rows.values())
    literals={id:r['fecha_movimiento'] for id,r in rows.items()}
    literals.update(FECHAS_FOTO)
    fechas={}
    for group in GRUPOS_FECHAS:
        ordered=sorted(literals[id] for id in group)
        for id,nueva in zip(group,ordered):
            if nueva!=literals[id]:
                fechas[id]=(nueva,'SECUENCIA_AJUSTADA',literals[id],
                    'Fechas permutadas para consulta según T10/T11, después del cotejo de cantidades. La fecha escrita y la extracción inicial se conservan; no acredita el día real.')
    fechas.update(FECHAS_TECNICAS)
    revisions=[];calc={6:0,83:0};paper={6:0,83:0};image_hash={};errores=[]
    for start,quantities,saldos,criterio in HOJAS:
        assert len(quantities)==len(saldos)
        for offset,(q,escrito) in enumerate(zip(quantities,saldos)):
            id=start+offset;r=rows[id];art=r['articulo_id']
            calc[art]+=q
            esperado=calc[art]
            literal_efectivo=440 if id==5113 else escrito
            diferencia_nueva=literal_efectivo-(paper[art]+q)
            paper[art]=literal_efectivo
            cambios={'ingresos':q if q>0 else None,'salidas':-q if q<0 else None,'saldo_registrado':escrito}
            tipos={criterio};hallazgos=['HOJA_COMPLETA_COTEJADA']
            motivo='Cantidades y saldo cotejados con la fotografía y filas vecinas. El saldo de consulta se calcula de forma independiente; se conserva la lectura literal.'
            if r['ingresos']!=cambios['ingresos'] or r['salidas']!=cambios['salidas']:
                tipos.add('T02' if (r['ingresos'] or 0)*(cambios['salidas'] or 0) or (r['salidas'] or 0)*(cambios['ingresos'] or 0) else 'T23')
                hallazgos.append('LECTURA_CANTIDAD_O_COLUMNA_CORREGIDA')
            if diferencia_nueva:
                errores.append({'id':id,'diferencia_local':diferencia_nueva,'diferencia_acumulada':escrito-esperado})
                tipos.add('T05');hallazgos.append('DESCUADRE_DEL_PAPEL_CONSERVADO')
            if escrito!=esperado:hallazgos.append('SALDO_VIGENTE_RECONSTRUIDO')
            rev={'criterios':sorted(tipos),'motivo':motivo,'hallazgos':hallazgos,'tipo_fila':'MOVIMIENTO',
                 'saldo_documental':escrito,'origen_saldo':'FOTO' if escrito==esperado else 'RECONSTRUIDO',
                 'usar_saldo_esperado':True,'reconstruir_cadena':True,
                 'diferencia_local_papel':diferencia_nueva,'cotejo_pagina_completa':True}
            if id in (255,5038):rev.update(saldo_base=0,origen_saldo_base='HIPOTESIS',
                motivo_base='Base cero inferida de la primera fila: ingreso y saldo iguales. No acredita existencias físicas previas al documento.')
            if id in FECHAS_FOTO:
                cambios['fecha_movimiento']=FECHAS_FOTO[id]
                rev.update(origen_fecha='FOTO',fecha_documental=FECHAS_FOTO[id],motivo_fecha='Fecha legible cotejada; lectura OCR de día o mes incorrecta.')
                rev['criterios']=sorted(set(rev['criterios']+['T10']))
                rev['hallazgos'].append('FECHA_OCR_CORREGIDA')
            if id in fechas:
                nueva,origen,documental,reason=fechas[id]
                cambios['fecha_movimiento']=nueva
                rev.update(origen_fecha=origen,fecha_documental=documental,motivo_fecha=reason)
                rev['motivo']+=' '+reason
                rev['criterios']=sorted(set(rev['criterios']+(['T09','T19'] if origen=='HIPOTESIS' else ['T10','T11'])))
                rev['hallazgos'].append('FECHA_TECNICA_NO_CONFIRMADA')
            if id==5117:rev['fecha_documental_texto']='26-9?-12, fecha repasada'
            if id==5113:
                rev.update(saldo_documental_rectificado=440,marcas_documentales={'saldo':'450 con rectificación manuscrita 440'})
                rev['motivo']+=' La rectificación a lápiz 450→440 concuerda con la cadena y se conserva como evidencia.'
            if id==5073:
                rev.update(origen_cantidades='INTERPRETACION_HUMANA',marcas_documentales={'ingreso':'grafía repasada/tachada','salida':'9 visible'})
                rev['criterios']=sorted(set(rev['criterios']+['T03','T07']))
                rev['motivo']+=' DEV y 101→110 sustentan devolución de 9; el 9 de salidas se conserva como marca y se interpreta como ingreso, sin doble movimiento.'
            if id==5149:rev['motivo']+=' La fotografía contiene un renglón posterior completamente tachado que el OCR ya omitió; se conserva en la foto y no se crea como ingreso.'
            if id==5146:rev['motivo']+=' EXPO ITURBIDE tiene salida 1 visible y saldo repetido 427; se conserva ese error del papel.'
            if id==5159:rev['motivo']+=' Venta entre paréntesis y nota «falta carta»: se conserva la salida 1; el paréntesis no se interpreta como anulación.'
            if id in (5209,5211):
                cambios.update(area=None,nodo_grafo='Origen no especificado',area_estado='SIN_AREA_REGISTRADA',requiere_auditoria_nodo=False)
                rev['motivo']+=' La cifra de ingreso estaba guardada en ÁREA; la columna de área está vacía en la fuente.'
            elif not (r['area'] or '').strip():
                cambios.update(nodo_grafo='Origen no especificado' if q>0 else 'Destino no especificado',
                               area_estado='SIN_AREA_REGISTRADA',requiere_auditoria_nodo=False)
            ruta=(BACKEND/r['ruta_imagen_respaldo'].replace('\\','/')).resolve()
            image_hash.setdefault(str(ruta),hashlib.sha256(ruta.read_bytes()).hexdigest())
            revisions.append({'id':id,'articulo_id':art,'pagina':f"L{r['lote_id']:04d}-P{r['numero_pagina']:02d}",
                'esperado':{k:r[k] for k in CAMPOS_BASE},'cambios':cambios,'revision':rev,
                'fuente':str(ruta),'sha256_imagen':image_hash[str(ruta)]})
    assert calc=={6:115,83:228},calc
    return {'version':3,'criterio_sha256':digest(policy),'respuestas_sha256':policy['procedencia']['sha256'],
        'revisiones':revisions,'observaciones_articulos':[
            {'articulo_id':6,'observado':True,'excluir_entrenamiento':False,
             'motivo':'Dos hojas cotejadas. Saldo documental final 98; cadena reconstruida 115. Diferencia 17 conservada; no es un conteo físico actual.'},
            {'articulo_id':83,'observado':True,'excluir_entrenamiento':False,
             'motivo':'Siete hojas cotejadas. Saldo documental final 229; cadena reconstruida 228. Se conservan errores compensados, anotaciones, fechas técnicas y diferencia final 1.'}],
        'sin_reasociaciones_ni_borrados':True,'cotejo':{'fotografias':len(image_hash),'movimientos':len(ids),'cierres_reconstruidos':calc,'diferencias_locales_papel':errores},
        'limites':['Se cotejaron estas nueve fotografías; el resto continúa pendiente.','Áreas y receptores no se normalizan por semejanza; T17 se mantiene para después.','Fechas técnicas no confirman cuándo ocurrió el hecho.','Saldo reconstruido no es un conteo físico institucional.']}


if __name__=='__main__':
    path=DEST/'plan_continuacion_03.json'
    if path.exists():raise RuntimeError('Conservar el plan existente: no regenerar un cotejo después de aplicarlo.')
    plan=generar()
    path.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'plan':str(path),'sha256':digest(plan),'cotejo':plan['cotejo']},ensure_ascii=False))
