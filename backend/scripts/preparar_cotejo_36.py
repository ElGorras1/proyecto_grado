"""Instantánea de solo lectura para el cotejo visual 36; no altera la base."""
import json
from pathlib import Path
from sqlalchemy import text
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex as M
from app.services.revision_documental import snapshot_revision,pagina_sql

def main():
    carpeta=Path('backups/continuacion_hil_36_20261015')
    carpeta.mkdir(exist_ok=True)
    destino=carpeta/'articulos_42_92_antes.json'
    assert not destino.exists(),'Conservar instantánea previa'
    with SessionLocal() as db:
        db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
        ms=db.query(M).filter(M.articulo_id.in_([42,92]),M.lote_id.isnot(None)).order_by(M.articulo_id,M.lote_id,pagina_sql(),M.orden_fila,M.id).all()
        rows=[snapshot_revision(m) for m in ms]
        assert len(rows)==168 and all(not m.revision_documental for m in ms)
    destino.write_text(json.dumps(rows,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    for r in rows:
        print(json.dumps({k:r[k] for k in ('id','articulo_id','numero_pagina','orden_fila','fecha_movimiento','detalle','referencia','area','ingresos','salidas','saldo_registrado','ruta_imagen_respaldo')},ensure_ascii=False))

if __name__=='__main__':main()
