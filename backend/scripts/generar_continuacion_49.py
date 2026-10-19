"""Cotejo de Maritza, Voces y vinilo; conserva referencia no inequívoca sin decidirla."""
from scripts.generar_continuacion_48 import generar as preparar
from scripts.cotejo_transcripcion_hil import congelar

def generar():
    plan=preparar();plan['version']=49
    for e in plan['revisiones']:
        if e['id']==6294:
            e['cambios'].update(referencia='CDA / CONSIG',referencia_estado='INCIERTA',requiere_auditoria_referencia=True)
            e['revision']['columnas_documentales']['referencia']='CBA/CDA no inequívoco; lectura OCR original CDA conservada sin certificar identidad.'
            e['revision']['motivo']=e['revision']['motivo'].replace('CBA queda como referencia literal','La lectura original CDA se conserva pendiente por trazo CBA/CDA no inequívoco')
            e['revision']['criterios']=sorted(set(e['revision']['criterios']+['T16']))
            e['revision']['referencia_documental_ambigua']=True
    plan['preparacion_previa_descartada']={'numero':48,'sha256':'6a20b631f85ba7b2bdfbb0ce66b878d4ac1409e9709df7199cbbd49f9923fd24',
        'motivo':'Antes de ensayo o aplicación se detectó una lectura CBA/CDA no inequívoca. Se conserva el plan 48 intacto entre los planes no aplicados y se prepara un número nuevo, sin decidir letras por frecuencia.'}
    return plan

if __name__=='__main__':congelar(generar())
