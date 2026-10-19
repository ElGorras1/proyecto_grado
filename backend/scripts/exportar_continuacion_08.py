"""Informe congelado del cotejo de Taller 3 y Bolivia Ecológica 37/41."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from sqlalchemy import text

from app.db.session import SessionLocal
from app.models.activos import Activo
from app.models.kardex import MovimientoKardex as M
from app.services.revision_documental import pagina_sql, snapshot_revision
from scripts.aplicar_revision_hil import BACKEND, DEST, fuente_hash
from scripts.exportar_continuacion_hil_20261014 import renderizar


def preparar():
    plan=json.loads((DEST/'plan_continuacion_08.json').read_text(encoding='utf-8'))
    resultado=json.loads((DEST/'resultado_continuacion_08.json').read_text(encoding='utf-8'))
    assert resultado['verificado'] is True
    entries={e['id']:e for e in plan['revisiones']}
    grupos=[];cierres=[]
    with SessionLocal() as db:
        db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
        assert fuente_hash(db)==resultado['fuente_sha256']
        for aid in (187,302,306):
            articulo=db.get(Activo,aid)
            rows=db.query(M).filter(M.articulo_id==aid).order_by(M.lote_id,pagina_sql(),M.orden_fila,M.id).all()
            filas=[]
            for m in rows:
                e=entries[m.id];foto=(BACKEND/m.ruta_imagen_respaldo).resolve()
                assert hashlib.sha256(foto.read_bytes()).hexdigest()==e['sha256_imagen']
                filas.append({'antes':e['esperado'],'actual':snapshot_revision(m),'pagina':e['pagina'],'foto':foto.as_uri()})
            grupos.append({'id':aid,'nombre':articulo.nombre,'observacion':articulo.observacion_hil,'filas':filas})
            cierres.append({'id':aid,'articulo':articulo.nombre,'saldo_vigente':rows[-1].saldo_registrado,'saldo_documental':rows[-1].revision_documental['saldo_documental']})
        db.rollback()
    assert sum(len(g['filas']) for g in grupos)==180
    return {'generado_en':datetime.now(ZoneInfo('America/La_Paz')).isoformat(),'articulos':grupos,
        'cierre_verificado':{'cierres':cierres},
        'presentacion':{'resumen':'180 movimientos cotejados en ocho fotos de tres revistas; 51 con cambios de campos.',
            'acumulado':'Acumulado: 907 movimientos distintos con revisión. Este informe contiene el lote 08; no es todo el dataset.',
            'aviso':'Los cierres reconstruidos coinciden con los escritos: Taller 3, 10; Bolivia Ecológica 37, 8; Bolivia Ecológica 41, 9. Las fechas, bases y saldos hipotéticos siguen marcados y excluidos del entrenamiento. Se conservan las notas marginales, incluida la de intención no resuelta junto al 7 de Bolivia Ecológica 37. El resto del histórico sigue en revisión.'}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida',type=Path,required=True);args=parser.parse_args()
    copia=DEST/'instantanea_informe_continuacion_08.json'
    if copia.exists():datos=json.loads(copia.read_text(encoding='utf-8'))
    else:
        datos=preparar();copia.write_text(json.dumps(datos,ensure_ascii=False,indent=2),encoding='utf-8')
    args.salida.parent.mkdir(parents=True,exist_ok=True)
    args.salida.write_text(renderizar(datos),encoding='utf-8')
    print(json.dumps({'informe':str(args.salida.resolve()),'movimientos':180},ensure_ascii=False))


if __name__=='__main__':main()
