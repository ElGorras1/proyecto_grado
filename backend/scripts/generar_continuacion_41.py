"""Amplía la incertidumbre de una cifra repasada sin cambiar datos vigentes de Bodega."""
from copy import deepcopy
import hashlib,json
from scripts.cotejo_transcripcion_hil import BACKEND,DERIVADOS,congelar
from scripts.generar_plan_revision_hil import CAMPOS_BASE,DEST,digest

def generar():
    rows=json.loads((BACKEND/'backups/continuacion_hil_41_20261015/articulo_11_revision_38_antes.json').read_text(encoding='utf-8'))
    assert len(rows)==37 and all(r['revision_documental'] for r in rows)
    cambios={608:{'origen_cantidades':'HIPOTESIS','candidatos_cantidad_documental':[0,3],
        'lectura_cantidad_parcial':'Cifra redondeada o cerrada, lectura 0/3 no inequívoca en el acercamiento.'}}
    entradas=[];protegidos={}
    for r in rows:
        id=r['id'];previa=deepcopy(r['revision_documental']);rev=deepcopy(previa)
        rev['revision_previa_rectificacion_documental']=deepcopy(previa)
        rev['motivo']+=' Se conserva íntegramente el cotejo 38 y todos los datos vigentes al ampliar el acercamiento de la devolución.'
        if id==608:
            rev.update(cambios[id]);rev['criterios']=sorted(set(rev['criterios']+['T19']))
            rev['hallazgos']=sorted(set(rev['hallazgos']+['CANTIDAD_DOCUMENTAL_NO_INEQUIVOCA']))
            rev['motivo']+=' El acercamiento muestra una cifra redondeada o cerrada, no inequívoca entre 0/3. Ingreso 3 se mantiene exclusivamente como hipótesis de consulta; saldo anterior 45 y posterior 48 no prueban por sí solos el dígito. No se cambia ninguna cantidad ni se inventa ajuste. El artículo completo se excluye del entrenamiento y el cierre 2 se declara condicional.'
        foto=(BACKEND/r['ruta_imagen_respaldo']).resolve()
        entradas.append({'id':id,'articulo_id':11,'pagina':f'L{r["lote_id"]:04d}-P{r["numero_pagina"]:02d}',
            'esperado':{k:r[k] for k in CAMPOS_BASE},'esperado_adicional':{**{k:r[k] for k in DERIVADOS},'revision_documental':deepcopy(previa)},
            'cambios':{},'revision':rev,'fuente':str(foto),'sha256_imagen':hashlib.sha256(foto.read_bytes()).hexdigest()})
        protegidos[str(id)]={'valores':{k:v for k,v in r.items() if k!='revision_documental'},'revision':deepcopy(previa),'metadatos_rectificables':list(cambios.get(id,{}))}
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    return {'version':41,'criterio_sha256':digest(policy),'revisiones':entradas,'sin_reasociaciones_ni_borrados':True,
        'autorizacion_adicional':'Ampliación asistida de incertidumbre según T19 y delegación del titular; nueva evidencia visual conservando íntegramente revisión anterior y todos los datos vigentes.',
        'observaciones_articulos':[{'articulo_id':11,'observado':True,'excluir_entrenamiento':True,'motivo':'Dos fotografías y 37 filas ya cotejadas se amplían con un acercamiento de la devolución 608. Su cifra redondeada no es inequívoca entre 0/3; ingreso 3 continúa exclusivamente como hipótesis, sin certificarlo por el paso 45 a 48. Cierre escrito 2 coincide condicionalmente; artículo completo excluido del entrenamiento hasta aclarar. Se conserva íntegro el cotejo 38, nota sin efecto, ingreso 59, fechas técnicas, saldos vacíos y todos los datos vigentes. No se inventan ajustes ni se afirma bloqueo automático de apertura por la exclusión.'}],
        'cotejo':{'fotografias':2,'movimientos':37,'nuevos_distintos':0,'cierres':{11:2},'cierres_documentales':{11:2},'discrepancias':[],
            'rectificaciones_previas':protegidos,'rectificaciones_documentales':[{'id':608,'metadatos':cambios[608]}],
            'limites_cierre':{11:'Cierre escrito 2 coincide condicionalmente con ingreso hipotético 3 de una cifra 0/3 no inequívoca. Artículo excluido del entrenamiento hasta aclarar; no se inventa ajuste.'}},
        'limites':['Solo se amplían metadatos de incertidumbre; todas las cantidades, fechas, saldos, fuentes y revisiones previas se conservan.','Las 37 filas ya estaban contabilizadas: cero históricos distintos adicionales.','Revisión asistida, no validación institucional.']}

if __name__=='__main__':congelar(generar())
