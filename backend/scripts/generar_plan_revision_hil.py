"""Genera un lote de cotejos concretos; no busca cifras por similitud ni escribe BD."""
from pathlib import Path
import json, hashlib
from copy import deepcopy
from scripts.catalogo_revision_hil_20261013 import CASOS

BACKEND=Path(__file__).resolve().parents[1]
AUDIT=BACKEND/"backups/revision_hil_20261013T181307"
DEST=BACKEND/"backups/aplicacion_hil_20261014"
CAMPOS_BASE=("articulo_id","lote_id","fecha_movimiento","detalle","referencia","area","ingresos","salidas","saldo_registrado","numero_pagina","orden_fila","estado")
def digest(x):
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def generar():
    expediente=json.loads((AUDIT/"expediente.json").read_text(encoding="utf-8"))
    pages={p["id"]:p for p in expediente["paginas"]}
    rows={r["id"]:r for p in pages.values() for r in p["filas"]}
    rowpages={r["id"]:p for p in pages.values() for r in p["filas"]}
    changes={}
    def add(id,tipos,cambios=None,**meta):
        row=rows[id];p=rowpages[id]
        entry=changes.setdefault(id,{"id":id,"articulo_id":row["articulo_id"],"pagina":p["id"],
            "esperado":{k:row[k] for k in CAMPOS_BASE},"cambios":{},
            "revision":{"criterios":[],"motivo":"","hallazgos":[],"tipo_fila":"MOVIMIENTO"},
            "fuente":p["imagen"],"sha256_imagen":p["sha256_imagen"]})
        entry["cambios"].update(cambios or {})
        rev=entry["revision"]
        rev["criterios"]=sorted(set(rev["criterios"]+tipos))
        for k,v in meta.items():
            if k=="hallazgos":rev[k]=sorted(set(rev[k]+v))
            else:rev[k]=v
        return entry

    add(9657,["T01"],{"ingresos":40,"saldo_registrado":41},saldo_documental=41,origen_saldo="FOTO",motivo="La foto muestra ingreso40/saldo41; se corrige la lectura10/11.",hallazgos=["ERROR_OCR"])
    add(9658,["T01"],{"saldo_registrado":36},saldo_documental=36,origen_saldo="FOTO",motivo="Salida5: saldo manuscrito36, no6. La siguiente fila29 era correcta.",hallazgos=["ERROR_OCR"])
    for id,n in [(4025,2),(4026,5),(4030,3),(4035,5)]:
        add(id,["T02","T23"],{"ingresos":n,"salidas":None,"area":None,"nodo_grafo":"Origen no especificado","area_estado":"SIN_AREA_REGISTRADA","requiere_auditoria_nodo":False},
            motivo="La cifra está en INGRESOS; el OCR la colocó en AREA. Se conserva la extracción inicial.",hallazgos=["COLUMNA_OCR_DESPLAZADA"])
    for id,n in [(4027,3),(4028,1),(4029,1),(4031,8),(4032,5),(4033,4),(4034,1)]:
        cambios={"ingresos":None,"salidas":n}
        if rows[id]["area"] is None:cambios["nodo_grafo"]="Destino no especificado"
        add(id,["T02"],cambios,motivo="La columna SALIDAS de la foto contiene la cifra guardada como ingreso.",hallazgos=["COLUMNA_OCR_INVERTIDA"])
    add(733,["T03"],{"ingresos":3,"salidas":None,"saldo_registrado":80},
        motivo="77+3=80. El (3) de salidas se conserva como anotación, según el criterio del titular.",
        saldo_documental=80,marcas_documentales={"salidas":"(3)"},hallazgos=["PARENTESIS_INTERPRETADO"],origen_cantidades="INTERPRETACION_HUMANA")

    # Bloque completo de JULIO: primero lectura literal; el esperado conserva
    # la diferencia del papel. La rectificación450→440 recupera la continuidad.
    amounts=[-2,2,-10,7,-3,1,-2,2,-1,-10,-10,-3,-75,-5,10,-2,-3,-10,-3,-1,-30,-5,-10,14,-5,-1]
    saldos=[587,589,579,586,583,584,582,584,593,583,573,570,495,490,500,498,495,485,482,481,451,446,436,450,435,434]
    assert len(amounts)==len(pages["L0094-P03"]["filas"])==len(saldos)
    for row,q,s in zip(pages["L0094-P03"]["filas"],amounts,saldos):
        add(row["id"],["T04"],{"ingresos":q if q>0 else None,"salidas":-q if q<0 else None,"saldo_registrado":s},
            motivo="Bloque cotejado por renglón. Se corrige OCR y se conserva saldo escrito frente a la cadena independiente.",
            saldo_documental=s,origen_saldo="FOTO",hallazgos=["BLOQUE_OCR_REVISADO"])
    add(5090,["T04"],reconstruir_cadena=True)
    add(5113,["T04","T16"],{"saldo_registrado":440},saldo_documental=450,
        anotacion_margen="440 a lápiz",hallazgos=["RECTIFICACION_MARGEN","DISCREPANCIA_DOCUMENTAL"],
        motivo="Se toma la rectificación440 anotada en el margen; coincide con el esperado440 y recupera la cadena tras el error inicial10.",origen_saldo="ANOTACION_MARGEN")
    # RIMSA, hoja completa: saldo vigente reconstruido, saldo escrito separado.
    for row in pages["L0005-P01"]["filas"]:
        add(row["id"],["T05"],motivo="Continuidad de RIMSA cotejada. Los saldos escritos se conservan separados del saldo reconstruido.",
            saldo_documental=row["saldo_registrado"],origen_saldo="FOTO")
    add(255,["T05"],saldo_base=0,reconstruir_cadena=True)
    for id in range(271,281):
        add(id,["T05"],usar_saldo_esperado=True,origen_saldo="RECONSTRUIDO",
            hallazgos=["DISCREPANCIA_DOCUMENTAL_NO_CORREGIDA_EN_PAPEL"])
    add(276,["T01","T05"],{"salidas":7},motivo="Reposición Recepción muestra salida7, no4; se corrige OCR antes de reconstruir el tramo.",hallazgos=["ERROR_OCR"])
    add(1449,["T06"],{"saldo_registrado":25},saldo_documental=25,lectura_asistente_previa=26,
        motivo="El titular confirma25 frente a la lectura previa26. Coincide con22+3 y la salida siguiente deja24.",
        origen_saldo="CONFIRMACION_USUARIO",hallazgos=["LECTURA_CORREGIDA_POR_CRITERIO_HUMANO"])
    add(1455,["T10"],{"fecha_movimiento":"2012-10-04"},fecha_documental="4-10-12",origen_fecha="FOTO",
        motivo="La fecha visible es4-10-12, no14-10-12.",hallazgos=["ERROR_OCR_FECHA"])
    add(10051,["T07"],{"ingresos":10,"salidas":None},
        motivo="S-INGRESO10 sube saldo1→11; se corrige la columna del trabajador conservando la columna literal en evidencia.",
        columnas_documentales={"ingresos":None,"salidas":10},hallazgos=["COLUMNA_DOCUMENTAL_INVERTIDA"],origen_cantidades="INTERPRETACION_HUMANA")
    for id,q in [(8023,2),(8024,2),(8025,1)]:
        add(id,["T07","T22"],{"ingresos":q,"salidas":None},motivo="Las cifras en SALIDAS aumentan los saldos3,5,6; se interpreta el efecto como ingreso según criterio.",
            columnas_documentales={"ingresos":None,"salidas":q},hallazgos=["COLUMNA_DOCUMENTAL_INVERTIDA"],origen_cantidades="INTERPRETACION_HUMANA")
    add(8023,["T22"],saldo_base=1,reconstruir_cadena=True,motivo="La foto contiene una línea previa con saldo1. Se conserva como base, sin crear un ingreso ficticio.")
    for id in [7712,7713,7726,7727,7296]:
        add(id,["T08"],saldo_documental=None,origen_saldo="RECONSTRUIDO",usar_saldo_esperado=True,
            motivo="Saldo vacío en la foto; se usa el esperado con marca de reconstrucción.",hallazgos=["SALDO_AUSENTE_RECONSTRUIDO"])
    # Fechas ausentes cotejadas: mantener una fecha técnica que no rompe el orden.
    for id in [12272,7294,*range(7712,7718),7722,7724,7296,7297,*range(9761,9765)]:
        add(id,["T09"],origen_fecha="HIPOTESIS",fecha_documental=None,
            motivo_fecha="Fecha ausente en la hoja; se conserva una asignación técnica, sin afirmar fecha real.",
            motivo="Dato reconstruido identificado; la fecha estimada se excluye de entrenamiento temporal.",
            hallazgos=["FECHA_ESTIMADA"])
        changes[id]["cambios"].setdefault("fecha_movimiento",rows[id]["fecha_movimiento"])
    # Fechas cruzadas: solo pares comprobados, no ordenar todas las filas.
    for a,b in [(746,747),(1025,1026),(1033,1034)]:
        dates=[rows[a]["fecha_movimiento"],rows[b]["fecha_movimiento"]]
        if b==1026:dates[1]="2011-08-01"
        for id,new,source in [(a,min(dates),dates[0]),(b,max(dates),dates[1])]:
            add(id,["T10","T11"],{"fecha_movimiento":new},fecha_documental=source,
                origen_fecha="SECUENCIA_AJUSTADA",fecha_documental_fuera_orden=True,
                motivo_fecha="Fechas intercambiadas para consulta según el criterio del titular; no se cambia el renglón ni la fuente.",
                motivo="Se conserva la fecha escrita y se marca el ajuste de secuencia como inferencia.",hallazgos=["FECHA_AJUSTADA_POR_SECUENCIA"])
    for page,new in [("L0001-P02",1),("L0001-P03",2),("L0001-P04",3),("L0001-P01",4)]:
        for r in pages[page]["filas"]:
            add(r["id"],["T12"],{"orden_pagina_validado":new},
                motivo="Orden validadoP02→P03→P04→P01; se conserva el número de foto original.",
                hallazgos=["ORDEN_DE_HOJAS_CORREGIDO"])
    add(6,["T22"],saldo_base=407,origen_saldo_base="HIPOTESIS",
        motivo="La primera fila disponible tiene ingreso1/saldo408; base previa407 inferida solo para continuidad, sin inventar otra transacción.")

    add(9755,["T13"],tipo_fila="BASE_DOCUMENTAL",saldo_documental=4,motivo="Saldo según inventario escrito4: punto de partida documental.")
    for id,q in [(9761,1),(9762,2),(9763,1),(9764,4)]:
        add(id,["T13"],{"ingresos":q,"salidas":None},tipo_fila="MOVIMIENTO",saldo_documental=None,
            usar_saldo_esperado=True,reconstruir_cadena=True,origen_saldo="RECONSTRUIDO",
            origen_cantidades="INTERPRETACION_USUARIO",contexto_fuente="Cuadro Para la Venta, Donación, Saldo y Total.",
            motivo="El titular indica tratar estas cuatro filas como ingresos1,2,1,4; se conserva que proceden del cuadro resumen.",
            hallazgos=["CUADRO_INTERPRETADO_COMO_INGRESOS","FECHA_ESTIMADA"])
    add(9765,["T13","T15"],{"saldo_registrado":1},tipo_fila="BASE_DOCUMENTAL",saldo_documental=1,
        motivo="Saldo1 visible al16-12-09; se conserva la diferencia con el tramo de ingresos interpretados.",hallazgos=["DIFERENCIA_CON_BASE_DOCUMENTAL"])
    for id in range(6389,6393):
        add(id,["T14"],{"estado":"ANULADO_DOCUMENTO"},tipo_fila="ANULADO",nota_anulacion_ids=[6393,6394],
            motivo="La hoja anula expresamente los cuatro registros anteriores; sus cantidades se conservan sin efecto vigente.",hallazgos=["ANULACION_EN_PAPEL"])
    for id in [6393,6394]:
        add(id,["T14"],{"estado":"NOTA_DOCUMENTAL"},tipo_fila="NOTA",anula_movimientos=list(range(6389,6393)),
            motivo="Nota de anulación en dos renglones, conservada como evidencia y excluida del cómputo.",hallazgos=["NOTA_DOCUMENTAL"])
    add(7294,["T15"],tipo_fila="RECUENTO",saldo_documental=3,
        motivo="Recuento físico escrito3 frente a saldo previo21. Se sigue desde3 y se conserva la diferencia18.",hallazgos=["DISCREPANCIA_RECUENTO"])
    add(7274,["T16"],saldo_documental=17,origen_saldo="ANOTACION_MARGEN",ajuste_disponibilidad=-3,
        anotacion_margen="(14), 3 s/disco",unidades_incompletas_documentales=3,
        motivo="17 totales, anotación14 utilizables y3 sin disco. Se interpreta disponibilidad14 sin crear una baja ni borrar la anotación.",hallazgos=["ANOTACION_MARGEN","DISPONIBILIDAD_DOCUMENTAL"])
    add(10287,["T18"],{"referencia":"Ventas","referencia_estado":"PRESENTE","requiere_auditoria_referencia":False},
        motivo="Comilla explícita en REF repite Ventas de la fila10286.",referencia_documental='"',antecedente_referencia_id=10286,hallazgos=["REPETICION_DOCUMENTAL"])
    add(10301,["T18"],{"referencia":"DEV.","referencia_estado":"PRESENTE","requiere_auditoria_referencia":False},
        motivo="Comilla en REF repite DEV de la entrada10299; la fila intermedia no tiene referencia. Se conserva el antecedente de la misma columna.",referencia_documental='"',antecedente_referencia_id=10299,hallazgos=["REPETICION_DOCUMENTAL"])
    for id in range(9240,9248):
        add(id,["T19"],saldo_documental=None,origen_saldo="HIPOTESIS",usar_saldo_esperado=True,reconstruir_cadena=True,
            motivo="El pliegue tapa el saldo. Se reconstruye por continuidad y se marca como hipótesis, no como lectura de la foto.",
            hallazgos=["SALDO_TAPADO_HIPOTETICO"])
    add(560,["T20"],motivo="El titular confirma conservar las agrupaciones realizadas al escanear; esta hoja sigue en el artículo original.",hallazgos=["AGRUPACION_CONFIRMADA_POR_USUARIO"])
    for id in [12084,12085]:
        add(id,["T21"],motivo="Dos filas físicas parecidas: se conservan sin eliminar; artículo observado y excluido del entrenamiento.",hallazgos=["FILAS_AMBIGUAS_SIN_ELIMINAR"])

    # Las observaciones no inhabilitan operaciones actuales: stock y apertura
    # continúan con sus controles, la exclusión afecta el conjunto histórico.
    observations={}
    for id,reason,excluded in [(12084,"DosFIL-25 ambiguos; conservar ambos hasta determinar su efecto.",True),
        (5098,"Diferencia10 en el papel, rectificada a lápiz en440 después de varios movimientos; hallazgo conservado.",False),
        (271,"Error del papel conservado; saldo vigente reconstruido y marcado.",False),
        (7294,"Recuento3 frente a21: discrepancia18 reconocida en el histórico.",False),
        (9765,"Cuatro ingresos interpretados y saldo posterior1; diferencia documental conservada.",False)]:
        observations[rows[id]["articulo_id"]]={"observado":True,"excluir_entrenamiento":excluded,"motivo":reason}
    policy=json.loads((DEST/"criterios_version_1.json").read_text(encoding="utf-8"))
    plan={"version":1,"corte":expediente["resumen"]["corte_bolivia"],"criterio_sha256":digest(policy),
        "respuestas_sha256":policy["procedencia"]["sha256"],"revisiones":list(changes.values()),
        "observaciones_articulos":[{"articulo_id":k,**v} for k,v in observations.items()],
        "sin_reasociaciones_ni_borrados":True,
        "limites":["Este lote cubre los ejemplos ampliados, no certifica las693hojas.","T17 pendiente de lecturas completas: no aplica unión por parecido o frecuencia.","Continuar el cotejo del resto con estos mismos criterios; no inventar cantidades sin una hipótesis trazable."]}
    return plan

if __name__=="__main__":
    DEST.mkdir(exist_ok=True)
    plan=generar()
    (DEST/"plan_correcciones.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"revisiones":len(plan["revisiones"]),"articulos":len({r["articulo_id"] for r in plan["revisiones"]}),"plan_sha256":digest(plan)},ensure_ascii=False))

