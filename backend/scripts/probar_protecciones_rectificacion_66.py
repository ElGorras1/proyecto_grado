"""Pruebas negativas de la agrupación, recepción y revisión aprobadas de 560."""
from copy import deepcopy
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.kardex import MovimientoKardex as M
from scripts.aplicar_revision_hil import DEST
from scripts.comprobar_cotejo_hil import verificar_protecciones_y_recuentos

def main():
    plan=json.loads((DEST/'plan_continuacion_66.json').read_text(encoding='utf-8'))
    ensayo=json.loads((DEST/'ensayo_plan_continuacion_66.json').read_text(encoding='utf-8'))
    assert ensayo['verificado'] and ensayo['base_ensayo'].startswith('activos_continuacion_qa_')
    qa=create_engine(engine.url.set(database=ensayo['base_ensayo']))
    resultados=[]
    with Session(qa,autoflush=False) as db:
        verificar_protecciones_y_recuentos(db,plan)
        m=db.get(M,560)
        campos=('ingresos','saldo_registrado','estado','revision_documental')
        for caso in ('eliminar_ingreso_aprobado','cambiar_saldo_a_cadena','convertir_en_nota','borrar_agrupacion_confirmada','borrar_revision_previa'):
            original={k:deepcopy(getattr(m,k)) for k in campos}
            if caso=='eliminar_ingreso_aprobado':m.ingresos=None
            elif caso=='cambiar_saldo_a_cadena':m.saldo_registrado=51
            elif caso=='convertir_en_nota':m.estado='NOTA_DOCUMENTAL'
            else:
                r=deepcopy(m.revision_documental)
                if caso=='borrar_agrupacion_confirmada':r['criterios'].remove('T20')
                else:r['revision_previa_rectificacion_documental'].pop('motivo')
                m.revision_documental=r
            try:verificar_protecciones_y_recuentos(db,plan)
            except AssertionError:resultados.append({'caso':caso,'rechazado':True})
            else:raise AssertionError('Protección insuficiente: '+caso)
            finally:
                for k,v in original.items():setattr(m,k,v)
        db.rollback()
        verificar_protecciones_y_recuentos(db,plan)
    qa.dispose()
    (DEST/'protecciones_rectificacion_66.json').write_text(json.dumps({'base':'copia_QA','casos':resultados,'sin_escrituras':True},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(resultados,ensure_ascii=False))

if __name__=='__main__':main()
