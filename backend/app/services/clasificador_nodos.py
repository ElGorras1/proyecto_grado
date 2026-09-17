from typing import Tuple, Optional
from thefuzz import fuzz
from sqlalchemy.orm import Session
from sqlalchemy import text

UMBRAL_FUZZY = 80  # % mínimo de similitud para sugerir coincidencia

def _resolver_area_con_catalogo(area_texto: str, db: Optional[Session] = None) -> Tuple[str, bool]:
    """
    Intenta resolver un texto de área del OCR contra el catálogo maestro.
    """
    texto = area_texto.strip().upper()
    if not texto:
        return "Desconocido / Sin Asignar", True
        
    if not db:
        return f"Área: {texto}", True
    
    try:
        # Paso 1: Coincidencia exacta en catálogo
        match = db.execute(
            text("SELECT nombre_oficial FROM catalogo_areas WHERE UPPER(nombre_oficial) = :txt OR UPPER(abreviatura) = :txt"),
            {"txt": texto}
        ).fetchone()
        
        if match:
            return f"Área: {match[0]}", False
            
        # Paso 2: Coincidencia en sinónimos confirmados
        match = db.execute(
            text("""
                SELECT ca.nombre_oficial, sa.confirmado 
                FROM sinonimos_area sa 
                JOIN catalogo_areas ca ON sa.area_oficial_id = ca.id
                WHERE UPPER(sa.texto_sucio) = :txt
            """), {"txt": texto}
        ).fetchone()
        
        if match:
            return f"Área: {match[0]}", not match[1]
            
        # Paso 3: Fuzzy match
        todas = db.execute(text("SELECT id, nombre_oficial, abreviatura FROM catalogo_areas")).fetchall()
        
        mejor_score = 0
        mejor_area = None
        mejor_id = None
        
        for area_id, nombre, abrev in todas:
            score_nombre = fuzz.ratio(texto, nombre.upper())
            score_abrev = fuzz.ratio(texto, (abrev or "").upper()) if abrev else 0
            score = max(score_nombre, score_abrev)
            
            if score > mejor_score:
                mejor_score = score
                mejor_area = nombre
                mejor_id = area_id
                
        if mejor_score >= UMBRAL_FUZZY:
            try:
                db.execute(text("""
                    INSERT INTO sinonimos_area (texto_sucio, area_oficial_id, confirmado) 
                    VALUES (:txt, :id, FALSE)
                    ON CONFLICT (texto_sucio) DO NOTHING
                """), {"txt": texto, "id": mejor_id})
                db.commit()
            except:
                db.rollback()
            return f"Área: {mejor_area}", True
            
        return f"Área: {texto}", True
        
    except Exception as e:
        return f"Área: {texto}", True


def clasificar_nodo_movimiento(detalle: Optional[str], ref: Optional[str], area: Optional[str], ingreso: Optional[int], salida: Optional[int], db: Optional[Session] = None) -> Tuple[str, bool]:
    """
    Motor Heurístico de Clasificación de Nodos para Teoría de Grafos.
    Ahora integrado con el Catálogo Maestro de Áreas y Fuzzy Matching.
    Retorna: (nombre_del_nodo, requiere_auditoria_hil)
    """
    d_text = (detalle or "").upper()
    r_text = (ref or "").upper()
    a_text = (area or "").upper()
    
    ing = ingreso if ingreso is not None else 0
    sal = salida if salida is not None else 0

    # Regla 1: Ferias (FIL / FERIA)
    if "FIL" in d_text or "FERIA" in d_text or "FIL" in r_text or "FERIA" in r_text:
        if "DEV" in r_text or "DEV" in d_text or ing > 0:
            return "Entrada: Devolución Feria", False
        else:
            return "Salida: Feria del Libro (FIL)", False

    # Regla 2: Obsequios y Donaciones
    if "OBS" in d_text or "DONA" in d_text or "OBSEQUIO" in d_text or \
       "OBS" in r_text or "DONA" in r_text or "OBSEQUIO" in r_text or \
       "OBS" in a_text or "DONA" in a_text:
        return "Salida: Obsequios y Donaciones", False

    # Regla 3: Ventas
    if "VENTA" in d_text or "VENTA" in r_text:
        return "Salida: Ventas", False

    # Regla 4: Consignaciones
    if "CONSIG" in d_text or "CONIG" in d_text or "CONSIG" in r_text or "CONIG" in r_text or "CONSIG" in a_text or "CONIG" in a_text:
        return "Salida: Consignación", False

    # Regla 5: Resolver Área con Catálogo Maestro + Fuzzy Match
    if a_text.strip():
        return _resolver_area_con_catalogo(a_text, db)
        
    # Si todo falla, y es un ingreso puro
    if ing > 0 and sal == 0:
        return "Entrada: Inventario / Compra", False

    # Si todo falla y no hay pistas → HIL
    return "Desconocido / Sin Asignar", True
