"""Lecturas inequívocas de unidades que ya están en el catálogo; sin alias nuevos."""
from sqlalchemy import text
from scripts.plan_enmienda_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar,DERIVADOS
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.clasificador_nodos import clasificar_movimiento

DIRECCION=[1422,1569,2673,4419,4892,4893,5771,5772,5777,5779,5788,5789,5790,5791,6429,7734]
def casos():
    out={}
    with SessionLocal() as db:
        for id,normal in [(i,'Dirección') for i in DIRECCION]+[(4252,'CAP'),(4258,'CAP'),(6758,'C+C'),(6761,'C+C')]:
            m=db.get(M,id)
            assert db.execute(text('SELECT id FROM catalogo_areas WHERE nombre_oficial=:n OR abreviatura=:n'),{'n':normal}).first()
            c=clasificar_movimiento(m.detalle,m.referencia,normal,m.ingresos,m.salidas,db)
            assert not c.requiere_auditoria_nodo
            literal='Dirección' if id in DIRECCION else 'CAP' if id==4252 else 'C.A.P.' if id==4258 else 'C+C'
            motivo=f'La fotografía propia permite leer {literal} en ÁREA. Se normaliza la grafía a {normal}, ya existente exactamente en el catálogo, conforme al criterio T17 del titular. Se corrige solo este movimiento observado; no se crea ni confirma alias, no se atribuye una persona responsable y no se cambia el destinatario del detalle. Cifras, saldos, fechas y vecinos intactos.'
            if id in [6758,6761]:motivo+=' C+C se conserva como C+C: no se fusiona con CTC ni se expande la sigla; solo se corrige el derivado pendiente pese a la coincidencia exacta existente.'
            extra={'columnas_documentales':{**(m.revision_documental.get('columnas_documentales') or {}),'area':literal},'normalizacion_grafia_area':{'literal':literal,'vigente':normal,'fundamento':'Foto propia y nombre o abreviatura exactos del catálogo existente; no fuzzy ni alias nuevo.'}}
            out[id]=({'area':normal,**{k:getattr(c,k) for k in DERIVADOS}},['T01','T17'],motivo,extra)
    return out
if __name__=='__main__':
    congelar(construir(numero=88,especificaciones=casos(),pendientes=[],limites=['Veinte avisos vigentes, once fotografías propias completas consultadas.','Se usa solo catálogo existente; no se modifica catálogo ni sinónimos y no se atribuye responsables.','Se conserva C+C separado de CTC y POLIGENESIS separado de REV DE HISTORIA POLIGENESIS 1.','Ningún vecino, cantidad, saldo o fecha cambia; revisión anterior íntegra.']))
