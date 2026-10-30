"""Una fuente revisada prevalece sobre el orden de importación de las hojas."""
from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from app.models.cobertura import CoberturaArticulo
from app.models.kardex import MovimientoKardex

RAIZ_STORAGE = Path(__file__).resolve().parents[2] / "storage"
CAMPOS = (
    "id", "articulo_id", "lote_id", "estado", "numero_pagina", "orden_pagina_validado",
    "orden_fila", "fecha_movimiento", "fecha_precision", "fecha_documental_texto",
    "fecha_estado", "detalle", "referencia", "area", "ingresos", "salidas",
    "saldo_registrado", "saldo_calculado", "tiene_error_saldo", "ruta_imagen_respaldo",
)


def foto_huella(ruta):
    """Solo archivos servibles por la ruta privada; nunca rutas arbitrarias."""
    from app.api.evidencia import EXTENSIONES
    try:
        relativa = (ruta or "").replace("\\", "/")
        if not relativa.startswith("storage/"):
            return None
        raiz = RAIZ_STORAGE.resolve()
        archivo = (raiz / relativa[len("storage/"):]).resolve()
        if not archivo.is_relative_to(raiz) or archivo.suffix.lower() not in EXTENSIONES:
            return None
        return sha256(archivo.read_bytes()).hexdigest()
    except (OSError, ValueError, RuntimeError):
        return None


def huella_filas(filas):
    datos = [{campo: getattr(m, campo) for campo in CAMPOS} for m in sorted(filas, key=lambda m: m.id)]
    return sha256(json.dumps(datos, sort_keys=True, default=str, ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")).hexdigest()


def version_revision(fuente, filas):
    """Control optimista de filas, fotos y decisión humana leídas en pantalla."""
    revision = fuente.revision if fuente else None
    datos = dict(filas=huella_filas(filas),
                 revision=[revision.estado, revision.revisado_en.isoformat(),
                           revision.cierre_movimiento_id] if revision else None,
                 fotos={ruta: foto_huella(ruta) for ruta in
                        {m.ruta_imagen_respaldo or "" for m in filas if m.estado == "ACTIVO"}})
    return sha256(json.dumps(datos, sort_keys=True, default=str).encode()).hexdigest()


def fila_dict(m):
    if m is None:
        return None
    return dict(movimiento_id=m.id, lote_id=m.lote_id, pagina=m.numero_pagina,
                orden_pagina=m.orden_pagina_validado or m.numero_pagina, fila=m.orden_fila,
                fecha_ocr=m.fecha_movimiento.isoformat() if m.fecha_movimiento else None,
                gestion=m.fecha_movimiento.year if m.fecha_movimiento else None,
                saldo_documental=m.saldo_registrado, ruta_imagen_respaldo=m.ruta_imagen_respaldo)


@dataclass
class FuenteCierre:
    cierre: MovimientoKardex | None
    propuesta: MovimientoKardex | None
    revision: CoberturaArticulo | None
    huella: str
    estado: str

    def publico(self):
        r = self.revision
        return dict(estado=self.estado, vigente=self.estado == "CONFIRMADA",
                    seleccion=fila_dict(self.cierre), propuesta=fila_dict(self.propuesta),
                    referencia=r.referencia if r else None, motivo=r.observacion if r else None,
                    revisado_por=r.revisado_por if r else None,
                    revisado_en=r.revisado_en.isoformat() if r else None,
                    evidencia_aprobada=r.cierre_snapshot if r else None)


def fuentes_cierre(db, articulo_id=None):
    m = MovimientoKardex
    consulta = db.query(m).filter(m.lote_id.isnot(None))
    revisiones = db.query(CoberturaArticulo)
    if articulo_id is not None:
        consulta = consulta.filter(m.articulo_id == articulo_id)
        revisiones = revisiones.filter(CoberturaArticulo.articulo_id == articulo_id)
    grupos = defaultdict(list)
    for fila in consulta.all():
        grupos[fila.articulo_id].append(fila)
    revisiones = {r.articulo_id: r for r in revisiones.all()}
    resultado = {}
    for aid in grupos.keys() | revisiones.keys():
        filas = grupos[aid]
        # PostgreSQL DESC usa NULLS FIRST; se conserva la propuesta anterior.
        def orden(f):
            pagina = f.orden_pagina_validado if f.orden_pagina_validado is not None else f.numero_pagina
            return f.lote_id, pagina if pagina is not None else float("inf"), f.orden_fila if f.orden_fila is not None else float("inf"), f.id
        propuesta = max((f for f in filas if f.estado == "ACTIVO"), key=orden, default=None)
        revision = revisiones.get(aid)
        huella = huella_filas(filas)
        cierre, estado = propuesta, "PROPUESTA"
        if revision and revision.cierre_movimiento_id is not None:
            cierre = next((f for f in filas if f.id == revision.cierre_movimiento_id), None)
            estado = "DESACTUALIZADA"
            if revision.estado != "CIERRE_CONFIRMADO":
                estado = "RETIRADA"
            elif (cierre and cierre.estado == "ACTIVO" and revision.cierre_huella_fuente == huella
                  and foto_huella(cierre.ruta_imagen_respaldo) == (revision.cierre_snapshot or {}).get("foto_sha256")
                  and (revision.cierre_snapshot or {}).get("foto_sha256")):
                estado = "CONFIRMADA"
        elif revision and revision.estado == "CIERRE_CONFIRMADO":
            estado = "DESACTUALIZADA"
        resultado[aid] = FuenteCierre(cierre, propuesta, revision, huella, estado)
    return resultado


def fuente_cierre(db, articulo_id):
    return fuentes_cierre(db, articulo_id).get(articulo_id)
