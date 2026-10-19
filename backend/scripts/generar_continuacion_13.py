"""Agustina y ellos: siete fotografías completas cotejadas."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(3106,3132),[110,-3,300,-1,-1,-5,-1,-10,-2,185,-60,-200,5,-5,-6,-5,-1,-4,-1,1,-5,-10,9,-5,-5,5],
  [110,107,407,406,405,400,399,389,387,572,512,312,317,312,306,301,300,296,295,296,291,281,290,285,280,285]),
 (range(3132,3158),[-4,-1,-10,9,-1,-5,5,-5,-2,-1,-5,-1,-1,4,-2,-10,10,-1,-2,-1,1,1,-20,-10,-5,-5],
  [281,280,270,279,278,273,278,273,271,270,265,264,263,267,265,255,265,264,262,261,262,263,243,233,228,223]),
 (range(3158,3184),[-10,-1,-10,20,-3,2,-5,-1,-3,-1,-1,-10,-1,7,-1,-1,1,-1,-1,-3,-5,-1,-4,-6,-1,3],
  [213,212,202,222,219,221,216,215,212,211,210,200,199,206,205,204,205,204,203,200,195,194,190,184,183,186]),
 (range(3184,3209),[-1,-1,-1,-3,-1,-2,-4,-2,-2,-1,-5,2,-5,4,-3,-2,-3,-3,-1,-1,-15,-5,-1,-1,1],
  [185,184,183,180,179,177,173,171,169,168,163,165,160,164,161,159,156,153,152,151,136,131,130,129,130]),
 (range(3209,3235),[-2,-3,-1,-1,-1,-2,-1,-2,-10,-1,-2,-4,-2,-2,-1,1,-1,-1,-2,-2,-1,-2,-1,-5,-2,-5],
  [128,125,124,123,122,120,119,117,107,106,104,100,98,96,95,96,95,94,92,90,89,87,86,81,79,74]),
 (range(3235,3261),[500,-50,-364,-10,8,-2,-5,-6,-4,-5,-2,-1,-2,-1,-2,-1,-3,1,-2,-1,-1,-3,-3,-1,-2,-2],
  [574,524,160,150,158,156,151,145,141,136,134,133,131,130,128,127,124,125,123,122,121,118,115,114,112,110]),
 (range(3261,3267),[-2,2,-3,-1,2,-2],[108,110,107,106,108,106]),
]


def generar():
    snapshot='backups/continuacion_hil_13_20261015/articulo_63_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={}
    for id,r in rows.items():
        if r['area'] in ('CEDDAL','CEDDAL.','CEDOCAL','CEDOC','CEDRAL','CHACAL'):cambios[id]={'area':'CEDOAL'}
        if r['area'] in ('COP','PAP','ZAP','CDP'):cambios[id]={'area':'CAP'}
    for id,fields in {
        3107:{'detalle':'Ventas CEDOAL'},3126:{'fecha_movimiento':'2012-07-24'},3127:{'fecha_movimiento':'2012-08-05'},
        3148:{'fecha_movimiento':'2013-03-04'},3152:{'fecha_movimiento':'2013-03-05'},3190:{'fecha_movimiento':'2015-06-19'},
        3191:{'detalle':'Larga Noche de Museos'},3194:{'referencia':None,'area':'Lucy'},3196:{'referencia':None,'area':'CAP'},
        3197:{'referencia':None,'area':'CAP'},3198:{'referencia':'OBSQ','area':'CAP'},3208:{'area':None},
        3215:{'detalle':'Venta personal ESIP'},3245:{'detalle':'Consig. Villa Albina'},3252:{'area':None},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        3126:('2012-08-21','SECUENCIA_AJUSTADA','2012-07-24','24-07-12 escrito después del 21-08: fecha técnica del antecedente; no se confirma otro mes real.'),
        3127:('2012-08-21','SECUENCIA_AJUSTADA','2012-08-05','05-08-12 después del 21-08. El OCR había convertido 5 de agosto en 5 de septiembre; literal conservada y consulta técnica del antecedente.'),
        3128:('2012-08-21','SECUENCIA_AJUSTADA','2012-08-14','14-08-12 después del 21-08: consulta técnica del antecedente.'),
        3163:('2013-05-07','SECUENCIA_AJUSTADA','2013-06-14','La devolución escribe 14-06-13 entre mayo 7 y 27. Se conserva junio; fecha técnica del antecedente sin afirmar que el papel decía mayo.'),
        3222:('2017-07-06','HIPOTESIS',None,'FIL tiene fecha en blanco; consulta con el antecedente y ausencia documental conservada.'),
        3245:('2022-02-10','SECUENCIA_AJUSTADA','2021-02-10','El papel escribe 10-02-21 después de noviembre de 2021 y antes de mayo de 2022. Año de consulta 2022 por contexto, sin certificar el año real.'),
        3252:('2022-10-17','HIPOTESIS',None,'Devolución con fecha en blanco; consulta con la del antecedente, sin atribuir un día confirmado.'),
    }
    extras={}
    for id,r in rows.items():
        if r['referencia']=='.':extras[id]={'clasificacion':{'referencia_estado':'INCIERTA','requiere_auditoria_referencia':True},'motivo':'Un punto aislado en REF se conserva como marca incierta: no acredita un documento ni una repetición inequívoca.'}
        if id in cambios and 'area' in cambios[id] and cambios[id]['area'] in ('CEDOAL','CAP'):
            extras.setdefault(id,{})['motivo']=extras.get(id,{}).get('motivo','')+' Se recupera la lectura de ÁREA desde la foto, sin crear áreas o alias.'
    for id,fields in {
        3194:{'criterios':['T23'],'motivo':'Lucy está en ÁREA, no en REF; se conserva el nombre literal sin convertirlo en un área institucional nueva.'},
        3196:{'criterios':['T23'],'motivo':'CAP está en ÁREA; REF no contiene COP.'},
        3197:{'criterios':['T23'],'motivo':'La devolución tiene ingreso 4 visible y ÁREA CAP; no hay un área llamada 4. Se recupera el ingreso omitido en su columna.'},
        3198:{'criterios':['T23'],'motivo':'Jurados libro álbum tiene REF OBSQ y ÁREA CAP; se recuperan sus columnas.'},
        3208:{'criterios':['T14','T23'],'motivo':'La última lectura visible de INGRESOS es 1 después del tachón de otra cifra. No se anula el movimiento ni se considera el 1 como área.'},
        3237:{'motivo':'La foto acredita salida 364 y continuidad 524→160. La cantidad elevada se conserva; no basta su magnitud para considerarla un error.'},
        3252:{'criterios':['T23'],'motivo':'El 1 está en INGRESOS y ÁREA está en blanco; no se usa una cifra como nombre de área.'},
    }.items():
        anterior=extras.setdefault(id,{});anterior['motivo']=anterior.get('motivo','')+' '+fields.pop('motivo','');anterior.update(fields)
    for id in (3145,3153):
        extras.setdefault(id,{})['clasificacion']={**extras.get(id,{}).get('clasificacion',{}),'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True}
        extras[id]['motivo']=extras[id].get('motivo','')+' El punto aislado en ÁREA no se expande a un área por semejanza ni se certifica como repetición.'
    plan=construir(version=13,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(3131,3132,3133),(3135,3136),(3148,3149,3150),(3151,3152),(3189,3190,3191)],
        bases={63:{'primera_fila':3106,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso 110 y saldo 110: base cero inferida; no acredita un conteo previo.'}},
        observaciones=[{'articulo_id':63,'observado':True,'excluir_entrenamiento':False,
            'motivo':'Siete fotos y 161 filas cotejadas. Cierre 106 coincide con el papel. Se recupera ingreso 4 y se corrigen columnas REF/ÁREA, áreas mal leídas y fechas OCR. Puntos ambiguos y fechas técnicas conservan sus dudas. Salida 364 acreditada por la foto, sin corregir cantidades por su magnitud.'}],extras=extras)
    assert plan['cotejo']['cierres']=={63:106} and plan['cotejo']['discrepancias']==[]
    return plan


if __name__=='__main__':congelar(generar())
