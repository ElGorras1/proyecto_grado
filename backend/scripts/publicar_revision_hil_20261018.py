"""Corte documental de solo lectura de la reanudación HIL del 18/10/2026."""
from collections import Counter
from datetime import datetime, UTC
from pathlib import Path
import hashlib, json
from sqlalchemy import inspect
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import SessionLocal, engine
from app.models.kardex import MovimientoKardex as M
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.services.calidad_kardex import tipos_alerta
from app.services.revision_documental import snapshot_revision
from scripts.aplicar_revision_hil import BACKEND, DEST, fuente_hash
from scripts.generar_plan_revision_hil import digest
from scripts.guardar_estado_avisos_hil import guardar
from scripts.preparar_analitica import digest_tablas

NUMEROS=[86,87,88,90,91,92,93,94]
CARPETA=BACKEND/'backups/revision_avisos_hil_20261018'

def leer(p): return json.loads(p.read_text(encoding='utf-8'))
def foto_link(p): return '../backend/'+str(Path(p).relative_to(BACKEND)).replace('\\','/')

def main():
    salidas=[CARPETA/'corte_posterior_planes_86_94.json', BACKEND.parent/'docs/revision-observados-hil-2026-10-18.md',
             BACKEND.parent/'docs/revision-observados-hil-pendientes-2026-10-18.md']
    assert not any(p.exists() for p in salidas), 'Conservar cortes inmutables'
    with engine.connect() as c: antes=digest_tablas(c,inspect(c).get_table_names())
    estado=guardar(); inicial=leer(CARPETA/'cola_reanudacion_244.json')
    base={c['id']:c for c in inicial['casos']}; assert len(base)==244
    bloques=[]; cambiados=set()
    for n in NUMEROS:
        p=leer(DEST/f'plan_continuacion_{n:02d}.json');r=leer(DEST/f'resultado_continuacion_{n:02d}.json')
        q=leer(DEST/f'ensayo_plan_continuacion_{n:02d}.json');a=leer(DEST/f'verificacion_avisos_{n:02d}_api.json')
        assert r['verificado'] and q['verificado'] and r['sin_cambios_en_filas_normales'] and not r['filas_fuera_objetivo_modificadas']
        assert r['plan_sha256']==q['plan_sha256']==digest(p) and not a['cambios_por_consultas']
        assert r['fuente_sha256']==a['fuente_sha256']==estado['fuente_sha256']
        ids=set(p['cotejo']['ids_objetivo']); assert ids<=base.keys() and not ids&cambiados
        assert set(r['resueltos'])==ids and not r['cotejados_con_pendiente']
        cambiados.update(ids)
        bloques.append({'plan':n,'objetivos':sorted(ids),'fotos':p['cotejo']['fotografias'],'sha256':r['plan_sha256']})
    catalogo=leer(BACKEND/'backups/revision_avisos_hil_20261016/cola_inicial_399.json')
    nombres={c['id']:c['articulo'] for c in catalogo['casos']}
    casos=[];tipos=Counter();fotos={}
    with SessionLocal() as db:
        assert fuente_hash(db)==estado['fuente_sha256']
        for id,anterior in base.items():
            m=db.get(M,id);r=snapshot_revision(m);avisos=tipos_alerta(m) if m.estado=='ACTIVO' else []
            if id not in cambiados: assert r==anterior, f'Pendiente ajeno a planes cambió: {id}'
            else: assert not avisos
            foto=(BACKEND/m.ruta_imagen_respaldo).resolve(); assert foto.exists() and foto.is_relative_to(BACKEND/'storage')
            fotos.setdefault(str(foto),hashlib.sha256(foto.read_bytes()).hexdigest())
            tipos.update(avisos)
            casos.append({'id':id,'articulo':nombres[id],'avisos':avisos,'corregido_en_esta_reanudacion':id in cambiados,
                          'foto':str(foto),'foto_sha256':fotos[str(foto)],'fila_actual':r})
        u=db.query(Usuario).join(Rol).filter(Usuario.estado=='activo',Rol.nombre=='Administrador').order_by(Usuario.id).first()
        assert u;token=create_access_token(u.id)
    cliente=TestClient(app); rutas=[];pendientes={c['id'] for c in casos if c['avisos']}
    for tipo in [None,'area','saldo','fecha','referencia']:
        r=cliente.get(settings.API_V1_PREFIX+'/kardex/errores',headers={'Authorization':'Bearer '+token},params={} if tipo is None else {'tipo':tipo})
        esperados=pendientes if tipo is None else {c['id'] for c in casos if tipo in c['avisos']}
        assert r.status_code==200 and {c['id'] for c in r.json()}==esperados
        rutas.append({'filtro':tipo,'http':200,'conteo':len(esperados)})
    with engine.connect() as c: despues=digest_tablas(c,inspect(c).get_table_names())
    assert antes==despues and len(cambiados)==128 and len(pendientes)==116
    assert estado['metricas']['RESUELTO']==283 and estado['metricas']['PENDIENTE_REVISION']==0
    corte={'generado_en':datetime.now(UTC).isoformat(),'alcance':'SOLO_AVISOS_HIL','pendientes_al_reanudar':244,
           'avisos_resueltos_en_reanudacion':len(cambiados),'pendientes_actuales':len(pendientes),
           'resueltos_acumulados_cola_399':estado['metricas']['RESUELTO'],'sin_revision':0,
           'avisos_por_tipo':dict(tipos),'planes':bloques,'fotos_verificadas':len(fotos),
           'fuente_sha256':estado['fuente_sha256'],'cambios_por_consultas':[],
           'filas_fuera_objetivos_modificadas':[],'pendientes_ajenos_a_planes_exactamente_intactos':True,
           'rutas_comprobadas':rutas,'casos':casos}
    salidas[0].write_text(json.dumps(corte,ensure_ascii=False,indent=2),encoding='utf-8')
    detalle='# HIL: pendientes materiales y fotografías · 18/10/2026\n\n'
    detalle+=f'Corte {corte["generado_en"]}. {len(pendientes)} movimientos con marcas documentadas, cero sin cotejo previo. Las diferencias reales del papel y la incertidumbre no se convierten en datos confirmados.\n\n'
    for c in casos:
        if not c['avisos']: continue
        f=c['fila_actual'];rev=f['revision_documental']
        detalle+=f'## {c["id"]} · {c["articulo"]}\n\nAvisos: **{", ".join(c["avisos"])}**. [Foto completa]({foto_link(c["foto"])}).\n\n'
        detalle+=f'{rev["motivo"]}\n\n'
        detalle+=f'Detalle: {f["detalle"]}. Área literal: {f["area"] or "en blanco"}; referencia: {f["referencia"] or "en blanco"}. '
        detalle+=f'Ingreso: {f["ingresos"]}; salida: {f["salidas"]}; saldo vigente: {f["saldo_registrado"]}; calculado: {f["saldo_calculado"]}. '
        detalle+=f'Fecha documental: {rev.get("fecha_documental")}; origen: {rev.get("origen_fecha")}.\n\n'
    salidas[2].write_text(detalle,encoding='utf-8')
    texto='# Reanudación focalizada HIL · 18/10/2026\n\n'
    texto+=f'Corte {corte["generado_en"]}. El titular autorizó retomar los pendientes con «entonces lo resolveras tu?». Se congeló el estado de los 244 avisos vigentes antes de modificar datos. Se han resuelto **128 avisos adicionales**: la cola inicial de 399 queda en **283 sin avisos HIL, 116 con pendientes documentados y cero sin revisión**. Esto no equivale a certificar todos los datos ni a concluir toda la depuración.\n\n'
    texto+='## Cambios aplicados\n\n'
    texto+='- Referencias geográficas, Feria y códigos documentales separados de unidades institucionales, manteniendo literalmente lo escrito y su posición en la fuente.\n- Lecturas directas de CEDOAL, Dirección, CAP, C+C y Sala corregidas hacia unidades ya catalogadas, sin crear ni confirmar alias.\n- Trece atribuciones funcionales a CEDOAL con palabra legible entre REF/ÁREA: la posición física ambigua sigue documentada; no se declara validación institucional.\n- Nombres documentales de receptores y referencias de consignación separados de áreas; no se inventan responsables registrados.\n- Detalles puntuales corregidos desde su propia foto; ninguna cantidad, fecha ni saldo cambia en estos planes.\n\n'
    texto+='## Verificación\n\n'
    texto+='Cada bloque tuvo plan congelado, respaldo coherente, ensayo restaurado, aplicación secuencial y comprobación posterior de consultas, fotografías, hipótesis y exclusiones. Cero modificaciones fuera de los objetivos y ninguna duplicación o eliminación. También se comprobó que los 116 pendientes ajenos a estos planes permanecieran exactamente como en la cola congelada de reanudación. Los cinco filtros de HIL devuelven HTTP 200 y los IDs esperados, sin escrituras por consulta.\n\n'
    texto+='| Plan | Avisos resueltos | Fotografías propias |\n|---|---:|---:|\n'
    for x in bloques: texto+=f'| {x["plan"]} | {len(x["objetivos"])} | {x["fotos"]} |\n'
    texto+='\nEl plan 89 está archivado sin ensayo ni aplicación institucional: 90 lo sustituye con la transcripción documental CAP sin puntos. Nunca ejecutar 89. Se conservan todas las revisiones anteriores, fotografías y primeras extracciones. Huella de fuente: `'+estado['fuente_sha256']+'`.\n\n'
    texto+='## Qué impide retirar las marcas restantes\n\n| Tipo | Movimientos |\n|---|---:|\n'
    for t,n in tipos.items(): texto+=f'| {t} | {n} |\n'
    texto+='\nLos tipos pueden coincidir en una fila. Las áreas restantes incluyen siglas sin equivalencia acreditada, palabras repasadas y marcas parciales. Las diferencias de saldo del papel requieren decisión o evidencia adicional: no se fabrican operaciones compensatorias. Las cinco fechas dependen de vecinos fuera del alcance autorizado. Las referencias inciertas conservan sus trazos, sin convertir puntos aislados en comillas.\n\n'
    texto+='[Cada pendiente con su fotografía y explicación](revision-observados-hil-pendientes-2026-10-18.md). Las marcas reales se conservan y los datos hipotéticos siguen excluidos según los criterios vigentes; aviso resuelto no significa dato certificado o aptitud automática de todo el artículo para entrenar. Campero mantiene cierre 300 frente a acumulado condicional 309 y bloqueo de apertura.\n\n'
    texto+='La tarea termina en revisión HIL. No se importó, repitió OCR, creó inventario operativo, definieron nuevas áreas ni entrenó Isolation Forest. La automatización eliminada no se recreó; no queda un aplicador trabajando en segundo plano. Los informes del 16/10 son cortes anteriores y no se sobrescriben.\n'
    salidas[1].write_text(texto,encoding='utf-8')
    print(json.dumps({k:v for k,v in corte.items() if k!='casos'},ensure_ascii=False))

if __name__=='__main__': main()
