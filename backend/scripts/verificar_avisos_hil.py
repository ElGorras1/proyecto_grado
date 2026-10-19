"""Comprueba consultas y exclusiones de un plan focalizado sin iniciar trabajadores."""
import argparse,hashlib,json
from datetime import datetime,UTC
from sqlalchemy import inspect
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
from scripts.aplicar_revision_hil import DEST,BACKEND,fuente_hash
from scripts.generar_plan_revision_hil import digest
from scripts.preparar_analitica import digest_tablas

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--numero',type=int,required=True);a=p.parse_args();s=f'{a.numero:02d}'
    plan=json.loads((DEST/f'plan_continuacion_{s}.json').read_text(encoding='utf-8'))
    resultado=json.loads((DEST/f'resultado_continuacion_{s}.json').read_text(encoding='utf-8'))
    assert plan['cotejo']['modo']=='SOLO_AVISOS_HIL' and resultado['verificado'] and resultado['plan_sha256']==digest(plan) and resultado['sin_cambios_en_filas_normales']
    with engine.connect() as c:antes=digest_tablas(c,inspect(c).get_table_names())
    with SessionLocal() as db:
        u=db.query(Usuario).join(Rol).filter(Usuario.estado=='activo',Rol.nombre=='Administrador').order_by(Usuario.id).first();assert u
        token=create_access_token(u.id)
    cliente=TestClient(app);filas={};rutas=[];fotos=set()
    for aid in sorted({e['articulo_id'] for e in plan['revisiones']}):
        r=cliente.get(f'{settings.API_V1_PREFIX}/kardex/historial/{aid}',headers={'Authorization':'Bearer '+token});assert r.status_code==200
        filas.update({m['id']:m for m in r.json()});rutas.append({'articulo':aid,'http':200})
    inferidos=[]
    for e in plan['revisiones']:
        m=filas[e['id']];assert all(m[k]==v for k,v in e['cambios'].items()),e['id']
        rev=m['revision_documental'];assert digest(plan) in rev['planes_aplicados'] and rev['alcance']=='SOLO_MOVIMIENTO_OBSERVADO_HIL' and not rev['cotejo_pagina_completa']
        if m['estado']!='ACTIVO':assert m['fecha_estado']=='NO_APLICA_DOCUMENTAL' and not m['tiene_error_saldo'] and not m['tiene_error_fecha']
        elif rev.get('origen_fecha') in ('HIPOTESIS','SECUENCIA_AJUSTADA'):assert m['fecha_estado']=='ESTIMADA_HIL'
        if m['estado']!='ACTIVO' or rev.get('origen_fecha') in ('HIPOTESIS','SECUENCIA_AJUSTADA') or rev.get('origen_saldo_base')=='HIPOTESIS' or rev.get('origen_saldo')=='HIPOTESIS' or rev.get('origen_cantidades')=='HIPOTESIS':inferidos.append(m['id'])
        foto=(BACKEND/m['ruta_imagen_respaldo']).resolve();assert hashlib.sha256(foto.read_bytes()).hexdigest()==e['sha256_imagen'];fotos.add(str(foto))
    with SessionLocal() as db:
        pendientes=[m for m in db.query(M).filter(M.lote_id.isnot(None),M.estado=='ACTIVO') if tipos_alerta(m)]
        ids_objetivo={e['id'] for e in plan['revisiones']};pendientes_objetivo={m.id:tipos_alerta(m) for m in pendientes if m.id in ids_objetivo}
        assert sorted(pendientes_objetivo)==sorted(plan['cotejo']['ids_pendientes_esperados'])
        elegibles,_=seleccionar(leer_corte(db)['filas']);assert not set(inferidos)&{f['id'] for f in elegibles}
        fuente=fuente_hash(db);assert fuente==resultado['fuente_sha256']
        conteos={'avisos_totales':len(pendientes),'sin_revision':sum(not m.revision_documental for m in pendientes),'con_revision_y_pendiente':sum(bool(m.revision_documental) for m in pendientes)}
    with engine.connect() as c:despues=digest_tablas(c,inspect(c).get_table_names())
    assert antes==despues,'La consulta no puede modificar tablas'
    salida={'generado_en':datetime.now(UTC).isoformat(),'plan':a.numero,'rutas':rutas,'objetivos_comprobados':sorted(ids_objetivo),'fotos_verificadas':len(fotos),'inferidos_y_notas_excluidos':inferidos,'cambios_por_consultas':[],'fuente_sha256':fuente,**conteos}
    out=DEST/f'verificacion_avisos_{s}_api.json';assert not out.exists(),'Conservar corte de verificación'
    out.write_text(json.dumps(salida,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(salida,ensure_ascii=False))

if __name__=='__main__':main()
