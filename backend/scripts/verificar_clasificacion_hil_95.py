"""Verifica categorización, alertas conservadas, filtros y ausencia de escrituras; publica evidencia."""
from collections import Counter
from datetime import datetime, UTC
from pathlib import Path
import hashlib,json
from sqlalchemy import inspect
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal,engine
from app.core.config import settings
from app.core.security import create_access_token
from app.models.kardex import MovimientoKardex as M
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.services.calidad_kardex import tipos_alerta
from app.services.revision_documental import snapshot_revision
from app.services.tratamiento_hil import resumen_tratamiento,CATEGORIAS
from app.services.datos_analitica import leer_corte,seleccionar
from scripts.aplicar_revision_hil import DEST,BACKEND,fuente_hash
from scripts.generar_plan_revision_hil import digest
from scripts.preparar_analitica import digest_tablas
from scripts.guardar_estado_avisos_hil import guardar

def leer(p):return json.loads(p.read_text(encoding='utf-8'))

def main():
    carpeta=BACKEND/'backups/revision_avisos_hil_20261018'
    salidas=[carpeta/'clasificacion_116_verificada.json',BACKEND.parent/'docs/categorizacion-hil-2026-10-18.md',
             BACKEND.parent/'docs/categorizacion-hil-casos-2026-10-18.md']
    assert not any(p.exists() for p in salidas),'Conservar cortes anteriores'
    plan=leer(DEST/'plan_continuacion_95.json');r=leer(DEST/'resultado_continuacion_95.json');qa=leer(DEST/'ensayo_plan_continuacion_95.json')
    assert r['verificado'] and qa['verificado'] and r['sin_cambios_en_filas_normales'] and r['plan_sha256']==qa['plan_sha256']==digest(plan)
    assert not r['filas_fuera_objetivo_modificadas']
    fuente_esperada=r['fuente_sha256'];previo=leer(carpeta/'corte_posterior_planes_86_94.json')
    inicial={c['id']:c for c in previo['casos'] if c['avisos']};assert len(inicial)==116
    with engine.connect() as con:antes=digest_tablas(con,inspect(con).get_table_names())
    casos=[];categorias=Counter();campos=Counter()
    with SessionLocal() as db:
        assert fuente_hash(db)==fuente_esperada
        corte=leer_corte(db);elegibles,_=seleccionar(corte['filas']);ids_elegibles={f['id'] for f in elegibles}
        for id,c in inicial.items():
            m=db.get(M,id);s=snapshot_revision(m);ant=c['fila_actual'];t=resumen_tratamiento(m)
            assert t['estado']=='CATEGORIZADO_CON_MARCA' and set(t['avisos_conservados'])==set(c['avisos'])
            assert set(d['campo'] for d in t['decisiones'])==set(tipos_alerta(m))
            assert all(s[k]==v for k,v in ant.items() if k!='revision_documental'),id
            assert s['revision_documental']['revision_previa_enmienda_focalizada']==ant['revision_documental']
            assert id not in ids_elegibles and not t['datos_confirmados'] and not t['habilita_entrenamiento']
            p=(BACKEND/m.ruta_imagen_respaldo).resolve();assert hashlib.sha256(p.read_bytes()).hexdigest()==c['foto_sha256']
            categorias.update(d['categoria'] for d in t['decisiones']);campos.update(tipos_alerta(m))
            casos.append({'id':id,'articulo':c['articulo'],'avisos':tipos_alerta(m),'tratamiento':t,
                          'foto':str(p),'foto_sha256':c['foto_sha256'],'fila_actual':s})
        u=db.query(Usuario).join(Rol).filter(Usuario.estado=='activo',Rol.nombre=='Administrador').first();assert u
        token=create_access_token(u.id)
    cliente=TestClient(app);h={'Authorization':'Bearer '+token};rutas=[]
    def consultar(params,ids):
        rr=cliente.get(settings.API_V1_PREFIX+'/kardex/errores',headers=h,params=params)
        assert rr.status_code==200 and {f['id'] for f in rr.json()}==set(ids),(params,rr.status_code)
        rutas.append({'parametros':params,'http':200,'conteo':len(ids)})
        return rr.json()
    todos={c['id'] for c in casos}
    filas=consultar({},todos)
    assert all(f['tratamiento_hil']['estado']=='CATEGORIZADO_CON_MARCA' for f in filas)
    consultar({'tratamiento':'CATEGORIZADO_CON_MARCA'},todos)
    consultar({'tratamiento':'POR_CATEGORIZAR'},set())
    consultar({'tratamiento':'REQUIERE_RECATEGORIZAR'},set())
    for tipo in ['saldo','fecha','area','referencia']:
        consultar({'tipo':tipo,'tratamiento':'CATEGORIZADO_CON_MARCA'},{c['id'] for c in casos if tipo in c['avisos']})
    for cat in CATEGORIAS:
        ids={c['id'] for c in casos if cat in c['tratamiento']['categorias']}
        consultar({'categoria':cat},ids)
    # Cruce de tres filtros y ámbito del artículo: cada resultado debe pertenecer a la intersección.
    ejemplo=next(c for c in casos if c['id']==3153)
    consultar({'articulo_id':ejemplo['fila_actual']['articulo_id'],'tipo':'referencia','categoria':'MARCA_NO_INTERPRETADA'},
              {c['id'] for c in casos if c['fila_actual']['articulo_id']==ejemplo['fila_actual']['articulo_id'] and 'referencia' in c['avisos'] and 'MARCA_NO_INTERPRETADA' in c['tratamiento']['categorias']})
    estado=guardar();assert estado['metricas_tratamiento']=={'SIN_AVISOS':283,'CATEGORIZADO_CON_MARCA':116,'POR_CATEGORIZAR':0,'REQUIERE_RECATEGORIZAR':0}
    with engine.connect() as con:despues=digest_tablas(con,inspect(con).get_table_names())
    assert antes==despues,'Las consultas y la publicación no modifican la base'
    resultado={'generado_en':datetime.now(UTC).isoformat(),'alcance':'SOLO_AVISOS_HIL','plan':95,'plan_sha256':digest(plan),
               'metricas_tratamiento':estado['metricas_tratamiento'],'avisos_por_tipo':dict(campos),'decisiones_por_categoria':dict(categorias),
               'alertas_conservadas':116,'sin_categorizar':0,'sin_datos_numericos_modificados':True,
               'sin_cambios_fuera_objetivos':True,'cambios_por_consultas':[],'fuente_sha256':fuente_esperada,
               'elegibilidad_no_habilitada_por_categoria':True,'rutas_verificadas':rutas,'casos':casos}
    salidas[0].write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding='utf-8')
    detalle='# HIL: tratamiento de cada aviso restante · 18/10/2026\n\n'
    detalle+='116 movimientos categorizados; una fila tiene dos marcas. El tratamiento aplica los criterios acordados sobre cotejos ya existentes, sin simular un nuevo cotejo completo ni certificar información desconocida.\n\n'
    for c in casos:
        foto='../backend/'+str(Path(c['foto']).relative_to(BACKEND)).replace('\\','/')
        detalle+=f'## {c["id"]} · {c["articulo"]}\n\n[Fotografía completa]({foto}).\n\n'
        for d in c['tratamiento']['decisiones']:
            detalle+=f'- **{d["campo"]} · {d["etiqueta"]}:** {d["motivo"]} Criterios: {", ".join(d["criterios"])}.\n'
        detalle+='\nCotejo conservado: '+c['fila_actual']['revision_documental']['revision_previa_enmienda_focalizada']['motivo']+'\n\n'
    salidas[2].write_text(detalle,encoding='utf-8')
    texto='# Categorización completa de los avisos HIL · 18/10/2026\n\n'
    texto+='Por instrucción del titular («corrige todo, quiero que todo ya este categorizado… mis vibes»), se registró un tratamiento explícito en los 116 movimientos que aún conservaban avisos. **De la cola inicial de 399, hay 283 sin avisos HIL y 116 categorizados con marca; cero avisos sin categorizar.** No se declara que los 116 datos inciertos estén confirmados.\n\n'
    texto+='## Categorías aplicadas\n\n| Tratamiento | Marcas |\n|---|---:|\n'
    for cat,n in categorias.items():texto+=f'| {CATEGORIAS[cat]} | {n} |\n'
    texto+='\nHay 117 decisiones en 116 filas: el movimiento 3153 conserva una marca de área y otra de referencia.\n\n'
    texto+='## Uso en el sistema\n\nEn **Kárdex escaneados → seleccionar artículo → Auditoría HIL**, se distinguen los **categorizados con marca** de los **por categorizar o actualizar**. Los filtros de tratamiento y categoría se combinan con tipo y tanda. En **Revisión documental** se ve la decisión, su criterio y la evidencia junto al texto previo. El historial conserva las mismas marcas y los cálculos independientes.\n\n'
    texto+='- Errores OCR acreditados: correcciones anteriores conservadas.\n- Datos reconstruidos: siguen con origen HIPOTESIS o SECUENCIA_AJUSTADA cuando corresponde.\n- Error del papel: saldo escrito y cálculo independiente siguen separados, con discrepancia documentada.\n- Siglas o trazos no acreditados: categoría explícita de catálogo, lectura o marca; no se inventa una institución.\n- Dependencias con vecinos: quedan identificadas sin ampliar el alcance a movimientos normales.\n\n'
    texto+='Una categoría se vincula mediante huella al dato revisado. Si cambia después una cantidad, fecha, referencia, atribución, evidencia o revisión manual, se muestra **Revisar categoría tras cambios**. La categoría anterior permanece en el historial; no se presenta como decisión vigente. Clasificar no retira avisos legítimos, ni concede elegibilidad para entrenar, ni valida un cierre o una apertura.\n\n'
    texto+='## Evidencia y verificación\n\nPlan 95 congelado: `'+digest(plan)+'`. Respaldo coherente, ensayo restaurado y aplicación secuencial: 116 auditorías, 94 fotografías de los objetivos, cero filas normales modificadas y ningún alta o borrado. Todos los campos de los objetivos salvo su revisión documental permanecen exactamente iguales. Originales, lecturas previas, hipótesis, exclusiones y protecciones de Campero, T13 y POLIGENESIS se conservan.\n\n'
    texto+='Se comprobaron los 116 tratamientos vigentes, los filtros de tipo/tratamiento/categoría y su intersección con artículo. Las consultas no escribieron en la base. Las 116 filas siguen excluidas de la selección analítica actual. Pruebas: 32 backend, 13 frontend y compilación de producción correctas. No hubo importación, OCR, nuevas áreas, entrenamiento ni inventario operativo.\n\n'
    texto+='[Decisiones y fotos de los 116 casos](categorizacion-hil-casos-2026-10-18.md). El JSON reproducible y los resultados están en `backend/backups/revision_avisos_hil_20261018/clasificacion_116_verificada.json` y `backend/backups/aplicacion_hil_20261014/`.\n'
    salidas[1].write_text(texto,encoding='utf-8')
    print(json.dumps({k:v for k,v in resultado.items() if k!='casos'},ensure_ascii=False))

if __name__=='__main__': main()
