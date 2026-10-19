"""Siete fotos cotejadas: Bolivia Ecológica 13, 35 y 39; sin normalizar catálogos."""
import hashlib
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex
from app.services.revision_documental import snapshot_revision
from scripts.generar_plan_revision_hil import CAMPOS_BASE, DEST, digest

BACKEND=Path(__file__).resolve().parents[1]
HOJAS=[
 (10377,[10,5,-1,-2,1,20,-3,-5,-5,-3,5,-2,-2,-1,1,-2,1,-10,3,1,-2,-5,2,-2,-2,1],
  [10,15,None,12,13,33,None,None,None,17,22,20,18,17,18,16,17,7,10,11,9,4,6,4,2,3]),
 (10403,[2,5,-1,-2,-1,2,-1],[5,10,9,7,6,8,7]),
 (10433,[0,-2,-2,-2,0,5,-1,-2,1,-1,20,-3,-5,-5,-3,7,-2,-1,2,-2,-10,6,2,-5,-2,-2],
  [10,None,None,4,4,9,None,6,7,6,26,None,None,None,10,17,15,14,16,14,4,10,12,7,5,3]),
 (10459,[6,-1,-1,-1,-1],[9,8,7,6,5]),
 (10258,[10,-2,-2,-2,5,-1,-2,1,-1,20,-3,-5,-5,-3,3,-2,-2,-1,2,-1,-2,2,-9,50,-10,1],
  [10,8,6,4,9,None,6,7,6,26,None,None,None,10,13,None,None,8,10,9,7,9,0,50,40,41]),
 (10284,[-5,3,-2,-5,3,-3,-1,-10,-10,11,1,-1,-3,1,-5,5,-10,6,-3,3,-3,1,-10,1,-2,5],
  [36,39,37,32,35,32,31,21,11,22,23,22,19,20,15,20,10,16,13,16,13,14,4,5,3,8]),
 (10310,[-1,-1,2,-2],[7,6,8,6]),
]
FECHAS_FOTO={10377:'2005-10-11',10259:'2005-08-17',10260:'2005-08-21'}
BLANCAS={
 **{id:'2005-10-13' for id in range(10379,10382)},
 **{id:'2006-08-01' for id in range(10383,10388)},
 10393:'2007-06-15',10395:'2007-08-08',10399:'2007-10-17',
 10437:'2005-08-26',**{id:'2005-10-06' for id in range(10439,10443)},
 **{id:'2006-08-01' for id in range(10444,10449)},10450:'2006-10-06',10460:'2014-07-30',
 **{id:'2005-10-13' for id in range(10263,10267)},
 **{id:'2006-08-01' for id in range(10268,10273)},10277:'2007-04-25',10279:'2007-06-15',10310:'2018-08-14',
}
PARCIALES={
 10382:('2006-08-01','08-06, mes y año'),10433:('2005-07-01','7-05, mes y año'),
 10443:('2006-08-01','8-06, mes y año'),10267:('2006-08-01','08-06, mes y año'),
 10273:('2006-10-09','9-10, año ausente'),
}
FUERA_ORDEN={
 10378:('2005-10-13','2001-10-13','El papel muestra 13-10-01 tras 11-10-05. Consulta ajustada por contexto a 2005; no se confirma el año del hecho.'),
 10391:('2007-04-22','2006-11-29','Fecha de noviembre de 2006 entre abril y junio de 2007. Se conserva la literal y se usa técnicamente la del antecedente.'),
 10276:('2007-04-25','2006-11-29','La fecha escrita vuelve a 2006 dentro del tramo de 2007. Se preserva y se ajusta solo la fecha para consulta.'),
 10299:('2011-08-01','2011-08-02','Permutación de las dos fechas vecinas tras cotejar cantidades, según T10/T11.'),
 10300:('2011-08-02','2011-08-01','Permutación de las dos fechas vecinas tras cotejar cantidades, según T10/T11.'),
}


def generar():
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    ids=[s+i for s,q,_ in HOJAS for i in range(len(q))]
    with SessionLocal() as db:
        rows={m.id:snapshot_revision(m) for m in db.query(MovimientoKardex).filter(MovimientoKardex.id.in_(ids)).all()}
    assert len(rows)==len(ids)==120
    calc={301:0,303:0,305:10};revisions=[];hashes={};inferred=[]
    for start,quantities,saldos in HOJAS:
        assert len(quantities)==len(saldos)
        for offset,(q,written) in enumerate(zip(quantities,saldos)):
            id=start+offset;r=rows[id];art=r['articulo_id'];calc[art]+=q;expected=calc[art]
            assert written is None or written==expected,(id,written,expected)
            cambios={'ingresos':q if q>0 else None,'salidas':-q if q<0 else None,'saldo_registrado':expected}
            rev={'criterios':['T01'],'motivo':'Hoja completa cotejada con las fotos y su continuidad; la lectura original permanece conservada.',
                 'tipo_fila':'MOVIMIENTO','saldo_documental':written,'origen_saldo':'HIPOTESIS' if written is None else 'FOTO',
                 'usar_saldo_esperado':True,'reconstruir_cadena':True,'hallazgos':['HOJA_COMPLETA_COTEJADA']}
            if id in (10377,10258):
                rev.update(saldo_base=0,origen_saldo_base='HIPOTESIS',motivo_base='Base cero inferida de igualdad ingreso/saldo inicial; no acredita un conteo físico previo.')
            if id==10433:
                rev.update(tipo_fila='BASE_DOCUMENTAL',saldo_base=10,origen_saldo_base='DOCUMENTO',
                    motivo='Saldo según inventario: base documental 10, sin inventar un ingreso de 10.',criterios=['T15','T22'])
            if written is None:
                inferred.append(id);rev['criterios'].append('T08');rev['hallazgos'].append('SALDO_EN_BLANCO_RECONSTRUIDO')
                rev['motivo']+=' El saldo está en blanco: se representa como hipótesis por continuidad y se excluye del entrenamiento histórico.'
            if (r['ingresos'] or 0)!=(cambios['ingresos'] or 0) or (r['salidas'] or 0)!=(cambios['salidas'] or 0):
                rev['criterios'].append('T23');rev['hallazgos'].append('CANTIDAD_O_COLUMNA_CORREGIDA')
            if id in FECHAS_FOTO:
                cambios['fecha_movimiento']=FECHAS_FOTO[id]
                rev.update(origen_fecha='FOTO',fecha_documental=FECHAS_FOTO[id],motivo_fecha='Fecha legible en la foto; se corrige la lectura OCR.')
                rev['criterios'].append('T10')
            if id in BLANCAS or id in PARCIALES:
                nueva=BLANCAS.get(id) or PARCIALES[id][0]
                cambios['fecha_movimiento']=nueva
                reason='Fecha ausente/incompleta: valor técnico para consulta dentro del tramo; no acredita el día exacto del hecho.'
                rev.update(origen_fecha='HIPOTESIS',fecha_documental=None,motivo_fecha=reason)
                if id in PARCIALES:rev['fecha_documental_texto']=PARCIALES[id][1]
                rev['criterios'].append('T09');rev['hallazgos'].append('FECHA_HIPOTETICA');rev['motivo']+=' '+reason
            if id in FUERA_ORDEN:
                nueva,literal,reason=FUERA_ORDEN[id];cambios['fecha_movimiento']=nueva
                rev.update(origen_fecha='SECUENCIA_AJUSTADA',fecha_documental=literal,motivo_fecha=reason)
                rev['criterios'].append('T11');rev['hallazgos'].append('FECHA_DOCUMENTAL_FUERA_ORDEN');rev['motivo']+=' '+reason
            if id==10454:
                rev.update(origen_fecha='FOTO',fecha_documental='2007-08-08',fecha_documental_texto='comilla de repetición',motivo_fecha='La marca de repetición en FECHA remite al 08-08-07 anterior.')
                rev['criterios'].append('T18')
            if id in (10435,10436,10384,10385,10386):
                cambios['detalle']='Feria del Libro' if art==305 else 'Para la Feria'
                rev.update(marcas_documentales={'detalle':'comillas de repetición'})
                rev['criterios'].append('T18');rev['motivo']+=' Las comillas repiten el detalle de la misma columna; se conserva la marca original.'
            if id==10437:
                rev['motivo']+=' La devolución contiene -0-: se mantiene sin efecto de stock, sin crear un ingreso positivo.'
                rev['marcas_documentales']={'ingresos':'-0-'}
            if id==10388:
                rev.update(origen_cantidades='INTERPRETACION_HUMANA',marcas_documentales={'ingresos':'2 escrito en columna de ingresos'})
                rev['criterios'].append('T07');rev['motivo']+=' El 2 está en ingresos, pero 22→20 acredita salida 2 según el criterio acordado; se conserva el error de columna del papel.'
            if id==10394:
                rev.update(marcas_documentales={'ingresos':'cifra tachada','salidas':'10 visible'})
                rev['criterios'].append('T14');rev['motivo']+=' Solo se descarta la cifra tachada de ingreso, no el renglón ni la salida 10.'
            if id==10395:
                rev.update(origen_cantidades='INTERPRETACION_HUMANA')
                rev['motivo']+=' La grafía del ingreso es 3 y la continuidad 7→10 lo respalda; el OCR había leído 9/16.'
            if id==10448:rev['motivo']+=' La devolución muestra 7 (no 4); 10+7=17.'
            if id==10301:
                cambios.update(area='CEDOAL',referencia=None,referencia_estado='AUSENTE',requiere_auditoria_referencia=False)
                rev['criterios']+=['T18','T23'];rev['marcas_documentales']={'area':'comilla de repetición','referencia':'vacía'}
                rev['motivo']+=' El cotejo ampliado rectifica la interpretación anterior: la comilla está en ÁREA, no en REF. Repite CEDOAL del renglón previo; se retira DEV de REF sin borrar su auditoría anterior.'
                rev['rectifica_cotejo_previo']=True
            if not (r['area'] or '').strip() and id!=10301:
                cambios.update(nodo_grafo='Origen no especificado' if q>0 else 'Destino no especificado',
                               area_estado='SIN_AREA_REGISTRADA',requiere_auditoria_nodo=False)
            ruta=(BACKEND/r['ruta_imagen_respaldo'].replace('\\','/')).resolve()
            hashes.setdefault(str(ruta),hashlib.sha256(ruta.read_bytes()).hexdigest())
            rev['criterios']=sorted(set(rev['criterios']))
            revisions.append({'id':id,'articulo_id':art,'pagina':f"L{r['lote_id']:04d}-P{r['numero_pagina']:02d}",
                'esperado':{k:r[k] for k in CAMPOS_BASE},'cambios':cambios,'revision':rev,
                'fuente':str(ruta),'sha256_imagen':hashes[str(ruta)]})
    assert calc=={301:6,303:7,305:5}
    return {'version':4,'criterio_sha256':digest(policy),'respuestas_sha256':policy['procedencia']['sha256'],
        'revisiones':revisions,'observaciones_articulos':[
            {'articulo_id':303,'observado':True,'excluir_entrenamiento':False,
             'motivo':'Cantidades y dos hojas cotejadas; cierre 7. Se conserva la columna incorrecta y fechas escritas fuera de secuencia/incompletas, con hipótesis diferenciadas.'},
            {'articulo_id':301,'observado':True,'excluir_entrenamiento':False,
             'motivo':'Tres hojas cotejadas, cierre 6. Fechas técnicas y fechas fuera de orden preservadas; la corrección de comilla en ÁREA queda auditada.'}],
        'sin_reasociaciones_ni_borrados':True,'cotejo':{'fotografias':len(hashes),'movimientos':len(ids),'cierres':calc,'saldos_en_blanco':inferred},
        'limites':['Se conserva el archivo y las inferencias se excluyen del entrenamiento.','No se normalizan áreas por semejanza ni se eliminan filas parecidas.','Las fechas técnicas no certifican la gestión del hecho.']}


if __name__=='__main__':
    p=DEST/'plan_continuacion_04.json'
    if p.exists():raise RuntimeError('Conservar el plan existente: no regenerar un cotejo después de aplicarlo.')
    plan=generar()
    p.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'plan':str(p),'sha256':digest(plan),'cotejo':plan['cotejo']},ensure_ascii=False))
