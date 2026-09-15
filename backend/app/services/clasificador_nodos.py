from typing import Tuple, Optional

def clasificar_nodo_movimiento(detalle: Optional[str], ref: Optional[str], area: Optional[str], ingreso: Optional[int], salida: Optional[int]) -> Tuple[str, bool]:
    """
    Motor Heurístico de Clasificación de Nodos para Teoría de Grafos.
    Retorna: (nombre_del_nodo, requiere_auditoria_hil)
    """
    d_text = (detalle or "").upper()
    r_text = (ref or "").upper()
    a_text = (area or "").upper()
    
    ing = ingreso if ingreso is not None else 0
    sal = salida if salida is not None else 0

    # Regla 1: Ferias (FIL / FERIA)
    if "FIL" in d_text or "FERIA" in d_text or "FIL" in r_text or "FERIA" in r_text:
        # Es una devolución de la feria si dice DEV o si simplemente es un ingreso (las ferias devuelven lo no vendido)
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

    # Fallback al Área si no es ninguna de las operaciones especiales
    if a_text:
        # Asignamos directamente al área física o departamento
        return f"Área: {a_text.strip()}", False
        
    # Si todo falla, y es un ingreso puro, lo marcamos como entrada general (Inventario Inicial o Compra)
    if ing > 0 and sal == 0:
        return "Entrada: Inventario / Compra", False

    # Si todo falla y no hay pistas, lo mandamos al HIL (Auditoría Humana)
    return "Desconocido / Sin Asignar", True
