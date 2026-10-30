"""Reglas retrospectivas sobre el documento vigente; consulta sin escrituras."""
from collections import Counter, defaultdict, deque
from datetime import UTC, datetime
from statistics import median

from sqlalchemy import func
from sqlalchemy.orm import defer

from app.models.activos import Activo
from app.models.kardex import LoteCarga, MovimientoKardex
from app.services.control_movimientos import parametros_control
from app.services.fechas_documentales import datos_fecha, fecha_asignable

VERSION = '2026-10-14.2'
REGLAS = {
    'SALDO_INCONSISTENTE': 'Saldo vigente inconsistente',
    'DESCUADRE_DOCUMENTAL': 'Diferencia conservada en el papel',
    'SALDO_NEGATIVO': 'Saldo negativo',
    'SALIDA_SUPERA_SALDO': 'Salida superior al saldo previo',
    'AGOTA_STOCK': 'Salida de todas las unidades',
    'SALIDA_MAYORITARIA': 'Salida mayoritaria',
    'CANTIDAD_EXTREMA': 'Cantidad elevada',
    'CANTIDAD_ATIPICA': 'Cantidad elevada frente a antecedentes',
    'CANTIDADES_INVALIDAS': 'Cantidades inválidas o dirección ambigua',
    'POSIBLE_REPETICION': 'Posible repetición documental',
    'POSICION_REPETIDA': 'Posición de fila repetida',
    'CAMBIO_BASE_DOCUMENTAL': 'Diferencia al establecer una nueva base',
}


def politica():
    p = parametros_control()
    return {'version': VERSION, 'estado': 'PROVISIONAL',
            'cantidad_extrema': p['cantidad_extrema'],
            'porcentaje_mayoritario': p['porcentaje_mayoritario'],
            'stock_minimo_mayoritario': p['stock_minimo_mayoritario'],
            'factor_atipico': p['factor_atipico'],
            'min_comparables': p['min_comparables'],
            'min_cantidad_atipica': p['min_cantidad_atipica'],
            'orden': 'Artículo, lote, página validada (o fotografía), fila e ID. Los antecedentes se leen antes de filtrar la gestión.',
            'limites': [
                'Son avisos para cotejar la fuente; no acreditan fraude ni validación integral.',
                'No se utiliza stock actual, fecha de escaneo ni hora de carga para juzgar una operación antigua.',
                'Horario y demora de registro no son evaluables: el Kárdex histórico no documenta esas horas.',
                'Una fecha estimada ubica la fila para consulta; no confirma la gestión del hecho.',
                'Las repeticiones se conservan y deben verificarse con sus fotografías.',
            ], 'reglas': [{'codigo': c, 'nombre': n} for c, n in REGLAS.items()]}


def texto(v):
    return ' '.join(str(v or '').split()).casefold()


def fecha_estimada(f):
    rev = f.get('revision_documental') or {}
    return not f.get('fecha') or f.get('fecha_estado') == 'ESTIMADA_HIL' or rev.get('origen_fecha') in {'HIPOTESIS', 'SECUENCIA_AJUSTADA'}


def cantidad(f):
    i, s = f.get('ingresos') or 0, f.get('salidas') or 0
    if type(i) is not int or type(s) is not int or i < 0 or s < 0 or (i > 0 and s > 0):
        return None, None
    if i > 0:
        return 'ingreso', i
    if s > 0:
        return 'salida', s
    return None, 0


def cantidad_hipotetica(f):
    return (f.get('revision_documental') or {}).get('origen_cantidades') == 'HIPOTESIS'


def evaluar(filas, config=None):
    """Recibe TODAS las filas históricas activas ordenadas, sin filtro de año."""
    p = config or politica()
    posiciones = Counter((f['articulo_id'], f['lote_id'], f.get('numero_pagina'), f.get('orden_fila'))
                         for f in filas if f.get('numero_pagina') and f.get('orden_fila'))
    repeticiones = defaultdict(list)
    for f in filas:
        if f.get('fecha') and not fecha_estimada(f) and not cantidad_hipotetica(f) and (texto(f.get('referencia')) or texto(f.get('detalle'))):
            clave = (f['articulo_id'], f['fecha'], f.get('ingresos') or 0, f.get('salidas') or 0,
                     texto(f.get('referencia')), texto(f.get('detalle')), texto(f.get('nodo')))
            repeticiones[clave].append(f['id'])
    previos = {}
    cantidades = defaultdict(lambda: deque(maxlen=20))
    resultados = []
    for f in filas:
        rev = f.get('revision_documental') or {}
        anterior = previos.get(f['articulo_id'])
        if anterior and anterior['lote_id'] != f['lote_id']:
            # El ID de un lote no acredita que sea posterior en el tiempo.
            # Sin vínculo documental explícito no arrastramos stock ni comparables.
            for key in [k for k in cantidades if k[0] == f['articulo_id']]:
                cantidades.pop(key)
        direccion, valor = cantidad(f)
        avisos, no_evaluables = [], []
        posicion = (f['articulo_id'], f['lote_id'], f.get('numero_pagina'), f.get('orden_fila'))
        duplicada = posiciones.get(posicion, 0) > 1
        base = anterior.get('saldo_vigente') if anterior else None
        base_origen = 'FILA_PREVIA' if anterior else None
        if type(rev.get('saldo_base')) is int:
            base = rev['saldo_base']
            base_origen = 'BASE_REVISION_DOCUMENTAL'
        ajuste = rev.get('ajuste_disponibilidad', 0)
        ajuste = ajuste if type(ajuste) is int else 0
        checkpoint = rev.get('tipo_fila') in {'RECUENTO', 'BASE_DOCUMENTAL'}
        base_dudosa = base is None or type(base) is not int or base < 0 or duplicada or f.get('observado', False) or cantidad_hipotetica(f)
        if base_origen == 'BASE_REVISION_DOCUMENTAL':
            base_dudosa |= rev.get('origen_saldo_base') == 'HIPOTESIS'
        elif anterior:
            ar = anterior.get('revision_documental') or {}
            ap = (anterior['articulo_id'], anterior['lote_id'], anterior.get('numero_pagina'), anterior.get('orden_fila'))
            base_dudosa |= bool(anterior.get('error_saldo')) or ar.get('origen_saldo') == 'HIPOTESIS' or posiciones.get(ap, 0) > 1 or cantidad(anterior)[1] is None
            base_dudosa |= anterior['lote_id'] != f['lote_id']
            base_dudosa |= cantidad_hipotetica(anterior)
        # Una cantidad cero no acredita una operación. Puede ser un saldo inicial o resumen.
        base_fiable = not base_dudosa and direccion is not None and not checkpoint
        esperado = None

        def aviso(codigo, nivel, mensaje, **datos):
            avisos.append({'codigo': codigo, 'nombre': REGLAS[codigo], 'nivel': nivel,
                           'mensaje': mensaje, 'datos': datos})

        if duplicada:
            aviso('POSICION_REPETIDA', 'medio', 'La misma posición física contiene varias filas guardadas. Revisa la fotografía antes de fijar su secuencia.')
        if valor is None:
            aviso('CANTIDADES_INVALIDAS', 'alto', 'Las cantidades son negativas o hay ingreso y salida simultáneos; falta confirmar la dirección.')
        if type(f.get('saldo_vigente')) is int and f['saldo_vigente'] < 0:
            aviso('SALDO_NEGATIVO', 'alto', 'El saldo vigente es negativo.', saldo=f['saldo_vigente'])
        if checkpoint:
            diferencia = rev.get('diferencia_con_cadena_previa')
            if diferencia:
                aviso('CAMBIO_BASE_DOCUMENTAL', 'medio', 'El recuento o nueva base conserva una diferencia con la cadena previa; no equivale a una salida inventada.', diferencia=diferencia)
        elif base_fiable:
            esperado = base + (f.get('ingresos') or 0) - (f.get('salidas') or 0) + ajuste
            if f['saldo_vigente'] != esperado and rev.get('origen_saldo') != 'HIPOTESIS':
                aviso('SALDO_INCONSISTENTE', 'alto', 'El saldo vigente no coincide con saldo previo + ingreso − salida y los ajustes documentados.',
                      saldo_previo=base, esperado=esperado, registrado=f['saldo_vigente'], ajuste_documental=ajuste)
            escrito = rev.get('saldo_documental')
            if type(escrito) is int and escrito != esperado and rev.get('origen_saldo') != 'HIPOTESIS':
                aviso('DESCUADRE_DOCUMENTAL', 'medio', 'La lectura corregida conserva un saldo escrito diferente del esperado. El hallazgo del papel no se borró.',
                      saldo_documental=escrito, esperado=esperado, diferencia=escrito-esperado)
            if direccion == 'salida' and valor > base:
                aviso('SALIDA_SUPERA_SALDO', 'alto', 'La salida supera el saldo de la fila previa. Coteja cantidades y antecedentes.', saldo_previo=base, cantidad=valor)
            elif direccion == 'salida' and base > 0 and valor == base:
                aviso('AGOTA_STOCK', 'alto', 'La salida comprende todas las unidades del saldo previo.', saldo_previo=base, cantidad=valor)
            elif direccion == 'salida' and base >= p['stock_minimo_mayoritario'] and valor*100 >= base*p['porcentaje_mayoritario']:
                aviso('SALIDA_MAYORITARIA', 'alto', f"La salida comprende al menos el {p['porcentaje_mayoritario']} % del saldo previo.",
                      saldo_previo=base, cantidad=valor, porcentaje=p['porcentaje_mayoritario'])
        if not base_fiable and not checkpoint:
            no_evaluables.append({'reglas': ['SALDO_INCONSISTENTE', 'SALIDA_SUPERA_SALDO', 'AGOTA_STOCK', 'SALIDA_MAYORITARIA'],
                                  'motivo': 'Falta un saldo previo utilizable, cambia el lote sin base explícita, o hay una base/posición observada o hipotética; no se utiliza stock actual.'})
        if cantidad_hipotetica(f):
            no_evaluables.append({'reglas': ['CANTIDAD_EXTREMA', 'CANTIDAD_ATIPICA', 'POSIBLE_REPETICION'],
                                  'motivo': 'La cantidad se reconstruyó como hipótesis; no es una lectura documental confirmada.'})
        if direccion and not cantidad_hipotetica(f) and valor >= p['cantidad_extrema']:
            aviso('CANTIDAD_EXTREMA', 'alto', f"La cantidad alcanza el umbral provisional de {p['cantidad_extrema']} unidades.", cantidad=valor, umbral=p['cantidad_extrema'])
        clave_comparable = (f['articulo_id'], direccion, texto(f.get('nodo')))
        comparables = list(cantidades[clave_comparable])
        contexto_fiable = direccion is not None and not cantidad_hipotetica(f) and not f.get('nodo_pendiente') and not f.get('observado') and not checkpoint and not duplicada
        referencia = median(comparables) if len(comparables) >= p['min_comparables'] else None
        if contexto_fiable and referencia is not None:
            if valor >= max(p['min_cantidad_atipica'], referencia*p['factor_atipico']):
                aviso('CANTIDAD_ATIPICA', 'medio', 'La cantidad supera el factor provisional frente a la mediana de hasta 20 filas previas del mismo artículo, dirección y nodo.',
                      cantidad=valor, mediana=referencia, comparables=len(comparables), factor=p['factor_atipico'])
        elif direccion:
            no_evaluables.append({'reglas': ['CANTIDAD_ATIPICA'], 'motivo': 'No hay suficientes antecedentes comparables o el contexto documental requiere revisión.'})
        if f.get('fecha') and not fecha_estimada(f) and not cantidad_hipotetica(f):
            clave = (f['articulo_id'], f['fecha'], f.get('ingresos') or 0, f.get('salidas') or 0,
                     texto(f.get('referencia')), texto(f.get('detalle')), texto(f.get('nodo')))
            otros = [i for i in repeticiones.get(clave, []) if i != f['id']]
            if otros:
                aviso('POSIBLE_REPETICION', 'medio', 'Hay otras filas del mismo artículo con fecha, cantidades y contexto coincidentes. Pueden ser hechos legítimos; verifica las fotos.', otros_movimientos=otros)
        if fecha_estimada(f):
            no_evaluables.append({'reglas': ['POSIBLE_REPETICION'], 'motivo': 'La fecha para consulta es estimada; no confirma una coincidencia temporal.'})
        resultados.append({**f, 'fecha_estimada': fecha_estimada(f), 'saldo_previo': base,
                           'movimiento_previo_id': anterior['id'] if anterior else None,
                           'origen_base': base_origen, 'base_utilizable': base_fiable,
                           'saldo_esperado_reglas': esperado, 'mediana_previa': referencia,
                           'comparables_previos': len(comparables), 'avisos': avisos,
                           'no_evaluables': no_evaluables,
                           'estado_evaluacion': 'CON_AVISOS' if avisos else 'EVIDENCIA_INSUFICIENTE' if no_evaluables else 'SIN_AVISOS'})
        if contexto_fiable and valor > 0:
            cantidades[clave_comparable].append(valor)
        previos[f['articulo_id']] = f
    return resultados


def leer(db, *, articulo_id=None, articulo=None):
    consulta = db.query(MovimientoKardex, Activo, LoteCarga.tanda).options(
        defer(MovimientoKardex.datos_originales),
    ).join(
        Activo, MovimientoKardex.articulo_id == Activo.id).join(
        LoteCarga, MovimientoKardex.lote_id == LoteCarga.id).filter(
        MovimientoKardex.estado == 'ACTIVO')
    if articulo_id is not None:
        consulta = consulta.filter(MovimientoKardex.articulo_id == articulo_id)
    if texto(articulo):
        # Mismo casefold que el filtro público, también para tildes y Unicode.
        # Se reduce por artículo completo; nunca por año antes de evaluar.
        nombre = texto(articulo)
        ids = [id for id, titulo, codigo in db.query(Activo.id, Activo.nombre, Activo.codigo)
               if nombre in texto(titulo + ' ' + codigo)]
        consulta = consulta.filter(MovimientoKardex.articulo_id.in_(ids))
    filas = consulta.order_by(
        MovimientoKardex.articulo_id, MovimientoKardex.lote_id,
        func.coalesce(MovimientoKardex.orden_pagina_validado, MovimientoKardex.numero_pagina),
        MovimientoKardex.orden_fila, MovimientoKardex.id).all()
    return evaluar([{
        'id': m.id, 'articulo_id': m.articulo_id, 'articulo': a.nombre, 'codigo': a.codigo,
        'fecha': m.fecha_movimiento.isoformat() if m.fecha_movimiento else None, 'fecha_original': m.fecha_original.isoformat() if m.fecha_original else None,
        **datos_fecha(m),
        'fecha_estado': m.fecha_estado, 'gestion': m.fecha_movimiento.year if fecha_asignable(m) else None,
        'detalle': m.detalle, 'referencia': m.referencia, 'nodo': m.nodo_grafo,
        'ingresos': m.ingresos, 'salidas': m.salidas, 'saldo_vigente': m.saldo_registrado,
        'saldo_calculado_hil': m.saldo_calculado, 'error_saldo': m.tiene_error_saldo,
        'nodo_pendiente': m.requiere_auditoria_nodo, 'lote_id': m.lote_id, 'tanda': tanda,
        'numero_pagina': m.numero_pagina, 'orden_pagina_validado': m.orden_pagina_validado,
        'orden_fila': m.orden_fila, 'ruta_imagen_respaldo': m.ruta_imagen_respaldo,
        'revision_documental': m.revision_documental,
        'observado': bool((a.observacion_hil or {}).get('observado')),
    } for m, a, tanda in filas])


def filtrar(filas, *, gestion=None, articulo=None, regla=None, seleccion='avisos'):
    nombre = texto(articulo)
    return [f for f in filas
            if (gestion is None or f['gestion'] == gestion)
            and (not nombre or nombre in texto(f['articulo'] + ' ' + f['codigo']))
            and (not regla or any(a['codigo'] == regla for a in f['avisos']))
            and (seleccion == 'todos' or (seleccion == 'avisos' and f['avisos'])
                 or (seleccion == 'sin_avisos' and not f['avisos'])
                 or (seleccion == 'insuficiente' and f['no_evaluables']))]


def resumen(filas):
    return {'movimientos': len(filas), 'con_avisos': sum(bool(f['avisos']) for f in filas),
            'sin_avisos': sum(not f['avisos'] for f in filas),
            'evaluacion_parcial': sum(bool(f['no_evaluables']) for f in filas),
            'por_regla': dict(Counter(a['codigo'] for f in filas for a in f['avisos'])),
            'consultado_en': datetime.now(UTC).isoformat()}
