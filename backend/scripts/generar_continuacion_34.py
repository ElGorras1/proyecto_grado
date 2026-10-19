"""Rectifica lectura documental 224 de Arquitectura conservando revisión y datos vigentes."""
from copy import deepcopy
import hashlib,json
from scripts.cotejo_transcripcion_hil import BACKEND,DERIVADOS,congelar
from scripts.generar_plan_revision_hil import CAMPOS_BASE,DEST,digest

def generar():
    rows=json.loads((BACKEND/'backups/continuacion_hil_34_20261015/articulo_25_revision_32_antes.json').read_text(encoding='utf-8'))
    assert len(rows)==26 and all(r['revision_documental'] for r in rows)
    entradas=[];protegidos={};cambios={971:{'saldo_documental':224,'origen_saldo':'RECONSTRUIDO','diferencia_local_papel':-10,'diferencia_saldo_documental':-10},972:{'diferencia_local_papel':10}}
    for r in rows:
        id=r['id'];previa=deepcopy(r['revision_documental']);rev=deepcopy(previa)
        rev['revision_previa_rectificacion_documental']=deepcopy(previa)
        rev['motivo']+=' Se conserva íntegramente esta revisión anterior y todos los datos vigentes al ampliar el acercamiento documental de la misma hoja.'
        if id in cambios:
            rev.update(cambios[id]);rev['criterios']=sorted(set(rev['criterios']+['T01','T05']))
            rev['hallazgos']=sorted(set(rev['hallazgos']+['DESCUADRE_DEL_PAPEL_CONSERVADO','LECTURA_DOCUMENTAL_RECTIFICADA_CON_EVIDENCIA']))
            rev['motivo']+=(' El acercamiento muestra saldo escrito 224 después de base 232 e ingreso 2, no 234 como se registró en el cotejo 32. El dato vigente 234 se mantiene por cálculo; diferencia documental -10. La siguiente devolución 5 escribe 239 y compensa +10 sobre el papel. No se inventan operaciones ni se cambia cantidad para cuadrar.' if id==971 else
                ' El saldo escrito 239 tras la fila que escribe 224 y este ingreso 5 deja diferencia local +10. Se conserva la compensación del error anterior, sin cambiar este ingreso ni el saldo vigente 239.')
        foto=(BACKEND/r['ruta_imagen_respaldo']).resolve()
        entradas.append({'id':id,'articulo_id':25,'pagina':f'L{r["lote_id"]:04d}-P{r["numero_pagina"]:02d}',
            'esperado':{k:r[k] for k in CAMPOS_BASE},'esperado_adicional':{**{k:r[k] for k in DERIVADOS},'revision_documental':deepcopy(previa)},
            'cambios':{},'revision':rev,'fuente':str(foto),'sha256_imagen':hashlib.sha256(foto.read_bytes()).hexdigest()})
        protegidos[str(id)]={'valores':{k:v for k,v in r.items() if k!='revision_documental'},'revision':deepcopy(previa),'metadatos_rectificables':list(cambios.get(id,{}))}
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    return {'version':34,'criterio_sha256':digest(policy),'revisiones':entradas,'sin_reasociaciones_ni_borrados':True,
        'autorizacion_adicional':'Rectificación asistida con nueva evidencia visual según T01/T05 y delegación del titular, preservando revisión anterior y datos vigentes.',
        'observaciones_articulos':[{'articulo_id':25,'observado':True,'excluir_entrenamiento':False,'motivo':'Hoja completa cotejada y acercamiento documental ampliado. El papel escribe 224 en la primera devolución 2 desde base 232, no 234; se conserva cálculo vigente 234 y diferencia documental -10. La siguiente devolución 5 escribe 239, compensando +10. Se preserva íntegra la revisión 32 y su auditoría; no se cambia ninguna cantidad, fecha, saldo vigente, clasificación o fuente. Cierre 195 coincide.'}],
        'cotejo':{'fotografias':1,'movimientos':26,'nuevos_distintos':0,'cierres':{25:195},'cierres_documentales':{25:195},
            'discrepancias':[{'id':971,'local':-10,'acumulada':-10},{'id':972,'local':10,'acumulada':0}],
            'rectificaciones_previas':protegidos,
            'rectificaciones_documentales':[{'id':id,'metadatos':meta} for id,meta in cambios.items()]},
        'limites':['Solo se rectifican metadatos documentales explícitos de dos filas; los datos vigentes y toda revisión anterior quedan protegidos.','No se suman 26 revisiones nuevas al acumulado de renglones distintos.','Cotejo asistido, no validación institucional.']}

if __name__=='__main__':congelar(generar())
