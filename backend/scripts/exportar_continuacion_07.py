"""Instantánea de consulta del lote 07, con la secuencia documental validada."""
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
    plan=json.loads((DEST/'plan_continuacion_07.json').read_text(encoding='utf-8'))
    resultado=json.loads((DEST/'resultado_continuacion_07.json').read_text(encoding='utf-8'))
    assert resultado['verificado'] is True
    entradas={e['id']:e for e in plan['revisiones']}
    with SessionLocal() as db:
        db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
        assert fuente_hash(db)==resultado['fuente_sha256']
        articulo=db.get(Activo,88)
        rows=db.query(M).filter(M.articulo_id==88).order_by(M.lote_id,pagina_sql(),M.orden_fila,M.id).all()
        assert len(rows)==241
        filas=[]
        for m in rows:
            e=entradas[m.id]
            foto=(BACKEND/m.ruta_imagen_respaldo).resolve()
            assert hashlib.sha256(foto.read_bytes()).hexdigest()==e['sha256_imagen']
            filas.append({'antes':e['esperado'],'actual':snapshot_revision(m),'pagina':e['pagina'],'foto':foto.as_uri()})
        grupo={'id':88,'nombre':articulo.nombre,'observacion':articulo.observacion_hil,'filas':filas}
        cierre={'cierres':[{'id':88,'articulo':articulo.nombre,'saldo_vigente':rows[-1].saldo_registrado,'saldo_documental':rows[-1].revision_documental['saldo_documental']}]}
        db.rollback()
    return {'generado_en':datetime.now(ZoneInfo('America/La_Paz')).isoformat(),
        'articulos':[grupo],'cierre_verificado':cierre,
        'presentacion':{'resumen':'241 movimientos cotejados en diez fotos de ARQUITECTURA HOY EN BOLIVIA; 87 con cambios de lectura o estado.',
            'acumulado':'Acumulado: 727 movimientos distintos con revisión. Este informe contiene el lote 07; no es todo el dataset.',
            'aviso':'La fila marcada como duplicada en el papel permanece guardada, sin efecto sobre el saldo. Se conservan las diferencias internas del papel y las correcciones a lápiz. El cierre reconstruido y el escrito son 1; esto no equivale a un conteo físico actual. El resto del histórico sigue en revisión.'}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida',type=Path,required=True)
    args=parser.parse_args()
    copia=DEST/'instantanea_informe_continuacion_07.json'
    if copia.exists():datos=json.loads(copia.read_text(encoding='utf-8'))
    else:
        datos=preparar();copia.write_text(json.dumps(datos,ensure_ascii=False,indent=2),encoding='utf-8')
    args.salida.parent.mkdir(parents=True,exist_ok=True)
    args.salida.write_text(renderizar(datos),encoding='utf-8')
    print(json.dumps({'informe':str(args.salida.resolve()),'movimientos':241},ensure_ascii=False))


if __name__=='__main__':main()
