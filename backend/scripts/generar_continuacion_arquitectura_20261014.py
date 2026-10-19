"""Cotejo de diez fotos de Arquitectura, con orden validado y fuentes intactas.

Las matrices son transcripciones visuales concretas, no correcciones obtenidas
por diferencias aritméticas ni por similitud de artículos.
"""
import hashlib
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex
from app.services.revision_documental import snapshot_revision
from app.services.clasificador_nodos import clasificar_movimiento, _resolver_area_con_catalogo
from scripts.generar_plan_revision_hil import CAMPOS_BASE, DEST, digest

BACKEND = Path(__file__).resolve().parents[1]
# Primer ID, orden validado dentro del lote, efecto, saldo escrito.
# La quinta foto del primer lote antecede a las otras cuatro.
HOJAS = [
 (5798,1,[0,-10,-3,-10,-1,-2,-1,-1,-1,-3,-3,-10,-70,-1,-1,-5,-1,-10,484,-5,-5,-5,8,-1,-75],
  [286,None,None,263,None,None,None,258,None,None,None,None,None,None,None,None,None,153,637,None,None,622,630,None,554]),
 (5695,2,[0,-3,1,-1,-2,-3,-3,-1,-1,-3,1,-2,-1,-1,-1,-2,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],
  [554,551,552,551,549,546,543,542,541,538,539,537,536,535,534,532,531,530,529,528,529,528,527,526,525,524]),
 (5721,3,[-1,-1,-3,-1,-10,-20,1,-3,-1,8,-5,-2,-2,-1,-5,-1,-10,-2,-2,-1,2,0,-1,-1,-5,-140],
  [523,522,519,518,508,None,None,None,485,493,488,486,484,483,478,477,467,465,463,462,None,None,461,460,455,315]),
 (5747,4,[1,-5,-1,-1,-2,-1,-3,-1,-1,-1,-1,-7,1,-1,-5,2,-2,-3,-5,-1,-10,-1,-1,-1,-8],
  [316,311,310,309,307,306,303,302,None,None,299,292,293,292,287,289,287,284,279,278,268,267,266,265,257]),
 (5772,5,[-2,-5,-10,-5,13,-3,-1,-6,-3,-1,3,-2,-3,-15,-1,-5,-18,-1,-1,-1,-3,-1,3,-1,-5,-10],
  [255,250,240,235,248,245,244,238,235,234,237,235,232,217,216,211,193,192,191,190,187,186,189,188,175,165]),
 (5823,1,[5,1,-1,-3,-1,-1,-3,-1,-10,-1,1,-1,-1,-1,-1,1,-10,6,-1,-1,-1,-1,-5,-1,-1,-5],
  [170,171,170,167,166,173,170,169,159,158,159,158,157,156,155,156,146,152,151,150,149,148,143,142,141,136]),
 (5849,2,[2,-1,-1,-10,-3,-1,4,-2,-2,1,-1,-3,-5,4,-5,1,2,-2,-1,-1,1,-1,-1,-6,-3,-3],
  [138,137,136,126,123,122,126,124,122,123,122,119,114,118,113,114,116,114,113,112,113,112,111,105,102,99]),
 (5875,3,[4,-1,-5,-1,-1,5,-1,-1,-10,-1,7,-1,1,-3,-3,-1,-2,-14,2,-1,-1,-1,-1,1,-2,-2],
  [103,102,97,96,95,100,99,98,88,87,94,93,94,91,88,87,85,71,73,72,71,70,69,70,68,66]),
 (5901,4,[-2,-1,-3,-3,-1,-1,-1,-8,-5,3,-2,-2,1,-1,-2,-1,-2,-1,-1,-2,-1,-5,-9,-1,-6,-3],
  [64,63,60,57,56,55,54,46,41,44,42,40,41,40,38,37,35,34,33,31,30,25,16,15,9,6]),
 (5927,5,[-2,-2,1,-1,-1,2,-1,1,-2],[4,2,3,2,1,3,2,3,1]),
]

# Únicamente lecturas de fecha cotejadas que difieren de la extracción.
FECHAS_FOTO = {5711:'2007-03-24',5755:'2008-06-19',5890:'2014-07-01',5892:'2014-07-24'}
# Fecha técnica, origen, fecha documental si es legible, motivo.
TECNICAS = {
 5803:('2005-09-30','SECUENCIA_AJUSTADA','2006-05-25','El papel dice 25-05-06 entre septiembre y octubre de 2005; fecha técnica del antecedente, sin certificar año del hecho.'),
 5804:('2005-09-30','SECUENCIA_AJUSTADA','2005-09-22','Fecha escrita anterior al antecedente. Se conserva la literal y se usa técnicamente la fecha previa para consulta.'),
 5808:('2005-12-12','SECUENCIA_AJUSTADA','2005-09-30','30-09-05 después de diciembre: ajuste de consulta, sin cambiar el texto original.'),
 5809:('2005-12-12','HIPOTESIS',None,'Fecha parcial, lectura 04-09?, sin año; no se convierte en un día confirmado. Se usa la del antecedente para consulta.'),
 5810:('2005-12-12','HIPOTESIS',None,'Fecha en blanco; fecha técnica del antecedente, sin acreditar el día del envío.'),
 5811:('2005-12-12','SECUENCIA_AJUSTADA','2005-11-29','29-11-05 después de diciembre; se preserva la fecha escrita y se ajusta solamente la consulta.'),
 5818:('2006-08-18','HIPOTESIS',None,'Fecha en blanco en otra fila de Feria del Libro; fecha técnica del antecedente.'),
 5819:('2006-08-18','HIPOTESIS',None,'Fecha en blanco en otra fila de Feria del Libro; fecha técnica del antecedente.'),
 5822:('2006-09-20','HIPOTESIS',None,'La terminación del año está repasada y parece 09/06. Fecha técnica 20-09-2006 por el antecedente y la hoja siguiente; no se confirma el año escrito.'),
 5695:('2006-09-20','HIPOTESIS',None,'Saldo trasladado sin fecha escrita; se usa técnicamente la fecha del cierre de la hoja anterior, ahora ordenada.'),
 5698:('2006-11-29','SECUENCIA_AJUSTADA','2006-09-14','14-09-06 después de 29-11-06. Ajuste de consulta autorizado; lectura literal conservada.'),
 5699:('2006-11-29','SECUENCIA_AJUSTADA','2006-05-25','25-05-06 después de noviembre; se conserva el papel y se ajusta solo la fecha de consulta.'),
 5737:('2007-10-24','SECUENCIA_AJUSTADA','2007-08-31','31-08-07 tras octubre; el OCR además leyó día 01. Se conserva el 31 legible y se marca la fecha técnica.'),
 5738:('2007-10-24','SECUENCIA_AJUSTADA','2007-04-19','Fecha escrita de abril dentro del tramo de octubre; se conserva y se usa fecha técnica del antecedente.'),
 5739:('2007-10-24','SECUENCIA_AJUSTADA','2007-03-09','Fecha escrita de marzo después de octubre; ajuste técnico, no fecha confirmada.'),
 5740:('2007-10-24','SECUENCIA_AJUSTADA','2007-03-13','Fecha escrita de marzo después de octubre; ajuste técnico, no fecha confirmada.'),
 5741:('2007-10-24','SECUENCIA_AJUSTADA','2007-02-18','Fecha escrita de febrero después de octubre; ajuste técnico de consulta.'),
 5746:('2007-11-27','SECUENCIA_AJUSTADA','2007-08-03','03-08-07 después de 27-11-07. Se conserva esa fecha, sin inventar un ingreso o reordenar cantidades.'),
 5747:('2007-11-27','SECUENCIA_AJUSTADA','2007-11-05','05-11-07 anterior al cierre de la hoja precedente; se conserva literal y se usa la fecha técnica previa.'),
 5756:('2008-06-19','HIPOTESIS',None,'Fecha en blanco junto a Donación Carcamo; se usa la del antecedente sin certificar el día.'),
 5757:('2008-06-19','HIPOTESIS',None,'Fecha en blanco junto a UPEA; se usa la del antecedente sin certificar el día.'),
 5758:('2008-06-19','SECUENCIA_AJUSTADA','2008-03-18','18-03-08 después de 19-06-08; fecha técnica del antecedente.'),
 5759:('2008-06-19','SECUENCIA_AJUSTADA','2008-03-13','13-03-08 después de junio; se preserva la literal y se utiliza la fecha técnica previa.'),
 5826:('2010-11-13','HIPOTESIS',None,'Día repasado, lectura 13/18-11-10. Se mantiene técnicamente 13-11-10 entre octubre y 23 de noviembre, sin confirmar el día.'),
 5858:('2012-07-05','HIPOTESIS',None,'Fecha ausente de la devolución FL POTOSÍ; se utiliza para consulta la del antecedente.'),
 5869:('2013-03-28','SECUENCIA_AJUSTADA','2013-08-15','El papel dice 15-8-13 dentro del tramo de marzo a mayo; se usa técnicamente la fecha de la fila siguiente y se conserva la literal.'),
}
PARES = [(5763,5764),(5830,5831),(5850,5851),(5859,5860,5861),(5889,5890),(5891,5892),(5893,5894),(5904,5905),(5914,5915)]


def generar():
    policy = json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    ids = [start+i for start,_,qs,_ in HOJAS for i in range(len(qs))]
    with SessionLocal() as db:
        rows = {m.id:snapshot_revision(m) for m in db.query(MovimientoKardex).filter(MovimientoKardex.id.in_(ids)).all()}
        assert len(rows) == len(ids) == 241
        assert all(r['articulo_id']==88 and not r['revision_documental'] for r in rows.values())
        literales = {id:r['fecha_movimiento'] for id,r in rows.items()}
        literales.update(FECHAS_FOTO)
        fechas = dict(TECNICAS)
        for par in PARES:
            for id,nueva in zip(par,sorted(literales[id] for id in par)):
                if nueva != literales[id]:
                    fechas[id]=(nueva,'SECUENCIA_AJUSTADA',literales[id],
                        'Fechas vecinas permutadas para consulta según T10/T11, con cantidades cotejadas y fecha escrita conservada. No acredita el día real del hecho.')
        revisiones=[];saldo=286;papel=286;errores=[];hashes={}
        for start,orden,qs,saldos in HOJAS:
            assert len(qs)==len(saldos)
            for offset,(q,escrito) in enumerate(zip(qs,saldos)):
                id=start+offset;r=rows[id];saldo+=q
                tipos={'T01'};hallazgos=['HOJA_COMPLETA_COTEJADA']
                cambios={'ingresos':q if q>0 else None,'salidas':-q if q<0 else None,'saldo_registrado':saldo}
                rev={'criterios':[],'motivo':'Cotejo visual de la hoja completa y las filas vecinas. Se distingue el dato escrito del saldo de consulta reconstruido.',
                     'tipo_fila':'MOVIMIENTO','saldo_documental':escrito,
                     'origen_saldo':'HIPOTESIS' if escrito is None else ('FOTO' if escrito==saldo else 'RECONSTRUIDO'),
                     'usar_saldo_esperado':True,'reconstruir_cadena':True,'cotejo_pagina_completa':True,
                     'fecha_documental':literales[id],'origen_fecha':'FOTO'}
                if r['lote_id']==rows[5798]['lote_id']:
                    cambios['orden_pagina_validado']=orden;tipos.add('T12')
                    hallazgos.append('ORDEN_DE_HOJAS_VALIDADO_SIN_RENUMERAR_FOTOS')
                if id==5798:
                    rev.update(tipo_fila='BASE_DOCUMENTAL',saldo_base=286,origen_saldo_base='DOCUMENTO')
                    tipos.update(['T15','T22'])
                    rev['motivo']+=' Saldo según inventario 286: base documental, sin inventar un ingreso.'
                if id==5695:
                    rev['motivo']+=' El saldo 554 traslada exactamente el cierre de la hoja anterior; no constituye otro ingreso ni un nuevo conteo.'
                if id==5742:
                    # Se conserva el registro y su lectura OCR de la cantidad
                    # tachada; la anulación excluye su efecto, no borra la fila.
                    cambios={'estado':'ANULADO_DOCUMENTO','orden_pagina_validado':orden}
                    rev.update(tipo_fila='ANULADO',usar_saldo_esperado=False,origen_saldo='NO_APLICA',
                        marcas_documentales={'area':'Co. Duplicado','cantidad':'tachada, sin lectura confirmada'},
                        motivo='Cantidad tachada y anotación Co. Duplicado: registro anulado en el papel. Se conserva la extracción completa y la foto, sin efecto en la cadena vigente.')
                    tipos.update(['T14','T21']);hallazgos.append('DUPLICADO_EXPRESAMENTE_ANULADO_EN_PAPEL')
                else:
                    if escrito is None:
                        tipos.add('T08');hallazgos.append('SALDO_EN_BLANCO_O_TENUE_RECONSTRUIDO')
                        rev['motivo']+=' Saldo vacío o demasiado tenue: valor de consulta hipotético por continuidad, excluido del entrenamiento.'
                    else:
                        diferencia_local=escrito-(papel+q)
                        rev['diferencia_local_papel']=diferencia_local
                        if diferencia_local:
                            errores.append({'id':id,'diferencia_local_papel':diferencia_local,'diferencia_con_cadena':escrito-saldo})
                            tipos.add('T05');hallazgos.append('DESCUADRE_DEL_PAPEL_CONSERVADO')
                        papel=escrito
                    if escrito is None:papel+=q
                    if escrito is not None and escrito!=saldo:
                        hallazgos.append('SALDO_VIGENTE_RECONSTRUIDO')
                    if (r['ingresos'] or 0)!=(cambios.get('ingresos') or 0) or (r['salidas'] or 0)!=(cambios.get('salidas') or 0):
                        tipos.add('T23');hallazgos.append('LECTURA_CANTIDAD_O_COLUMNA_CORREGIDA')
                        clas=clasificar_movimiento(r['detalle'],r['referencia'],r['area'],cambios['ingresos'],cambios['salidas'],db)
                        derivados={k:getattr(clas,k) for k in ('nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia')}
                        if q>0 and derivados['nodo_grafo'].startswith('Salida:'):
                            nodo,estado,pendiente=(_resolver_area_con_catalogo(r['area'],db) if r['area'] else ('Origen no especificado','SIN_AREA_REGISTRADA',False))
                            derivados.update(nodo_grafo=nodo,area_estado=estado,requiere_auditoria_nodo=pendiente)
                        cambios.update(derivados)
                if id in FECHAS_FOTO:cambios['fecha_movimiento']=FECHAS_FOTO[id]
                if id in fechas:
                    nueva,origen,literal,motivo=fechas[id]
                    cambios['fecha_movimiento']=nueva
                    rev.update(origen_fecha=origen,fecha_documental=literal,motivo_fecha=motivo)
                    tipos.add('T09' if origen=='HIPOTESIS' else 'T11');hallazgos.append('FECHA_TECNICA_NO_CONFIRMADA')
                if id==5809:rev['lectura_fecha_parcial']='04-09?, año ausente'
                if id in (5833,5934):
                    tipos.add('T07');rev['origen_cantidades']='INTERPRETACION_HUMANA'
                    rev['marcas_documentales']={'salidas':1,'referencia':r['referencia']}
                    rev['motivo']+=' El papel usa SALIDAS, pero DEV y el aumento de saldo indican devolución: se interpreta como ingreso 1, conservando el error de columna.'
                if id==5932:
                    tipos.add('T03');rev['origen_cantidades']='INTERPRETACION_HUMANA'
                    rev['marcas_documentales']={'ingresos':2,'salidas':'4 o cifra repasada','saldo':'3 precedido de marca oscura'}
                    rev['motivo']+=' Ingreso 2: de 1 a 3. La cifra de SALIDAS no se cuenta como una segunda operación, según T03.'
                if id in (5796,5797):
                    tipos.add('T04');rev['saldo_documental_rectificado']=183 if id==5796 else 173
                    rev['anotacion_margen']='Rectificación a lápiz del saldo: '+str(rev['saldo_documental_rectificado'])
                    rev['motivo']+=' La anotación a lápiz recoge el saldo aritmético; se conservan tanto el saldo de tinta como la rectificación.'
                if id==5828:
                    tipos.add('T04');rev['motivo']+=' El saldo escrito 173 recupera la diferencia de 8 que venía de la hoja anterior; no se inventa una operación de ajuste.'
                    hallazgos.append('CONTINUIDAD_RECUPERADA_EN_EL_PAPEL')
                if id in (5715,5743):
                    rev['motivo']+=' Se conserva el desajuste escrito de la fuente y se continúa con el esperado independiente.'
                if id==5747:
                    rev['anotacion_margen']='Firma y fecha 18/12/07 junto al tramo de 316/311; no se interpreta como otro movimiento.'
                    rev['encabezado_documental']='Arquitecturas hoy en Bolivia CD'
                rev['criterios']=sorted(tipos);rev['hallazgos']=hallazgos
                foto=(BACKEND/r['ruta_imagen_respaldo']).resolve()
                hashes.setdefault(str(foto),hashlib.sha256(foto.read_bytes()).hexdigest())
                revisiones.append({'id':id,'articulo_id':88,'pagina':f"L{r['lote_id']:04d}-P{r['numero_pagina']:02d}",
                    'esperado':{k:r[k] for k in CAMPOS_BASE},
                    'esperado_adicional':{k:r[k] for k in ('nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia','orden_pagina_validado')},
                    'cambios':cambios,'revision':rev,'fuente':str(foto),'sha256_imagen':hashes[str(foto)]})
        assert saldo==1, saldo
        assert len(hashes)==10
    return {'version':7,'criterio_sha256':digest(policy),'revisiones':revisiones,
            'observaciones_articulos':[{'articulo_id':88,'observado':True,'excluir_entrenamiento':False,
                'motivo':'Diez fotos cotejadas: orden P05→P01→P02→P03→P04 del primer lote, sin cambiar números de foto; cierre reconstruido y escrito 1. Se conservan desajustes del papel que luego se compensan, una fila expresamente anulada, saldos hipotéticos y fechas técnicas. Áreas y referencias pendientes no se certifican por este cotejo.'}],
            'sin_reasociaciones_ni_borrados':True,
            'cotejo':{'fotografias':10,'movimientos':241,'cierre_reconstruido':1,'cierre_documental':1,'incidencias_locales_papel':errores},
            'limites':['No certifica existencias físicas actuales.','Las hipótesis y fechas técnicas quedan excluidas del entrenamiento.','Se conserva la cantidad tachada de la fila anulada como lectura OCR, sin validarla.','No normaliza nombres de áreas ni modifica títulos o agrupación de artículos.']}


if __name__=='__main__':
    path=DEST/'plan_continuacion_07.json'
    if path.exists():raise RuntimeError('El plan ya existe: conservarlo y crear otro lote para nuevas decisiones.')
    plan=generar();path.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'plan':str(path),'filas':len(plan['revisiones']),'sha256':digest(plan),'cotejo':plan['cotejo']},ensure_ascii=False))
