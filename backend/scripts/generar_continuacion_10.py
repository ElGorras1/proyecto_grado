"""Nueve fotografías cotejadas: Dibujo y Artes Gráficas y CD Jornadas."""
import hashlib,json
from copy import deepcopy
from pathlib import Path
from app.db.session import SessionLocal
from app.services.clasificador_nodos import clasificar_movimiento,_resolver_area_con_catalogo
from scripts.generar_plan_revision_hil import CAMPOS_BASE,DEST,digest

BACKEND=Path(__file__).resolve().parents[1];ANTES=BACKEND/'backups/continuacion_hil_09_20261014'
HOJAS=[
 (["inventario",*range(6063,6068),"utecnica",*range(6068,6087)],
  [0,-3,-1,-1,-1,-1,-1,-1,-3,-5,-5,6,-1,-1,-1,-8,-2,-5,-10,-5,16,-3,-2,-15,-2,-2],
  [283,280,279,278,None,None,275,274,271,266,261,267,266,265,264,256,254,249,239,234,250,247,245,230,228,226]),
 (list(range(6087,6113)),[-3,-1,3,-1,-5,1,-3,1,-1,-3,-1,-2,-1,-1,-1,-10,9,-1,-1,-1,-3,-1,-1,-2,-5,-5],
  [223,222,225,224,219,220,217,218,217,214,213,211,210,209,208,198,207,206,205,204,201,200,199,197,192,187]),
 (list(range(6113,6139)),[-10,12,5,-5,1,3,-3,3,-1,1,-3,2,-5,-1,1,-10,-1,8,-1,5,-3,-2,-2,-2,1,-1],
  [177,187,192,187,188,191,188,191,190,191,188,190,185,184,185,175,174,182,181,186,183,181,179,177,178,177]),
 (list(range(6139,6165)),[1,-1,-1,-3,-5,-8,2,0,0,-1,-1,-3,-1,-6,-1,-2,-1,-1,-5,-1,-2,-6,-2,-3,-1,-1],
  [178,177,176,173,168,160,162,159,162,161,160,157,156,150,149,147,146,145,140,139,137,131,129,126,125,124]),
 (list(range(6165,6172)),[3,-1,-1,2,3,-1,-2],[127,126,125,127,130,129,127]),
 (list(range(1160,1186)),[113,-1,-3,-1,-1,-1,-3,1,-1,-1,-1,-1,-7,-1,-2,-5,4,-5,-5,-1,-1,-1,-8,-1,-5,5],
  [113,112,109,108,107,106,103,104,103,None,None,100,93,92,90,85,89,84,79,78,77,76,68,67,62,67]),
 (list(range(1236,1262)),[-1,-1,-1,-1,-5,-1,-1,-1,-1,5,-3,-1,-3,-1,3,-1,-10,9,1,-1,-3,-1,-1,1,-1,-2],
  [66,65,64,63,58,57,56,55,54,59,56,55,52,51,54,53,43,52,53,52,49,48,47,48,47,45]),
 (list(range(1210,1236)),[2,-10,9,-1,-1,-1,-3,-1,1,-1,-1,1,-5,5,-5,1,2,-1,5,-1,1,-1,-1,-6,-3,3],
  [47,37,46,45,44,43,40,39,40,39,38,39,34,39,34,35,37,36,41,40,41,40,39,33,30,33]),
 (list(range(1186,1210)),[-5,-1,5,-5,-1,5,-3,-1,-2,-2,2,-2,-1,3,-2,-1,-1,-1,-1,-1,-1,-2,2,1],
  [28,27,32,27,26,31,28,27,25,23,25,23,22,25,23,22,21,20,19,18,17,15,17,18]),
]
FECHAS_FOTO={6122:'2013-03-05',1193:'2014-06-09',1194:'2014-07-05'}
TECNICAS={
 **{id:('2008-05-19','HIPOTESIS',None,'Fecha ausente; contexto del 19-05-2008 de Donación Caranavi. No se confirma el día de la salida.') for id in (6067,)},
 6162:('2017-04-20','HIPOTESIS',None,'Fecha en blanco de FIL: consulta con la del antecedente, sin acreditar el día.'),
 **{id:('2008-05-19','HIPOTESIS',None,'Fecha en blanco en la fila de donación; fecha técnica del antecedente.') for id in (1170,1171)},
 1172:('2008-05-19','SECUENCIA_AJUSTADA','2008-03-18','18-03-08 después de mayo; fecha técnica del antecedente y literal conservada.'),
 1192:('2013-11-04','HIPOTESIS',None,'Fecha ausente de FIL Santa Cruz; fecha técnica del antecedente.'),
 1203:('2015-12-08','SECUENCIA_AJUSTADA','2015-07-07','07-07-15 después de diciembre; fecha literal conservada y consulta ajustada.'),
 1230:('2013-03-28','SECUENCIA_AJUSTADA','2013-08-15','15-8-13 escrito entre marzo y mayo; fecha técnica de la fila siguiente, sin acreditar el día del hecho.'),
}
PARES=[(6135,6136),(1210,1211),(1206,1207)]


def generar():
    rows={r['id']:r for aid in (91,28) for r in json.loads((ANTES/f'articulo_{aid}_antes.json').read_text(encoding='utf-8'))}
    assert len(rows)==211 and all(not r['revision_documental'] for r in rows.values())
    literal={id:r['fecha_movimiento'] for id,r in rows.items()};literal.update(FECHAS_FOTO)
    fechas=dict(TECNICAS)
    for par in PARES:
        for id,nueva in zip(par,sorted(literal[id] for id in par)):
            if nueva!=literal[id]:fechas[id]=(nueva,'SECUENCIA_AJUSTADA',literal[id],'Fechas vecinas permutadas según T10/T11 tras cotejar cantidades, con fecha escrita conservada.')
    calc={91:283,28:0};papel=dict(calc);revisiones=[];recuperaciones=[];hashes={};errores=[]
    with SessionLocal() as db:
        for ids,qs,saldos in HOJAS:
            assert len(ids)==len(qs)==len(saldos)
            for pos,(id,q,written) in enumerate(zip(ids,qs,saldos),1):
                if isinstance(id,str):
                    r=rows[6063];aid=91;calc[aid]+=q
                    foto=(BACKEND/r['ruta_imagen_respaldo']).resolve();h=hashlib.sha256(foto.read_bytes()).hexdigest()
                    fecha='2007-12-11' if id=='inventario' else '2008-05-19'
                    detalle='Saldo segun inventario' if id=='inventario' else 'Donacion U. Tecnica'
                    rev={'criterios':['T08','T09','T23'],'motivo':'Fila visible omitida por la extracción: recuperación de evidencia desde la foto existente, sin atribuirla al OCR original.',
                        'origen_fecha':'HIPOTESIS','fecha_documental':None,'motivo_fecha':'La fila no tiene fecha; se asigna la del contexto inmediato solo para consulta.',
                        'saldo_documental':written,'origen_saldo':'FOTO','tipo_fila':'BASE_DOCUMENTAL' if id=='inventario' else 'MOVIMIENTO',
                        'usar_saldo_esperado':True,'reconstruir_cadena':True,'cotejo_pagina_completa':True,'hallazgos':['FILA_OMITIDA_RECUPERADA_DESDE_FOTO']}
                    if id=='inventario':rev.update(saldo_base=283,origen_saldo_base='DOCUMENTO')
                    campos={'articulo_id':91,'lote_id':r['lote_id'],'ruta_imagen_respaldo':r['ruta_imagen_respaldo'],'numero_pagina':1,'orden_fila':pos,
                        'fecha_movimiento':fecha,'fecha_original':None,'detalle':detalle,'ingresos':None,'salidas':1 if q else None,
                        'saldo_registrado':written,'saldo_calculado':written,'fecha_estado':'ESTIMADA_HIL','estado':'ACTIVO',
                        'nodo_grafo':'Destino no especificado' if q else 'Origen no especificado','area_estado':'SIN_AREA_REGISTRADA','referencia_estado':'AUSENTE',
                        'requiere_auditoria_nodo':False,'requiere_auditoria_referencia':False,
                        'datos_originales':{'fuente':'LECTURA_FOTO_HIL','fecha_documental':None,'detalle':detalle,'ingresos':None,'salidas':1 if q else None,'saldo_registrado':written,'orden_fila':pos,'no_existia_en_extraccion_ocr':True}}
                    recuperaciones.append({'clave':f'art91-lote{r["lote_id"]}-p1-fila{pos}-recuperada-v1','fuente':str(foto),'sha256_imagen':h,'campos':campos,'revision':rev})
                    hashes[str(foto)]=h;papel[aid]=written;continue
                r=rows[id];aid=r['articulo_id'];calc[aid]+=q;expected=calc[aid]
                cambios={'ingresos':q if q>0 else None,'salidas':-q if q<0 else None,'saldo_registrado':expected}
                rev={'motivo':'Foto completa cotejada con filas vecinas; se conserva el dato escrito y la extracción original.',
                    'tipo_fila':'MOVIMIENTO','saldo_documental':written,'origen_saldo':'HIPOTESIS' if written is None else ('FOTO' if written==expected else 'RECONSTRUIDO'),
                    'origen_fecha':'FOTO','fecha_documental':literal[id],'usar_saldo_esperado':True,'reconstruir_cadena':True,'cotejo_pagina_completa':True}
                tipos={'T01'};hallazgos=['HOJA_COMPLETA_COTEJADA']
                if aid==91 and r['numero_pagina']==1:cambios['orden_fila']=pos;tipos.add('T23')
                if id==6146:
                    cambios={'estado':'ANULADO_DOCUMENTO'}
                    rev.update(tipo_fila='ANULADO',origen_saldo='NO_APLICA',usar_saldo_esperado=False,motivo='GISBERT está señalado expresamente como REGISTRO EQUIVOCADO. Se conserva el renglón sin efecto en el saldo.')
                    tipos.add('T14')
                elif id==6147:
                    cambios={'estado':'NOTA_DOCUMENTAL'}
                    rev.update(tipo_fila='NOTA',origen_saldo='NO_APLICA',usar_saldo_esperado=False,movimiento_total_id=6145,
                        motivo='La fila sin cantidad vuelve al saldo 162 de la devolución anterior tras el registro equivocado. Nota de rectificación: no inventa un segundo ingreso de 3.')
                    tipos.update(['T14','T16'])
                else:
                    if written is None:
                        tipos.add('T08');rev['motivo']+=' Saldo en blanco: se representa como hipótesis por continuidad.'
                        papel[aid]+=q
                    else:
                        delta=written-(papel[aid]+q)
                        if delta:
                            tipos.add('T05');rev['diferencia_local_papel']=delta;hallazgos.append('DESCUADRE_DEL_PAPEL_CONSERVADO')
                            errores.append({'id':id,'local':delta,'acumulada':written-expected})
                        papel[aid]=written
                if aid==28 and r['lote_id']!=rows[1160]['lote_id']:
                    cambios['orden_pagina_validado']={3:1,2:2,1:3}[r['numero_pagina']];tipos.add('T12')
                if id==1160:rev.update(saldo_base=0,origen_saldo_base='HIPOTESIS',motivo_base='Base cero inferida de igualdad del primer ingreso y saldo; no acredita existencias previas.')
                if id==1185:
                    tipos.add('T03');rev.update(origen_cantidades='INTERPRETACION_HUMANA',marcas_documentales={'salidas':'(5)'})
                    rev['motivo']+=' De 62 a 67: ingreso 5. El (5) de SALIDAS se conserva como anotación, sin contar otra operación.'
                if id==6161:rev['motivo']+=' La foto muestra salida 2, no 7, en La Paz Lee.'
                if id==6114:rev['motivo']+=' El ingreso 12 está escrito, pero 177+12 da 189 y el papel dice 187. La diferencia 2 se conserva, sin cambiar la cantidad para cuadrar.'
                if id==6122:
                    cambios['area']='CEDOAL';tipos.add('T18');rev['motivo']+=' La comilla repite CEDOAL en ÁREA.'
                if id==1239:
                    cambios.update(referencia_estado='INCIERTA',requiere_auditoria_referencia=True)
                    rev['lectura_referencia_parcial']='S/ART o S/REF';rev['motivo']+=' Hay una anotación en REF de lectura incierta; no se certifica como ausente.'
                if id in FECHAS_FOTO:cambios['fecha_movimiento']=FECHAS_FOTO[id]
                if id in fechas:
                    fecha,origen,doc,motivo=fechas[id];cambios['fecha_movimiento']=fecha
                    rev.update(origen_fecha=origen,fecha_documental=doc,motivo_fecha=motivo);tipos.add('T09' if origen=='HIPOTESIS' else 'T11')
                if id not in (6146,6147) and any(cambios.get(k,r[k])!=r[k] for k in ('ingresos','salidas','area','referencia','detalle')):
                    clas=clasificar_movimiento(r['detalle'],r['referencia'],cambios.get('area',r['area']),cambios['ingresos'],cambios['salidas'],db)
                    d={k:getattr(clas,k) for k in ('nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia')}
                    if q>0 and d['nodo_grafo'].startswith('Salida:'):
                        area=cambios.get('area',r['area']);n,e,p=(_resolver_area_con_catalogo(area,db) if area else ('Origen no especificado','SIN_AREA_REGISTRADA',False))
                        d.update(nodo_grafo=n,area_estado=e,requiere_auditoria_nodo=p)
                    cambios.update(d)
                rev['criterios']=sorted(tipos);rev['hallazgos']=hallazgos
                foto=(BACKEND/r['ruta_imagen_respaldo']).resolve();hashes.setdefault(str(foto),hashlib.sha256(foto.read_bytes()).hexdigest())
                revisiones.append({'id':id,'articulo_id':aid,'pagina':f"L{r['lote_id']:04d}-P{r['numero_pagina']:02d}",
                    'esperado':{k:r[k] for k in CAMPOS_BASE},'esperado_adicional':{k:r[k] for k in ('nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia')},
                    'cambios':cambios,'revision':rev,'fuente':str(foto),'sha256_imagen':hashes[str(foto)]})
    assert calc=={91:129,28:18},calc
    assert len(hashes)==9 and len(revisiones)==211 and len(recuperaciones)==2
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    return {'version':10,'criterio_sha256':digest(policy),'revisiones':revisiones,'recuperaciones':recuperaciones,
        'observaciones_articulos':[{'articulo_id':aid,'observado':True,'excluir_entrenamiento':False,'motivo':motivo} for aid,motivo in [
            (91,'Cinco fotos cotejadas. Se recuperan dos filas omitidas de la primera foto, conservando el OCR anterior. Cierre reconstruido 129 frente a 127 escrito por un error de suma de 2 del papel. Registro equivocado y nota correctiva sin efecto.'),
            (28,'Cuatro fotos cotejadas. Segundo lote en orden P03→P02→P01; cierre disponible 18 en 2019, no el 45 de una hoja de 2011 que estaba al final por orden de carga. Hipótesis y referencia incierta conservadas.')]],
        'cotejo':{'fotografias':9,'movimientos':213,'cierres':{'91':129,'28':18},'cierres_documentales':{'91':127,'28':18},'discrepancias':errores},
        'sin_reasociaciones_ni_borrados':True,'limites':['Dos filas se recuperan desde evidencia existente; no son nuevas operaciones digitales.','Los originales preexistentes permanecen intactos.']}


if __name__=='__main__':
    path=DEST/'plan_continuacion_10.json'
    if path.exists():raise RuntimeError('El plan ya existe; conservar el cotejo congelado.')
    plan=generar();path.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'plan':str(path),'sha256':digest(json.loads(path.read_text(encoding='utf-8'))),'cotejo':plan['cotejo']},ensure_ascii=False))
