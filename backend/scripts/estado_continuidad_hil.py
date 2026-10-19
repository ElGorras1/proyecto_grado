"""Inventario de avance HIL de solo lectura; --guardar conserva el punto de continuidad."""
import argparse,json
from collections import Counter,defaultdict
from datetime import UTC,datetime
from pathlib import Path
from sqlalchemy import text
from app.db.session import SessionLocal
from app.models.activos import Activo
from app.models.kardex import MovimientoKardex as M
from app.services.calidad_kardex import tipos_alerta
from scripts.aplicar_revision_hil import DEST,fuente_hash
from scripts.generar_plan_revision_hil import digest


def consultar():
    grupos=defaultdict(list);fotos=defaultdict(list)
    with SessionLocal() as db:
        db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
        historicos=db.query(M).filter(M.lote_id.isnot(None)).order_by(M.id).all()
        huellas={m.id:set((m.revision_documental or {}).get('planes_aplicados',[]))|{(m.revision_documental or {}).get('plan_sha256')} for m in historicos}
        nombres={a.id:a.nombre for a in db.query(Activo)}
        for m in historicos:grupos[m.articulo_id].append(m);fotos[m.ruta_imagen_respaldo].append(m)
        cola=[];avisos=[]
        for aid,rows in grupos.items():
            sin=[m for m in rows if not m.revision_documental]
            pendientes=[m for m in rows if m.estado=='ACTIVO' and tipos_alerta(m)];avisos.extend(pendientes)
            if not sin:continue
            nuevos=[m for m in pendientes if not m.revision_documental]
            cola.append({'articulo_id':aid,'nombre':nombres[aid],'filas':len(rows),'sin_cotejar':len(sin),
                'ya_cotejadas':len(rows)-len(sin),'fotos':len({m.ruta_imagen_respaldo for m in rows}),
                'avisos_sin_cotejar':len(nuevos),'tipos':dict(Counter(t for m in nuevos for t in tipos_alerta(m)))})
        sin=sum(not m.revision_documental for m in historicos)
        estado={'generado_en':datetime.now(UTC).isoformat(),'estado':'COTEJO_COMPLETO_CON_DUDAS_DOCUMENTADAS' if sin==0 else 'EN_CURSO',
            'historicos':len(historicos),'revisados':len(historicos)-sin,'sin_cotejar':sin,
            'filas_con_avisos':len(avisos),'avisos_sin_cotejar':sum(not m.revision_documental for m in avisos),
            'avisos_con_cotejo':sum(bool(m.revision_documental) for m in avisos),
            'fotos_totales':len(fotos),'fotos_completas':sum(all(m.revision_documental for m in ms) for ms in fotos.values()),
            'fuente_sha256':fuente_hash(db),
            'cola':sorted(cola,key=lambda a:(-a['avisos_sin_cotejar'],a['sin_cotejar'],a['articulo_id']))}
    planes=[]
    agrupado=json.loads((DEST/'cierre_continuacion_03_06.json').read_text(encoding='utf-8'))
    for path in sorted(DEST.glob('plan_continuacion_[0-9][0-9].json')):
        plan=json.loads(path.read_text(encoding='utf-8'));sha=digest(plan);n=plan['version']
        resultado=DEST/f'resultado_continuacion_{n:02d}.json';ensayo=DEST/f'ensayo_plan_continuacion_{n:02d}.json'
        aplicado=all(sha in huellas.get(e['id'],set()) for e in plan['revisiones'])
        prueba_antigua=agrupado.get('reintentos_sin_cambios',{}).get(path.name)
        verificado_agrupado=n<=6 and aplicado and prueba_antigua is not None and all(v==0 for v in prueba_antigua.values())
        if resultado.exists():
            r=json.loads(resultado.read_text(encoding='utf-8'))
            assert r['plan_sha256']==sha and aplicado,path
            if r.get('verificado'):fase='APLICADO_VERIFICADO'
            elif verificado_agrupado:fase='APLICADO_VERIFICADO_AGRUPADO'
            else:fase='APLICADO_REQUIERE_CIERRE'
        elif verificado_agrupado:fase='APLICADO_VERIFICADO_AGRUPADO'
        elif aplicado:fase='APLICADO_REQUIERE_CIERRE'
        elif ensayo.exists():
            r=json.loads(ensayo.read_text(encoding='utf-8'))
            fase='ENSAYADO' if r.get('verificado') and r.get('plan_sha256')==sha else 'ENSAYO_NO_VIGENTE'
        else:fase='PREPARADO'
        planes.append({'numero':n,'sha256':sha,'fase':fase})
    estado['planes']=planes;estado['proximo_numero']=max(p['numero'] for p in planes)+1 if planes else 3
    estado['planes_sin_terminar']=[p for p in planes if not p['fase'].startswith('APLICADO_VERIFICADO')]
    estado['pausa_solicitada']=(DEST/'detener_continuidad_hil.flag').exists()
    return estado


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--guardar',action='store_true');args=p.parse_args()
    estado=consultar()
    if args.guardar:
        salida=DEST/'estado_continuidad_hil.json';temporal=salida.with_suffix('.tmp')
        temporal.write_text(json.dumps(estado,ensure_ascii=False,indent=2),encoding='utf-8');temporal.replace(salida)
    print(json.dumps({**{k:v for k,v in estado.items() if k not in ('cola','planes')},'siguientes':estado['cola'][:10]},ensure_ascii=False))


if __name__=='__main__':main()
