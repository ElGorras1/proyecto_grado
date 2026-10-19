"""Nueve fotos completas: Caer en el cielo, Cerruto tapa blanda y Algas."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(3440,3466),[105,135,110,-35,-2,-2,-2,-1,-1,-1,-1,-1,-1,-6,-2,-6,-4,-2,-2,-2,-1,-2,-9,-2,-1,-6],
  [105,240,350,315,313,311,309,308,307,306,305,304,303,297,295,289,285,283,281,279,278,276,267,265,264,258]),
 (range(3466,3492),[-2,-2,-5,500,-50,-364,-26,4,-3,-5,-6,-3,-5,-1,-1,-2,-1,-2,-1,-2,-2,-1,2,-1,-3,-5],
  [256,254,249,749,699,335,309,313,310,305,299,296,291,290,289,287,286,284,283,281,279,278,280,279,276,271]),
 (range(3492,3503),[-3,-3,-2,-2,-10,-1,-4,2,-2,-1,2],[268,265,263,261,251,250,246,248,246,245,247]),
 (range(5936,5962),[0,-1,-1,-2,-1,-20,-17,-3,-34,-12,-1,-3,-2,-1,-1,-4,-5,2,-30,-1,-1,-2,-1,-2,-1,-3],
  [223,None,None,219,218,198,181,178,144,132,131,128,126,125,124,120,115,117,87,86,85,83,82,80,79,76]),
 (range(5962,5988),[-5,-1,-1,-1,-10,1,-1,-3,-3,-2,3,1,-1,-1,1,-1,-1,-1,-24,-1,-10,-4,3,-1,3,-1],
  [71,70,None,None,58,59,58,55,52,50,53,54,53,52,53,52,51,50,26,25,15,11,14,13,16,15]),
 (range(5988,5992),[1,-13,1,-1],[16,3,4,3]),
 (range(9448,9474),[19,-5,-5,-3,5,-1,-2,2,-2,12,-5,-1,1,-2,0,-3,-5,40,-7,10,-2,-3,1,-1,-5,2],
  [19,None,None,6,11,None,8,10,8,20,15,14,15,13,12,9,4,44,37,47,45,42,43,42,37,39]),
 (range(9474,9499),[1,-1,1,-1,1,-6,5,-1,-5,-2,7,2,-3,2,-3,-2,-1,-3,-3,-10,-1,-1,-3,2,-1],
  [40,39,40,39,40,34,39,38,33,31,38,40,37,39,36,34,33,30,27,17,16,15,12,14,13]),
 (range(9499,9504),[-2,-2,-1,-3,-2],[11,9,8,5,3]),
]

def generar():
    snapshot='backups/continuacion_hil_42_20261015/articulos_89_233_65_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','Cedoc','CEDAL')}
    cambios.update({**{id:{'area':'CAP'} for id in (3440,3441,3442,3444)},3473:{'area':None},3478:{'detalle':'FIL - CBBA'},3490:{'detalle':'VENTAS - ESIP'},
        5944:{'area':'CEDOAL'},5952:{'area':'CEDOAL'},5955:{'area':'CEDOAL'},5956:{'area':'CEDOAL'},5964:{'detalle':'Para la Venta','area':'CEDOAL'},
        5965:{'detalle':'Donación Caranavi','area':'CEDOAL'},9456:{'fecha_movimiento':'2007-02-06','area':'CEDOAL'},9459:{'detalle':'Donación Emb.','referencia':'Británica','area':None},
        9462:{'ingresos':1,'salidas':1,'area':'CEDOAL'},9477:{'detalle':'LLALLAGUA'},9478:{'detalle':'LLALLAGUA'},9496:{'detalle':'FIL - 2019'}})
    codigos={5940:'094/07',5941:'103/07',5946:'118/07',5948:'131/07',5949:'132-07',5951:'152/07',5958:'013-08',5959:'016-08',5960:'019-08'}
    for id,codigo in codigos.items():cambios.setdefault(id,{}).update(area=codigo,referencia='ESIP' if id not in (5948,5949,5951) else None)
    tecnicas={
        3488:('2022-10-17','HIPOTESIS',None,'Devolución sin fecha propia. Consulta técnica del antecedente, sin copiar una fecha documental inexistente.'),
        3490:('2023-06-16','SECUENCIA_AJUSTADA','2023-01-28','28-1-23 aparece después de 16-6-23. Se conserva literal y consulta técnica del antecedente.'),
        5936:('2007-08-01','HIPOTESIS',None,'Base documental 223 sin fecha escrita. Consulta técnica de 1-08-07 siguiente; no se inventa recepción.'),
        5938:('2007-08-01','HIPOTESIS',None,'Donación Ramos sin fecha propia; consulta técnica del antecedente.'),
        5952:('2007-12-06','SECUENCIA_AJUSTADA','2007-10-16','16-10-07 está después del 6-12-07. Se conserva literal y consulta técnica del antecedente.'),
        5953:('2007-12-06','HIPOTESIS',None,'Devolución no tiene fecha en su celda; nota lateral 14-12-07 conservada sin asignación automática. Consulta técnica del antecedente.'),
        5955:('2008-03-06','SECUENCIA_AJUSTADA','2008-01-15','15-01-08 después de 6-3-08. Se conserva literal y consulta técnica del antecedente.'),
        5956:('2008-03-06','SECUENCIA_AJUSTADA','2008-01-07','La foto escribe 7-01-08, no 17-01-08, después de 6-3-08. Se conserva literal y consulta técnica del antecedente.'),
        **{id:('2008-03-06','SECUENCIA_AJUSTADA',literal,'Fecha literal anterior a 6-3-08 intercalada después de esa fecha; se conserva literal y consulta técnica del antecedente.') for id,literal in ((5957,'2008-02-11'),(5958,'2008-02-12'),(5959,'2008-01-28'),(5960,'2008-03-05'))},
        5967:('2008-05-29','SECUENCIA_AJUSTADA','2008-03-17','17-03-08 aparece después del 29-05-08. Se conserva literal y consulta técnica del antecedente.'),
        5986:('2012-10-10','HIPOTESIS',None,'El día está repasado y parece 40 en 40-10-12. Se conserva la lectura parcial, sin certificar un día imposible ni el 10 de OCR; 10-10-12 queda solo técnico para consulta.'),
        **{id:('2006-10-06','HIPOTESIS',None,'FECHA vacía o parcial 6-10 sin año, anterior a 6-02-07 explícito. Contexto 2006 solo técnico; no se certifica el 10 de junio de 2007 atribuido por OCR.') for id in range(9448,9456)},
        9465:('2009-07-28','SECUENCIA_AJUSTADA','2009-07-17','17-7-09 está después de 28-7-09 en el papel. Se conserva literal y consulta técnica del antecedente.'),
        9479:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','1-08-11 aparece después de 02-08-11. Se conserva literal y consulta técnica del antecedente.'),
        9498:('2021-09-10','SECUENCIA_AJUSTADA','2024-10-01','La fila escribe 1-10-24 antes de 5-8-22 en la siguiente hoja. Se conserva literalmente 2024, sin corregirlo a 2021 por contexto; consulta técnica del antecedente de 2021 para mantener orden físico.'),
        9502:('2023-08-08','HIPOTESIS',None,'La foto escribe 15-15-24, mes imposible. Se conserva texto documental y consulta técnica del antecedente; no se inventa 15 de mayo confirmado.'),
    }
    extras={
        **{id:{'motivo':'ÁREA se lee CAP, no COP; se recupera la letra de la fotografía sin crear alias.'} for id in (3440,3441,3442,3444)},
        3464:{'criterios':['T16'],'motivo':'La última letra de CIO/CID no es inequívoca. Se conserva CIO de la extracción y la foto, sin crear alias ni resolver por frecuencia.'},
        3471:{'motivo':'La salida 364 está escrita claramente y el saldo pasa 699 a 335. Se conserva la magnitud, sin reducirla por ser grande.'},
        3473:{'criterios':['T23'],'motivo':'4 está en INGRESOS, no en ÁREA. Se recupera una sola recepción 4 y saldo 313, sin área numérica.'},
        5936:{'criterios':['T22'],'motivo':'Ingresa Arc. María Tapia tiene solo saldo 223 y cantidades vacías: se conserva como BASE_DOCUMENTAL sin ingreso 223 ficticio.', 'revision':{'tipo_fila':'BASE_DOCUMENTAL'}},
        5953:{'criterios':['T16'],'motivo':'Nota lateral 14-12-07 conservada, sin convertir automáticamente la fecha vacía en fecha confirmada.', 'revision':{'anotacion_margen_fecha':'14-12-07 al lado de devolución; vínculo no confirmado.'}},
        5956:{'criterios':['T18'],'motivo':'Comillas inequívocas en ÁREA repiten CEDOAL de la fila anterior.'},
        **{id:{'criterios':['T16'],'motivo':'El código documental está escrito en ÁREA. Se conserva literal sin crear institución, área o alias numérico.', 'clasificacion':{'area_estado':'PENDIENTE_HIL','requiere_auditoria_nodo':True}} for id in codigos},
        5986:{'criterios':['T16'],'motivo':'Se conserva la cifra de día repasada como lectura parcial y fecha técnica, sin certificarla por parecido.', 'revision':{'fecha_documental_texto':'40-10-12, día repasado no inequívoco.'}},
        9454:{'revision':{'fecha_documental_texto':'6-10, sin año escrito.'}},
        9462:{'criterios':['T16','T19'],'motivo':'La foto contiene 1 en INGRESOS y 1 en SALIDAS, ambos sin anulación inequívoca, y saldo 12 desde 13. Se conservan ambas cifras y el efecto neto cero solo como consulta condicional; el papel difiere -1. No se elimina uno de los números únicamente porque el saldo cuadre ni se inventa una operación.', 'revision':{'origen_cantidades':'HIPOTESIS','columnas_documentales':{'ingresos':1,'salidas':1},'efecto_cuantitativo_no_acreditado':True}},
        9493:{'criterios':['T02'],'motivo':'DEV. A STA. CRUZ tiene 10 en SALIDAS y reduce 27 a 17. Se corrige el ingreso OCR a salida 10, sin invertirlo por el nombre.'},
        9502:{'criterios':['T16'],'motivo':'Mes literal 15 imposible conservado como texto; la fecha de consulta no representa 15 de mayo confirmado.', 'revision':{'fecha_documental_texto':'15-15-24','fecha_documental_imposible':True}},
    }
    plan=construir(version=42,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={65:{'primera_fila':3440,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 105; base cero inferida sin recuento acreditado.'},
            89:{'primera_fila':5936,'saldo_base':223,'origen_saldo_base':'FOTO','motivo_base':'Base documental escrita 223, sin ingreso fabricado.'},
            233:{'primera_fila':9448,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 19, base cero inferida sin recuento acreditado.'}},
        observaciones=[
            {'articulo_id':65,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotografías en lotes distintos y 63 filas cotejadas, conservando numeración original. CAP recuperado de COP, ingreso 4 desplazado a ÁREA corregido y salida 364 legible preservada. Devolución sin fecha y 28-1-23 intercalado siguen técnicos. CIO/CID no se resuelve por frecuencia ni crea alias. Cierre 247 coincide.'},
            {'articulo_id':89,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos y 56 filas cotejadas. Base 223 escrita sin ingreso ficticio, saldos vacíos preservados. CEDOAL recuperado y códigos documentales de ÁREA conservados como pendientes, sin instituciones inventadas. Fechas fuera de orden, nota lateral y día repasado 40-10-12 siguen identificados y técnicos. Cierre 3 coincide.'},
            {'articulo_id':233,'observado':True,'excluir_entrenamiento':True,'motivo':'Tres fotos y 56 filas cotejadas. Primera fecha parcial 6-10 sin año, mes imposible 15-15-24 y fila 1-10-24 anterior a 2022 conservados sin inventar fechas confirmadas. Devolución a Santa Cruz escribe salida 10, corregida desde ingreso OCR. Una fila registra 1 en INGRESOS y 1 en SALIDAS sin anulación inequívoca y saldo 12 desde 13: se conservan ambas cifras, efecto neto cero solo condicional. Diferencia persistente -1, cierre escrito 3 frente a cálculo condicional 4. Apertura bloqueada y artículo excluido del entrenamiento; no se elimina una cifra por cuadrar.'},
        ],extras=extras)
    assert plan['cotejo']['cierres']=={65:247,89:3,233:4},plan['cotejo']
    assert plan['cotejo']['discrepancias']==[{'id':9462,'local':-1,'acumulada':-1}],plan['cotejo']
    for e in plan['revisiones']:
        if e['articulo_id']==233 and e['id']>=9462:e['revision']['origen_saldo']='HIPOTESIS'
        if e['id']==9503:e['cambios']['saldo_registrado']=3;e['revision'].update(usar_saldo_esperado=False,origen_saldo='FOTO')
    plan['cotejo'].update(cierres={65:247,89:3,233:3},cierres_calculados={65:247,89:3,233:4},pendientes_documentales={9503:['saldo']},
        limites_cierre={233:'Cierre escrito 3 frente a cálculo condicional 4. La fila con 1 en ambas columnas tiene efecto no acreditado; no se elimina una cifra para cuadrar. Apertura bloqueada y artículo excluido del entrenamiento.'})
    return plan

if __name__=='__main__':congelar(generar())
