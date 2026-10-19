"""Matilde Casazola, Cuerpoemas: cuatro fotografías completas cotejadas."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(5436,5462),[50,-35,-15,39,-26,360,-5,7,-1,-2,-10,-1,-3,1,-5,-1,-12,-1,-225,-1,1,1,-1,-1,-1,-2],
  [50,15,None,39,13,373,368,375,374,372,362,361,358,359,354,353,341,340,115,114,115,116,115,114,113,111]),
 (range(5462,5488),[2,-10,2,-3,-3,1,-5,-2,-1,-10,-10,-3,-5,7,-2,-3,-10,-3,-5,-10,10,-5,-1,1,-2,-2],
  [113,103,105,102,99,100,95,93,92,82,72,69,64,71,69,66,56,53,48,38,48,43,42,43,41,39]),
 (range(5488,5514),[1,3,-1,-2,2,-2,-1,-1,1,-1,-1,1,-10,-5,9,-3,2,-5,-1,-2,-1,5,-1,-1,-10,-3],
  [40,43,42,40,42,40,39,38,39,38,37,38,28,23,32,29,31,26,25,23,22,27,26,25,15,12]),
 (range(5514,5528),[-1,7,-2,-3,-5,-5,-2,5,-2,-2,2,-2,-2,2],[11,18,16,13,8,3,1,6,4,2,4,2,0,2]),
]


def generar():
    snapshot='backups/continuacion_hil_18_20261015/articulo_86_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    for id,r in rows.items():
        if r['area'] in ('CDOAL.','CEDOCAL'):
            cambios[id]={'area':'CEDOAL'}
            extras[id]={'motivo':'La lectura de ÁREA es CEDOAL en la foto; no se crean áreas o equivalencias nuevas.'}
    for id,fields in {5451:{'fecha_movimiento':'2010-12-27'},5455:{'fecha_movimiento':'2011-04-28'},
        5497:{'detalle':'LETRAS PACEÑAS'},5503:{'detalle':'LARGA NOCHE MUSEOS'},5504:{'detalle':'LARGA NOCHE MUSEOS'},
        5510:{'detalle':'INAUG. YOLANDA'},5514:{'detalle':'CLAUSURA METODOLOGIA','area':'CAP'}}.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        5438:('2010-08-26','SECUENCIA_AJUSTADA','2010-08-25','25-08-10 está escrito después del ingreso y salida del 26-08. Se conserva la literal y consulta técnica del antecedente.'),
        5443:('2010-10-20','SECUENCIA_AJUSTADA','2010-09-03','Devolución con fecha 03-09-10 después del 20-10-10. Consulta técnica del antecedente y literal conservada, sin cambiar la cantidad 7.'),
        5447:('2010-11-22','SECUENCIA_AJUSTADA','2010-11-10','10-11-10 aparece después del 22-11-10; consulta técnica del antecedente sin afirmar un nuevo día real.'),
        5480:('2012-08-08','SECUENCIA_AJUSTADA','2012-07-24','24-07-12 aparece después del 08-08-12. Literal conservada y consulta técnica del antecedente.'),
        5481:('2012-08-08','SECUENCIA_AJUSTADA','2012-08-05','05-08-12 queda antes del antecedente 08-08. Se conserva la literal y se marca la fecha de consulta.'),
        5486:('2012-10-02','SECUENCIA_AJUSTADA','2012-09-26','26-09-12 está repasado y aparece después de 02-10. No se altera el año ni se anula la fila; consulta técnica del antecedente.'),
        5489:('2012-10-08','HIPOTESIS',None,'Día 4/7 repasado, antes del antecedente 08-10-12. Se conserva la lectura parcial y una consulta técnica; no se certifica día 10.'),
        5490:('2012-10-08','SECUENCIA_AJUSTADA','2012-10-05','La foto escribe 5-10-12, no 15. Se conserva la literal y fecha técnica del antecedente 08-10-12.'),
        5524:('2015-05-15','HIPOTESIS',None,'Devolución con FECHA en blanco; consulta técnica del antecedente, sin certificar día propio.'),
        5527:('2022-09-07','HIPOTESIS',None,'Última devolución sin fecha: se conserva la ausencia y fecha técnica del antecedente, no una fecha confirmada.'),
    }
    extras.update({
        5438:{'revision':{'lectura_saldo_parcial':'Guion en SALDO; no hay un cero numérico escrito.','motivo':'Hoja completa cotejada. Salida 15 desde 15: saldo de consulta 0, mientras el documento deja un guion. Se conserva esa distinción y la fecha técnica.'}},
        5440:{'motivo':'Entrega autora tiene salida 26 visible; 39 - 26 = 13. Se conserva la cantidad.'},
        5454:{'motivo':'La salida 225 está escrita y explica 340 - 225 = 115. Se conserva, sin reducirla por su magnitud.'},
        5457:{'revision':{'lectura_referencia_parcial':'Trazo vertical aislado en REF; no se expande como DEV. inequívoco.'}},
        5462:{'criterios':['T16'],'motivo':'El detalle manuscrito no permite confirmar el nombre completo. Se conserva la extracción y lectura parcial, sin asociarlo a una persona o institución por semejanza.',
            'revision':{'lectura_detalle_parcial':'Ll...gua'}},
        5478:{'motivo':'El acercamiento confirma saldo 56 después de 66 - 10. Se conserva la última cifra visible, sin introducir un supuesto saldo 66 por semejanza del trazo.'},
        5486:{'criterios':['T14'],'revision':{'anotacion_documental':'Mes repasado en la fecha, sin anular el movimiento.'}},
        5489:{'revision':{'lectura_fecha_parcial':'4/7-10-12, día repasado.'}},
        5490:{'criterios':['T14'],'motivo':'Sr. Puiggros tiene 1 tachado en INGRESOS y salida 1 legible: 43 - 1 = 42. No se cuenta otra entrada ni se anula toda la fila.',
            'revision':{'marcas_documentales':{'ingresos':'1 tachado'}}},
        5516:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'CEDOAL cruza REF/ÁREA; se conserva la atribución en REF y la incertidumbre de columna, sin certificar un área ausente o resuelta.'},
        5524:{'criterios':['T14'],'motivo':'La devolución tiene ingreso 2 y una marca tachada en SALIDAS. Se conserva 2 + 2 = 4, sin segundo descuento ni anular la fila.',
            'revision':{'marcas_documentales':{'salidas':'Marca redondeada tachada, no una segunda cantidad confirmada'}}},
    })
    plan=construir(version=21,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(5439,5440),(5462,5463)],
        bases={86:{'primera_fila':5436,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 50: base cero inferida, sin acreditar recuento previo.'}},
        observaciones=[{'articulo_id':86,'observado':True,'excluir_entrenamiento':False,
            'motivo':'Cuatro fotografías y 92 filas cotejadas. Las cantidades se conservan y el cierre reconstruido 2 coincide con el papel. Se distinguen saldo cero calculado y guion escrito, fechas documentales y técnicas, cifras tachadas sin doble efecto, nombres parciales y atribución REF/ÁREA pendiente. No se crean operaciones compensatorias ni áreas.'}],extras=extras)
    assert plan['cotejo']['cierres']=={86:2} and plan['cotejo']['discrepancias']==[]
    return plan


if __name__=='__main__':congelar(generar())
