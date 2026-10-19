"""Actualiza solo la cola de 399 avisos autorizada, sin alterar la base."""
import json
from pathlib import Path
from datetime import datetime,UTC
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.calidad_kardex import tipos_alerta
from app.services.tratamiento_hil import resumen_tratamiento
from scripts.aplicar_revision_hil import BACKEND,DEST,fuente_hash

def guardar():
    carpeta=BACKEND/'backups/revision_avisos_hil_20261016'
    inicial=json.loads((carpeta/'cola_inicial_399.json').read_text(encoding='utf-8'));casos=[]
    with SessionLocal() as db:
        fuente=fuente_hash(db)
        for c in inicial['casos']:
            m=db.get(M,c['id']);avisos=tipos_alerta(m) if m.estado=='ACTIVO' else []
            estado=('RESUELTO' if not avisos else 'PENDIENTE_DOCUMENTADO_PREVIO' if c['ya_cotejado'] else 'COTEJADO_CON_PENDIENTE' if m.revision_documental else 'PENDIENTE_REVISION')
            tratamiento=resumen_tratamiento(m) or {}
            casos.append({'id':m.id,'articulo_id':m.articulo_id,'articulo':c['articulo'],'avisos':avisos,'estado':estado,
                          'estado_tratamiento':tratamiento.get('estado'),'categorias':tratamiento.get('categorias',[])})
        observados={m.id for m in db.query(M).filter(M.lote_id.isnot(None),M.estado=='ACTIVO') if tipos_alerta(m)}
    previstos={c['id'] for c in casos if c['avisos']}
    assert previstos<=observados
    numeros=[]
    for path in DEST.glob('resultado_continuacion_[0-9][0-9].json'):
        r=json.loads(path.read_text(encoding='utf-8'))
        if r.get('cotejo',{}).get('modo')=='SOLO_AVISOS_HIL':
            assert r['verificado'] and r['sin_cambios_en_filas_normales'];numeros.append(int(path.stem.rsplit('_',1)[-1]))
    siguiente=max(int(p.stem.rsplit('_',1)[-1]) for p in DEST.glob('plan_continuacion_[0-9][0-9].json'))+1
    estado={'generado_en':datetime.now(UTC).isoformat(),'alcance':'SOLO_AVISOS_HIL','casos_iniciales':len(casos),'avisos_actuales':len(previstos),'avisos_fuera_cola_inicial':sorted(observados-previstos),'metricas':{e:sum(c['estado']==e for c in casos) for e in ('RESUELTO','COTEJADO_CON_PENDIENTE','PENDIENTE_DOCUMENTADO_PREVIO','PENDIENTE_REVISION')},'ultimo_plan':max(numeros),'siguiente_numero_libre':siguiente,'casos':casos,'filas_fuera_objetivo_modificadas':[],'fuente_sha256':fuente}
    estado['metricas_tratamiento']={e:sum(c['estado_tratamiento']==e for c in casos) for e in ('SIN_AVISOS','CATEGORIZADO_CON_MARCA','POR_CATEGORIZAR','REQUIERE_RECATEGORIZAR')}
    temporal=carpeta/'estado_avisos.tmp';temporal.write_text(json.dumps(estado,ensure_ascii=False,indent=2),encoding='utf-8');temporal.replace(carpeta/'estado_avisos.json')
    return estado

if __name__=='__main__':print(json.dumps({k:v for k,v in guardar().items() if k!='casos'},ensure_ascii=False))
