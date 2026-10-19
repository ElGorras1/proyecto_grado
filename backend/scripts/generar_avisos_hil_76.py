"""Ocho avisos de clasificación, con ocho fotos contrastadas."""
from scripts.plan_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar

def nota(saldo):
    return ({'estado':'NOTA_DOCUMENTAL','nodo_grafo':'Nota documental','area_estado':'NO_APLICA','requiere_auditoria_nodo':False},['T13'],f'Saldo {saldo} repite el saldo anterior sin ingresos ni salidas. Nota documental sin efecto, no recuento físico ni ingreso y sin área operativa aplicable. No se extiende la excepción T13 de cuatro ingresos.',{'tipo_fila':'NOTA_DOCUMENTAL'})

def base():
    return ({'nodo_grafo':'Base documental','area_estado':'NO_APLICA','requiere_auditoria_nodo':False},['T22'],'Según inventario escribe saldo inicial 1 con cantidades vacías. Se reconoce base documental, sin inventar ingreso ni área operativa. Los movimientos posteriores se conservan intactos.',{'tipo_fila':'BASE_DOCUMENTAL'})

CASOS={
8663:({'area':None},['T17'],'En ÁREA solo hay un punto aislado, no palabra ni comillas de repetición. Se retira el punto como área y se conserva su evidencia; no se inventa unidad ni procedencia para el ingreso 2/saldo 2.',{'columnas_documentales':{'area':'punto aislado'},'marca_no_identifica_area':True}),
8822:({'referencia':'CBB.','area':None},['T17','T23'],'CBB. del ingreso 15/saldo 15 describe procedencia en ÁREA. Se conserva como referencia literal sin expandir sigla ni crear área institucional.',{'columnas_documentales':{'area':'CBB.'},'procedencia_documental':'CBB.'}),
9010:({'referencia':'CENTRO STA C.','area':None},['T17','T23'],'REF CENTRO y ÁREA STA C. del ingreso describen procedencia. Se conservan ambos textos en referencia sin expandir sigla ni inventar área institucional.',{'columnas_documentales':{'referencia':'CENTRO','area':'STA C.'},'procedencia_documental':'STA C.'}),
9799:nota(1),
9822:nota(2),
10514:base(),
10623:base(),
11847:nota(1),
}

if __name__=='__main__':
    congelar(construir(numero=76,snapshot='backups/revision_avisos_hil_20261016/bloque_76/contexto_antes.json',especificaciones=CASOS,pendientes=[],limites=['Solo ocho avisos de clasificación, ninguna fila vecina modificada.','Bases escritas no son ingresos; notas de saldo no son recuentos físicos.','No crear áreas ni alias; no recuperar filas ni cotejar masivamente.']))
