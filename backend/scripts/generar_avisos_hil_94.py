"""Cuatro separaciones y lecturas directas en objetivos HIL concretos."""
from scripts.plan_enmienda_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar, DERIVADOS
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.clasificador_nodos import clasificar_movimiento

def casos():
    out={}
    with SessionLocal() as db:
        especificos={
            1255:('Galería',None,'La celda de área del movimiento CBA TARIJA se lee Galería en la foto propia; GAFERIA es una transcripción OCR incorrecta. Se usa Galería, que ya existe en el catálogo.',{'lectura_area_fotografia':'Galería'}),
            2682:('CEDOAL','VENTAS','La foto propia escribe CEDOAL en REF y VENTAS en ÁREA. Se separa funcionalmente la unidad CEDOAL de la operación VENTAS, conservando las posiciones escritas como evidencia.',{'columnas_documentales':{'referencia':'CEDOAL','area':'VENTAS'},'interpretacion_area':'UNIDAD_Y_OPERACION_INTERCAMBIADAS_EN_PAPEL'}),
            6514:('Dirección','Arq. Eliza / Cbba.','La foto propia escribe Cbba. y Dirección en ÁREA, junto a Arq. Eliza en REF. Se separa el lugar documental Cbba. de la unidad Dirección, ya catalogada, sin expandir la abreviatura ni inventar nombre completo de la receptora.',{'columnas_documentales':{'referencia':'Arq. Eliza','area':'Cbba. Dirección'},'procedencia_documental':'Cbba.'}),
            5164:(None,'COSIG.','La foto propia escribe COSIG. en ÁREA junto a MARTINEZ ACCHINI y salida 10. Es una indicación documental de consignación, no el nombre de una unidad. Se conserva el literal COSIG. como referencia sin crear un área o alias ni modificar cantidades.',{'columnas_documentales':{'referencia':None,'area':'COSIG.'},'interpretacion_area':'INDICACION_DE_CONSIGNACION_NO_UNIDAD'})
        }
        for id,(area,ref,motivo,extra) in especificos.items():
            m=db.get(M,id)
            c=clasificar_movimiento(m.detalle,ref,area,m.ingresos,m.salidas,db)
            assert not c.requiere_auditoria_nodo and not c.requiere_auditoria_referencia
            cambios={'area':area,'referencia':ref,**{k:getattr(c,k) for k in DERIVADOS}}
            out[id]=(cambios,['T01','T17','T23'],motivo+' Se conservan íntegramente fecha, cifras, saldo documental y reconstruido, hipótesis, revisión anterior y vecinos.',extra)
    return out

if __name__=='__main__':
    congelar(construir(numero=94,especificaciones=casos(),pendientes=[],limites=[
        'Cuatro objetivos HIL y cuatro fotos propias completas; vecinos de contexto sin modificaciones.',
        'Unidades Galería, CEDOAL y Dirección ya existentes; sin nuevas áreas ni alias.',
        'Conservar posiciones documentales, receptora literal y COSIG. sin expandir o inventar datos.'
    ]))
