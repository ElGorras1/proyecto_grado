"""Dieciséis observados; las ocho fotos se consultan sin revisar filas normales."""
from copy import deepcopy
import json,hashlib
from scripts.aplicar_revision_hil import BACKEND,DEST
from scripts.generar_plan_revision_hil import CAMPOS_BASE
from scripts.cotejo_transcripcion_hil import DERIVADOS,congelar
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.calidad_kardex import tipos_alerta
from app.services.revision_documental import snapshot_revision
from app.services.clasificador_nodos import clasificar_movimiento

ESPECIFICACIONES={
 9049:({'referencia':'CENTRO STA CRUZ','area':None},['T17','T23'],'CENTRO está en REF y STA CRUZ en ÁREA: se conserva literalmente la procedencia en referencia, sin inventar un área institucional ni alias.',{'columnas_documentales':{'referencia':'CENTRO','area':'STA CRUZ'},'procedencia_documental':'CENTRO STA CRUZ'}),
 9053:({'ingresos':None,'salidas':1},['T07'],'El papel coloca 1 en INGRESOS, pero FIL-LP y el saldo de 8 a 7 acreditan salida 1 según el criterio de columna equivocada del titular. Se conserva la columna escrita y se corrige el sentido; no se inventa otra operación.',{'columna_reinterpretada':'INGRESOS a SALIDAS','columnas_documentales':{'ingresos':1,'salidas':None,'saldo':7}}),
 9419:({'area':None},['T18'],'ÁREA contiene solo un punto, sin nombre ni comillas inequívocas. Se conserva la marca en evidencia y el área ausente, sin copiar CEDOAL de otra hoja.',{'columnas_documentales':{'area':'.'}}),
 9422:({'fecha_movimiento':'2018-12-27'},['T11'],'Literal 14-8-18 después de 27-12-18. Fecha técnica del antecedente para consulta, sin cambiar ni certificar el literal.',{'origen_fecha':'SECUENCIA_AJUSTADA','fecha_documental':'2018-08-14','motivo_fecha':'14-8-18 está escrito fuera de orden; consulta técnica del antecedente 27-12-18, sin modificar la fila vecina.'}),
 9582:({'fecha_movimiento':'2019-07-05'},['T10','T22'],'Primera venta: salida 2 y saldo 10, con saldo 12 explícito en el renglón anterior sin cantidades. Se toma esa base escrita sin añadir ingreso ni recuento ficticio. Fecha propia 5-7-19 corregida del OCR 7-5-19.',{'saldo_base':12,'origen_saldo_base':'FOTO','motivo_base':'Saldo 12 explícito sobre la primera venta, sin cantidades, fecha ni leyenda de recuento. Base de contexto, no una transacción nueva.','base_documental_contexto':{'saldo':12,'ingresos':None,'salidas':None,'fecha':None}}),
 9583:({},['T05'],'INGRESO 10 y saldo 8 son legibles después de saldo 10: cálculo local 20 y diferencia -12 del papel. Se conservan cantidad y saldo escritos; no se sustituye por salida 2 ni se inventa un recuento. Vecinos normales intactos; el acumulado global de contexto cerraría en 17 frente al escrito 5 y su evaluación queda documentada sin modificar vecinos.',{'descuadre_del_papel_conservado':True,'diferencia_local_papel':-12,'dependencia_contexto':{'articulo_id':242,'cierre_escrito_contexto':5,'cierre_condicional_contexto':17,'limite':'No recalcular ni modificar movimientos normales por fuera del aviso. Diferencia material pendiente; no equivale a cierre global validado.'}}),
 11050:({'nodo_grafo':'Base documental','area_estado':'NO_APLICA','requiere_auditoria_nodo':False},['T22'],'Según Inventario, saldo 1, cantidades vacías. Es base escrita, sin área operativa aplicable ni ingreso ficticio.',{'tipo_fila':'BASE_DOCUMENTAL'}),
 11051:({'referencia':'ECOLO. STA CRUZ','area':None},['T17','T23'],'ECOLO. figura en REF y STA CRUZ en ÁREA: procedencia conservada como texto de referencia sin crear alias o institución. Se corrige BOLO. OCR desde la foto.',{'columnas_documentales':{'referencia':'ECOLO.','area':'STA CRUZ'},'procedencia_documental':'ECOLO. STA CRUZ'}),
 8010:({'nodo_grafo':'Recuento documental','area_estado':'NO_APLICA','requiere_auditoria_nodo':False},['T15'],'La fila dice Saldo Según Recuento Físico y escribe 6, sin cantidades. Se conserva como recuento documental, no como entrada/salida ni solicitud de inventar un área. Anotaciones marginales se mantienen en la foto sin asignarlas como operaciones.',{'tipo_fila':'RECUENTO','recuento_documental_explicito':True}),
 8012:({'ingresos':4,'area':None},['T23'],'El 4 de FIL está en INGRESOS, no en ÁREA. Recepción recuperada de columna visible y área vacía; saldo pasa de 2 a 6.',{'desplazamiento_columna_ocr':True,'columnas_documentales':{'ingresos':4,'area':None}}),
 9734:({'estado':'ANULADO_DOCUMENTO','ingresos':None,'salidas':None},['T14','T19'],'Renglón PAGO VENTA completamente tachado en fecha, detalle, referencia, área y cantidad. Se anula documentalmente sin efecto, conservando foto y extracción original; no se certifica la fecha ni cifra tapadas.',{'tipo_fila':'ANULADO_DOCUMENTO','saldo_documental':None,'origen_saldo':'HIPOTESIS','origen_fecha':'HIPOTESIS','fecha_documental':None,'motivo_fecha':'Fecha propia oculta por tachadura: valor de consulta previo conservado solo como técnico, sin certificar lectura bajo tinta.','marcas_documentales':'Cancelación integral de fecha, detalle, REF, ÁREA y cantidad.'}),
 9735:({},['T14'],'Venta CID con salida 2 y saldo 0 legibles. Su aviso venía de contabilizar la fila anterior completamente tachada: al anular 9734, el saldo anterior válido es 2 y el esperado es 0. No se cambia esta salida para cuadrar.',{'aviso_causado_por_fila_anulada':9734}),
 9826:({'nodo_grafo':'Base documental','area_estado':'NO_APLICA','requiere_auditoria_nodo':False},['T22'],'Saldo según Inventario 3 sin cantidades: base documental, no movimiento que requiera área operativa ni ingreso fabricado.',{'tipo_fila':'BASE_DOCUMENTAL'}),
 9830:({'estado':'NOTA_DOCUMENTAL','nodo_grafo':'Nota documental','area_estado':'NO_APLICA','requiere_auditoria_nodo':False},['T13'],'Saldo 1 del 16-12-09 solo confirma el saldo anterior y carece de cantidades. Se conserva como nota sin efecto ni área operativa; no se declara recuento físico ni se extiende la excepción T13 de cuatro ingresos.',{'tipo_fila':'NOTA_DOCUMENTAL'}),
 8218:({},['T10'],'La fecha propia 17-10-13 es correcta. El aviso proviene del vecino 8217: vigente 21-10-13 pero foto 2-10-13. Se documenta la dependencia sin modificar la fila no observada ni fabricar una fecha técnica para encubrir ese error OCR.',{'dependencia_fuera_objetivo':{'id':8217,'fecha_vigente':'2013-10-21','fecha_documental_contexto':'2013-10-02','motivo':'Corrección de vecino fuera de la cola autorizada; no aplicada. El aviso del objetivo se conserva.'}}),
 8220:({'area':None,'fecha_movimiento':'2019-07-05'},['T09','T23'],'Ingreso 9 y saldo 10 legibles, pero ÁREA y FECHA propias están vacías. SDH no aparece en la foto. Se retira el área OCR y se conserva fecha de consulta previa solo como hipótesis, sin copiar como literal el 5-7-19 de la venta siguiente.',{'origen_fecha':'HIPOTESIS','fecha_documental':None,'motivo_fecha':'FECHA vacía; consulta técnica anterior conservada, no fecha documental certificada.','columnas_documentales':{'area':None,'fecha':None}}),
}

def generar():
    path=BACKEND/'backups/revision_avisos_hil_20261016/bloque_69/contexto_antes.json'
    rows={r['id']:r for r in json.loads(path.read_text(encoding='utf-8'))}
    entries=[]
    with SessionLocal() as db:
        for id,(cambios,criterios,motivo,extra) in ESPECIFICACIONES.items():
            r=rows[id];m=db.get(M,id);assert snapshot_revision(m)==r and tipos_alerta(m) and not r['revision_documental']
            cambios=deepcopy(cambios)
            if any(k in cambios for k in ('area','referencia','detalle','ingresos','salidas')):
                c=clasificar_movimiento(cambios.get('detalle',r['detalle']),cambios.get('referencia',r['referencia']),cambios.get('area',r['area']),cambios.get('ingresos',r['ingresos']),cambios.get('salidas',r['salidas']),db)
                cambios.update({k:getattr(c,k) for k in DERIVADOS})
            rev={'criterios':criterios,'motivo':motivo,'hallazgos':['AVISO_HIL_COTEJADO_CON_FOTO'],'tipo_fila':'MOVIMIENTO','saldo_documental':r['saldo_registrado'],'origen_saldo':'FOTO','origen_cantidades':'FOTO','origen_fecha':'FOTO','fecha_documental':cambios.get('fecha_movimiento',r['fecha_movimiento']),'usar_saldo_esperado':False,'reconstruir_cadena':False,'cotejo_pagina_completa':False,'alcance':'SOLO_MOVIMIENTO_OBSERVADO_HIL','avisos_antes':tipos_alerta(m),**extra}
            foto=(BACKEND/r['ruta_imagen_respaldo']).resolve()
            entries.append({'id':id,'articulo_id':r['articulo_id'],'pagina':f'L{r["lote_id"]:04d}-P{r["numero_pagina"]:02d}','esperado':{k:r[k] for k in CAMPOS_BASE},'esperado_adicional':{k:r[k] for k in DERIVADOS},'cambios':cambios,'revision':rev,'fuente':str(foto),'sha256_imagen':hashlib.sha256(foto.read_bytes()).hexdigest()})
    policy=json.loads((DEST/'criterios_version_1.json').read_text(encoding='utf-8'))
    from scripts.generar_plan_revision_hil import digest
    return {'version':69,'criterio_sha256':digest(policy),'revisiones':entries,'sin_reasociaciones_ni_borrados':True,'autorizacion_adicional':'Solo movimientos con observaciones HIL por instrucción expresa del titular; vecinos como contexto sin modificaciones.','observaciones_articulos':[],'cotejo':{'modo':'SOLO_AVISOS_HIL','movimientos':len(entries),'fotografias':len({e['fuente'] for e in entries}),'ids_objetivo':sorted(ESPECIFICACIONES),'ids_pendientes_esperados':[8218,9583],'contexto_snapshot':str(path.relative_to(BACKEND))},'limites':['No declarar revisadas las filas normales ni modificar vecinos.','No inventar áreas ni operaciones para quitar diferencias legítimas.','8218 depende de un vecino no observado; 9583 conserva diferencia -12 del papel y cierre contextual discrepante.']}

if __name__=='__main__':congelar(generar())
