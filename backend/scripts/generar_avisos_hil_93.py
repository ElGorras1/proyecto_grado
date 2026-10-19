"""Atribución funcional de CEDOAL legible entre REF y ÁREA, con posición física conservada."""
from scripts.plan_enmienda_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar, DERIVADOS
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.clasificador_nodos import clasificar_movimiento

IDS = [2836,3561,3711,4018,4332,4495,4817,4976,5150,5388,5516,5634,6043]

def casos():
    out={}
    with SessionLocal() as db:
        for id in IDS:
            m=db.get(M,id)
            assert m.detalle=='VENTAS' and m.area in [None,'CEDOAL'] and m.referencia in [None,'CEDOAL']
            assert 'CEDOAL' in [m.area,m.referencia] and m.salidas and not m.ingresos
            c=clasificar_movimiento(m.detalle,None,'CEDOAL',m.ingresos,m.salidas,db)
            assert not c.requiere_auditoria_nodo and not c.requiere_auditoria_referencia
            cambios={'area':'CEDOAL','referencia':None,**{k:getattr(c,k) for k in DERIVADOS}}
            motivo=('La fotografía propia del movimiento VENTAS permite leer inequívocamente CEDOAL: '
                    'la palabra cruza el límite REF/ÁREA. Se atribuye funcionalmente a CEDOAL, unidad ya '
                    'catalogada, por interpretación documental con T17. No se certifica una ubicación física '
                    'exclusiva de la palabra ni se añade otra unidad o referencia. La ambigüedad de posición '
                    'y la revisión anterior se conservan como evidencia. Cifras, fechas, discrepancias del '
                    'papel, hipótesis y exclusiones previas permanecen intactas; vecinos solo de contexto.')
            extra={'atribucion_funcional':'CEDOAL', 'origen_atribucion_funcional':'INTERPRETACION_DOCUMENTAL_ASISTIDA',
                   'posicion_documental':'CEDOAL cruza el límite REF/ÁREA; ubicación física exclusiva no acreditada',
                   'ambiguedad_fisica_conservada':True,
                   'motivo_resolucion_atribucion':'La identidad de la unidad es legible aunque el texto atraviese la línea entre columnas.'}
            out[id]=(cambios,['T01','T17'],motivo,extra)
    return out

if __name__=='__main__':
    congelar(construir(numero=93,especificaciones=casos(),pendientes=[],limites=[
        'Trece objetivos vigentes y sus trece fotos propias completas; ninguna fila normal se modifica.',
        'Identidad CEDOAL legible en cada foto; atribución funcional explícita, sin certificar la columna física ambigua.',
        'No se decide por coincidencia de fecha, frecuencia, semejanza entre artículos ni expansión de siglas.',
        'Se mantienen discrepancias, hipótesis y exclusiones, incluidos Campero, Luksic, Tía Dorita y Mar de sueños.'
    ]))
