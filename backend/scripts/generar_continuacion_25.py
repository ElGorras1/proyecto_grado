"""Cuatro fotos completas del Coloquio Teatro y sociedad en América Latina."""
import json
from scripts.cotejo_transcripcion_hil import construir,congelar,BACKEND

HOJAS=[
 (range(1888,1914),[-5,-15,18,-1,-1,-1,-2,-5,5,-3,-15,-1,-2,-1,-1,-3,-1,3,-1,-10,-5,10,-4,-3,-1,-3],
  [115,100,118,117,116,115,113,108,113,110,95,94,92,91,90,87,86,89,88,78,73,83,79,76,75,72]),
 (range(1914,1940),[-1,-1,-1,-1,1,-1,-1,-2,2,-10,8,-1,-1,-3,-1,-5,-1,-2,-1,-10,-1,8,-2,-1,2,-5],
  [71,70,69,68,69,68,67,65,67,57,65,64,63,60,59,54,53,51,50,40,39,47,45,44,46,41]),
 (range(1940,1966),[4,1,-5,2,-1,-1,-13,1,-1,-7,1,-1,-1,-1,-3,3,-5,-1,2,-1,-1,-10,8,-1,1,-2],
  [45,46,41,43,42,41,28,29,28,21,22,21,20,19,16,19,14,13,15,14,13,3,11,10,11,9]),
 (range(1966,1981),[-2,2,-3,1,-2,-3,2,-2,2,-2,2,-2,1,9,4],[7,9,6,7,5,2,4,2,4,2,4,2,3,12,16]),
]


def generar():
    snapshot='backups/continuacion_hil_25_20261015/articulo_49_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))};cambios={};extras={}
    for id,r in rows.items():
        if r['area'] in ('Cedoal','CEDODL','CEDOCAL'):
            cambios[id]={'area':'CEDOAL'}
            extras[id]={'motivo':'CEDOAL se lee en esta fotografía; se normaliza la transcripción sin crear áreas o alias.'}
    for id,fields in {
        1920:{'referencia':'CANJE'},1921:{'detalle':'LLALLAGUA'},1922:{'detalle':'LLALLAGUA'},
        1931:{'detalle':'MASCAREÑO - PASGUIDO'},1941:{'detalle':'DEVOLUCION - CEDOAL'},1942:{'detalle':'FIL CBBA.'},
        1966:{'detalle':'VENTAS CEDOAL','referencia':'ACTIV.'},1967:{'detalle':'DEVOLUCION'},1978:{'referencia':'DEV.'},
    }.items():cambios.setdefault(id,{}).update(fields)
    tecnicas={
        1913:('2011-01-10','HIPOTESIS','2010-01-10','El año de 10-01-10 está repasado después del 27-12-10, antes de febrero de 2011. Se conserva la lectura del papel y 2011 solo como hipótesis de consulta.'),
        1923:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','La foto escribe 1-08-11 después del 02-08-11, no 10-08. Se conserva la literal y se usa el antecedente solo para consulta.'),
        1947:('2013-03-12','SECUENCIA_AJUSTADA','2013-03-05','La foto escribe 5-03-13 después del 12-03-13, no 15-03. Consulta técnica del antecedente y fecha literal conservada.'),
        1971:('2014-07-25','SECUENCIA_AJUSTADA','2014-07-24','24-07-14 después del 25-07-14. Se conserva literal y orden físico; consulta técnica del antecedente.'),
    }
    extras.update({
        1888:{'motivo':'La primera operación es salida 5 con saldo 115: base 120 inferida, sin inventar un ingreso ni un recuento.'},
        1919:{'criterios':['T14'],'motivo':'QUIME presenta salida 1 y una marca tachada en INGRESOS. No se añade una segunda operación ni se anula todo el renglón.',
            'revision':{'marcas_documentales':{'ingresos':'Marca tachada sin cantidad adicional legible.'}}},
        1940:{'motivo':'Ingreso 4 de devolución y saldo 45 visibles; se conserva una sola devolución.'},
        1947:{'motivo':'Se coteja también el renglón anterior de Gestores Teatrales, salida 13 y saldo 28; la devolución 1 deja 29. No se cambia la cantidad para corregir la fecha.'},
        1950:{'motivo':'Galería escribe ingreso 1 con referencia en blanco. Se conserva el ingreso sin atribuir una venta ni una referencia inventada.'},
        1967:{'criterios':['T23'],'motivo':'El detalle dice DEVOLUCIÓN, no el nombre que produjo el OCR. Ingreso 2 y saldo 9 se conservan.'},
        1976:{'criterios':['T23'],'motivo':'DEVOLUCIÓN es parte del detalle extendida entre columnas; se conserva un solo ingreso 2 y no se crea un área.'},
        1980:{'criterios':['T07'],'motivo':'DEV. FUN. BCB escribe 4 en la columna SALIDAS pero el saldo sube de 12 a 16. El texto de devolución y la cadena completa sustentan ingreso 4 como interpretación vigente; se conserva que la columna documental es SALIDAS. No se cambia la cantidad ni se añade un ajuste para cuadrar.',
            'revision':{'columna_documental_cantidad':'SALIDAS','interpretacion_cantidad':'INGRESO','cantidad_documental':4,'saldo_anterior_documental':12,
                'hallazgos':['HOJA_COMPLETA_COTEJADA','COLUMNA_EQUIVOCADA_EN_DOCUMENTO_CONSERVADA']}}
    })
    plan=construir(version=25,instantanea=snapshot,hojas=HOJAS,correcciones=cambios,tecnicas=tecnicas,
        grupos_fechas=[(1965,1966)],
        bases={49:{'primera_fila':1888,'saldo_base':120,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primera salida 5 y saldo 115: base 120 inferida para reconstrucción, sin recepción o recuento fabricados.'}},
        observaciones=[{'articulo_id':49,'observado':True,'excluir_entrenamiento':False,'motivo':'Cuatro fotos y 93 filas cotejadas completas. Se conserva base 120 inferida, fechas técnicas y una tachadura de celda sin anular la operación. La última devolución 4 está escrita en SALIDAS pero aumenta 12 a 16; se interpreta ingreso por texto y cadena, preservando columna y cifra originales. Se corrigen detalle DevOLUCIÓN y áreas leídas como CEDOAL, sin crear entidades. Cierre 16 coincide.'}],extras=extras)
    assert plan['cotejo']['cierres']=={49:16} and not plan['cotejo']['discrepancias'],plan['cotejo']
    return plan


if __name__=='__main__':congelar(generar())
