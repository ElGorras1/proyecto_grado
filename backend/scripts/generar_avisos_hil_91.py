"""Códigos documentales escritos en ÁREA, sin atribuirles una unidad institucional."""
from scripts.plan_enmienda_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar,DERIVADOS
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.clasificador_nodos import clasificar_movimiento

IDS=[85,512,513,707,976,977,983,1160,1161,1164,1165,1274,1277,1278,1496,1499,1987,1988,5724,5725,5726,5739,5740,5741,5746,5750,5752,5753,5940,5941,5946,5948,5949,5951,5958,5959,5960,7310]
def casos():
    out={}
    with SessionLocal() as db:
        for id in IDS:
            m=db.get(M,id);assert m.area and any(c.isdigit() for c in m.area)
            codigo='019-08' if id==977 else m.area
            ref=(m.referencia+' / ' if m.referencia else '')+codigo
            c=clasificar_movimiento(m.detalle,ref,None,m.ingresos,m.salidas,db)
            assert not c.requiere_auditoria_nodo and not c.requiere_auditoria_referencia
            cambios={'area':None,'referencia':ref,**{k:getattr(c,k) for k in DERIVADOS}}
            motivo=f'La foto propia escribe el código {codigo} en ÁREA'+(f' y {m.referencia} en REF' if m.referencia else '')+'. Se conserva como referencia documental literal y se documenta su posición original. El número no acredita un área institucional: no se crea unidad numérica ni se identifica emisor, receptor o significado del código por semejanza. El área institucional queda sin registrar; cantidades, saldos, fechas e hipótesis previas permanecen intactos.'
            if id==977:motivo+=' La celda permite leer 019-08, no 014-08 de la extracción; la lectura anterior se conserva en auditoría y primera extracción.'
            extra={'columnas_documentales':{**(m.revision_documental.get('columnas_documentales') or {}),'area':codigo,'referencia':m.referencia},'codigo_documental_sin_interpretar':codigo,'interpretacion_area':'CODIGO_DOCUMENTAL_NO_UNIDAD_INSTITUCIONAL','significado_codigo_no_acreditado':True}
            out[id]=(cambios,['T01','T17','T23'],motivo,extra)
    return out
if __name__=='__main__':
    congelar(construir(numero=91,especificaciones=casos(),pendientes=[],limites=['Treinta y ocho avisos vigentes y doce fotografías propias completas; vecinos de consulta intactos.','Los códigos conservan su texto y posición documental sin inventar significado, institución ni responsable.','Área institucional sin registrar no significa atribuir ESIP ni Sala como responsables o destinos por su aparición en REF.','Sin cambios al catálogo, alias, cantidades, fechas o saldos; fuentes y revisiones anteriores íntegras.']))
