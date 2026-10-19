"""Comprueba un rango de cotejos ya aplicados mediante rutas de consulta, sin lifespan."""
import argparse,hashlib,json
from collections import Counter,defaultdict
from datetime import datetime,UTC
from sqlalchemy import inspect,text
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import SessionLocal,engine
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.kardex import MovimientoKardex as M
from app.services.calidad_kardex import tipos_alerta
from app.services.datos_analitica import leer_corte,seleccionar
from app.services.inventario import base_kardex_dict
from app.models.activos import Activo
from scripts.aplicar_revision_hil import BACKEND,DEST,fuente_hash
from scripts.generar_plan_revision_hil import digest
from scripts.preparar_analitica import digest_tablas


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--desde',type=int,required=True);p.add_argument('--hasta',type=int,required=True)
    args=p.parse_args();assert 13<=args.desde<=args.hasta<100
    with engine.connect() as c:antes=digest_tablas(c,inspect(c).get_table_names())
    planes=[json.loads((DEST/f'plan_continuacion_{n:02d}.json').read_text(encoding='utf-8')) for n in range(args.desde,args.hasta+1)]
    resultados=[json.loads((DEST/f'resultado_continuacion_{n:02d}.json').read_text(encoding='utf-8')) for n in range(args.desde,args.hasta+1)]
    with SessionLocal() as db:
        u=db.query(Usuario).join(Rol).filter(Usuario.estado=='activo',Rol.nombre=='Administrador').order_by(Usuario.id).first()
        assert u is not None;token=create_access_token(u.id)
    cliente=TestClient(app);rutas=[];fotos=set();por_id={};catalogo=cliente.get(f'{settings.API_V1_PREFIX}/kardex/articulos',headers={'Authorization':'Bearer '+token})
    assert catalogo.status_code==200;catalogo={a['id']:a for a in catalogo.json()}
    for plan,resultado in zip(planes,resultados):
        sha=digest(plan);assert resultado['verificado'] and sha==resultado['plan_sha256']
        for aid,cierre in plan['cotejo']['cierres'].items():
            aid=int(aid);res=cliente.get(f'{settings.API_V1_PREFIX}/kardex/historial/{aid}',headers={'Authorization':'Bearer '+token})
            assert res.status_code==200
            filas=res.json();esperadas=[e for e in plan['revisiones'] if e['articulo_id']==aid]
            recuperadas=[r for r in plan.get('recuperaciones',[]) if r['campos']['articulo_id']==aid]
            calculado=plan['cotejo'].get('cierres_calculados',{}).get(str(aid),cierre)
            assert len(filas)==len(esperadas)+len(recuperadas) and filas[-1]['saldo_registrado']==cierre
            assert filas[-1]['saldo_calculado']==calculado
            assert sha in catalogo[aid]['observacion_hil']['planes_aplicados']
            por_id.update({m['id']:m for m in filas})
            rutas.append({'articulo':aid,'filas':len(filas),'cierre':cierre,'calculado':calculado,'http':200})
            for recuperacion in recuperadas:
                candidatas=[m for m in filas if (m['revision_documental'] or {}).get('recuperacion_clave')==recuperacion['clave']]
                assert len(candidatas)==1
                m=candidatas[0]
                assert all(m[k]==v for k,v in recuperacion['campos'].items())
                assert sha in m['revision_documental']['planes_aplicados']
                foto=BACKEND/m['ruta_imagen_respaldo'];assert hashlib.sha256(foto.read_bytes()).hexdigest()==recuperacion['sha256_imagen'];fotos.add(str(foto))
        presentes={str(m['id']):[t for t,v in (('saldo',m['tiene_error_saldo']),('fecha',m['tiene_error_fecha'])) if v]
            for m in por_id.values() if m['articulo_id'] in {e['articulo_id'] for e in plan['revisiones']}
            and m['estado']=='ACTIVO' and (m['tiene_error_saldo'] or m['tiene_error_fecha'])}
        assert presentes==plan['cotejo'].get('pendientes_documentales',{})
        for e in plan['revisiones']:
            m=por_id[e['id']]
            assert all(m[k]==v for k,v in e['cambios'].items()),e['id']
            assert sha in m['revision_documental']['planes_aplicados']
            assert m['datos_originales'] is not None and m['ruta_imagen_respaldo']
            if m['estado']!='ACTIVO':
                assert m['fecha_estado']=='NO_APLICA_DOCUMENTAL' and not m['tiene_error_fecha'] and not m['tiene_error_saldo']
            elif m['revision_documental']['origen_fecha'] in ('HIPOTESIS','SECUENCIA_AJUSTADA'):
                assert m['fecha_estado']=='ESTIMADA_HIL'
            foto=BACKEND/m['ruta_imagen_respaldo'];assert hashlib.sha256(foto.read_bytes()).hexdigest()==e['sha256_imagen'];fotos.add(str(foto))
    with SessionLocal() as db:
        db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
        filas=db.query(M).all();hist=[m for m in filas if m.lote_id is not None];activos=[m for m in hist if m.estado=='ACTIVO'];avisos=[m for m in activos if tipos_alerta(m)]
        fotos_hist=defaultdict(list)
        for m in hist:fotos_hist[m.ruta_imagen_respaldo].append(m)
        corte=leer_corte(db);elegibles,_=seleccionar(corte['filas']);elegibles={m['id'] for m in elegibles}
        inferidos=[m['id'] for m in por_id.values() if m['estado']!='ACTIVO'
            or m['revision_documental']['origen_fecha'] in ('HIPOTESIS','SECUENCIA_AJUSTADA')
            or m['revision_documental'].get('origen_saldo_base')=='HIPOTESIS'
            or m['revision_documental'].get('origen_saldo')=='HIPOTESIS'
            or m['revision_documental'].get('origen_cantidades')=='HIPOTESIS']
        assert not elegibles.intersection(inferidos)
        articulos_excluidos=[];cierres_bloqueados=[]
        for plan in planes:
            from scripts.comprobar_cotejo_hil import verificar_protecciones_y_recuentos
            verificar_protecciones_y_recuentos(db,plan)
            if plan['cotejo'].get('anclajes_previos'):
                from scripts.cotejo_con_anclajes_hil import verificar_anclajes
                verificar_anclajes(plan,{m.id:m for m in hist})
            for nota in plan['observaciones_articulos']:
                if nota.get('excluir_entrenamiento'):
                    aid=nota['articulo_id'];obs=db.get(Activo,aid).observacion_hil
                    assert obs['excluir_entrenamiento']
                    ids={m.id for m in hist if m.articulo_id==aid}
                    assert not ids.intersection(elegibles)
                    articulos_excluidos.append(aid)
            for aid,cierre in plan['cotejo']['cierres'].items():
                if plan['cotejo'].get('cierres_calculados',{}).get(str(aid),cierre)!=cierre or int(aid) in plan['cotejo'].get('cierres_no_operables',[]):
                    ultima=next(m for m in reversed(list(por_id.values())) if m['articulo_id']==int(aid) and m['estado']=='ACTIVO')
                    assert not base_kardex_dict(db.get(M,ultima['id']))['operable']
                    cierres_bloqueados.append(int(aid))
        estado={'generado_en':datetime.now(UTC).isoformat(),'desde':args.desde,'hasta':args.hasta,
            'rutas':rutas,'fotos_verificadas':len(fotos),'filas_verificadas':len(por_id),'inferidos_excluidos':len(inferidos),
            'articulos_excluidos_entrenamiento':articulos_excluidos,'cierres_bloqueados':cierres_bloqueados,
            'movimientos_totales':len(filas),'historicos_conservados':len(hist),'historicos_activos':len(activos),'modernos':len(filas)-len(hist),
            'revisados_distintos':sum(bool(m.revision_documental) for m in hist),'historicos_sin_cotejar':sum(not m.revision_documental for m in hist),
            'filas_con_avisos_hil':len(avisos),'filas_con_avisos_aun_sin_cotejar':sum(not m.revision_documental for m in avisos),
            'tipos_avisos':dict(Counter(t for m in avisos for t in tipos_alerta(m))),
            'fotos_historicas':len(fotos_hist),'fotos_completamente_cotejadas':sum(all(m.revision_documental for m in ms) for ms in fotos_hist.values()),
            'fotos_con_filas_sin_cotejar':sum(any(not m.revision_documental for m in ms) for ms in fotos_hist.values()),'fuente_sha256':fuente_hash(db)}
        assert estado['fuente_sha256']==resultados[-1]['fuente_sha256']
    with engine.connect() as c:despues=digest_tablas(c,inspect(c).get_table_names())
    assert antes==despues,'Una consulta no debe cambiar tablas';estado['tablas_modificadas_por_consultas']=[]
    (DEST/f'verificacion_cotejos_{args.desde:02d}_{args.hasta:02d}.json').write_text(json.dumps(estado,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(estado,ensure_ascii=False))


if __name__=='__main__':main()
