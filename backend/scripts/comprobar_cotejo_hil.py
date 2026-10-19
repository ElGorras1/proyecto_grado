"""Ensaya y aplica un plan congelado con comprobaciones de conservación y elegibilidad."""
import argparse
import json
from datetime import datetime,UTC
from pathlib import Path
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.kardex import MovimientoKardex as M
from app.models.activos import Activo
from app.models.inventario import AperturaInventario
from app.services.revision_documental import snapshot_revision,pagina_sql
from app.services.calidad_kardex import tipos_alerta
from app.services.datos_analitica import leer_corte,seleccionar
from scripts.aplicar_revision_hil import aplicar,fuente_hash,DEST,BACKEND
from scripts.generar_plan_revision_hil import digest
from scripts.respaldo_recuperacion import nueva_copia
from scripts.preparar_analitica import digest_tablas


def verificar_protecciones_y_recuentos(db,plan):
    for id,anterior in plan['cotejo'].get('rectificaciones_previas',{}).items():
        m=db.get(M,int(id));actual=snapshot_revision(m);previa=anterior['revision']
        assert all(actual[k]==v for k,v in anterior['valores'].items()),'Una rectificación de lectura documental alteró datos vigentes protegidos'
        rev=m.revision_documental
        assert rev['revision_previa_rectificacion_documental']==previa,'Se perdió la revisión anterior a la rectificación'
        permitidos=set(anterior['metadatos_rectificables'])
        for k,v in previa.items():
            if k in permitidos or k in ('plan_sha256','revisado_en','autor_registro'):continue
            if k in ('criterios','hallazgos','planes_aplicados'):assert set(v)<=set(rev[k])
            elif k=='motivo':assert rev[k].startswith(v)
            else:assert rev[k]==v,('Metadato previo alterado sin autorización específica',id,k)
    for rectificacion in plan['cotejo'].get('rectificaciones_documentales',[]):
        m=db.get(M,rectificacion['id'])
        assert all(m.revision_documental[k]==v for k,v in rectificacion['metadatos'].items()),'La rectificación no coincide con su evidencia congelada'
    for protegido in plan['cotejo'].get('articulos_protegidos',[]):
        aid=protegido['id'];articulo=db.get(Activo,aid)
        assert articulo is not None and digest(snapshot_revision(articulo))==protegido['sha256_articulo'],('Artículo protegido modificado',aid)
        filas=[snapshot_revision(m) for m in db.query(M).filter(M.articulo_id==aid).order_by(M.id)]
        assert len(filas)==protegido['filas'] and digest(filas)==protegido['sha256_filas'],('Filas protegidas modificadas',aid)
    for recuento in [*plan['cotejo'].get('recuentos_recuperados',[]),*plan['cotejo'].get('recuentos_documentales',[])]:
        filas=([db.get(M,recuento['id'])] if 'id' in recuento else
            db.query(M).filter(M.revision_documental['recuperacion_clave'].as_string()==recuento['clave']).all())
        assert len(filas)==1,'El recuento recuperado debe ser único'
        m=filas[0];assert m is not None;rev=m.revision_documental
        assert m.estado=='ACTIVO' and rev['tipo_fila']=='RECUENTO'
        assert m.saldo_registrado==m.saldo_calculado==rev['saldo_documental']==recuento['escrito']
        assert rev['diferencia_con_cadena_previa']==recuento['diferencia']==recuento['escrito']-recuento['previo']
        assert m.ingresos is None and m.salidas is None,'Un recuento no debe crear un movimiento de compensación'


def verificar(db,plan,sha):
    verificar_protecciones_y_recuentos(db,plan)
    ids={e['articulo_id'] for e in plan['revisiones']}
    filas=db.query(M).filter(M.articulo_id.in_(ids)).order_by(M.articulo_id,M.lote_id,pagina_sql(),M.orden_fila,M.id).all()
    por_id={m.id:m for m in filas}
    if plan['cotejo'].get('anclajes_previos'):
        from scripts.cotejo_con_anclajes_hil import verificar_anclajes
        verificar_anclajes(plan,por_id)
    for e in plan['revisiones']:
        m=por_id[e['id']];actual=snapshot_revision(m)
        assert all(actual[k]==v for k,v in e['cambios'].items()),e['id']
        assert sha in m.revision_documental['planes_aplicados']
    for recuperacion in plan.get('recuperaciones',[]):
        candidatas=[m for m in filas if (m.revision_documental or {}).get('recuperacion_clave')==recuperacion['clave']]
        assert len(candidatas)==1,'La recuperación debe existir una sola vez'
        actual=snapshot_revision(candidatas[0])
        assert all(actual[k]==v for k,v in recuperacion['campos'].items()),'La recuperación no coincide con el plan congelado'
        assert sha in candidatas[0].revision_documental['planes_aplicados']
    for nota in plan['observaciones_articulos']:
        observacion=db.get(Activo,nota['articulo_id']).observacion_hil or {}
        assert sha in observacion.get('planes_aplicados',[]),'Falta la observación del artículo'
    activos=[m for m in filas if m.estado=='ACTIVO']
    if plan.get('recuperaciones'):
        posiciones=[(m.articulo_id,m.lote_id,m.numero_pagina,m.orden_fila) for m in activos]
        assert len(posiciones)==len(set(posiciones)),'La recuperación dejó posiciones físicas repetidas'
    # Un cotejo puede conservar una duda material. Exigir la resolución de
    # todos los avisos obligaría a certificar inferencias o borrar evidencia.
    pendientes=plan['cotejo'].get('pendientes_documentales',{})
    presentes={str(m.id):[t for t,v in (('saldo',m.tiene_error_saldo),('fecha',m.tiene_error_fecha)) if v]
        for m in activos if m.tiene_error_saldo or m.tiene_error_fecha}
    assert presentes==pendientes,(presentes,pendientes)
    for aid,cierre in plan['cotejo']['cierres'].items():
        ultima=next(m for m in reversed(activos) if m.articulo_id==int(aid))
        calculado=plan['cotejo'].get('cierres_calculados',{}).get(str(aid),cierre)
        assert ultima.saldo_registrado==cierre and ultima.saldo_calculado==calculado
        if calculado!=cierre:
            from app.services.inventario import base_kardex_dict
            assert not base_kardex_dict(ultima)['operable'],'El cierre pendiente no debe abrir inventario automáticamente'
        assert db.get(AperturaInventario,int(aid)) is None
        if int(aid) in plan['cotejo'].get('cierres_no_operables',[]):
            from app.services.inventario import base_kardex_dict
            assert not base_kardex_dict(ultima)['operable'],'Un cierre negativo o pendiente no puede abrir inventario'
    corte=leer_corte(db);elegibles,_=seleccionar(corte['filas']);elegibles={f['id'] for f in elegibles}
    inferidos=[]
    for m in filas:
        r=m.revision_documental
        if m.estado!='ACTIVO' or r.get('origen_fecha') in ('HIPOTESIS','SECUENCIA_AJUSTADA') or r.get('origen_saldo')=='HIPOTESIS' or r.get('origen_saldo_base')=='HIPOTESIS' or r.get('origen_cantidades')=='HIPOTESIS':
            assert m.id not in elegibles,m.id
            inferidos.append(m.id)
    reintentos={}
    for path in [DEST/'plan_correcciones.json',*sorted(DEST.glob('plan_continuacion_[0-9][0-9].json'))]:
        if path.name!='plan_correcciones.json' and int(path.stem.rsplit('_',1)[-1])>plan['version']:continue
        r=aplicar(db,json.loads(path.read_text(encoding='utf-8')),confirmar=False)
        reintentos[path.name]={k:r[k] for k in ('aplicadas','auditorias_movimientos','observaciones_articulos')}
        assert all(v==0 for v in reintentos[path.name].values()),path.name
    return filas,inferidos,reintentos


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--numero',type=int,choices=range(9,100),required=True)
    parser.add_argument('--respaldo',type=Path,required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--ensayo',action='store_true');mode.add_argument('--ejecutar',action='store_true')
    args=parser.parse_args();sufijo=f'{args.numero:02d}'
    path=DEST/f'plan_continuacion_{sufijo}.json';plan=json.loads(path.read_text(encoding='utf-8'))
    assert plan['version']==args.numero
    resultado_path=DEST/f'resultado_continuacion_{sufijo}.json'
    prueba_path=DEST/f'ensayo_plan_continuacion_{sufijo}.json'
    respaldo=args.respaldo.resolve();assert respaldo.is_relative_to((BACKEND/'backups').resolve())
    if args.ensayo:
        target,nombre,_=nueva_copia(respaldo,'hil'+sufijo+datetime.now(UTC).strftime('%Y%m%d%H%M%S'),'activos_continuacion_qa_')
    else:
        if resultado_path.exists():raise RuntimeError('Conservar el resultado existente; verificar reintentos aparte.')
        prueba=json.loads(prueba_path.read_text(encoding='utf-8'))
        assert prueba['verificado'] and prueba['plan_sha256']==digest(plan)
        target,nombre=engine,'institucional'
    aids={e['articulo_id'] for e in plan['revisiones']}
    with target.connect() as conn:antes=digest_tablas(conn,inspect(conn).get_table_names())
    with Session(target) as db:
        original=fuente_hash(db)
        previos={m.id:snapshot_revision(m) for m in db.query(M).filter(M.articulo_id.in_(aids))}
        reporte=aplicar(db,plan,confirmar=True)
    with Session(target) as db:
        filas,inferidos,reintentos=verificar(db,plan,digest(plan))
        assert fuente_hash(db,excluir_ids=reporte.get('filas_recuperadas',[]))==original
        fuente_final=fuente_hash(db)
        actuales={m.id:snapshot_revision(m) for m in db.query(M).filter(M.articulo_id.in_(aids))}
        campos=('fecha_movimiento','detalle','referencia','area','ingresos','salidas','saldo_registrado','estado','orden_pagina_validado','orden_fila')
        # Las recuperadas no tienen un registro previo: se informan como altas
        # documentales, no como correcciones de una extracción inexistente.
        comparables={id:r for id,r in actuales.items() if id in previos}
        assert set(actuales)-set(previos)==set(reporte.get('filas_recuperadas',[]))
        cambios={k:sum(previos[id][k]!=r[k] for id,r in comparables.items()) for k in campos}
        cambiados=sum(any(previos[id][k]!=r[k] for k in campos) for id,r in comparables.items())
        revisados=db.query(M).filter(M.revision_documental.isnot(None)).count()
        pendientes=sum(bool(tipos_alerta(m)) for m in db.query(M).filter(M.lote_id.isnot(None),M.estado=='ACTIVO'))
    with target.connect() as conn:despues=digest_tablas(conn,inspect(conn).get_table_names())
    modificadas=[t for t in antes if antes[t]!=despues[t]]
    assert set(modificadas)<={'movimientos_kardex','activo','auditoria_sistema'},modificadas
    reporte.update(verificado=True,base_ensayo=nombre,fuente_sha256=fuente_final,fuente_preexistente_sha256=original,tablas_modificadas=modificadas,
        inferidos_y_notas_excluidos=inferidos,reintentos=reintentos,cotejo=plan['cotejo'],
        revisados_acumulados=revisados,pendientes_hil=pendientes,campos_modificados=cambios,movimientos_con_cambios=cambiados)
    out=prueba_path if args.ensayo else resultado_path
    out.write_text(json.dumps(reporte,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps({k:v for k,v in reporte.items() if k not in ('perfil_analitica','reintentos','inferidos_y_notas_excluidos')},ensure_ascii=False))


if __name__=='__main__':main()
