"""Sustituye el ensayo 65 ajustando únicamente la expectativa de avisos técnicos."""
from scripts.generar_continuacion_65 import generar as preparar
from scripts.cotejo_transcripcion_hil import congelar

def generar():
    plan=preparar();plan['version']=66
    plan['cotejo']['pendientes_documentales']={'560':['saldo'],'589':['saldo']}
    plan['limites'].append('Sustituye el plan 65 rechazado en copia QA y nunca aplicado a institución. Las fechas SECUENCIA_AJUSTADA conservan literal, origen y exclusión del entrenamiento; el recálculo no les asigna tiene_error_fecha. Se corrige solo la expectativa de comprobación de avisos, sin alterar cantidades, fechas ni protecciones.')
    return plan

if __name__=='__main__':congelar(generar())
