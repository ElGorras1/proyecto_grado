from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.services.preparacion_inventario import preparar

router = APIRouter(prefix="/inventario", tags=["Preparación del inventario"])


@router.get("/preparacion")
def consultar(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return preparar(db)
