"""Blanca Wiethuchter: siete fotografías completas cotejadas."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(4385,4411),[482,-1,-8,-1,-5,-1,-50,-5,-15,21,-1,-1,-1,-1,-18,-3,2,-5,-10,-15,-1,-4,-1,-8,-5,-1],
  [482,481,473,472,467,466,416,411,396,417,416,415,414,413,395,392,394,389,379,364,363,359,358,350,345,344]),
 (range(4411,4437),[-1,4,-3,-1,-10,-2,-110,-10,-1,-5,8,1,-5,-5,-1,1,-5,-1,-3,-1,-1,1,-1,100,100,300],
  [343,347,344,343,333,331,221,211,210,205,213,214,209,204,203,204,199,198,195,194,193,194,193,293,393,693]),
 (range(4437,4463),[-1,-2,2,-10,7,-3,1,-2,1,-1,-10,-10,-3,-75,-5,8,-2,-3,-3,-1,-30,-5,-10,13,-5,-1],
  [692,690,692,682,689,686,697,685,686,685,675,665,662,587,582,590,588,585,582,581,551,546,536,549,544,543]),
 (range(4463,4489),[1,-1,-2,5,-2,2,-2,-1,-1,1,5,-1,-1,1,1,-10,-5,13,-3,-5,8,-5,-1,-2,-1,5],
  [544,543,541,546,544,546,544,543,542,543,548,547,546,547,548,538,533,546,543,538,546,541,540,538,537,542]),
 (range(4489,4514),[-1,-1,-10,-1,-1,6,-2,-3,-5,-5,-2,-3,-1,5,-1,-1,-3,-2,-1,-6,2,-3,-2,-5,-1],
  [541,540,530,529,528,534,532,529,524,519,517,514,513,518,517,516,513,511,510,504,506,503,501,496,495]),
 (range(4514,4540),[-1,4,-3,-1,-3,-1,-2,-2,-3,-1,-1,1,-2,-2,-10,-2,-2,-5,-5,11,-5,3,-5,-2,-2,-3],
  [494,498,495,494,491,490,488,486,483,482,481,482,480,478,468,466,464,459,454,465,460,463,458,456,454,451]),
 (range(4540,4564),[-2,-2,-1,-1,-1,2,-2,-9,-3,-3,-4,-2,-1,-2,-2,-1,-4,-20,-5,2,-5,5,-10,-5],
  [449,447,446,445,444,446,444,435,432,429,425,423,422,420,418,417,413,393,388,390,385,390,380,375]),
]


def generar():
    snapshot='backups/continuacion_hil_13_20261015/articulo_78_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={}
    for id,r in rows.items():
        if r['area'] in ('CEDDAL','CEDEAL','CEDOCAL'):cambios[id]={'area':'CEDOAL'}
        if r['area']=='CUSP':cambios[id]={'area':'CAP'}
    for id,fields in {4407:{'detalle':'C/Carta Marien Garten','referencia':'Biblio'},4408:{'detalle':'C/Carta Comp. Lectura','referencia':'SCZ'},
        4415:{'detalle':'Semin. taller album'},4453:{'fecha_movimiento':'2012-06-26'},4562:{'fecha_movimiento':'2025-08-12'}}.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        4397:('2009-08-31','SECUENCIA_AJUSTADA','2009-08-21','21-08-09 después del 31-08: consulta técnica del antecedente, sin certificar otra fecha real.'),
        4417:('2010-08-11','HIPOTESIS',None,'Día repasado de lectura 11/19 no inequívoca: se conserva el 11 técnico de la lectura anterior, sin afirmar un día confirmado.'),
        4451:('2012-05-22','SECUENCIA_AJUSTADA','2012-05-09','09-05-12 después del 22-05; consulta técnica del antecedente y literal conservada.'),
        4452:('2012-05-22','SECUENCIA_AJUSTADA','2012-05-19','19-05-12 después del 22-05; consulta técnica del antecedente.'),
        **{id:('2012-08-21','SECUENCIA_AJUSTADA',fecha,'Fecha de julio/agosto escrita después del 21-08. Se conserva el literal; consulta técnica con el antecedente.') for id,fecha in [(4458,'2012-07-24'),(4459,'2012-08-05'),(4460,'2012-08-14')]},
        4480:('2013-05-07','HIPOTESIS',None,'Mes manuscrito de lectura 5/6 en la devolución; contexto de mayo entre abril 30 y los movimientos de mayo 7. Consulta técnica de mayo, sin certificar el mes leído.'),
        4500:('2014-07-29','HIPOTESIS',None,'Obsequio FIL tiene fecha en blanco; consulta con el antecedente y ausencia documental conservada.'),
        4522:('2017-05-20','HIPOTESIS',None,'FIL tiene fecha en blanco; la fecha técnica del antecedente no confirma el día real.'),
        4533:('2019-10-03','HIPOTESIS',None,'Ingreso 11 tiene fecha en blanco; consulta con el antecedente, sin fecha original acreditada.'),
        4545:('2022-10-17','HIPOTESIS',None,'Devolución con fecha en blanco; consulta técnica del antecedente, sin confirmar el día.'),
    }
    extras={
        4407:{'criterios':['T23'],'motivo':'Biblio está en REF; se conserva Dirección en ÁREA.'},
        4408:{'criterios':['T23'],'motivo':'SCZ está en REF, no forma parte del nombre del área.'},
        4417:{'criterios':['T02'],'motivo':'La foto acredita SALIDA 110 y saldo 221 sobre 331. El nombre Reposición no convierte la cifra en un ingreso.','revision':{'lectura_fecha_parcial':'11/19-08-10 repasado'}},
        4421:{'criterios':['T14'],'motivo':'La devolución tiene ingreso 8. La cifra de SALIDAS está tachada: se conserva la marca documental y se excluye su efecto; el movimiento no está anulado.','revision':{'marcas_documentales':{'salidas':'8 tachado'}}},
        4443:{'motivo':'La foto escribe 697 sobre 686 con ingreso 1: el esperado es 687. La siguiente salida 2 vuelve a 685; ambos saltos de decena del papel quedan documentados.'},
        4480:{'revision':{'lectura_fecha_parcial':'7-5/6-13'}},
        4495:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'CEDOAL cruza REF/ÁREA: se corrige su lectura literal en la atribución actual, pero la columna queda pendiente; no se certifica un área resuelta.'},
        4547:{'revision':{'anotacion_documental':'Saldo 435 repasado; las cantidades 444 - 9 = 435 y la salida posterior 3 = 432 respaldan la lectura final.'}},
    }
    for id in cambios:
        if cambios[id].get('area') in ('CEDOAL','CAP'):
            extras.setdefault(id,{})['motivo']=extras.get(id,{}).get('motivo','')+' ÁREA recuperada por lectura de la foto; no se crean áreas ni alias.'
    plan=construir(version=14,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(4424,4425),(4433,4434),(4439,4440),(4463,4464),(4475,4476),(4506,4507),(4523,4524),(4534,4535,4536)],
        bases={78:{'primera_fila':4385,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 482: base previa cero inferida, sin acreditar recuento anterior.'}},
        observaciones=[{'articulo_id':78,'observado':True,'excluir_entrenamiento':False,
            'motivo':'Siete fotografías y 179 filas cotejadas. Cierre 375 coincide con el papel. Reposición es salida 110, no ingreso; la devolución 8 tiene SALIDA tachada sin efecto. Errores locales 697/687 y su corrección posterior conservados. Fechas ausentes o de lectura dudosa, y una atribución REF/ÁREA, conservan incertidumbre.'}],extras=extras)
    assert plan['cotejo']['cierres']=={78:375}
    assert plan['cotejo']['discrepancias']==[{'id':4443,'local':10,'acumulada':10},{'id':4444,'local':-10,'acumulada':0}]
    return plan


if __name__=='__main__':congelar(generar())
