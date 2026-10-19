"""Corte de solo lectura: comprueba los 399 objetivos HIL y publica evidencia y límites."""
from collections import Counter
from datetime import datetime,UTC
from pathlib import Path
import hashlib,json,re
from sqlalchemy import inspect
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import SessionLocal,engine
from app.models.kardex import MovimientoKardex as M
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.auditoria import AuditoriaSistema
from app.services.calidad_kardex import tipos_alerta
from app.services.revision_documental import snapshot_revision
from app.services.datos_analitica import leer_corte,seleccionar
from scripts.aplicar_revision_hil import BACKEND,DEST,fuente_hash
from scripts.generar_plan_revision_hil import digest
from scripts.guardar_estado_avisos_hil import guardar
from scripts.preparar_analitica import digest_tablas

FOCO=BACKEND/'backups/revision_avisos_hil_20261016'
NUMEROS=[75,76,77,78,79,80,82,83,84,85]

def leer(path):return json.loads(path.read_text(encoding='utf-8'))
def enlace_foto(path):return '../backend/'+str(Path(path).resolve().relative_to(BACKEND)).replace('\\','/')
def limpio(v):return str(v if v is not None else 'vacío').replace('|','/').replace('\n',' ')

def main():
    root=BACKEND.parent
    salidas=[root/'docs/revision-observados-hil-cierre-2026-10-16.md',root/'docs/revision-observados-hil-casos-2026-10-16.md',root/'docs/revision-avisos-hil-75-85-2026-10-16.md',FOCO/'cierre_revision_399_20261016.json']
    assert not any(p.exists() for p in salidas),'Conservar cortes anteriores'
    with engine.connect() as c:antes=digest_tablas(c,inspect(c).get_table_names())
    inicial=leer(FOCO/'cola_inicial_399.json');ids={c['id'] for c in inicial['casos']};assert len(ids)==399
    estado=guardar();assert estado['metricas']['PENDIENTE_REVISION']==0 and not estado['avisos_fuera_cola_inicial']
    bloques=[]
    for numero in NUMEROS:
        plan=leer(DEST/f'plan_continuacion_{numero:02d}.json');r=leer(DEST/f'resultado_continuacion_{numero:02d}.json');q=leer(DEST/f'ensayo_plan_continuacion_{numero:02d}.json');api=leer(DEST/f'verificacion_avisos_{numero:02d}_api.json')
        assert r['verificado'] and q['verificado'] and r['plan_sha256']==q['plan_sha256']==digest(plan)
        assert not r['filas_fuera_objetivo_modificadas'] and r['sin_cambios_en_filas_normales'] and not api['cambios_por_consultas']
        assert set(plan['cotejo']['ids_objetivo'])<=ids and plan['cotejo']['modo']=='SOLO_AVISOS_HIL'
        assert r['fuente_sha256']==estado['fuente_sha256']==api['fuente_sha256']
        bloques.append((numero,plan,r,api))
    casos=[];fotos={};tipos=Counter()
    with SessionLocal() as db:
        assert fuente_hash(db)==estado['fuente_sha256']
        elegibles,_=seleccionar(leer_corte(db)['filas']);elegibles={r['id'] for r in elegibles}
        audits={id:n for id,n in db.query(AuditoriaSistema.recurso_id,AuditoriaSistema.id).filter(AuditoriaSistema.accion=='corregir_kardex_hil',AuditoriaSistema.recurso=='movimientos_kardex',AuditoriaSistema.recurso_id.in_(ids))}
        for c in inicial['casos']:
            m=db.get(M,c['id']);rev=m.revision_documental;assert rev and rev.get('criterios') and rev.get('motivo') and m.datos_originales and m.id in audits
            assert rev.get('cotejo_pagina_completa') or rev.get('alcance')=='SOLO_MOVIMIENTO_OBSERVADO_HIL' or any(t in rev['motivo'].lower() for t in ['foto','filas físicas'])
            p=(BACKEND/m.ruta_imagen_respaldo).resolve();assert p.is_relative_to((BACKEND/'storage').resolve()) and p.exists()
            fotos.setdefault(str(p),hashlib.sha256(p.read_bytes()).hexdigest())
            avisos=tipos_alerta(m) if m.estado=='ACTIVO' else [];tipos.update(avisos)
            if avisos or rev.get('origen_fecha') in ['HIPOTESIS','SECUENCIA_AJUSTADA'] or rev.get('origen_saldo_base')=='HIPOTESIS' or rev.get('origen_cantidades')=='HIPOTESIS':assert m.id not in elegibles
            casos.append({'id':m.id,'articulo_id':m.articulo_id,'articulo':c['articulo'],'avisos_iniciales':c['avisos'],'avisos_actuales':avisos,'resultado':'PENDIENTE_DOCUMENTADO' if avisos else 'AVISO_RESUELTO','elegible_analitica':m.id in elegibles,'foto':str(p),'foto_sha256':fotos[str(p)],'fila_actual':snapshot_revision(m)})
        u=db.query(Usuario).join(Rol).filter(Usuario.estado=='activo',Rol.nombre=='Administrador').order_by(Usuario.id).first();assert u;token=create_access_token(u.id)
    cliente=TestClient(app);cab={'Authorization':'Bearer '+token};rutas=[]
    pendientes={c['id'] for c in casos if c['avisos_actuales']}
    for tipo in [None,'saldo','fecha','area','referencia']:
        params={} if tipo is None else {'tipo':tipo}
        r=cliente.get(settings.API_V1_PREFIX+'/kardex/errores',headers=cab,params=params);assert r.status_code==200
        esperados=pendientes if tipo is None else {c['id'] for c in casos if tipo in c['avisos_actuales']}
        assert {c['id'] for c in r.json()}==esperados
        rutas.append({'ruta':'/kardex/errores','filtro':tipo,'http':200,'conteo':len(esperados)})
    # Se comprueban auditorías visibles de correcciones de columna, cantidad, fecha, hipótesis, papel discrepante y base.
    for id in [7871,7890,10990,7369,10226,8392,20,7294]:
        r=cliente.get(f'{settings.API_V1_PREFIX}/kardex/movimiento/{id}/revisiones',headers=cab);assert r.status_code==200 and r.json()
        rutas.append({'ruta':f'/kardex/movimiento/{id}/revisiones','http':200,'conteo':len(r.json())})
    with engine.connect() as c:despues=digest_tablas(c,inspect(c).get_table_names())
    assert antes==despues,'El cierre documental y las consultas no deben modificar la base'
    m=estado['metricas'];assert len(casos)==m['RESUELTO']+len(pendientes) and len(pendientes)==estado['avisos_actuales']
    corte={'generado_en':datetime.now(UTC).isoformat(),'estado':'REVISION_ASISTIDA_CUBIERTA_CON_PENDIENTES_MATERIALES','alcance':'SOLO_AVISOS_HIL','no_equivale_a_todo_corregido':True,'casos_iniciales':399,'metricas':m,'avisos_por_tipo':dict(tipos),'movimientos_observados_actuales':len(pendientes),'fuente_sha256':estado['fuente_sha256'],'fotos_de_objetivos_verificadas':len(fotos),'cambios_por_consultas':[],'rutas_comprobadas':rutas,'planes_nuevos':[n for n,_,_,_ in bloques],'casos':casos}
    salidas[3].write_text(json.dumps(corte,ensure_ascii=False,indent=2),encoding='utf-8')
    detalle='# Movimientos observados HIL: decisiones y fotografías\n\n'
    detalle+=f"Corte {corte['generado_en']}. Solo la cola de 399 movimientos originalmente observados. {m['RESUELTO']} avisos resueltos y {len(pendientes)} movimientos con pendientes documentados. Cero sin revisión. Un aviso resuelto puede conservar hipótesis y exclusiones; no equivale a dato certificado.\n\n"
    for titulo,filas in [('Pendientes documentados',[c for c in casos if c['avisos_actuales']]),('Avisos resueltos',[c for c in casos if not c['avisos_actuales']])]:
        detalle+='## '+titulo+'\n\n'
        for c in filas:
            f=c['fila_actual'];rev=f['revision_documental'];detalle+=f"### Movimiento {c['id']} · {c['articulo']}\n\n"
            detalle+=f"Avisos actuales: **{', '.join(c['avisos_actuales']) or 'ninguno'}**. [Fotografía completa]({enlace_foto(c['foto'])}).\n\n"
            detalle+=f"{rev['motivo']}\n\n"
            detalle+='| Fecha de consulta | Fecha documental | Ingreso | Salida | Saldo vigente | Saldo calculado | Área literal | Referencia literal |\n|---|---|---:|---:|---:|---:|---|---|\n'
            detalle+='| '+' | '.join(limpio(v) for v in [f['fecha_movimiento'],rev.get('fecha_documental'),f['ingresos'],f['salidas'],f['saldo_registrado'],f['saldo_calculado'],f['area'],f['referencia']])+' |\n\n'
            detalle+=f"Criterios: {', '.join(rev['criterios'])}. Origen de fecha: {rev.get('origen_fecha','ver revisión anterior')}; de saldo: {rev.get('origen_saldo','ver revisión anterior')}. Elegible en selección analítica actual: {'sí' if c['elegible_analitica'] else 'no'}.\n\n"
    salidas[1].write_text(detalle,encoding='utf-8')
    tramo='# Observados HIL: planes 75–85 aplicados y verificados\n\n'
    tramo+='Solo avisos vigentes de la cola inicial, con originales y vecinos intactos. La revisión anterior de las enmiendas 84 y 85 se conserva completa y queda protegida por precondición. El plan 81 fue rechazado en ensayo por una expectativa incorrecta de la etiqueta de fecha de 10006 y archivado sin aplicación institucional; 82 conserva su hipótesis explícita. Nunca aplicar 81.\n\n'
    tramo+='| Plan | Movimientos | Fotos | Avisos resueltos | Pendientes documentados | SHA256 |\n|---|---:|---:|---:|---:|---|\n'
    for n,p,r,a in bloques:tramo+=f"| {n} | {len(p['revisiones'])} | {p['cotejo']['fotografias']} | {len(r['resueltos'])} | {len(r['cotejados_con_pendiente'])} | `{r['plan_sha256']}` |\n"
    tramo+='\nEn todos: respaldo coherente, ensayo en copia restaurada, aplicación secuencial y consulta comprobados. Cero cambios fuera de los objetivos de cada plan, cero movimientos nuevos o borrados, originales y fotos intactos, reintento sin cambios, exclusiones verificadas, solo tablas de movimientos y auditoría modificadas. Los historiales consultados no escribieron en la base. No se importó, repitió OCR, entrenó ni creó inventario operativo.\n\n'
    for n,p,r,a in bloques:
        tramo+=f'## Plan {n}\n\n'
        for e in p['revisiones']:
            tramo+=f"- **{e['id']} · {'pendiente documentado' if e['id'] in r['cotejados_con_pendiente'] else 'aviso resuelto'}:** {e['revision']['motivo']} [Foto]({enlace_foto(e['fuente'])}).\n"
        tramo+='\n'
    salidas[2].write_text(tramo,encoding='utf-8')
    texto=f'''# Cierre de la revisión asistida de observados HIL · 16/10/2026

Corte de base: {corte['generado_en']}. Se terminó de tratar la cola autorizada de **399 movimientos observados**: **{m['RESUELTO']} ya no presentan avisos HIL, {len(pendientes)} conservan pendientes documentados y cero quedaron sin revisión**. Esto cierra la cobertura de revisión asistida, **no significa que todos los datos estén confirmados o que todos los errores materiales estén resueltos**.

Desde el último corte publicado (plan 73) se aplicaron **104 objetivos distintos**, con **92 avisos resueltos y 12 pendientes documentados**. Fueron los 89 que todavía no tenían cotejo y 15 enmiendas a avisos ya revisados: tres fechas y doce clasificaciones de bases/recuentos sin flujo. No se continuó el cotejo masivo del histórico ni se modificaron vecinos normales.

## Qué está corregido y qué sigue marcado

- Lecturas OCR de cantidades, columnas, fechas y textos corregidas según cada fotografía y los criterios del titular.
- Fechas ausentes o fuera de orden identificadas; consulta técnica separada de fecha documental. Hipótesis y exclusiones conservadas.
- Columnas equivocadas en el papel interpretadas cuando detalle, cifra y saldo lo acreditan, conservando su posición escrita y la marca de error del trabajador.
- Bases, notas y recuentos documentales separados de ingresos o salidas; no se crean operaciones compensatorias ni recuentos actuales.
- Los errores aritméticos reales del papel, las lecturas no inequívocas y las dependencias con filas fuera del objetivo siguen visibles. Las áreas no se normalizaron por frecuencia ni se crearon alias.

## Pendientes reales

| Tipo de aviso | Movimientos |
|---|---:|
| Área o atribución documental/catálogo pendiente | {tipos['area']} |
| Diferencia de saldo | {tipos['saldo']} |
| Fecha dependiente de otra fila fuera del objetivo | {tipos['fecha']} |
| Referencia de lectura incierta | {tipos['referencia']} |

Los tipos pueden coincidir en una misma fila: **{len(pendientes)} movimientos distintos**. No son {len(pendientes)} OCR fallidos ni casos sin revisar. {m['PENDIENTE_DOCUMENTADO_PREVIO']} conservan pendientes de cotejos anteriores y {m['COTEJADO_CON_PENDIENTE']} proceden de los nuevos cotejos focalizados.

Ejemplos materiales con evidencia:

'''
    porid={c['id']:c for c in casos}
    for id in [7871,8218,10921,11112,236,3971,12063,10226,12011,11084,882,10941]:
        c=porid[id];texto+=f"- **{id} · {c['articulo']}:** {c['fila_actual']['revision_documental']['motivo']} [Ver foto]({enlace_foto(c['foto'])}).\n"
    texto+=f'''
## Evidencia y comprobaciones

[Decisión, valores y fotografía de cada uno de los 399 movimientos]({salidas[1].name}). [Detalle de los planes 75–85]({salidas[2].name}). [Corte JSON reproducible](../backend/backups/revision_avisos_hil_20261016/{salidas[3].name}).

Se comprobaron {len(fotos)} fotografías diferentes asociadas a objetivos; no se usa este total como meta de cotejo de todo el histórico. Las fotografías, primeras extracciones y fechas originales se conservan. Fuente SHA256 `{estado['fuente_sha256']}`.

Los filtros HIL general, saldo, fecha, área y referencia devolvieron HTTP 200 y exactamente los IDs de la base. Auditorías de ocho correcciones representativas accesibles. Las consultas y la generación de este corte no alteraron tablas. Los ensayos y aplicaciones de cada bloque comprobaron igualdad exacta de todas las filas ajenas a sus objetivos, no duplicación, integridad de fuentes, aperturas intactas y exclusión de hipótesis.

Se mantienen POLIGENESIS separado, cuatro ingresos T13 y el cierre Campero 300 frente a 309 condicional con bloqueo de apertura y exclusión. No se declara validación institucional ni dataset totalmente confirmado. No se definieron áreas, entrenaron modelos ni abrieron inventarios.

## Límite de este cierre

Por la instrucción final del titular, el trabajo termina aquí, en HIL. Los pendientes con evidencia insuficiente permanecen marcados; las dependencias que exigen modificar filas normales se documentan sin ampliar el alcance. Para retomarlos se necesita evidencia o criterio específico adicional; no corresponde repetir indefinidamente el mismo cotejo ni borrar sus avisos. La importación de tanda 3 permanece pausada.
'''
    salidas[0].write_text(texto,encoding='utf-8')
    readme=root/'README.md';s=readme.read_text(encoding='utf-8');titulo,resto=s.split('\n',1)
    resumen=f"**Cierre de revisión de observados HIL (16/10/2026):** [399 movimientos tratados, evidencia y límites](docs/{salidas[0].name}). **{m['RESUELTO']} avisos resueltos, {len(pendientes)} movimientos con pendientes documentados y cero sin revisar.** Revisión asistida cubierta; los datos con dudas materiales no se declaran corregidos ni certificados. Planes 75–85 verificados, sin cambios fuera de objetivos. El trabajo se detiene en HIL por instrucción del titular; los cortes siguientes son antecedentes históricos."
    s=titulo+'\n\n'+resumen+'\n'+resto
    s=re.sub(r'\*\*Última revisión HIL:\*\*[^\n]*',f"**Última revisión HIL:** 16/10/2026, plan 85; cola de 399 tratada, {len(pendientes)} avisos materiales conservados, cero sin revisión<br>",s,count=1);readme.write_text(s,encoding='utf-8')
    guia=root/'docs/continuidad-revision-hil-2026-10-15.md';s=guia.read_text(encoding='utf-8')
    nuevo=f"**Último punto focalizado:** [cierre de la cola de 399]({salidas[0].name}), {m['RESUELTO']} avisos resueltos, {len(pendientes)} con pendiente documentado y cero sin revisar. Planes 75–80, 82–85 aplicados y verificados; 81 archivado sin aplicación, nunca ejecutarlo. No hay planes abiertos. Por instrucción del titular se termina aquí: no ampliar a áreas, entrenamiento, inventario ni cotejo de normales. Mantener los pendientes y sus dependencias; no repetirlos sin nueva evidencia o criterio. Importación tanda 3 pausada."
    assert '**Último punto focalizado:**' in s;s=re.sub(r'\*\*Último punto focalizado:\*\*[^\n]*',nuevo,s,count=1);guia.write_text(s,encoding='utf-8')
    print(json.dumps({k:v for k,v in corte.items() if k!='casos'},ensure_ascii=False));print(json.dumps({'informes':[str(p) for p in salidas[:3]]},ensure_ascii=False))

if __name__=='__main__':main()
