"""El lenguaje de las historietas y el cine: seis fotografías completas."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(2275,2301),[1034,-500,-4,-1,-1,-2,-2,-1,-1,-3,-1,-2,-30,-1,-1,-33,-1,-12,-15,-1,-1,-1,-1,1,-1,-2],
  [1034,534,530,529,528,526,524,523,522,519,518,516,486,485,484,451,450,438,423,422,421,420,419,420,419,417]),
 (range(2301,2327),[1,-10,-1,-1,-5,-1,-1,-5,1,-2,-1,-10,-1,10,-5,-3,-3,-5,-20,17,-5,1,-3,-1,-1,3],
  [418,408,407,406,401,400,399,394,395,393,392,382,381,391,386,383,380,375,355,372,367,368,365,364,363,366]),
 (range(2327,2353),[1,-1,1,-1,-1,-3,2,-5,-1,-1,-1,2,-1,-10,-1,4,-2,-1,-1,1,-3,-1,-5,-2,-2,-4],
  [367,366,367,366,365,362,364,359,358,357,356,358,357,347,346,350,348,347,346,347,344,343,338,336,334,330]),
 (range(2353,2378),[1,-1,-2,-6,-1,-8,-1,-1,-3,-3,-5,-1,-1,-4,2,-5,-2,-1,-2,-3,-2,-1,-3,-5,-1],
  [331,330,328,322,321,313,312,311,308,305,300,299,298,294,296,291,289,288,286,283,281,280,277,272,271]),
 (range(2378,2404),[-1,-3,-1,-1,4,-3,-1,-6,-1,-1,-10,-2,-4,-1,-1,-1,-2,-2,-2,-2,-5,1,8,-3,-2,-2],
  [270,267,266,265,269,266,265,259,258,257,247,245,241,240,239,238,236,234,232,230,225,226,234,231,229,227]),
 (range(2404,2418),[-2,-1,-5,-2,-7,-2,-1,-2,-4,-3,-1,-10,13,-35],
  [225,224,219,217,210,208,207,205,201,198,197,187,200,165]),
]


def generar():
    snapshot='backups/continuacion_hil_18_20261015/articulo_53_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    for id,r in rows.items():
        if r['area'] in ('EDOAL','CIDOC'):
            cambios[id]={'area':'CEDOAL'}
            extras[id]={'motivo':'La foto escribe CEDOAL en ÁREA; se corrige la extracción sin crear áreas o alias.'}
    for id,fields in {2275:{'fecha_movimiento':'2010-04-09'},2276:{'referencia':'CINEMATECA'},
        2290:{'detalle':'BIBLIO. LA PAZ'},2291:{'fecha_movimiento':'2010-12-27'},2299:{'referencia':'OBSEQUIO'},
        2339:{'detalle':'INAUGURACION YOLANDA'},2379:{'fecha_movimiento':'2016-06-10','area':'CEDOAL'},
        2380:{'detalle':'BIBLIO UNCIA','area':'CEDOAL'},2382:{'area':None},2391:{'detalle':'ORURO CASA CULTURA','area':'CEDOAL'},
        2399:{'area':None},2400:{'area':None}}.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        2315:('2012-06-19','SECUENCIA_AJUSTADA','2012-05-09','09-05-12 aparece después del 19-06-12. Se conserva la literal y consulta técnica del antecedente.'),
        2318:('2012-08-08','SECUENCIA_AJUSTADA','2012-07-24','24-07-12 después de 08-08-12; consulta técnica del antecedente, sin trasladar fechas desde otro artículo.'),
        2319:('2012-08-08','SECUENCIA_AJUSTADA','2012-08-05','05-08-12 queda antes del antecedente 08-08-12. Literal conservada y consulta técnica, no fecha confirmada.'),
        2390:('2017-04-28','HIPOTESIS',None,'FIL tiene fecha en blanco. Consulta técnica de las filas de abril cotejadas, sin acreditar un día propio.'),
    }
    extras.update({
        2275:{'motivo':'La primera fecha es 09-04-10: abril, no septiembre. Ingreso 1034 y saldo 1034 están escritos; se conserva la marca repasada de ÁREA Galería.',
            'revision':{'anotacion_documental':'Galería repasado en ÁREA, sin anular toda la fila.'}},
        2276:{'motivo':'Salida 500 visible y saldo 534: 1034 - 500 = 534. Su magnitud no autoriza a reducirla; Cinemateca ocupa REF, sin atribuir una nueva área.'},
        2299:{'criterios':['T16'],'motivo':'OBQUIO en REF se interpreta como Obsequio por el contexto del renglón, con abreviatura documental conservada.',
            'revision':{'referencia_documental':'OBQUIO'}},
        2301:{'criterios':['T16'],'motivo':'El nombre del detalle no es inequívoco; se conserva la extracción con lectura parcial sin fusionar destinatarios.',
            'revision':{'lectura_detalle_parcial':'Ll...gua'}},
        2314:{'criterios':['T14'],'motivo':'La devolución tiene ingreso 10 y una marca tachada en SALIDAS. Se conserva 381 + 10 = 391, sin contar la marca ni anular el movimiento.',
            'revision':{'marcas_documentales':{'salidas':'Marca tachada, sin segunda cantidad confirmada'}}},
        2319:{'motivo':'El acercamiento confirma saldo 355 para la salida 20 desde 375; no se introduce un error del papel por confundir su trazo con 365.'},
        2326:{'motivo':'CTC se conserva como abreviatura literal no resuelta; no se sustituye por un área parecida para retirar el aviso.'},
        2343:{'motivo':'La abreviatura CtC de Biblioteca permanece sin una equivalencia institucional confirmada.'},
        2382:{'criterios':['T23'],'motivo':'DEV. FIL STA. CRUZ tiene ingreso 4, no un área llamada 4: 265 + 4 = 269. Se recupera la cantidad en la misma fila, sin nueva operación.',
            'revision':{'cantidades_documentales':{'ingresos':4,'salidas':None},'area_documental':None}},
        2388:{'motivo':'La abreviatura CFC/CTC no es inequívoca; permanece pendiente sin crear ni asignar otra área.',
            'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'revision':{'lectura_area_parcial':'CFC/CTC'}},
        2399:{'criterios':['T23'],'motivo':'La devolución de consignación tiene 1 en INGRESOS y ÁREA en blanco: 225 + 1 = 226; no existe un área 1.'},
        2400:{'criterios':['T23'],'motivo':'INGRESO tiene 8 en la columna INGRESOS, con saldo 234 desde 226. La extracción lo había colocado en ÁREA.'},
        2413:{'criterios':['T14'],'motivo':'Hay una marca negra antes del saldo 198, que sigue legible. Se conserva 201 - 3 = 198, sin anular el renglón.'},
        2417:{'motivo':'La salida 35 está escrita y explica 200 - 35 = 165. No se altera por su magnitud.'},
    })
    plan=construir(version=20,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(2277,2278),(2284,2285),(2370,2371),(2388,2389)],
        bases={53:{'primera_fila':2275,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 1034: base cero inferida, no un recuento físico previo.'}},
        observaciones=[{'articulo_id':53,'observado':True,'excluir_entrenamiento':False,
            'motivo':'Seis fotografías y 143 filas cotejadas. Ingresos 4, 1 y 8 recuperados desde la columna correcta, sin insertar nuevos movimientos. Primera fecha 09-04-2010 y otra fecha 10-06-2016 corregidas desde la foto. Cierre 165 coincide con el papel. Fechas técnicas, nombres parciales y abreviaturas CTC/CFC continúan identificados; no se fusionan instituciones por semejanza.'}],extras=extras)
    assert plan['cotejo']['cierres']=={53:165} and plan['cotejo']['discrepancias']==[]
    return plan


if __name__=='__main__':congelar(generar())
