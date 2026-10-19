"""Retira exigencia de área operativa de doce bases/recuentos ya acreditados documentalmente."""
from scripts.plan_enmienda_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.calidad_kardex import tipos_alerta

IDS=[408,510,970,1981,5936,7162,7294,7384,7930,8534,9765,9792]
def casos():
    out={}
    with SessionLocal() as db:
        for id in IDS:
            m=db.get(M,id);r=m.revision_documental
            assert tipos_alerta(m)==['area'] and m.area is None and m.ingresos is None and m.salidas is None
            assert r['tipo_fila'] in ['BASE_DOCUMENTAL','RECUENTO']
            nodo='Recuento documental' if r['tipo_fila']=='RECUENTO' else 'Base documental'
            motivo=r['motivo']+' Enmienda de clasificación: esta base/recuento documental sin ingreso ni salida no representa una transferencia a un área operativa. Se retira solo esa exigencia; se conservan base, fecha, discrepancias, hipótesis, revisión anterior y exclusiones. No acredita conteo actual ni conciliación institucional.'
            out[id]=({'nodo_grafo':nodo,'area_estado':'NO_APLICA','requiere_auditoria_nodo':False},['T15' if r['tipo_fila']=='RECUENTO' else 'T22'],motivo,{'clasificacion_documental_sin_flujo':True})
    return out
if __name__=='__main__':
    congelar(construir(numero=85,especificaciones=casos(),pendientes=[],limites=['Doce avisos de área de bases/recuentos ya cotejados con fotos, sin cantidades de flujo.','Solo se corrigen tres campos derivados de clasificación; no se asigna, define ni crea ninguna área o alias.','Diferencias de recuentos, saldos hipotéticos y revisiones anteriores quedan intactos.','Los avisos de columnas ambiguas y de áreas realmente pendientes se conservan aunque se conozca la clase de operación.']))
