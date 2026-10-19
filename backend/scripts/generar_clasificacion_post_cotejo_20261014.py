"""Sincroniza derivados tras corregir cantidades/detalles, sin crear alias ni áreas."""
import hashlib
import json
from pathlib import Path
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex
from app.services.clasificador_nodos import clasificar_movimiento, _resolver_area_con_catalogo
from app.services.revision_documental import snapshot_revision
from scripts.generar_plan_revision_hil import CAMPOS_BASE,DEST,digest

BACKEND=Path(__file__).resolve().parents[1]


def generar():
    planes=[json.loads((DEST/n).read_text(encoding='utf-8')) for n in ['plan_continuacion_03.json','plan_continuacion_04.json']]
    ids={e['id'] for p in planes for e in p['revisiones']}
    entries=[]
    fields=['nodo_grafo','area_estado','referencia_estado','requiere_auditoria_nodo','requiere_auditoria_referencia']
    with SessionLocal() as db:
        for m in db.query(MovimientoKardex).filter(MovimientoKardex.id.in_(ids)).order_by(MovimientoKardex.id):
            actual=snapshot_revision(m)
            if any(s in (m.area_estado or '') for s in ('MANUAL','HUMAN','CONFIRM')):continue
            clasificacion=clasificar_movimiento(m.detalle,m.referencia,m.area,m.ingresos,m.salidas,db)
            derivados={k:getattr(clasificacion,k) for k in fields}
            # El texto histórico puede decir VENTAS con REF DEV y cantidad de
            # ingreso. No convertir esa devolución en un nodo de salida.
            if (m.ingresos or 0)>0 and derivados['nodo_grafo'].startswith('Salida:'):
                nodo,estado,pendiente=(_resolver_area_con_catalogo(m.area,db) if m.area else
                    ('Origen no especificado','SIN_AREA_REGISTRADA',False))
                derivados.update(nodo_grafo=nodo,area_estado=estado,requiere_auditoria_nodo=pendiente)
            cambios={k:v for k,v in derivados.items() if v!=getattr(m,k)}
            motivo=((m.revision_documental or {}).get('motivo','')+' Se actualizan los derivados de la clasificación con las cantidades y el detalle ya cotejados. Se reutiliza el catálogo existente; no se normalizan nombres por semejanza ni se crean áreas o alias.').strip()
            if m.id==5150:
                cambios.update(area_estado='PENDIENTE_HIL',requiere_auditoria_nodo=True)
                motivo+=' El texto CEDOAL cruza el límite REF/ÁREA: se conserva la lectura actual en REF y se deja pendiente su atribución documental. No se certifica como área ausente.'
            cambios={k:v for k,v in cambios.items() if v!=getattr(m,k)}
            if not cambios:continue
            foto=(BACKEND/m.ruta_imagen_respaldo).resolve()
            entries.append({'id':m.id,'articulo_id':m.articulo_id,'esperado':{k:actual[k] for k in CAMPOS_BASE},
                'esperado_adicional':{k:actual[k] for k in fields},'cambios':cambios,
                'fuente':str(foto),'sha256_imagen':hashlib.sha256(foto.read_bytes()).hexdigest(),
                'revision':{'criterios':['T02','T23'],'motivo':motivo,'hallazgos':['DERIVADOS_ACTUALIZADOS_TRAS_COTEJO']}})
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    return {'version':5,'criterio_sha256':digest(policy),'revisiones':entries,'observaciones_articulos':[],
            'sin_reasociaciones_ni_borrados':True,'limites':['Solo derivados de los movimientos cotejados en los lotes 03/04.','No modifica cantidades, fechas, áreas literales ni referencias.','La normalización por coincidencias de T17 permanece pendiente.']}


if __name__=='__main__':
    p=DEST/'plan_continuacion_05.json'
    if p.exists():raise RuntimeError('El plan ya existe. Conservar el cotejo ejecutado y crear otro lote si hace falta.')
    plan=generar();p.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'plan':str(p),'revisiones_derivados':len(plan['revisiones']),'sha256':digest(plan)},ensure_ascii=False))
