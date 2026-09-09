"""
Módulo de OCR/HTR y preprocesamiento de imágenes para documentos históricos (Kardex).
"""

from app.services.legacy_ocr.ocr_engine import cargar_modelo_trocr, ejecutar_ocr
from app.services.legacy_ocr.preprocessing import preprocesar_imagen

__all__ = ["preprocesar_imagen", "cargar_modelo_trocr", "ejecutar_ocr"]
