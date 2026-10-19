"""Categoriza los 116 avisos restantes usando sus cotejos conservados y los criterios del titular."""
from collections import Counter
from datetime import datetime, UTC
from pathlib import Path
import hashlib, json
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.calidad_kardex import tipos_alerta
from app.services.revision_documental import snapshot_revision
from app.services.tratamiento_hil import huella_datos, CATEGORIAS
from scripts.aplicar_revision_hil import BACKEND
from scripts.plan_enmienda_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar

# Solo estas lecturas se consideran no inequívocas, según su cotejo previo.
LECTURAS_INCIERTAS={2181,2388,3648,3828,5235,5271,6328,6680,6838,6959,7772,8078,8097,9599,9676,11084,12158}
MARCAS_AREA={2547,3145,3153,3838,7961,8953}
MARCAS_REF={2209,3141,3142,3150,3151,3153,3155,3157,3163,3173,3174,3208,6626,11012}
AMBITOS_SALDO={560,4871,6062,7667,8359}

def decision(m,campo):
    r=m.revision_documental; id=m.id
    if campo=='saldo':
        if r.get('dependencia_fuera_objetivo'):
            categoria='DEPENDENCIA_OTRA_FILA'; criterios=['T04','T05']
            motivo='El saldo de esta fila depende de una lectura o fila faltante del contexto fuera de los objetivos. Se conserva la dependencia y el cálculo condicional, sin modificar vecinos ni fabricar una operación.'
        elif id==12084:
            categoria='POSIBLE_DUPLICIDAD_DOCUMENTAL';criterios=['T21']
            motivo='Se conservan los dos renglones físicos parecidos y su efecto condicionado. La similitud no acredita duplicación: no se elimina ninguna operación y sigue la exclusión ya documentada.'
        elif id in AMBITOS_SALDO:
            categoria='AMBITO_DOCUMENTAL_INCIERTO';criterios=['T05','T20']
            motivo='La continuidad entre hojas o el ámbito STAND/general no está acreditado. Se conserva el saldo escrito y el cálculo condicional; no se inventa un recuento o movimiento compensatorio.'
        else:
            categoria='DISCREPANCIA_DOCUMENTAL';criterios=['T05']
            motivo='El dato escrito cotejado difiere del cálculo independiente. El saldo calculado ya permite consultar la reconstrucción; el valor documental y su diferencia quedan marcados, sin corregir cantidades legibles para cuadrar.'
        motivo+=f' Saldo escrito cotejado: {r.get("saldo_documental")}; vigente: {m.saldo_registrado}; cálculo independiente: {m.saldo_calculado}.'
    elif campo=='fecha':
        categoria='DEPENDENCIA_OTRA_FILA';criterios=['T10','T11']
        assert r.get('dependencia_fuera_objetivo'),id
        motivo='La fecha escrita se conserva. La cronología requiere un ajuste conjunto con filas vecinas fuera del alcance, que no se modifican; no se presenta otra fecha como confirmada.'
    elif campo=='area':
        criterios=['T17']
        if id==7455:
            categoria='EFECTO_INDETERMINADO';criterios=['T19']
            motivo='La devolución carece de ingreso, salida y saldo propios. Se mantiene como efecto indeterminado; continuar la consulta sin efecto cuantificado es una hipótesis y no una cantidad cero confirmada.'
        elif id in MARCAS_AREA:
            categoria='MARCA_NO_INTERPRETADA';criterios=['T18','T19']
            motivo='La marca pequeña o punto aislado de ÁREA se conserva como evidencia. No acredita por sí solo repetición, nombre de unidad ni ausencia confirmada.'
        elif id in LECTURAS_INCIERTAS:
            categoria='LECTURA_INCIERTA';criterios=['T17','T19']
            motivo=f'Lectura vigente {m.area!r}, con ambigüedad ya documentada en el cotejo. Se conserva literal, sin completar letras ni asignar por frecuencia una institución que la foto no acredita.'
        else:
            categoria='CATALOGO_NO_CONFIRMADO'
            motivo=f'Nombre o sigla documental {m.area!r} conservado. Falta equivalencia institucional acreditada; esto se separa de un error OCR sin crear un alias o confundir persona, lugar y unidad.'
    else:
        assert campo=='referencia'
        criterios=['T18','T19']
        categoria='MARCA_NO_INTERPRETADA' if id in MARCAS_REF else 'LECTURA_INCIERTA'
        motivo=('La referencia contiene un punto o trazo aislado sin significado acreditado; se conserva como marca, sin tratarlo como comilla inequívoca ni documento numerado.'
                if id in MARCAS_REF else 'La atribución o abreviatura de REF no es inequívoca. Se conserva el literal y la foto, sin inventar documento, embajada, institución ni nombre completo.')
    assert categoria in CATEGORIAS
    return {'campo':campo,'categoria':categoria,'motivo':motivo,'criterios':criterios,
            'dato_confirmado':False,'marca_conservada':True}

def main():
    carpeta=BACKEND/'backups/revision_avisos_hil_20261018'
    previo=json.loads((carpeta/'corte_posterior_planes_86_94.json').read_text(encoding='utf-8'))
    anteriores={c['id']:c for c in previo['casos'] if c['avisos']};assert len(anteriores)==116
    especificaciones={};snapshots=[];conteos=Counter();ahora=datetime.now(UTC).isoformat()
    with SessionLocal() as db:
        actuales={m.id for m in db.query(M).filter(M.lote_id.isnot(None),M.estado=='ACTIVO') if tipos_alerta(m)}
        assert actuales==anteriores.keys(),'No alterar ni ampliar la cola congelada'
        for id,c in anteriores.items():
            m=db.get(M,id);r=snapshot_revision(m);assert r==c['fila_actual'],id
            foto=(BACKEND/m.ruta_imagen_respaldo).resolve()
            assert hashlib.sha256(foto.read_bytes()).hexdigest()==c['foto_sha256']
            avisos=tipos_alerta(m);decisiones=[decision(m,campo) for campo in avisos]
            conteos.update(d['categoria'] for d in decisiones)
            tratamiento={'version':1,'avisos':avisos,'decisiones':decisiones,'huella_datos':huella_datos(m),
                         'categorizado_en':ahora,'autor':'Codex, revisión asistida según criterios del titular',
                         'foto_sha256':c['foto_sha256'],'basado_en_cotejo_previo':True,
                         'autorizacion':'corrige todo, quiero que todo ya este categorizado; aplicar mis criterios y conservar marcas',
                         'datos_confirmados':False,'habilita_entrenamiento':False}
            motivo=m.revision_documental['motivo']+' Tratamiento explícito: '+'; '.join(CATEGORIAS[d['categoria']] for d in decisiones)+'. Se conservan las advertencias legítimas y las exclusiones; categorizado no equivale a confirmado.'
            criterios=sorted({k for d in decisiones for k in d['criterios']})
            especificaciones[id]=({},criterios,motivo,{'tratamiento_hil':tratamiento})
            snapshots.append(r)
    out=carpeta/'cola_clasificacion_116.json';assert not out.exists()
    out.write_text(json.dumps({'generado_en':ahora,'autorizacion':'Solicitud expresa de categorización completa de los avisos restantes, 18/10/2026','casos':snapshots,'categorias':dict(conteos)},ensure_ascii=False,indent=2),encoding='utf-8')
    congelar(construir(numero=95,especificaciones=especificaciones,pendientes=sorted(anteriores),limites=[
        '116 objetivos observados: categorizar el tratamiento apoyándose en su cotejo previo y fotos con huella verificada.',
        'Solo añade decisiones documentales y auditoría; no declara un nuevo cotejo de hojas ni modifica valores o vecinos.',
        'Diferencias reales, hipótesis, fechas documentales, marcas y dependencias quedan visibles; no se habilita entrenamiento.',
        'Sin inventar áreas, alias, fechas confirmadas, recuentos ni operaciones. Campero y artículos separados conservan sus protecciones.'
    ]))

if __name__=='__main__': main()
