"""
Servicio de preprocesamiento de imágenes para documentos históricos (Kardex) usando OpenCV.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def detectar_angulo_inclinacion(gray_img: np.ndarray) -> float:
    """
    Detecta el ángulo dominante de inclinación del texto usando minAreaRect sobre píxeles
    de primer plano. Devuelve el ángulo en grados necesario para rotar y enderezar la imagen.
    """
    # Umbral inverso de Otsu para separar texto del fondo
    _, thresh = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Coordenadas de píxeles no cero (y, x)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 15:
        # Menos de 15 píxeles de texto: considerar sin inclinación
        return 0.0

    coords_xy = np.column_stack([coords[:, 1], coords[:, 0]])
    box = cv2.minAreaRect(coords_xy)
    (w, h) = box[1]
    angle = box[2]

    # Normalización del ángulo según dimensiones del rectángulo mínimo
    if w < h:
        angle = -(90 - angle) if angle > 0 else (angle + 90)
    else:
        angle = angle if angle <= 45 else (angle - 90)

    # Si el ángulo es irrelevante (< 0.1°) o mayor a 45° (no es inclinación típica), descartar
    if abs(angle) < 0.1 or abs(angle) > 45.0:
        return 0.0

    return float(angle)


def deskew_imagen(gray_img: np.ndarray, angulo: float) -> np.ndarray:
    """
    Rota la imagen en escala de grises para corregir la inclinación detectada,
    rellenando los bordes con blanco (255).
    """
    if abs(angulo) < 0.1:
        return gray_img

    (h, w) = gray_img.shape[:2]
    centro = (w // 2, h // 2)
    matriz_rotacion = cv2.getRotationMatrix2D(centro, angulo, 1.0)
    rotada = cv2.warpAffine(
        gray_img,
        matriz_rotacion,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )
    return rotada


def preprocesar_imagen(ruta_entrada: str | Path, ruta_salida: str | Path) -> dict[str, Any]:
    """
    Preprocesa una imagen para optimizar la extracción OCR/HTR:
      1. Valida y carga la imagen con OpenCV.
      2. Convierte a escala de grises.
      3. Aplica reducción de ruido mediante suavizado Gaussiano.
      4. Detecta y corrige inclinación (deskew).
      5. Binariza usando umbralización adaptativa (Gaussian C).
      6. Guarda la imagen resultante en la ruta especificada.
      7. Retorna métricas del procesamiento.

    Parámetros:
      - ruta_entrada: Ruta al archivo de imagen original.
      - ruta_salida: Ruta donde se guardará la imagen preprocesada.

    Retorna:
      dict con: ancho, alto, angulo_correccion, tiempo_procesamiento, tiempo_segundos.
    """
    t_inicio = time.perf_counter()
    ruta_in = Path(ruta_entrada)
    ruta_out = Path(ruta_salida)

    if not ruta_in.exists() or not ruta_in.is_file():
        raise FileNotFoundError(f"No se encontró la imagen en la ruta especificada: {ruta_entrada}")

    # 1. Cargar imagen
    img = cv2.imread(str(ruta_in))
    if img is None:
        raise ValueError(
            "No se pudo cargar o decodificar la imagen "
            f"(formato no soportado o archivo corrupto): {ruta_entrada}"
        )

    alto, ancho = img.shape[:2]

    # 2. Escala de grises
    if len(img.shape) == 3 and img.shape[2] == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif len(img.shape) == 3 and img.shape[2] == 4:
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    else:
        gray = img.copy()

    # 3. Reducción de ruido (filtro Gaussiano suave para preservar contornos)
    denoised = cv2.GaussianBlur(gray, (3, 3), 0)

    # 4. Corrección de inclinación (deskew)
    angulo_detectado = detectar_angulo_inclinacion(denoised)
    deskewed = deskew_imagen(denoised, angulo_detectado)

    # 5. Binarización adaptativa (óptima para papel antiguo con iluminación variable)
    binarizada = cv2.adaptiveThreshold(
        deskewed,
        maxValue=255,
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY,
        blockSize=15,
        C=8,
    )

    # 6. Guardar imagen resultante
    ruta_out.parent.mkdir(parents=True, exist_ok=True)
    guardado_ok = cv2.imwrite(str(ruta_out), binarizada)
    if not guardado_ok:
        raise OSError(f"No se pudo escribir el archivo de imagen de salida en: {ruta_salida}")

    tiempo_total = time.perf_counter() - t_inicio

    return {
        "ancho": int(ancho),
        "alto": int(alto),
        "angulo_correccion": round(float(angulo_detectado), 2),
        "tiempo_procesamiento": round(tiempo_total, 4),
        "tiempo_segundos": round(tiempo_total, 4),
    }
