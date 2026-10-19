"""Trece lecturas de áreas, recuperadas de seis fotografías propias."""
from scripts.plan_enmienda_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar,DERIVADOS
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.clasificador_nodos import clasificar_movimiento

IDS=[2217,5179,8602,8603,8610,8617,10264,10276,10279,10330,10333,10335,10458]
def casos():
    out={}
    with SessionLocal() as db:
        for id in IDS:
            m=db.get(M,id);area='CAP' if id==8610 else 'CEDOAL'
            cambios={'area':area}
            if id==8602:cambios['referencia']='E. Arandia'
            if id==8610:cambios['detalle']='Chile'
            if id==10330:cambios['detalle']='Cedoal Oruro'
            c=clasificar_movimiento(cambios.get('detalle',m.detalle),cambios.get('referencia',m.referencia),area,m.ingresos,m.salidas,db)
            assert not c.requiere_auditoria_nodo
            cambios.update({k:getattr(c,k) for k in DERIVADOS})
            motivo=f'La foto propia permite leer {area} en ÁREA; se corrige la lectura OCR {m.area!r} y se usa únicamente la abreviatura exacta del catálogo existente. No se completa una sigla parcial por frecuencia ni se crea alias. Cantidades, fechas y saldos permanecen intactos; se mantienen todas las hipótesis y discrepancias anteriores.'
            if id==8602:motivo+=' REF se lee E. Arandia, y la nota adherida explicita Edgar Arandia para Carrera de Artes; se corrige E. A. Pandia sin asignarlo como responsable de una transacción digital.'
            if id==8610:motivo+=' DETALLE dice Chile y ÁREA CAP, no Chilo/PAP; se conservan como destinatario literal y área separados.'
            if id==10330:motivo+=' DETALLE dice Cedoal Oruro; se corrige Cedeal sin crear otra institución o localidad.'
            extra={'columnas_documentales':{**(m.revision_documental.get('columnas_documentales') or {}),'area':'C.A.P.' if id==8610 else 'Cedoal' if id in [8602,8603,8617,10264,10276,10279,10330,10333,10335,10458,5179] else 'CEDOAL.'},'lectura_area_corregida_desde_foto':True}
            out[id]=(cambios,['T01','T17','T23'],motivo,extra)
    return out
if __name__=='__main__':
    congelar(construir(numero=89,especificaciones=casos(),pendientes=[],limites=['Solo trece observados, seis fotografías propias consultadas; vecinos intactos.','Solo unidades CEDOAL/CAP ya existentes; sin cambios a catálogo ni alias.','No se cambian cantidades, saldos, fechas ni hipótesis; referencia E. Arandia procede de celda y nota de la misma foto.']))
