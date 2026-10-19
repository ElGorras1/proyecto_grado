"""Siete hojas completas, cuatro fechas anteriores protegidas y columnas recuperadas."""
import json
from scripts.cotejo_transcripcion_hil import BACKEND,congelar
from scripts.cotejo_con_anclajes_hil import construir_con_anclajes

HOJAS=[
 (range(996,1022),[5,-1,-1,-1,-8,-1,-5,-1,-1,-1,-1,5,-3,-15,-1,-3,-1,2,-1,-10,8,1,-1,-2,-1,-1],[200,199,198,197,189,188,183,182,181,180,179,184,181,166,165,162,161,163,162,152,160,161,160,158,157,156]),
 (range(1022,1048),[1,-1,-2,2,-10,9,-1,-1,-1,-3,-1,3,-1,-1,-1,1,-5,5,-5,1,4,-1,3,-1,1,-1],[157,156,154,156,146,155,154,153,152,149,148,151,150,149,148,149,144,149,144,145,149,148,151,150,151,150]),
 (range(1048,1074),[-6,-3,3,-5,-1,5,-5,-1,3,-1,8,-3,-2,-4,1,-2,-1,3,-2,-2,-1,-1,-1,-1,-1,-1],[144,141,144,139,138,143,138,137,140,139,147,144,142,138,139,137,136,139,137,135,134,133,132,131,130,129]),
 (range(1074,1078),[2,-1,1,-1],[131,130,131,130]),
 (range(4155,4181),[253,-5,-1,5,-1,-10,9,-3,1,-1,-1,-1,-3,-1,-1,-1,1,-1,-2,2,-10,9,-1,-1,-5,-1],[253,248,247,252,251,241,250,247,248,247,246,245,242,241,240,239,240,239,237,239,229,238,237,236,231,230]),
 (range(4181,4207),[3,-1,-1,-2,2,-5,5,-5,1,-1,-1,1,-1,-1,1,1,-1,-1,-3,3,-5,-1,-1,5,-10,-1],[233,232,231,229,231,226,231,226,227,226,225,226,225,224,225,226,225,224,221,224,219,218,217,222,212,211]),
 (range(4207,4231),[10,-1,1,-3,-2,-2,1,-2,3,-3,-2,-1,-2,3,-1,-1,-1,-1,-1,-1,-1,-2,2,1],[221,220,221,218,216,214,215,213,216,213,211,210,208,211,210,209,208,207,206,205,204,202,204,205]),
]

def generar():
    snapshot='backups/continuacion_hil_67_20261016/articulos_26_75_antes.json'
    rows={r['id']:r for r in json.loads((BACKEND/snapshot).read_text(encoding='utf-8'))}
    cambios={id:{'area':'CEDOAL'} for id,r in rows.items() if r['area'] in ('Cedoal','CDOAL','CEDOOL','CooD. L.')}
    for id,fields in {
        1009:{'area':'FUSIP'},1018:{'area':'GALERIA'},1020:{'detalle':'DONACION LUIS OPORTO'},1023:{'detalle':'QUIME'},1024:{'detalle':'LLALLAGUA'},1025:{'detalle':'LLALLAGUA'},1067:{'area':'LUCY'},1071:{'detalle':'ARTEBATES'},1076:{'detalle':'DEV. ENTREGADOS EN CONSIGNAC.'},
        4158:{'fecha_movimiento':'2010-06-11'},4161:{'fecha_movimiento':'2010-09-03'},4169:{'referencia':'OBQUIO'},4172:{'detalle':'QUIME'},4173:{'detalle':'LLALLAGUA'},4174:{'detalle':'LLALLAGUA'},4180:{'detalle':'APAC - PALCA'},4192:{'fecha_movimiento':'2012-12-05'},4204:{'fecha_movimiento':'2013-07-01'},4213:{'area':None},4220:{'area':None},
    }.items():cambios.setdefault(id,{}).update(fields)
    extras={
        1009:{'criterios':['T23'],'motivo':'FUSIP escrito en ÁREA se conserva literalmente sin fusionarlo con ESIP ni crear alias.'},
        1012:{'criterios':['T23'],'motivo':'Tocaña continúa en DETALLE, tal como está en esta hoja, sin trasladarlo desde otras fotografías.'},
        1018:{'criterios':['T23'],'motivo':'ÁREA se lee GALERIA, no SGRIA.'},
        1020:{'criterios':['T23'],'motivo':'OPORTO se lee en esta foto, no APORTo; corrección solo textual sin asignar persona responsable.'},
        1047:{'criterios':['T14'],'motivo':'Saldo 150 repasado legible; corrección de una celda no anula la salida 1.'},
        1071:{'criterios':['T23'],'motivo':'DETALLE se lee ARTEBATES, no ARTEVIES; se conserva el texto sin crear institución ni alias.'},
        **{id:{'criterios':['T01'],'motivo':motivo} for id,motivo in ((4158,'Fecha escrita 11-6-10, no 6-6-10.'),(4161,'Fecha escrita 03-09-10, no 23-09-10.'),(4192,'Fecha escrita 5-12-12, no 3-12-12.'),(4204,'Fecha escrita 1-7-13, no 4-7-13.'))},
        4190:{'criterios':['T14'],'motivo':'Saldo 226 repasado legible; se conserva salida 1, sin anular todo el renglón.'},
        **{id:{'criterios':['T02','T23'],'motivo':f'Cantidad {q} está en INGRESOS, con ÁREA vacía. OCR la desplazó a área numérica y dejó la cantidad ausente; se recupera desde columna visible, no solamente desde el saldo.', 'revision':{'desplazamiento_columna_ocr':True,'columnas_documentales':{'area':None,'ingresos':q}}} for id,q in ((4213,1),(4220,3))},
    }
    plan=construir_con_anclajes(version=67,instantanea=snapshot,anclajes=[1025,1026,1033,1034],hojas=HOJAS,correcciones=cambios,
        tecnicas={4175:('2011-08-02','SECUENCIA_AJUSTADA','2011-08-01','Se lee 1-08-11, no 11-08-11. Literal anterior al 02-08-11 precedente: consulta técnica del antecedente, sin certificar el día por secuencia.'),4195:('2013-03-06','SECUENCIA_AJUSTADA','2013-03-05','5-3-13 aparece después de 6-3-13; literal y orden físico conservados, fecha técnica solo de consulta.')},grupos_fechas=[],tipos={},
        bases={26:{'primera_fila':996,'saldo_base':195,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso 5 y saldo 200 escritos implican base previa 195 inferida, sin ingreso fabricado.'},75:{'primera_fila':4155,'saldo_base':0,'origen_saldo_base':'HIPOTESIS','motivo_base':'Primer ingreso y saldo 253 escritos; base previa cero inferida, sin recepción adicional.'}},
        observaciones=[
            {'articulo_id':26,'observado':True,'excluir_entrenamiento':False,'motivo':'Cuatro fotos y 82 filas cotejadas. Cuatro decisiones anteriores de fechas ajustadas se mantienen íntegras, sin cambiar sus consultas ni certificar sus literales por orden. Base previa 195 inferida, sin ingreso inventado. FUSIP literal no se fusiona con ESIP; Galería, Oporto, Llallagua, Quime, Lucy y Artebates recuperados solo como textos de sus columnas. Saldo repasado no anula la operación. Cantidades y cierre escrito 130 coinciden con cálculo independiente.'},
            {'articulo_id':75,'observado':True,'excluir_entrenamiento':False,'motivo':'Tres fotos y 76 filas cotejadas. Recepciones 1 y 3 estaban desplazadas por OCR a ÁREA: se recuperan de INGRESOS y el área vacía, sin inventar operaciones. Se corrigen fechas 11-6-10, 03-09-10, 5-12-12 y 1-7-13 desde la fotografía. Literales 1-08-11 y 5-3-13 que retroceden permanecen con consulta técnica. Quime, Llallagua y APAC-Palca corregidos como texto sin alias; saldos repasados conservan las filas activas. Cierre escrito 205 coincide con cálculo independiente.'},
        ],extras=extras)
    assert plan['cotejo']['discrepancias']==[] and plan['cotejo']['cierres']=={26:130,75:205},plan['cotejo']
    plan['cotejo']['pendientes_documentales']={str(id):['fecha'] for id in (1025,1026,1033,1034)}
    return plan

if __name__=='__main__':raise RuntimeError('Plan 67 archivado sin aplicación institucional: el titular restringió el trabajo a avisos HIL. No recrear el cotejo masivo.')
