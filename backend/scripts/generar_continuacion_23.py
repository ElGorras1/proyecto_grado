"""Trece fotos completas: El tren de la noche y La increíble tía Dorita."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(3503,3529),[30,-5,-1,30,-4,248,-110,-1,1,125,167,-20,16,-150,-3,-5,-4,-10,10,1,-1,-5,5,-5,-1,-2],
  [30,25,24,54,50,298,188,187,188,313,480,460,476,326,323,318,314,304,314,315,314,309,314,309,308,306]),
 (range(3529,3555),[-1,-4,-1,-1,-1,5,-1,-10,10,-1,-2,-1,1,1,-20,-10,-5,-5,-10,-1,12,-3,3,-5,-1,-3],
  [305,301,300,299,298,303,302,292,302,301,299,298,299,300,280,270,265,260,250,249,261,258,261,256,255,252]),
 (range(3555,3580),[5,-1,-10,-1,-5,9,-1,-1,1,-1,-1,-3,-5,-2,1,-6,5,-1,-1,-3,-1,-2,-4,-2,-1],
  [257,256,246,245,240,249,248,247,248,247,246,243,238,236,237,231,236,235,234,231,230,228,224,222,221]),
 (range(3580,3606),[-1,3,-5,5,-2,-3,-3,-1,-15,-1,-1,-3,-1,-1,-1,-2,-1,-2,-15,-2,-4,-1,2,-1,-1,-1],
  [220,223,218,223,221,218,215,214,199,198,197,194,193,192,191,189,188,186,171,169,165,164,166,165,164,163]),
 (range(3606,3632),[-1,-9,-2,-1,-1,-2,-5,200,-20,-100,-2,11,-5,-2,-1,-9,-2,-1,-2,-2,-1,-3,2,-2,-3,2],
  [162,153,151,150,149,147,142,342,322,222,220,231,226,224,223,214,212,211,209,207,206,203,205,203,200,202]),
 (range(3632,3637),[-2,-6,-2,2,-1],[200,194,192,194,193]),
 (range(3637,3663),[598,-10,-260,-2,-2,-5,4,-3,-8,-1,-3,-1,-1,-5,-20,5,-5,-5,-1,-4,-1,1,-5,-10,11,-7],
  [598,588,328,326,324,319,323,320,312,311,308,307,306,301,291,296,291,286,285,281,280,281,276,266,277,270]),
 (range(3663,3689),[-5,-5,5,-4,-1,-10,8,1,-1,-5,5,-5,-1,-2,-1,-4,-1,-1,-1,4,-1,-10,10,-1,-2,-1],
  [265,260,265,261,260,250,258,259,258,253,258,263,252,250,249,245,244,243,242,246,245,235,245,244,242,241]),
 (range(3689,3715),[1,1,-20,-10,-5,-5,-10,-1,-10,12,-3,3,-5,-1,-3,1,-1,-1,-10,-1,-1,4,-2,-1,1,-1],
  [242,243,223,213,208,203,193,192,182,194,191,194,189,188,185,186,185,184,174,173,172,176,174,173,174,173]),
 (range(3715,3740),[-1,-3,-5,-4,1,-6,-2,2,-5,-1,-2,-1,-2,-4,-2,-2,-1,-5,1,-5,5,-3,-2,-3,-3],
  [172,169,164,160,161,155,153,155,150,149,147,146,144,140,138,136,135,130,131,126,131,128,126,123,120]),
 (range(3740,3766),[-1,-1,-15,-2,-2,-3,-5,-2,-1,-1,1,-2,-4,-1,-1,-2,-1,-2,-2,-2,-2,-1,2,-1,-1,-2],
  [119,118,103,101,99,96,91,89,88,87,88,86,82,81,80,78,77,75,73,71,69,68,70,69,68,66]),
 (range(3766,3792),[-6,-2,-2,-2,-2,-5,500,-50,-364,-2,-5,6,-2,-5,-6,-5,-1,-2,-1,-2,-2,-2,-1,-3,2,-3],
  [60,58,56,54,52,47,547,497,133,131,126,132,130,125,119,114,113,111,110,108,106,104,103,100,102,99]),
 (range(3792,3805),[-4,-3,-3,-3,-2,-2,-10,-2,2,-3,-1,2,-3],[95,92,89,86,84,82,72,70,72,69,68,70,67]),
]


def generar():
    snapshot='backups/continuacion_hil_23_20261015/articulos_66_67_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    for id,r in rows.items():
        if r['articulo_id']==66 and r['area'] in ('CEDOC','CEDOSL','CDD0SL.','CDDOOL','C. SOCIAL','C. GDO.'):
            cambios[id]={'area':'CEDOAL'}
            extras[id]={'motivo':'El área se lee CEDOAL en esta foto; se corrige la transcripción sin crear áreas ni alias.'}
    for id,fields in {
        3538:{'detalle':'LETRAS PACEÑAS'},3541:{'detalle':'LETRAS PACEÑAS'},3548:{'fecha_movimiento':'2013-06-03'},3553:{'detalle':'PATIPIÑA'},
        3588:{'referencia':'CONSIG.'},3595:{'detalle':'BIBLIO - CASAS DIST.'},3596:{'detalle':'VENTAS - PERSONAL ESIP'},
        3611:{'referencia':'OBSQ.'},3617:{'area':None},3628:{'area':None},3631:{'area':None},
        3648:{'detalle':'ISTVAN SCHRITTER'},3662:{'fecha_movimiento':'2012-07-19'},
        3680:{'detalle':'ALCIRA SEIFERT'},3684:{'detalle':'VENTA PROF. AYATA'},3685:{'detalle':'DEV. PROF. AYATA'},
        3686:{'detalle':'LETRAS PACEÑAS'},3729:{'detalle':'LARGA NOCHE MUSEOS'},3739:{'fecha_movimiento':'2016-01-01'},
        3742:{'referencia':'CONSIG.'},3755:{'detalle':'BIBLIO - CASAS DIST.'},3763:{'detalle':'MI TELEFERICO','area':'CAP'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        **{id:('2012-08-08','SECUENCIA_AJUSTADA','2012-07-30','30-07-12 aparece después del ingreso 08-08-12. Se conserva la fecha escrita y una consulta técnica del antecedente.') for id in (3504,3505)},
        3514:('2012-08-29','SECUENCIA_AJUSTADA','2012-08-08','08-08-12 después del ingreso 29-08-12. Consulta técnica sin mover la fila física ni alterar la fecha documental.'),
        3515:('2012-08-29','SECUENCIA_AJUSTADA','2012-08-14','14-08-12 está después del ingreso 29-08-12; consulta técnica del antecedente.'),
        **{id:('2013-06-03','SECUENCIA_AJUSTADA',literal,'Fecha de mayo escrita después de la actividad 03-06-13. Se conserva la literal, sin copiar el 03-05 de otro artículo parecido.') for id,literal in [(3549,'2013-05-07'),(3550,'2013-05-07'),(3551,'2013-05-14'),(3552,'2013-05-27')]},
        3568:('2014-07-29','HIPOTESIS',None,'El mes está repasado y no puede certificarse. Lectura parcial 29-?-14; julio se usa solo como hipótesis de consulta antes de la devolución 11-08-14.'),
        3615:('2019-11-20','HIPOTESIS',None,'Fecha repasada: se distingue noviembre de 2019, pero el día 20/30 no es inequívoco. El 20-11 es solo consulta hipotética, no el 30-12 atribuido por la extracción.'),
        3616:('2019-12-30','HIPOTESIS',None,'Fecha fuertemente repasada; se conserva lectura parcial de diciembre sin certificar día/año. 30-12-2019 sigue solo como consulta hipotética.'),
        3620:('2021-10-05','HIPOTESIS',None,'OBSQ. U.E. Guillermo Monje no tiene fecha escrita; se usa el antecedente únicamente para consulta, sin copiar la fecha de ABC Deletreo de la fila siguiente.'),
        3628:('2022-10-17','HIPOTESIS',None,'Devolución sin fecha escrita: consulta técnica del antecedente. El 2 corresponde a INGRESOS, no a un área.'),
        **{id:('2012-08-21','SECUENCIA_AJUSTADA',literal,'Fecha de julio/agosto escrita después del 21-08. Consulta técnica del antecedente y literal conservada sin alterar el orden de la hoja.') for id,literal in [(3659,'2012-07-24'),(3660,'2012-08-05'),(3661,'2012-08-14'),(3662,'2012-07-19')]},
        3729:('2015-06-19','SECUENCIA_AJUSTADA','2015-05-15','15-05-15 después del 19-06-15. Consulta técnica del antecedente sin inventar julio para la fecha literal.'),
        3759:('2017-05-30','HIPOTESIS',None,'FIL tiene FECHA en blanco; el 30-05 procede del antecedente solo para consulta.'),
        3790:('2022-10-17','HIPOTESIS',None,'La devolución no tiene FECHA escrita. Se conserva ausencia y consulta técnica del antecedente.'),
    }
    extras.update({
        3507:{'motivo':'Salida 4 y saldo 50 legibles aunque un papel blanco cubre parte del borde derecho. No se completa ninguna cifra oculta por comparación con otro artículo.'},
        3542:{'revision':{'marcas_documentales':{'saldo':'300 repasado; lectura final conservada.'}}},
        3548:{'motivo':'La foto escribe 03-06-13, distinto del 03-05-13 que aparece en Tía Dorita. No se cambia por similitud; las fechas de mayo siguientes se marcan técnicas.'},
        **{id:{'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'CEDOAL cruza REF/ÁREA; se mantiene la atribución actual del área como pendiente, sin certificar su columna por semejanza.'} for id in (3561,3711)},
        3566:{'criterios':['T14'],'revision':{'marcas_documentales':{'detalle':'Palabra anterior tachada antes de PIPIRIPI.'}},'motivo':'La tachadura afecta texto del detalle; salida 3 y saldo 243 permanecen legibles. No se anula la operación.'},
        3587:{'criterios':['T01'],'motivo':'La foto muestra salida 1, no 4: desde 215 deja 214. Se corrige la cantidad por lectura visual y se comprueban las filas siguientes.'},
        3617:{'criterios':['T23'],'motivo':'CSIP escribe ingreso 11, desplazado por OCR al área; 220 + 11 = 231. Se recupera la columna y se deja ÁREA vacía, sin inventar institución.'},
        3631:{'criterios':['T23'],'motivo':'El 2 se encuentra en INGRESOS y ÁREA está vacía. Se conserva una sola devolución de 2, sin área numérica.'},
        3648:{'criterios':['T14'],'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True},'motivo':'El nombre es Istvan Schritter, pero ÁREA está sobrescrita CAP/GALERÍA. Se conserva su atribución sin certificarla y se mantiene pendiente.',
            'revision':{'lectura_area_parcial':'CAP/GALERÍA sobrescrito; columna y destino no concluyentes.'}},
        3651:{'criterios':['T05'],'motivo':'Instituciones Potosí tiene salida 20 legible y saldo escrito 291 desde 301. El cálculo independiente es 281. No se reduce la salida a 10 para hacer coincidir el saldo; la diferencia de diez persiste hasta el cierre.'},
        3654:{'criterios':['T14'],'motivo':'Jurado Libro Álbum escribe salida 5 y una marca tachada en INGRESOS. Se conserva un solo egreso, no una entrada adicional.',
            'revision':{'marcas_documentales':{'ingresos':'Marca tachada sin cantidad adicional legible.'}}},
        3674:{'criterios':['T05'],'motivo':'Repositorio NAL escribe salida 5 desde 258 y saldo 263, en lugar de 253. La salida 1 siguiente escribe 252 y recupera ese error local; se conservan los dos saldos documentales sin invertir la salida a ingreso.'},
        3675:{'motivo':'Saldo 252 escrito después de 263 con salida 1. Compensa diez unidades del error local anterior, pero no elimina la diferencia de diez originada por Instituciones Potosí.'},
        3701:{'revision':{'marcas_documentales':{'saldo':'189 repasado, lectura final conservada.'}}},
        3731:{'criterios':['T11'],'motivo':'22-07-15 está escrito después del 23-07-15. Se ordenan esas dos fechas solo para consulta y se conserva la literal de cada operación.'},
        3803:{'revision':{'marcas_documentales':{'saldo':'Cifra anterior tachada y lectura final 70.'}}},
    })
    plan=construir(version=23,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(3521,3522,3523),(3537,3538,3539,3540,3541),(3644,3645,3646,3647),(3665,3666,3667),(3669,3670,3671),(3685,3686,3687,3688,3689),(3730,3731)],
        bases={66:{'primera_fila':3503,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso 30 con saldo 30: base cero inferida, sin acreditar recuento previo.'},
            67:{'primera_fila':3637,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso 598 y saldo 598: base cero inferida, sin inventar ingreso adicional ni recuento.'}},
        observaciones=[
            {'articulo_id':66,'observado':True,'excluir_entrenamiento':False,'motivo':'Seis fotos y 134 filas cotejadas completas. Salida 1 de U.E. Taiwan e ingreso 11 de CSIP recuperados de la foto; áreas numéricas eliminadas de las devoluciones, fechas ausentes/repasadas e inversiones temporales conservadas como técnicas. Cierre 193 coincide sin ajustes; la atribución CEDOAL entre columnas sigue pendiente en una fila.'},
            {'articulo_id':67,'observado':True,'excluir_entrenamiento':True,'motivo':'Siete fotos y 168 filas cotejadas, incluidas ambas cargas. Salida 20 legible desde 301 tiene saldo escrito 291 en vez de 281 y deja diferencia persistente de diez. Otro error local 263/252 se compensa, sin eliminar el anterior. Se conserva cierre escrito 67 frente a acumulado condicional 57, aviso final y apertura bloqueada. Artículo excluido del entrenamiento hasta conciliación, con fechas técnicas y área sobrescrita pendientes.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={66:193,67:57},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':3651,'local':10,'acumulada':10},{'id':3674,'local':10,'acumulada':20},{'id':3675,'local':-10,'acumulada':10}],plan['cotejo']
    for e in plan['revisiones']:
        if e['articulo_id']==67 and e['id']>=3651:
            e['revision']['origen_saldo']='HIPOTESIS'
            e['revision']['motivo']+=' El acumulado de consulta sigue condicionado por la diferencia de diez del papel, sin certificar existencias físicas.'
        if e['id']==3804:
            e['cambios']['saldo_registrado']=67
            e['revision'].update(origen_saldo='FOTO',usar_saldo_esperado=False)
            e['revision']['motivo']+=' Se conserva el cierre escrito 67 con aviso frente a cálculo 57 y bloqueo de apertura automática.'
    plan['cotejo'].update(cierres={66:193,67:67},cierres_calculados={66:193,67:57},pendientes_documentales={'3804':['saldo']},
        limites_cierre={67:'Salida 20 desde 301 con saldo escrito 291: diferencia persistente de diez. Cierre 67 frente a acumulado condicional 57; pendiente de conciliación, no operable.'})
    return plan


if __name__=='__main__':congelar(generar())
