"""Enmienda focalizada de avisos ya cotejados, conservando íntegra su revisión anterior."""
from copy import deepcopy
import hashlib,json
from scripts.aplicar_revision_hil import BACKEND,DEST
from scripts.generar_plan_revision_hil import CAMPOS_BASE,digest
from scripts.cotejo_transcripcion_hil import DERIVADOS
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.calidad_kardex import tipos_alerta
from app.services.revision_documental import snapshot_revision

def construir(*,numero,especificaciones,pendientes,limites):
    inicial=json.loads((BACKEND/'backups/revision_avisos_hil_20261016/cola_inicial_399.json').read_text(encoding='utf-8'))
    autorizados={c['id'] for c in inicial['casos']};assert set(especificaciones)<=autorizados
    entries=[];snapshots=[]
    with SessionLocal() as db:
        for id,(cambios,criterios,motivo,extra) in especificaciones.items():
            m=db.get(M,id);r=snapshot_revision(m);prev=deepcopy(m.revision_documental)
            assert tipos_alerta(m) and prev,'Solo avisos vigentes previamente cotejados'
            snapshots.append(r)
            rev={**prev,**extra,'criterios':sorted(set(prev.get('criterios',[])+criterios)),
                 'motivo':motivo,'revision_previa_enmienda_focalizada':prev,
                 'alcance':'SOLO_MOVIMIENTO_OBSERVADO_HIL','cotejo_pagina_completa':False,
                 'avisos_antes':tipos_alerta(m),'hallazgos':['ENMIENDA_DE_AVISO_PREVIAMENTE_COTEJADO']}
            for key in ['version','criterio_sha256','plan_sha256','autor_registro','revisado_en','planes_aplicados']:
                rev.pop(key,None)
            foto=(BACKEND/r['ruta_imagen_respaldo']).resolve()
            entries.append({'id':id,'articulo_id':r['articulo_id'],'pagina':f'L{r["lote_id"]:04d}-P{r["numero_pagina"]:02d}',
                'esperado':{k:r[k] for k in CAMPOS_BASE},
                'esperado_adicional':{**{k:r[k] for k in DERIVADOS},'revision_documental':prev},
                'cambios':cambios,'revision':rev,'fuente':str(foto),'sha256_imagen':hashlib.sha256(foto.read_bytes()).hexdigest()})
    carpeta=BACKEND/f'backups/revision_avisos_hil_20261016/bloque_{numero:02d}';carpeta.mkdir(exist_ok=True)
    out=carpeta/'objetivos_antes.json';assert not out.exists();out.write_text(json.dumps(snapshots,ensure_ascii=False,indent=2),encoding='utf-8')
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    return {'version':numero,'criterio_sha256':digest(policy),'revisiones':entries,'sin_reasociaciones_ni_borrados':True,
            'autorizacion_adicional':'Solo avisos de la cola inicial; enmienda conserva revisión previa completa y exige que siga intacta.',
            'observaciones_articulos':[],'cotejo':{'modo':'SOLO_AVISOS_HIL','movimientos':len(entries),'fotografias':len({e['fuente'] for e in entries}),
                'ids_objetivo':sorted(especificaciones),'ids_pendientes_esperados':pendientes,'contexto_snapshot':str(out.relative_to(BACKEND)).replace('\\','/')},'limites':limites}
