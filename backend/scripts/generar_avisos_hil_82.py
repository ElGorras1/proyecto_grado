"""Sustituye ensayo 81 no aplicado: fecha hipotética se clasifica sin aviso abierto."""
from scripts.generar_avisos_hil_81 import CASOS
from scripts.plan_avisos_hil import construir
from scripts.cotejo_transcripcion_hil import congelar
if __name__=='__main__':
    congelar(construir(numero=82,snapshot='backups/revision_avisos_hil_20261016/bloque_81/contexto_antes.json',especificaciones=CASOS,pendientes=[10226],limites=['Solo diez movimientos observados; sin cambios a vecinos.','Ensayo 81 rechazado por expectativa incorrecta del aviso de fecha; nunca aplicado institucionalmente.','10006 queda ESTIMADA_HIL y excluido: se documenta dependencia temporal y fecha ausente; aviso retirado no significa fecha certificada.','10226 conserva diferencia +2 del papel con aviso abierto y cantidades escritas intactas.']))
