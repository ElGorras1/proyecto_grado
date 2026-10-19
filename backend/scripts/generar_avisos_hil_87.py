"""Feria escrita como evento de contexto, no como unidad institucional."""
from scripts.plan_enmienda_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar,DERIVADOS
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.clasificador_nodos import clasificar_movimiento

IDS=[7449,7518,7565,7723,8469,8599,9637,10396,10455,10479,10598,11286,11884]
def casos():
    out={}
    with SessionLocal() as db:
        for id in IDS:
            m=db.get(M,id);assert m.area=='Feria' and m.referencia is None
            assert bool(m.ingresos)!=bool(m.salidas)
            c=clasificar_movimiento(m.detalle,'Feria',None,m.ingresos,m.salidas,db)
            cambios={'area':None,'referencia':'Feria',**{k:getattr(c,k) for k in DERIVADOS}}
            # El texto Devolución no invierte el efecto cuantitativo documentado.
            if m.salidas:cambios.update(nodo_grafo='Salida: Feria del Libro (FIL)',area_estado='NO_APLICA',requiere_auditoria_nodo=False)
            motivo='La foto completa escribe Feria en ÁREA de esta fila, como evento de la operación y sin nombre de unidad institucional. Se conserva como referencia literal Feria y su posición documental; no se crea un área Feria ni se asigna una institución. Se mantienen cantidades, fecha, saldos y toda hipótesis o discrepancia anterior.'
            if id==7449:motivo+=' La columna escrita es SALIDAS 6: se conserva como egreso aunque el detalle diga Devolución; no se transforma en ingreso.'
            if id==8469:motivo+=' Ingreso 6 y saldo repasado continúan hipotéticos según la revisión anterior; no se certifican por esta clasificación.'
            extra={'columnas_documentales':{**(m.revision_documental.get('columnas_documentales') or {}),'area':'Feria','referencia':None},'referencia_tipo_documental':'EVENTO','interpretacion_area':'EVENTO_NO_UNIDAD_INSTITUCIONAL'}
            out[id]=(cambios,['T17','T23'],motivo,extra)
    return out
if __name__=='__main__':
    congelar(construir(numero=87,especificaciones=casos(),pendientes=[],limites=['Trece observados y trece fotos propias completas; sin cambios en cantidades, fechas, saldos o vecinos.','Feria se conserva como evento escrito; no se define área ni se crea alias.','7449 sigue egreso 6; 8469 mantiene cantidad hipotética y exclusión.']))
