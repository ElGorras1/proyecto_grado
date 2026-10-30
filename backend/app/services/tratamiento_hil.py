"""Distingue el tratamiento de un aviso de la confirmación de sus datos."""
from datetime import date, datetime
import hashlib
import json
from app.services.calidad_kardex import tipos_alerta

CATEGORIAS = {
    'ASIGNACION_INFERIDA': 'Área asignada por correlación',
    'DATO_AUSENTE': 'Dato ausente en el documento',
    'DISCREPANCIA_DOCUMENTAL': 'Discrepancia del documento',
    'AMBITO_DOCUMENTAL_INCIERTO': 'Ámbito de la hoja no confirmado',
    'DEPENDENCIA_OTRA_FILA': 'Depende de otra fila',
    'POSIBLE_DUPLICIDAD_DOCUMENTAL': 'Operaciones parecidas conservadas',
    'CATALOGO_NO_CONFIRMADO': 'Nombre o sigla sin equivalencia confirmada',
    'LECTURA_INCIERTA': 'Lectura no inequívoca',
    'MARCA_NO_INTERPRETADA': 'Marca del papel conservada',
    'EFECTO_INDETERMINADO': 'Efecto del movimiento no acreditado',
}
_CAMPOS = ('id','articulo_id','lote_id','estado','fecha_movimiento','detalle','area','referencia',
           'ingresos','salidas','saldo_registrado','saldo_calculado','fecha_estado','tiene_error_fecha',
           'tiene_error_saldo','area_estado','referencia_estado','requiere_auditoria_nodo',
           'requiere_auditoria_referencia','nodo_grafo','ruta_imagen_respaldo','numero_pagina',
           'orden_fila','orden_pagina_validado')
_LECTURAS = ('tipo_fila','fecha_documental','saldo_documental','origen_fecha','origen_saldo',
             'origen_cantidades','origen_saldo_base','saldo_base','usar_saldo_esperado',
             'reconstruir_cadena','diferencia_saldo_documental','ultima_revision_manual')

def huella_datos(m):
    """Una corrección posterior invalida la categoría anterior, sin borrar su auditoría."""
    rev=m.revision_documental or {}
    valores={k:getattr(m,k,None) for k in _CAMPOS}
    # Conservar las huellas anteriores mientras no se incorporen lecturas nuevas.
    for k in ('fecha_documental_texto', 'fecha_precision'):
        if getattr(m,k,None) is not None:
            valores[k]=getattr(m,k)
    valores['lectura_documental']={k:rev.get(k) for k in _LECTURAS}
    if 'asignacion_area' in rev:
        valores['asignacion_area']=rev['asignacion_area']
    def serializar(v):
        if isinstance(v,(date,datetime)): return v.isoformat()
        raise TypeError(type(v).__name__)
    raw=json.dumps(valores,ensure_ascii=False,sort_keys=True,separators=(',',':'),default=serializar)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def resumen_tratamiento(m):
    """Solo lectura: nunca elimina avisos ni concede elegibilidad de entrenamiento."""
    if m.lote_id is None: return None
    avisos=tipos_alerta(m) if m.estado=='ACTIVO' else []
    rev=m.revision_documental or {}
    registro=rev.get('tratamiento_hil')
    resultado={'estado':'POR_CATEGORIZAR' if avisos else 'SIN_AVISOS',
               'etiqueta':'Por categorizar' if avisos else 'Sin avisos HIL',
               'avisos_conservados':avisos,'decisiones':[], 'categorias':[],
               'datos_confirmados':False,'habilita_entrenamiento':False}
    if not registro: return resultado
    decisiones=registro.get('decisiones') if isinstance(registro,dict) else None
    valido=(isinstance(decisiones,list) and bool(decisiones)
            and registro.get('version')==1 and registro.get('huella_datos')==huella_datos(m)
            and isinstance(registro.get('avisos'),list)
            and all(isinstance(a,str) for a in registro['avisos'])
            and sorted(registro['avisos'])==sorted(avisos)
            and all(isinstance(d,dict) and d.get('categoria') in CATEGORIAS
                    and d.get('campo') in avisos and isinstance(d.get('motivo'),str)
                    and d['motivo'].strip() and isinstance(d.get('criterios'),list) and d['criterios']
                    for d in decisiones))
    if valido: valido={d['campo'] for d in decisiones}==set(avisos)
    if not valido:
        resultado.update(estado='REQUIERE_RECATEGORIZAR',etiqueta='Revisar categoría tras cambios')
        return resultado
    resultado.update(estado='CATEGORIZADO_CON_MARCA',etiqueta='Categorizado con marca',
                     decisiones=[{**d,'etiqueta':CATEGORIAS[d['categoria']]} for d in decisiones],
                     categorias=sorted({d['categoria'] for d in decisiones}),
                     autor=registro.get('autor'),categorizado_en=registro.get('categorizado_en'))
    return resultado
