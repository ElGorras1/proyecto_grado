"""Congela exclusivamente avisos sin revisión previa, con lectura explícita por caso."""
from copy import deepcopy
import hashlib,json
from scripts.aplicar_revision_hil import BACKEND,DEST
from scripts.generar_plan_revision_hil import CAMPOS_BASE,digest
from scripts.cotejo_transcripcion_hil import DERIVADOS
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.calidad_kardex import tipos_alerta
from app.services.revision_documental import snapshot_revision
from app.services.clasificador_nodos import clasificar_movimiento

def construir(*,numero,snapshot,especificaciones,pendientes,limites):
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};entries=[]
    with SessionLocal() as db:
        for id,(cambios,criterios,motivo,extra) in especificaciones.items():
            r=rows[id];m=db.get(M,id);assert snapshot_revision(m)==r and tipos_alerta(m) and not r['revision_documental'],'No sobrescribir un cotejo previo'
            cambios=deepcopy(cambios)
            if any(k in cambios for k in ('area','referencia','detalle','ingresos','salidas')):
                c=clasificar_movimiento(cambios.get('detalle',r['detalle']),cambios.get('referencia',r['referencia']),cambios.get('area',r['area']),cambios.get('ingresos',r['ingresos']),cambios.get('salidas',r['salidas']),db)
                cambios.update({k:getattr(c,k) for k in DERIVADOS})
            rev={'criterios':criterios,'motivo':motivo,'hallazgos':['AVISO_HIL_COTEJADO_CON_FOTO'],'tipo_fila':'MOVIMIENTO','saldo_documental':r['saldo_registrado'],'origen_saldo':'FOTO','origen_cantidades':'FOTO','origen_fecha':'FOTO','fecha_documental':cambios.get('fecha_movimiento',r['fecha_movimiento']),'usar_saldo_esperado':False,'reconstruir_cadena':False,'cotejo_pagina_completa':False,'alcance':'SOLO_MOVIMIENTO_OBSERVADO_HIL','avisos_antes':tipos_alerta(m),**extra}
            foto=(BACKEND/r['ruta_imagen_respaldo']).resolve()
            entries.append({'id':id,'articulo_id':r['articulo_id'],'pagina':f'L{r["lote_id"]:04d}-P{r["numero_pagina"]:02d}','esperado':{k:r[k] for k in CAMPOS_BASE},'esperado_adicional':{k:r[k] for k in DERIVADOS},'cambios':cambios,'revision':rev,'fuente':str(foto),'sha256_imagen':hashlib.sha256(foto.read_bytes()).hexdigest()})
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    return {'version':numero,'criterio_sha256':digest(policy),'revisiones':entries,'sin_reasociaciones_ni_borrados':True,'autorizacion_adicional':'Solo movimientos con observaciones HIL por instrucción expresa del titular; vecinos como contexto sin modificaciones.','observaciones_articulos':[],'cotejo':{'modo':'SOLO_AVISOS_HIL','movimientos':len(entries),'fotografias':len({e['fuente'] for e in entries}),'ids_objetivo':sorted(especificaciones),'ids_pendientes_esperados':pendientes,'contexto_snapshot':snapshot},'limites':limites}
