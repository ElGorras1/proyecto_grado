"""Historias de Oruro 40: tres fotografías completas cotejadas."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(6877,6903),[2000,-140,-10,-3,-50,-10,-15,-20,-200,-360,-20,-2,-1,-2,-1,-2,-3,-1,-2,-150,-10,-8,-3,-7,-150,-100],
  [2000,1860,1850,1847,1797,1787,1772,1752,1552,1192,1172,1170,1169,1167,1166,1164,1161,1160,1158,1008,998,990,987,980,830,730]),
 (range(6903,6929),[-2,-2,-3,-26,-100,-3,-1,10,-6,132,-3,-100,-3,-50,-100,-5,-4,-4,-1,-2,-2,-2,-2,-2,-150,-3],
  [728,726,723,697,597,594,593,603,597,729,726,626,623,573,473,468,464,460,459,457,455,453,451,449,299,296]),
 (range(6929,6943),[-2,-2,-2,-2,-2,-10,-3,-2,-2,-2,-6,-6,2,-10],
  [294,292,290,288,286,276,273,271,269,267,261,255,257,247]),
]


def generar():
    snapshot='backups/continuacion_hil_18_20261015/articulo_99_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    for id,r in rows.items():
        if r['area']=='CEDEOC':
            cambios[id]={'area':'CEDOAL'}
            extras[id]={'motivo':'CEDOAL es la lectura del área en esta fotografía; CEDEOC era una lectura incorrecta, sin crear áreas o alias.'}
    cambios.update({6886:{'referencia':'Inauguración ESIP'},6889:{'detalle':'LIC. TONIA BENAVENTE'}})
    tecnicas={
        **{id:('2018-12-27','SECUENCIA_AJUSTADA',rows[id]['fecha_movimiento'],'Fecha de diciembre anterior al ingreso escrito 27-12-18. Consulta técnica del antecedente, conservando la literal de cada salida y sin alterar cantidades.') for id in range(6878,6886)},
        6902:('2019-07-01','SECUENCIA_AJUSTADA','2019-05-28','28-05-19 después del 01-07-19: consulta técnica del antecedente y literal conservada.'),
        6914:('2020-02-10','HIPOTESIS',None,'Celda de fecha con punto aislado; no se certifica como comilla de repetición. Consulta técnica del antecedente y ausencia documental conservada.'),
        6928:('2023-01-17','HIPOTESIS','2022-01-17','El papel escribe 17-01-22 después del 30-11-22 y antes de junio de 2023. Año 2023 solo como hipótesis de consulta; 2022 se conserva como literal.'),
        6932:('2023-06-22','SECUENCIA_AJUSTADA','2023-03-07','07-03-23 aparece después del 22-06-23; consulta técnica del antecedente, sin afirmar julio como fecha del papel.'),
        6939:('2024-05-24','HIPOTESIS',None,'Envío Santa Cruz tiene fecha en blanco. Se conserva ausencia y fecha técnica del antecedente; no se convierte en una comilla inequívoca.'),
        6942:('2024-11-26','SECUENCIA_AJUSTADA','2024-10-08','08-10-24 escrito después del 26-11-24. Se conserva el año y fecha literales con consulta técnica del antecedente, sin inventar 2025.'),
    }
    extras.update({
        6886:{'criterios':['T02','T23'],'motivo':'Donación y venta tiene SALIDA 360 y saldo 1192 desde 1552. Inauguración ESIP cruza REF/ÁREA; se conserva como referencia completa, sin atribuir todo a una sola área ni separar cantidades no desglosadas.',
            'revision':{'operacion_mixta':'DONACION_Y_VENTA','sin_desglose_documental':True,'columnas_documentales':{'referencia':'INAUGURA...','area':'...CION ESIP'}},
            'clasificacion':{'nodo_grafo':'Salida: Donación y venta sin desglose','area_estado':'NO_APLICA','requiere_auditoria_nodo':False}},
        6914:{'revision':{'lectura_fecha_parcial':'Punto aislado en FECHA, sin día escrito.'}},
        6913:{'criterios':['T16'],'motivo':'El nombre antes de Peña M. no es inequívoco. Se conserva la extracción y su lectura parcial, sin atribuirlo a otra persona por similitud.',
            'revision':{'lectura_detalle_parcial':'Lic. S... Peña M.'}},
        6917:{'criterios':['T02'],'motivo':'100 está en SALIDAS, no en INGRESOS. La foto baja de 573 a 473.'},
        6918:{'criterios':['T02'],'motivo':'FIL tiene 5 en SALIDAS, no en INGRESOS, y saldo 468 desde 473.'},
        6927:{'criterios':['T02'],'motivo':'150 está en SALIDAS. El papel baja de 449 a 299; no se reduce ni se divide esa cantidad por ser grande.'},
        6939:{'revision':{'lectura_fecha_parcial':'Celda FECHA en blanco.'}},
    })
    plan=construir(version=19,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,grupos_fechas=[],
        bases={99:{'primera_fila':6877,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 2000: base cero inferida, no un conteo físico previo.'}},
        observaciones=[{'articulo_id':99,'observado':True,'excluir_entrenamiento':False,
            'motivo':'Tres fotografías y 66 filas cotejadas. Cuatro cantidades extraídas como ingresos son salidas documentadas (360, 100, 5 y 150). Cierre reconstruido 247 coincide con el papel. Fechas técnicas y año hipotético conservan su exclusión; donación y venta 360 se mantiene sin un desglose inexistente.'}],extras=extras)
    assert plan['cotejo']['cierres']=={99:247} and plan['cotejo']['discrepancias']==[]
    return plan


if __name__=='__main__':congelar(generar())
