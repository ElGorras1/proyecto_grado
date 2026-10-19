"""Control negativo del cierre pendiente de Campero, únicamente en la copia QA."""
import copy,json
from sqlalchemy import create_engine,inspect,text
from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.kardex import MovimientoKardex as M
from app.services.datos_analitica import leer_corte,seleccionar
from app.services.inventario import base_kardex_dict
from scripts.aplicar_revision_hil import DEST
from scripts.comprobar_cotejo_hil import verificar
from scripts.generar_plan_revision_hil import digest
from scripts.preparar_analitica import digest_tablas


def main():
    plan=json.loads((DEST/'plan_continuacion_17.json').read_text(encoding='utf-8'))
    prueba=json.loads((DEST/'ensayo_plan_continuacion_17.json').read_text(encoding='utf-8'))
    assert prueba['verificado'] and prueba['plan_sha256']==digest(plan)
    nombre=prueba['base_ensayo'];assert nombre.startswith('activos_continuacion_qa_hil17')
    target=create_engine(engine.url.set(database=nombre))
    with target.connect() as c:antes=digest_tablas(c,inspect(c).get_table_names())
    with Session(target,autoflush=False) as db:
        db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
        incorrecto=copy.deepcopy(plan);incorrecto['cotejo'].pop('pendientes_documentales')
        try:verificar(db,incorrecto,digest(plan))
        except AssertionError as exc:
            assert exc.args==(({'4871':['saldo']},{}),),exc
        else:raise AssertionError('El verificador aceptó ocultar una duda documental')
        filas=db.query(M).filter(M.articulo_id==81).all();assert len(filas)==161
        elegibles,_=seleccionar(leer_corte(db)['filas'])
        assert not {m.id for m in filas}.intersection(f['id'] for f in elegibles)
        cierre=db.get(M,4871);base=base_kardex_dict(cierre)
        assert cierre.saldo_registrado==300 and cierre.saldo_calculado==309
        assert cierre.tiene_error_saldo and not base['operable']
        db.rollback()
    with target.connect() as c:despues=digest_tablas(c,inspect(c).get_table_names())
    assert antes==despues
    resultado={'base_ensayo':nombre,'plan_sha256':digest(plan),'ocultar_pendiente_rechazado':True,
        'filas_excluidas_entrenamiento':161,'cierre_escrito':300,'calculado_condicional':309,
        'apertura_automatica_bloqueada':True,'tablas_modificadas':[]}
    (DEST/'control_negativo_pendiente_17.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(resultado,ensure_ascii=False))


if __name__=='__main__':main()
