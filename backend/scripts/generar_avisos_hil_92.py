"""Lecturas puntuales acreditadas por las fotografías de catorce avisos vigentes."""
from scripts.plan_enmienda_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar, DERIVADOS
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.clasificador_nodos import clasificar_movimiento

LECTURAS = {
    5171: ('CEDOAL', None), 5177: ('CEDOAL', 'LA PAZ LEE'),
    5905: ('CEDOAL', None), 5918: ('CEDOAL', None),
    5927: ('CEDOAL', None), 5928: ('CEDOAL', None),
    6386: ('CEDOAL', None), 6456: ('CEDOAL', 'COLECCION CEDOAL'),
    8263: ('Sala', None),
}

def casos():
    out = {}
    with SessionLocal() as db:
        for id, (area, detalle) in LECTURAS.items():
            m = db.get(M, id)
            cambios = {'area': area}
            if detalle:
                cambios['detalle'] = detalle
            c = clasificar_movimiento(cambios.get('detalle', m.detalle), m.referencia,
                                      area, m.ingresos, m.salidas, db)
            assert not c.requiere_auditoria_nodo and not c.requiere_auditoria_referencia
            cambios.update({k: getattr(c, k) for k in DERIVADOS})
            motivo = ('La celda propia de la fotografía permite leer '+area+
                      '. Se corrige la transcripción OCR hacia la unidad ya existente, sin crear alias. '
                      'Se mantienen referencia, fecha, cantidades, saldos e hipótesis anteriores; las filas vecinas son solo contexto.')
            if detalle:
                motivo += ' El detalle propio legible se transcribe como '+detalle+'.'
            out[id] = (cambios, ['T01', 'T17'], motivo,
                       {'lectura_area_fotografia': area, 'normalizacion':'LECTURA_DIRECTA_UNIDAD_EXISTENTE'})
        for id, literal in [(7308, 'Chile'), (7394, 'Oruro'), (7627, 'Potosí'), (10601, 'Potosi'), (5743, 'E. Arandia')]:
            m = db.get(M, id)
            ref = (m.referencia+' / ' if m.referencia else '')+literal
            detalle = 'Devolución Cedoal' if id == 10601 else m.detalle
            cambios = {'area':None, 'referencia':ref}
            if detalle != m.detalle:
                cambios['detalle'] = detalle
            c = clasificar_movimiento(detalle, ref, None, m.ingresos, m.salidas, db)
            assert not c.requiere_auditoria_nodo and not c.requiere_auditoria_referencia
            cambios.update({k:getattr(c,k) for k in DERIVADOS})
            naturaleza = 'NOMBRE_DOCUMENTAL_RECEPTOR' if id == 5743 else 'REFERENCIA_GEOGRAFICA'
            motivo = ('La fotografía escribe '+literal+' en el espacio de ÁREA; '+
                      ('es el nombre documental E. Arandia, que el OCR leyó El Grande' if id == 5743 else 'es una referencia geográfica')+
                      '. Se conserva como referencia, sin inventar una unidad, sede, alias ni responsable registrado. '
                      'Se conserva la columna física como evidencia y toda revisión anterior. No se alteran cantidades, fecha ni saldos.')
            if id == 10601:
                motivo += ' El detalle propio dice Devolución Cedoal; Potosi se conserva como referencia separada.'
            extra = {'columnas_documentales':{**(m.revision_documental.get('columnas_documentales') or {}),
                                             'area':literal, 'referencia':m.referencia},
                     'interpretacion_area':naturaleza}
            out[id] = (cambios, ['T01','T17','T23'], motivo, extra)
    return out

if __name__ == '__main__':
    congelar(construir(numero=92, especificaciones=casos(), pendientes=[], limites=[
        'Catorce avisos vigentes; fotografías propias completas y vecinos únicamente como contexto.',
        'Solo lecturas directas, catálogo existente y separación de referencias; ningún alias ni área nueva.',
        '7394 conserva la fecha documental 11-01-07 y la consulta técnica previa: no se transforma en julio para ordenar la cadena.',
        'No cambia ninguna cantidad, saldo, fecha, hipótesis ni movimiento ajeno a los objetivos.'
    ]))
