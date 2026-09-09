from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.activos import Activo, CategoriaActivo, Existencia
from app.models.area import Area
from app.models.usuario import Usuario
from app.schemas.inventario import ItemReporteInventario

router = APIRouter(prefix="/inventario", tags=["Inventario y Reportes"])


@router.get("/reporte", response_model=list[ItemReporteInventario])
def reporte_inventario(
    categoria_id: int | None = Query(default=None),
    area_id: int | None = Query(default=None),
    solo_stock_bajo: bool = Query(default=False),
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    """
    Genera el reporte consolidado de inventario.
    Accesible por cualquier usuario autenticado (Administrador, Operador, Auditor).
    """
    query = (
        db.query(Existencia, Activo, CategoriaActivo, Area)
        .join(Activo, Existencia.activo_id == Activo.id)
        .join(CategoriaActivo, Activo.categoria_id == CategoriaActivo.id)
        .join(Area, Existencia.area_id == Area.id)
    )

    if categoria_id is not None:
        query = query.filter(Activo.categoria_id == categoria_id)

    if area_id is not None:
        query = query.filter(Existencia.area_id == area_id)

    if solo_stock_bajo:
        query = query.filter(
            Existencia.stock_minimo.isnot(None),
            Existencia.cantidad < Existencia.stock_minimo,
        )

    filas = query.order_by(Activo.nombre.asc(), Area.nombre.asc()).all()

    resultado: list[ItemReporteInventario] = []
    for existencia, activo, categoria, area in filas:
        stock_bajo = (
            existencia.stock_minimo is not None
            and float(existencia.cantidad) < float(existencia.stock_minimo)
        )
        resultado.append(
            ItemReporteInventario(
                existencia_id=existencia.id,
                activo_id=activo.id,
                activo_codigo=activo.codigo,
                activo_nombre=activo.nombre,
                categoria_id=categoria.id,
                categoria_nombre=categoria.nombre,
                area_id=area.id,
                area_nombre=area.nombre,
                cantidad=float(existencia.cantidad),
                stock_minimo=float(existencia.stock_minimo) if existencia.stock_minimo is not None else None,
                stock_maximo=float(existencia.stock_maximo) if existencia.stock_maximo is not None else None,
                unidad_medida=activo.unidad_medida,
                stock_bajo=stock_bajo,
                estado=existencia.estado,
            )
        )

    return resultado
