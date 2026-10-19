"""Pruebas negativas en copia QA de decisiones previas conservadas en Poetas."""
from copy import deepcopy
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.kardex import MovimientoKardex as M
from scripts.aplicar_revision_hil import DEST
from scripts.comprobar_cotejo_hil import verificar_protecciones_y_recuentos

def main():
    plan=json.loads((DEST/'plan_continuacion_57.json').read_text(encoding='utf-8'))
    ensayo=json.loads((DEST/'ensayo_plan_continuacion_57.json').read_text(encoding='utf-8'))
    assert ensayo['verificado'] and ensayo['base_ensayo'].startswith('activos_continuacion_qa_')
    qa=create_engine(engine.url.set(database=ensayo['base_ensayo']))
    resultados=[]
    with Session(qa,autoflush=False) as db:
        verificar_protecciones_y_recuentos(db,plan)
        for caso in ('cambiar_ingreso_aprobado','borrar_revision_previa','certificar_fecha_ajustada','cambiar_saldo_aprobado'):
            m=db.get(M,746 if caso=='certificar_fecha_ajustada' else 733)
            original={k:deepcopy(getattr(m,k)) for k in ('ingresos','saldo_registrado','revision_documental')}
            if caso=='cambiar_ingreso_aprobado':m.ingresos=0
            elif caso=='borrar_revision_previa':
                r=deepcopy(m.revision_documental)
                r['revision_previa_rectificacion_documental'].pop('motivo')
                m.revision_documental=r
            elif caso=='certificar_fecha_ajustada':
                r=deepcopy(m.revision_documental);r['origen_fecha']='FOTO';m.revision_documental=r
            else:m.saldo_registrado=79
            try:verificar_protecciones_y_recuentos(db,plan)
            except AssertionError:resultados.append({'caso':caso,'rechazado':True})
            else:raise AssertionError('La protección permitió '+caso)
            finally:
                for k,v in original.items():setattr(m,k,v)
        db.rollback()
        verificar_protecciones_y_recuentos(db,plan)
    qa.dispose()
    (DEST/'protecciones_rectificacion_57.json').write_text(json.dumps({'base':'copia_QA','casos':resultados,'sin_escrituras':True},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(resultados,ensure_ascii=False))

if __name__=='__main__':main()
