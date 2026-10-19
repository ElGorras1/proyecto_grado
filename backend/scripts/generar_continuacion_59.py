"""Sustituye el ensayo no aplicado 58 sin retirar la protección del detalle."""
from scripts.generar_continuacion_58 import generar as preparar
from scripts.cotejo_transcripcion_hil import congelar

def generar():
    plan=preparar()
    plan['version']=59
    fila=next(e for e in plan['revisiones'] if e['id']==7718)
    fila['cambios']['detalle']='Renglón sin detalle documental'
    fila['revision']['detalle_documental']=None
    fila['revision']['etiqueta_descriptiva_sin_texto_en_fuente']=True
    plan['limites'].append('Sustituye el plan 58, rechazado en ensayo sin aplicación institucional. La etiqueta de ausencia de detalle no se presenta como texto de la foto; se conserva detalle_documental nulo.')
    return plan

if __name__=='__main__':congelar(generar())
