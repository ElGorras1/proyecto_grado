"""Alberto Guerra: seis fotografías completas cotejadas."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(4242,4268),[199,-6,4,-116,-1,-1,1,-1,-1,25,-2,-1,-1,-10,-40,38,-10,-1,-3,-1,-8,-1,-5,-1,-15,18],
  [199,193,197,81,80,79,80,79,78,103,101,100,99,89,49,87,77,76,73,72,64,63,58,57,42,60]),
 (range(4268,4294),[-1,-1,-1,-1,-1,-52,-1,100,100,300,-1,-2,2,-10,9,-3,-2,2,-10,-10,-3,-75,9,-5,-2,-3],
  [59,58,57,56,55,3,2,102,202,502,501,499,501,491,500,497,495,497,487,477,474,399,408,403,401,398]),
 (range(4294,4320),[-10,-3,-1,-30,-5,-10,13,-5,-1,1,-1,-2,-2,2,-2,-1,-1,1,5,-1,-1,1,1,-10,-5,14],
  [388,385,384,354,349,339,352,347,346,347,346,344,342,344,342,341,340,341,346,345,344,345,346,336,331,345]),
 (range(4320,4345),[-3,-5,8,-5,-1,-1,4,-1,-1,-10,-1,9,-2,-3,-5,-5,-4,1,-1,5,-3,-3,2,-3,-2],
  [342,337,345,340,339,338,342,341,340,330,329,338,336,333,328,323,319,320,319,324,321,318,320,317,315]),
 (range(4345,4371),[-5,-1,-1,4,-2,-1,-3,-1,-2,-1,-1,-2,-1,-2,-2,-4,-3,4,-2,-2,-1,-1,-1,-5,-3,-3],
  [310,309,308,312,310,309,306,305,303,302,301,299,295,296,294,290,287,271,289,287,286,285,284,279,276,273]),
 (range(4371,4385),[-2,-2,-2,-2,-5,-4,-20,-5,2,1,-5,4,-8,-5],
  [271,269,267,265,260,256,236,231,233,234,229,233,225,220]),
]


def generar():
    snapshot='backups/continuacion_hil_13_20261015/articulo_77_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={}
    for id,r in rows.items():
        if r['area'] in ('CEDOCAL','CEDOSL'):cambios[id]={'area':'CEDOAL'}
    for id,fields in {4262:{'detalle':'Municipios Sucre','referencia':'Sala'},4263:{'detalle':'Jovenes P/Cultura','referencia':'Sala'},
        4274:{'referencia':'Biblioteca','area':'Dirección'},4278:{'referencia':'Biblioteca','area':'Galería'},4287:{'fecha_movimiento':'2012-05-09'},
        4307:{'detalle':'Taller Metodologia'},4346:{'area':'CAP'},4353:{'detalle':'La Paz Lee'},4355:{'fecha_movimiento':'2017-10-05'},
        4376:{'fecha_movimiento':'2024-08-15'}}.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        4270:('2009-08-31','SECUENCIA_AJUSTADA','2009-08-02','02-08-09 escrito después del 31-08: fecha técnica del antecedente y literal conservada.'),
        4271:('2009-08-31','SECUENCIA_AJUSTADA','2009-08-21','21-08-09 después del 31-08: consulta técnica del antecedente.'),
        4291:('2012-06-19','SECUENCIA_AJUSTADA','2012-05-09','09-05-12 después de la devolución fechada 19-06: consulta técnica del antecedente; no se cambia la cantidad de la devolución.'),
        **{id:('2012-08-21','SECUENCIA_AJUSTADA',fecha,'Fecha de julio/agosto escrita después del 21-08. Literal conservada y consulta técnica del antecedente.') for id,fecha in [(4298,'2012-07-24'),(4299,'2012-08-05'),(4300,'2012-08-14')]},
    }
    extras={
        4245:{'motivo':'La salida 116 es visible y consistente: 197 - 116 = 81. La cantidad elevada no se corrige por su magnitud.'},
        4256:{'motivo':'La foto dice salida 40 y saldo 49, no salida 10 y saldo 79. Así, 89 - 40 = 49.'},
        4257:{'motivo':'La devolución 38 está documentada. Con la salida anterior recuperada, 49 + 38 = 87: no se reduce el ingreso para compensar un error del OCR en otra fila.'},
        4274:{'criterios':['T23'],'motivo':'Biblioteca está en REF y Dirección en ÁREA; no se fusionan en un área compuesta.'},
        4278:{'criterios':['T23'],'motivo':'Biblioteca ocupa REF y Galería ocupa ÁREA; se recupera la separación de columnas.'},
        4307:{'criterios':['T18'],'motivo':'La comilla en DETALLE repite Taller Metodología de la misma columna anterior.'},
        4332:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'CEDOAL cruza REF/ÁREA: la atribución actual se conserva con revisión pendiente; no se certifica la columna como resuelta.'},
        4357:{'motivo':'La salida 1 desde 299 da 298; el papel escribe 295. La siguiente salida 2 escribe 296 y vuelve a la cadena: se conservan ambos errores locales del papel.'},
        4362:{'motivo':'La devolución 4 sobre 287 da 291; la foto escribe 271. El siguiente saldo 289 tras salida 2 recupera la cadena. Se conserva el 271 documental, sin inventar un ajuste.'},
    }
    for id in cambios:
        if cambios[id].get('area') in ('CEDOAL','CAP'):
            extras.setdefault(id,{})['motivo']=extras.get(id,{}).get('motivo','')+' Lectura de ÁREA recuperada desde la foto; no se crean áreas ni alias.'
    plan=construir(version=15,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(4280,4281),(4287,4288),(4303,4304),(4314,4315),(4323,4324,4325),(4355,4356)],
        bases={77:{'primera_fila':4242,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 199: base cero inferida, sin acreditar un conteo previo.'}},
        observaciones=[{'articulo_id':77,'observado':True,'excluir_entrenamiento':False,
            'motivo':'Seis fotografías y 143 filas cotejadas. Cierre 220 coincide con el papel. Salida 40 y saldo 49 mal extraídos explican la devolución 38, que se conserva. Los saldos documentales 295 y 271 y su recuperación posterior de la cadena quedan conservados. Fechas técnicas y atribución REF/ÁREA pendiente siguen identificadas.'}],extras=extras)
    assert plan['cotejo']['cierres']=={77:220}
    assert plan['cotejo']['discrepancias']==[{'id':4357,'local':-3,'acumulada':-3},{'id':4358,'local':3,'acumulada':0},{'id':4362,'local':-20,'acumulada':-20},{'id':4363,'local':20,'acumulada':0}]
    return plan


if __name__=='__main__':congelar(generar())
