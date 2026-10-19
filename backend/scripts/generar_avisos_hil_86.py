"""Procedencias geográficas de trece ingresos observados; fotos propias cotejadas."""
from scripts.plan_enmienda_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar,DERIVADOS
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.clasificador_nodos import clasificar_movimiento

LECTURAS={7212:'CBBA.',7699:'CBBA.',7786:'CBB.',7909:'S. Cruz',7910:'Cbba',8041:'CBBA.',8278:'CBB',8283:'CBBA',8316:'CBB',8774:'CBB',8874:'CBBA.',9602:'CBB.',10992:'ST CRUZ.'}
def casos():
    out={}
    with SessionLocal() as db:
        for id,literal in LECTURAS.items():
            m=db.get(M,id);assert (m.ingresos or 0)>0 and not m.salidas and m.area==literal
            ref=(m.referencia+' / ' if m.referencia else '')+literal
            c=clasificar_movimiento(m.detalle,ref,None,m.ingresos,m.salidas,db)
            assert not c.requiere_auditoria_nodo and not c.requiere_auditoria_referencia
            cambios={'area':None,'referencia':ref,**{k:getattr(c,k) for k in DERIVADOS}}
            motivo=f'La fotografía completa del objetivo escribe {literal} en ÁREA de un ingreso. Es procedencia geográfica, sin nombre de unidad institucional acreditado. Se conserva literalmente como referencia'+(' junto a la carta ya escrita' if m.referencia else '')+' y se retira su tratamiento como área, sin expandir siglas ni inventar sede o alias. Se conservan cifras, fecha, saldo documental, hipótesis anteriores y todos los vecinos.'
            extra={'columnas_documentales':{**(m.revision_documental.get('columnas_documentales') or {}),'area':literal,'referencia':m.referencia},'procedencia_documental':literal,'interpretacion_area':'PROCEDENCIA_GEOGRAFICA_NO_UNIDAD_INSTITUCIONAL'}
            out[id]=(cambios,['T17','T23'],motivo,extra)
    return out

if __name__=='__main__':
    congelar(construir(numero=86,especificaciones=casos(),pendientes=[],limites=['Trece observados HIL vigentes y once fotos propias completas; vecinos solo contexto.','No se crea o confirma catálogo, equivalencia o alias ni se expande CBB/CBBA/S. Cruz.','La columna documental y la revisión anterior quedan íntegras; ninguna cantidad, fecha o saldo cambia.']))
