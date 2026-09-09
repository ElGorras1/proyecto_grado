"""
Pruebas de integración y unidad para el pipeline de OCR/HTR de documentos legacy (OpenCV + TrOCR).

Objetivo:
  Verificar que el andamiaje técnico funcione de punta a punta (carga, preprocesamiento,
  inferencia del transformer y persistencia en DB) sin errores sobre una imagen sintética,
  sin calibrar precisión todavía.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from app.models.legacy import DocumentoLegacy, ExtraccionLegacy
from app.services.legacy_ocr.ocr_engine import ejecutar_ocr
from app.services.legacy_ocr.preprocessing import preprocesar_imagen


def crear_imagen_sintetica(ruta: Path, texto: str = "PRUEBA 123") -> Path:
    """
    Crea una imagen sintética simple con fondo blanco y texto negro usando PIL.
    """
    ancho, alto = 400, 100
    imagen = Image.new("RGB", (ancho, alto), color="white")
    draw = ImageDraw.Draw(imagen)
    draw.text((30, 35), texto, fill="black")
    imagen.save(ruta, format="PNG")
    return ruta


def test_preprocesar_imagen_archivo_inexistente_lanza_error(tmp_path):
    """Verifica que preprocesar un archivo inexistente lance FileNotFoundError."""
    ruta_inexistente = tmp_path / "no_existe.png"
    ruta_salida = tmp_path / "salida.png"

    with pytest.raises(FileNotFoundError, match="No se encontró la imagen"):
        preprocesar_imagen(ruta_inexistente, ruta_salida)


def test_preprocesar_imagen_sintetica(tmp_path):
    """Verifica el preprocesamiento, generación de archivo y cálculo de métricas con OpenCV."""
    img_entrada = tmp_path / "entrada.png"
    img_salida = tmp_path / "salida_binaria.png"

    crear_imagen_sintetica(img_entrada, "KARDEX 2026")

    metricas = preprocesar_imagen(img_entrada, img_salida)

    assert img_salida.exists(), "La imagen de salida binarizada debe haber sido creada."
    assert "ancho" in metricas and metricas["ancho"] == 400
    assert "alto" in metricas and metricas["alto"] == 100
    assert "angulo_correccion" in metricas
    assert isinstance(metricas["angulo_correccion"], float)
    assert "tiempo_procesamiento" in metricas
    assert metricas["tiempo_procesamiento"] > 0


def test_pipeline_legacy_ocr_end_to_end_sintetico(tmp_path):
    """
    Verifica que el pipeline completo (OpenCV preproceso + TrOCR inferencia)
    se ejecute sin excepciones sobre una imagen sintética y devuelva texto no vacío.
    (No se valida exactitud del texto, solo funcionalidad técnica de punta a punta).
    """
    img_in = tmp_path / "doc_prueba.png"
    img_prep = tmp_path / "doc_prueba_bin.png"

    crear_imagen_sintetica(img_in, "PRUEBA 123")

    # 1. Preprocesamiento OpenCV
    metricas = preprocesar_imagen(img_in, img_prep)
    assert img_prep.exists()
    assert metricas["ancho"] > 0

    # 2. Inferencia TrOCR
    resultado = ejecutar_ocr(img_prep)

    assert isinstance(resultado, dict)
    assert "texto" in resultado
    assert "confianza" in resultado
    assert "tiempo_segundos" in resultado

    # El andamiaje debe devolver texto no vacío y confianza válida [0.0, 1.0]
    assert isinstance(resultado["texto"], str)
    assert len(resultado["texto"]) > 0, "TrOCR debe devolver una cadena de texto no vacía."
    assert 0.0 <= resultado["confianza"] <= 1.0
    assert resultado["tiempo_segundos"] > 0


def test_persistencia_documento_y_extraccion_legacy(db_session, tmp_path):
    """
    Verifica que los modelos DocumentoLegacy y ExtraccionLegacy
    puedan registrarse y persistir en la base de datos con los datos generados por el pipeline.
    """
    img_in = tmp_path / "doc_kardex_001.png"
    img_prep = tmp_path / "doc_kardex_001_bin.png"
    crear_imagen_sintetica(img_in, "ACTIVO 987")

    metricas = preprocesar_imagen(img_in, img_prep)
    resultado = ejecutar_ocr(img_prep)

    # Crear DocumentoLegacy
    doc = DocumentoLegacy(
        codigo_documento="LEGACY-TEST-001",
        periodo_documental="1970-1980",
        ruta_original=str(img_in),
        checksum_original="fakechecksum123456",
        estado="historico",
        observacion="Documento de prueba sintética",
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    assert doc.id is not None
    assert doc.codigo_documento == "LEGACY-TEST-001"

    # Crear ExtraccionLegacy vinculada
    extraccion = ExtraccionLegacy(
        documento_legacy_id=doc.id,
        motor="TrOCR",
        modelo_version="microsoft/trocr-base-handwritten",
        texto_extraido=resultado["texto"],
        confianza_global=resultado["confianza"],
        procesado_at=datetime.now(UTC),
        estado="activo",
        observacion=f"Prep deskew: {metricas['angulo_correccion']}°",
    )
    db_session.add(extraccion)
    db_session.commit()
    db_session.refresh(extraccion)

    assert extraccion.id is not None
    assert extraccion.documento_legacy_id == doc.id
    assert extraccion.motor == "TrOCR"
    assert extraccion.texto_extraido == resultado["texto"]
    assert float(extraccion.confianza_global) == pytest.approx(resultado["confianza"], rel=1e-4)
