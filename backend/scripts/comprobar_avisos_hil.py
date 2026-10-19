"""Aplica planes focalizados: ninguna fila ajena a los avisos puede cambiar."""
import argparse,json
from datetime import datetime,UTC
from sqlalchemy import inspect,text
from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.kardex import MovimientoKardex as M
from app.models.inventario import AperturaInventario
from app.services.calidad_kardex import tipos_alerta
from app.services.revision_documental import snapshot_revision
from app.services.datos_analitica import leer_corte,seleccionar
from scripts.aplicar_revision_hil import DEST,BACKEND,aplicar,fuente_hash
from scripts.generar_plan_revision_hil import digest
from scripts.preparar_analitica import digest_tablas
from scripts.respaldo_recuperacion import nueva_copia

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--numero',type=int,required=True);p.add_argument('--respaldo',required=True)
    grupo=p.add_mutually_exclusive_group(required=True);grupo.add_argument('--ensayo',action='store_true');grupo.add_argument('--ejecutar',action='store_true')
    a=p.parse_args();s=f'{a.numero:02d}';plan=json.loads((DEST/f'plan_continuacion_{s}.json').read_text(encoding='utf-8'));sha=digest(plan)
    assert plan['cotejo']['modo']=='SOLO_AVISOS_HIL' and not plan.get('recuperaciones') and not plan['observaciones_articulos']
    assert not (DEST/'detener_continuidad_hil.flag').exists(),'Respetar pausa humana'
    ids={e['id'] for e in plan['revisiones']};assert ids==set(plan['cotejo']['ids_objetivo'])
    out=DEST/(f'ensayo_plan_continuacion_{s}.json' if a.ensayo else f'resultado_continuacion_{s}.json');assert not out.exists(),'No sobrescribir resultados'
    if a.ensayo:
        target,nombre,_=nueva_copia((BACKEND/a.respaldo).resolve(),'avisos'+s+datetime.now(UTC).strftime('%Y%m%d%H%M%S'),'activos_continuacion_qa_')
    else:
        prueba=json.loads((DEST/f'ensayo_plan_continuacion_{s}.json').read_text(encoding='utf-8'))
        assert prueba['verificado'] and prueba['plan_sha256']==sha and prueba['filas_fuera_objetivo_modificadas']==[]
        target,nombre=engine,'institucional'
    with target.connect() as c:tablas_antes=digest_tablas(c,inspect(c).get_table_names())
    with Session(target) as db:
        antes={m.id:snapshot_revision(m) for m in db.query(M)};fuente=fuente_hash(db)
        ajuste=plan.get('ajuste_fecha_inferida_de_plan')
        if ajuste:
            padre=json.loads((DEST/f'plan_continuacion_{ajuste:02d}.json').read_text(encoding='utf-8'))
            rp=json.loads((DEST/f'resultado_continuacion_{ajuste:02d}.json').read_text(encoding='utf-8'))
            assert padre['cotejo']['modo']=='SOLO_AVISOS_HIL' and rp['verificado'] and rp['plan_sha256']==digest(padre)
            origenes={e['id']:e for e in padre['revisiones']}
            # Enmienda exclusivamente de la etiqueta de fechas ya revisadas: no abre nuevos objetivos.
            for e in plan['revisiones']:
                m=db.get(M,e['id']);rev=m.revision_documental or {};prev=origenes[e['id']]
                assert prev['revision']['avisos_antes'] and rp['plan_sha256'] in rev['planes_aplicados']
                assert rev['origen_fecha']=='HIPOTESIS' and rev['fecha_documental'] is None
                assert e['cambios']=={'fecha_movimiento':m.fecha_movimiento.isoformat()}
                assert e['revision']['origen_fecha']=='HIPOTESIS' and e['revision']['fecha_documental'] is None
                assert e['revision']['origen_saldo']==rev['origen_saldo'] and e['revision']['saldo_documental']==rev['saldo_documental']
        else:
            for id in ids:assert tipos_alerta(db.get(M,id)),('La fila no es un aviso HIL',id)
        avisos_antes={m.id:tipos_alerta(m) for m in db.query(M) if m.lote_id and m.estado=='ACTIVO' and tipos_alerta(m)}
        r=aplicar(db,plan,confirmar=True)
    with Session(target) as db:
        actuales={m.id:snapshot_revision(m) for m in db.query(M)}
        assert set(antes)==set(actuales) and fuente_hash(db)==fuente
        ajenos=[id for id in antes if id not in ids and antes[id]!=actuales[id]]
        assert not ajenos,('No cambiar filas normales ni anclajes por contexto',ajenos)
        for e in plan['revisiones']:
            id=e['id'];actual=actuales[id]
            assert all(actual[k]==v for k,v in e['cambios'].items()),id
            assert sha in actual['revision_documental']['planes_aplicados']
            assert actual['revision_documental']['alcance']=='SOLO_MOVIMIENTO_OBSERVADO_HIL' and not actual['revision_documental']['cotejo_pagina_completa']
            permitidos=set(e['cambios'])|{'revision_documental','saldo_calculado','tiene_error_saldo','tiene_error_fecha','fecha_estado'}
            assert not {k for k in actual if actual[k]!=antes[id][k]}-permitidos
        pendientes={id:tipos_alerta(db.get(M,id)) for id in ids if tipos_alerta(db.get(M,id))}
        assert sorted(pendientes)==sorted(plan['cotejo']['ids_pendientes_esperados']),pendientes
        elegibles,_=seleccionar(leer_corte(db)['filas']);elegibles={f['id'] for f in elegibles}
        for id in ids:
            rev=actuales[id]['revision_documental']
            if rev.get('origen_saldo_base')=='HIPOTESIS' or rev.get('origen_fecha') in ('HIPOTESIS','SECUENCIA_AJUSTADA'):assert id not in elegibles
        for aid in {e['articulo_id'] for e in plan['revisiones']}:assert db.get(AperturaInventario,aid) is None
        reintento=aplicar(db,plan,confirmar=False)
        assert all(reintento[k]==0 for k in ('aplicadas','auditorias_movimientos','observaciones_articulos'))
    with target.connect() as c:tablas_despues=digest_tablas(c,inspect(c).get_table_names())
    modificadas=[t for t in tablas_antes if tablas_antes[t]!=tablas_despues[t]]
    assert set(modificadas)<={'movimientos_kardex','auditoria_sistema'}
    r['estados_contexto_solo_consulta']=r.pop('estados')
    r.update(limite='Solo movimientos observados HIL; filas fuera de los objetivos intactas y sin cotejo masivo.',verificado=True,base_ensayo=nombre,fuente_sha256=fuente,filas_fuera_objetivo_modificadas=ajenos,
        avisos_antes={str(id):avisos_antes.get(id,[]) for id in sorted(ids)},avisos_despues=pendientes,
        resueltos=sorted(ids-set(pendientes)),cotejados_con_pendiente=sorted(pendientes),tablas_modificadas=modificadas,
        cotejo=plan['cotejo'],sin_cambios_en_filas_normales=True,reintento_sin_cambios=True)
    out.write_text(json.dumps(r,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps({k:v for k,v in r.items() if k!='perfil_analitica'},ensure_ascii=False))

if __name__=='__main__':main()
