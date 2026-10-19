"""Cotejo visual de ocho hojas: Taller 3 y Bolivia Ecológica 37/41."""
import hashlib
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.services.clasificador_nodos import clasificar_movimiento, _resolver_area_con_catalogo
from scripts.generar_plan_revision_hil import CAMPOS_BASE, DEST, digest

BACKEND=Path(__file__).resolve().parents[1]
ANTES=BACKEND/'backups/continuacion_hil_08_20261014'
# Primer ID, efecto cotejado, saldo escrito (None = vacío/ilegible).
HOJAS=[
 (8592,[0,-3,-1,-1,-2,20,-10,9,-2,-2,-1,-1,-1,-2,-1,-1,-1,-1,-1,-1,-3,46,-3,1,-1,-1],
  [7,None,3,2,0,20,10,19,17,15,None,None,12,10,9,None,None,6,5,4,1,47,44,45,44,43]),
 (8618,[-1,-8,-5,-5,9,-1,-1,-1,-2,-5,3,-5,-4,-3,3,-1,-5,3,1,-1,-1,-1,1,-2,2,-8],
  [42,34,29,24,33,32,31,30,28,23,26,21,17,14,17,16,11,14,15,14,13,12,13,11,13,5]),
 (8644,[5,-2,2,10,-5,3,4,-10,8,-1,-1,-2,-2,-3,-1],
  [10,8,10,20,15,18,22,12,20,19,18,16,14,11,10]),
 (10314,[10,-2,-2,-2,5,-1,-2,1,-2,20,-5,-3,-5,-3,1,-2,-1,-2,-1,1,-2,2,-5,15,-10],
  [10,8,6,4,9,None,6,7,5,25,None,None,None,9,10,8,7,5,4,5,3,5,0,15,5]),
 (10339,[-2,-3,50,-10,-10,4,-5,2,-2,-5,2,-3,-1,-10,-10,10,1,-1,-3,2,-5,5,-5,-3,2,-4],
  [3,0,50,40,30,34,29,31,29,24,26,23,22,12,2,12,13,12,9,11,6,11,6,3,5,1]),
 (10365,[4,-3,2,-1,20,-2,-2,-9,-1,-2,2,-1],
  [5,2,4,3,23,21,19,10,9,7,9,8]),
 (10464,[20,-3,-5,-5,-3,6,-2,-2,-1,2,-2,2,-6,13,-10,10,-5,3,-2,40,-10,2,-5,3,-2,-5],
  [20,None,None,None,4,10,None,None,5,7,5,7,1,14,4,14,9,12,10,50,40,42,37,40,38,33]),
 (10490,[5,-3,-1,-10,-10,16,1,-1,-3,2,-5,5,-10,8,3,-10,7,-1,-16,-1,-1,1,2,-2],
  [38,35,34,24,14,30,31,30,27,29,24,29,19,27,30,20,27,26,10,9,8,9,11,9]),
]
FECHAS_FOTO={10330:'2006-11-07',10339:'2007-09-04'}
# Nueva fecha de consulta, origen, fecha literal si tiene todos sus componentes, motivo.
TECNICAS={
 8592:('2006-06-26','HIPOTESIS',None,'Solo consta 26-6; año 2006 hipotético para mantener el tramo anterior al primer año legible, agosto de 2007. No se certifica el año del inventario.'),
 8593:('2006-10-06','HIPOTESIS',None,'Solo consta 6-10; se interpreta día y mes y se asigna técnicamente 2006 por contexto. Año no confirmado.'),
 8594:('2006-10-11','HIPOTESIS',None,'Solo consta 11-10. Año técnico 2006, no confirmado; el OCR había convertido el mes en noviembre.'),
 8595:('2006-10-11','HIPOTESIS',None,'Consta 14-09 sin año después de octubre. Fecha técnica de consulta del antecedente, conservando la lectura parcial.'),
 8596:('2006-12-15','HIPOTESIS',None,'Solo consta 15-12; año 2006 hipotético anterior a agosto de 2007. No acredita una fecha completa.'),
 8598:('2007-08-08','HIPOTESIS',None,'Fecha ausente: se usa para consulta la del ingreso anterior, sin confirmar el día de salida.'),
 8608:('2008-05-19','HIPOTESIS',None,'Fecha en blanco en Donación UPEA; fecha técnica del antecedente.'),
 8609:('2008-05-19','HIPOTESIS',None,'Fecha en blanco en Donación U. Técnica; fecha técnica del antecedente.'),
 8656:('2017-01-01','HIPOTESIS',None,'Fecha en blanco; el detalle FIL 17 sugiere gestión 2017. Se usa 01-01-2017 solo como fecha técnica, sin certificar día ni mes.'),
 10314:('2005-08-17','HIPOTESIS',None,'Ingreso inicial sin fecha. Se usa técnicamente el inicio del tramo atribuido a agosto, sin acreditar el día del ingreso.'),
 10315:('2005-08-17','HIPOTESIS',None,'Mes de lectura 8/9 en la foto. Se usa agosto por contexto con la fila 26-08-05; no se certifica la lectura del mes.'),
 10316:('2005-08-21','HIPOTESIS',None,'Mes de lectura 8/9 en la foto. Se usa agosto por contexto con la fila 26-08-05; no se certifica la lectura del mes.'),
 **{id:('2005-10-15','HIPOTESIS',None,'Fecha en blanco: consulta con la del antecedente legible de octubre de 2005.') for id in range(10319,10323)},
 **{id:('2006-08-01','HIPOTESIS',None,'El ingreso solo indica 08-06 (mes y año); el resto de estas filas no tiene fecha. Se usa técnicamente el primer día de agosto, sin certificar el día.') for id in range(10323,10329)},
 10329:('2006-09-01','HIPOTESIS',None,'Solo se escribe 09-06, mes y año. Fecha técnica 01-09-2006; no es el 9 de junio confirmado.'),
 10333:('2007-04-25','SECUENCIA_AJUSTADA','2007-11-29','29-11-07 dentro del tramo de abril a junio: se conserva la literal y se utiliza técnicamente la del antecedente.'),
 10335:('2007-06-15','HIPOTESIS',None,'Fecha ausente de devolución; se usa para consulta la del antecedente.'),
 10373:('2016-12-08','HIPOTESIS',None,'La fila FIL no tiene fecha; se usa para consulta la del antecedente, sin confirmarla.'),
 **{id:('2006-10-06','HIPOTESIS',None,'Las seis primeras filas no tienen fecha. Se usa técnicamente la primera fecha legible, 06-10-2006, sin acreditar el día de cada operación.') for id in range(10464,10470)},
 10473:('2007-04-25','SECUENCIA_AJUSTADA','2006-11-29','29-11-06 después de abril de 2007; lectura literal conservada y consulta técnica del antecedente.'),
 10475:('2007-06-15','HIPOTESIS',None,'Fecha ausente de la devolución; se utiliza técnicamente la del antecedente.'),
 10481:('2007-10-17','HIPOTESIS',None,'Fecha en blanco de la devolución Potosí; fecha técnica del antecedente.'),
 10482:('2009-07-17','HIPOTESIS',None,'Lectura parcial 25-?-09 con mes tapado y año no completamente limpio. Se usa la siguiente fecha legible, 17-07-2009; no se confirma el 25-08-2008 extraído.'),
 10504:('2012-10-04','HIPOTESIS',None,'Año repasado, lectura 4-10-11/12. Se usa técnicamente 2012, entre 2011 y 2013, sin certificar el año escrito.'),
 10509:('2016-12-08','HIPOTESIS',None,'Fecha ausente de FIL; fecha técnica del antecedente.'),
}
PARES=[(8642,8643),(8647,8648),(8650,8651),(10360,10361),(10501,10502)]
DETALLES={10316:'FERIA DEL LIBRO',10317:'FERIA DEL LIBRO',
          10325:'Para la Venta Feria',10326:'Para la Venta Feria',10327:'Para la Venta Feria',
          8608:'Donacion UPEA',8609:'Donacion U. Tecnica'}
PARCIALES={8592:'26-6',8593:'6-10',8594:'11-10',8595:'14-09',8596:'15-12',
           10315:'17-8/9-05',10316:'21-8/9-05',10323:'08-06, mes y año',10329:'09-06, mes y año',10482:'25-?-09, mes tapado',10504:'4-10-11/12, año repasado'}


def generar():
    rows={r['id']:r for aid in (187,302,306) for r in json.loads((ANTES/f'articulo_{aid}_antes.json').read_text(encoding='utf-8'))}
    ids=[s+i for s,q,_ in HOJAS for i in range(len(q))]
    assert len(rows)==len(ids)==180 and all(not r['revision_documental'] for r in rows.values())
    literales={id:r['fecha_movimiento'] for id,r in rows.items()};literales.update(FECHAS_FOTO)
    fechas=dict(TECNICAS)
    for grupo in PARES:
        for id,nueva in zip(grupo,sorted(literales[id] for id in grupo)):
            if nueva!=literales[id]:
                fechas[id]=(nueva,'SECUENCIA_AJUSTADA',literales[id],
                    'Fechas vecinas permutadas según T10/T11 tras cotejar cantidades. Se mantiene la fecha escrita y no se acredita el día real del hecho.')
    calc={187:7,302:0,306:0};revisiones=[];hashes={}
    with SessionLocal() as db:
        for start,qs,saldos in HOJAS:
            assert len(qs)==len(saldos)
            for offset,(q,escrito) in enumerate(zip(qs,saldos)):
                id=start+offset;r=rows[id];aid=r['articulo_id'];calc[aid]+=q;esperado=calc[aid]
                assert escrito is None or escrito==esperado,(id,escrito,esperado)
                tipos={'T01'};hallazgos=['HOJA_COMPLETA_COTEJADA']
                cambios={'ingresos':q if q>0 else None,'salidas':-q if q<0 else None,'saldo_registrado':esperado}
                rev={'criterios':[],'motivo':'Hoja completa cotejada con la fotografía y las filas vecinas. Se conserva la extracción original y se distingue el saldo escrito del de consulta.',
                    'tipo_fila':'MOVIMIENTO','saldo_documental':escrito,'origen_saldo':'HIPOTESIS' if escrito is None else 'FOTO',
                    'usar_saldo_esperado':True,'reconstruir_cadena':True,'cotejo_pagina_completa':True,
                    'origen_fecha':'FOTO','fecha_documental':literales[id]}
                if id==8592:
                    tipos.update(['T15','T22']);rev.update(tipo_fila='BASE_DOCUMENTAL',saldo_base=7,origen_saldo_base='DOCUMENTO')
                    rev['motivo']+=' Saldo según inventario 7: base documental; no se inventa un ingreso de 7.'
                if id in (10314,10464):
                    tipos.add('T22');rev.update(saldo_base=0,origen_saldo_base='HIPOTESIS',
                        motivo_base='Base cero inferida de igualdad del primer ingreso y saldo; no acredita existencia física previa.')
                if escrito is None:
                    tipos.add('T08');hallazgos.append('SALDO_EN_BLANCO_RECONSTRUIDO')
                    rev['motivo']+=' Saldo escrito en blanco: se rellena como hipótesis por continuidad y se excluye del entrenamiento.'
                if id in DETALLES:
                    cambios['detalle']=DETALLES[id];tipos.add('T18');hallazgos.append('REPETICION_DE_LA_MISMA_COLUMNA_EXPANDIDA')
                if id in (10319,10320):
                    cambios.update(referencia=None,area='Cedoal');tipos.add('T23')
                    hallazgos.append('AREA_LEIDA_COMO_REFERENCIA_CORREGIDA')
                if id==10321:
                    cambios.update(area='Cedoal');tipos.update(['T18','T23'])
                    rev['motivo']+=' El 1 está en INGRESOS; la comilla de ÁREA repite Cedoal. Se conserva el 6 a lápiz junto al saldo 7 y el 5 marginal de la fila siguiente; no justifican contar otra operación.'
                    rev['anotacion_margen']='6 a lápiz junto al saldo 7; 5 junto al siguiente. Su intención no queda acreditada.'
                    hallazgos.append('ANOTACION_MARGINAL_CONSERVADA_PARA_REVISION')
                if id==10503:
                    cambios['area']='CEDOAL';tipos.add('T18')
                    rev['motivo']+=' La comilla está en ÁREA y repite CEDOAL, no es un área llamada 1.'
                if id==10367:
                    tipos.add('T03');rev['origen_cantidades']='INTERPRETACION_HUMANA'
                    rev['marcas_documentales']={'ingresos':2,'salidas':'cifra repasada o anulada'}
                    rev['motivo']+=' De 2 a 4 con ingreso 2: la marca de SALIDAS no se cuenta como otra operación.'
                if id in (10372,10508):
                    rev['motivo']+=' Aunque el detalle dice devolución, la cantidad está en SALIDAS y el saldo disminuye exactamente en esa cantidad; se conserva la dirección documentada.'
                if (r['ingresos'] or 0)!=(cambios['ingresos'] or 0) or (r['salidas'] or 0)!=(cambios['salidas'] or 0):
                    tipos.add('T23');hallazgos.append('CANTIDAD_O_COLUMNA_CORREGIDA')
                if id in FECHAS_FOTO:cambios['fecha_movimiento']=FECHAS_FOTO[id]
                if id in fechas:
                    nueva,origen,literal,motivo=fechas[id];cambios['fecha_movimiento']=nueva
                    rev.update(origen_fecha=origen,fecha_documental=literal,motivo_fecha=motivo)
                    tipos.add('T09' if origen=='HIPOTESIS' else 'T11');hallazgos.append('FECHA_TECNICA_NO_CONFIRMADA')
                if id in PARCIALES:rev['lectura_fecha_parcial']=PARCIALES[id]
                if id in (10337,10477):
                    tipos.add('T18');rev['motivo_fecha']='La comilla de FECHA repite el 08-08-2007 legible de la fila anterior.'
                if id in (8602,8603,8604):
                    tipos.add('T16');rev['anotacion_respaldo']='Notas adheridas: 1 libro para carrera de Artes 12-11-07, 1 para Psicología 12-11-07 y 1 donación C. de Agua 13-11-07. Corresponden a las filas ya registradas; no se vuelven a contar.'
                if id==8601:
                    tipos.add('T16');rev['anotacion_margen']='12 a lápiz junto al tramo que termina en 12 tras las tres salidas siguientes; se conserva sin adelantar su efecto.'
                # Recalificar solo si cambió un insumo documental. El catálogo
                # existente puede resolver un alias ya reconocido, sin crearlo.
                if any(cambios.get(k,r[k])!=r[k] for k in ('ingresos','salidas','area','referencia','detalle')):
                    clas=clasificar_movimiento(cambios.get('detalle',r['detalle']),cambios.get('referencia',r['referencia']),cambios.get('area',r['area']),cambios['ingresos'],cambios['salidas'],db)
                    derivados={k:getattr(clas,k) for k in ('nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia')}
                    if q>0 and derivados['nodo_grafo'].startswith('Salida:'):
                        area=cambios.get('area',r['area'])
                        nodo,estado,pendiente=(_resolver_area_con_catalogo(area,db) if area else ('Origen no especificado','SIN_AREA_REGISTRADA',False))
                        derivados.update(nodo_grafo=nodo,area_estado=estado,requiere_auditoria_nodo=pendiente)
                    cambios.update(derivados)
                rev['criterios']=sorted(tipos);rev['hallazgos']=hallazgos
                foto=(BACKEND/r['ruta_imagen_respaldo']).resolve()
                hashes.setdefault(str(foto),hashlib.sha256(foto.read_bytes()).hexdigest())
                revisiones.append({'id':id,'articulo_id':aid,'pagina':f"L{r['lote_id']:04d}-P{r['numero_pagina']:02d}",
                    'esperado':{k:r[k] for k in CAMPOS_BASE},
                    'esperado_adicional':{k:r[k] for k in ('nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia')},
                    'cambios':cambios,'revision':rev,'fuente':str(foto),'sha256_imagen':hashes[str(foto)]})
    assert calc=={187:10,302:8,306:9} and len(hashes)==8
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    return {'version':8,'criterio_sha256':digest(policy),'revisiones':revisiones,
        'observaciones_articulos':[{'articulo_id':aid,'observado':True,'excluir_entrenamiento':False,
            'motivo':f'Ocho fotos del bloque Taller 3 / Bolivia Ecológica 37 y 41 cotejadas. Cierre de este artículo {saldo}. Se conservan fechas técnicas, saldos hipotéticos y anotaciones marginales; áreas y referencias no normalizadas siguen pendientes de su revisión específica.'} for aid,saldo in calc.items()],
        'cotejo':{'fotografias':8,'movimientos':180,'cierres':calc},'sin_reasociaciones_ni_borrados':True,
        'limites':['Las fechas y bases hipotéticas no certifican gestiones o conteos físicos.','No se crean áreas ni alias ni se fusionan artículos.','La anotación marginal 6/7 de Bolivia Ecológica 37 se conserva sin resolver su intención.','No se crean movimientos a partir de notas que ya respaldan filas existentes.']}


if __name__=='__main__':
    path=DEST/'plan_continuacion_08.json'
    if path.exists():raise RuntimeError('Conservar el plan existente; nuevas decisiones requieren otro lote.')
    plan=generar();path.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'plan':str(path),'sha256':digest(plan),'cotejo':plan['cotejo']},ensure_ascii=False))
