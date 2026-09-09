"""
Motor OCR/HTR basado en TrOCR (VisionEncoderDecoderModel de HuggingFace) para texto manuscrito.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from PIL import Image

# Variables de caché global para singleton del modelo y procesador
_MODELO_CACHE: Any = None
_PROCESSOR_CACHE: Any = None
_MODELO_NOMBRE_ACTUAL: str | None = None

DEFAULT_MODELO = "microsoft/trocr-base-handwritten"


def cargar_modelo_trocr(nombre_modelo: str = DEFAULT_MODELO) -> tuple[Any, Any]:
    """
    Carga y cachea en memoria el procesador y modelo TrOCR de HuggingFace.
    Si ya fue cargado previamente con el mismo identificador, devuelve las instancias en caché.

    Parámetros:
      - nombre_modelo: Identificador del modelo en HuggingFace Hub.

    Retorna:
      tuple[TrOCRProcessor, VisionEncoderDecoderModel]
    """
    global _MODELO_CACHE, _PROCESSOR_CACHE, _MODELO_NOMBRE_ACTUAL

    if (
        _MODELO_CACHE is not None
        and _PROCESSOR_CACHE is not None
        and _MODELO_NOMBRE_ACTUAL == nombre_modelo
    ):
        return _PROCESSOR_CACHE, _MODELO_CACHE

    try:
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    except ImportError as exc:
        raise ImportError(
            "Las librerías 'torch' y 'transformers' son requeridas para ejecutar TrOCR. "
            "Instálalas en tu entorno virtual."
        ) from exc

    try:
        processor = TrOCRProcessor.from_pretrained(nombre_modelo)
    except Exception:
        # En modelos TrOCR basados en RoBERTa (como microsoft/trocr-base-handwritten) donde no
        # se incluye tokenizer.json unificado para el backend Fast de transformers 5+,
        # se inicializa de forma explícita y robusta con RobertaTokenizer y AutoImageProcessor.
        from transformers import AutoImageProcessor, RobertaTokenizer

        tokenizer = RobertaTokenizer.from_pretrained(nombre_modelo)
        image_processor = AutoImageProcessor.from_pretrained(nombre_modelo)
        processor = TrOCRProcessor(image_processor=image_processor, tokenizer=tokenizer)

    model = VisionEncoderDecoderModel.from_pretrained(nombre_modelo)
    model.eval()

    _PROCESSOR_CACHE = processor
    _MODELO_CACHE = model
    _MODELO_NOMBRE_ACTUAL = nombre_modelo

    return _PROCESSOR_CACHE, _MODELO_CACHE


def ejecutar_ocr(
    ruta_imagen: str | Path,
    nombre_modelo: str = DEFAULT_MODELO,
) -> dict[str, Any]:
    """
    Ejecuta el reconocimiento óptico de caracteres / texto manuscrito (OCR/HTR) sobre una imagen.

    Cálculo del score de confianza:
      TrOCR es un modelo autorregresivo encoder-decoder (ViT + RoBERTa decoder). Durante
      la generación autorregresiva (model.generate), para cada token generado en el paso t,
      el decodificador emite un vector de logits sobre el vocabulario.
      1. Aplicamos softmax sobre los logits de cada paso t para obtener la distribución
         de probabilidades condicionales P(y_t | y_{<t}, x).
      2. Tomamos la probabilidad asignada a la predicción con mayor verosimilitud: max(P(y_t)).
      3. Calculamos la media de estas probabilidades sobre la longitud generada (T):
             confianza = (1 / T) * sum_{t=1}^T max(P(y_t))
         Si la secuencia generada está vacía, la confianza es 0.0.
      Este valor provee un indicador de certidumbre acotado en el intervalo [0.0, 1.0].

    Parámetros:
      - ruta_imagen: Ruta a la imagen a transcribir.
      - nombre_modelo: Identificador del modelo TrOCR a emplear.

    Retorna:
      dict con:
        - "texto": Texto reconocido decodificado (str).
        - "confianza": Promedio de probabilidad de los tokens predichos [0.0, 1.0] (float).
        - "tiempo_segundos": Duración de la inferencia en segundos (float).
    """
    ruta = Path(ruta_imagen)
    if not ruta.exists() or not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el archivo de imagen en: {ruta_imagen}")

    t_inicio = time.perf_counter()

    try:
        imagen = Image.open(str(ruta)).convert("RGB")
    except Exception as exc:
        raise ValueError(f"No se pudo abrir la imagen '{ruta_imagen}': {exc}") from exc

    import torch

    processor, model = cargar_modelo_trocr(nombre_modelo)

    # Preprocesamiento de tensores de imagen para el Vision Transformer
    pixel_values = processor(imagen, return_tensors="pt").pixel_values

    # Generación autorregresiva con retención de logits para cálculo de confianza
    with torch.no_grad():
        outputs = model.generate(
            pixel_values,
            max_new_tokens=64,
            return_dict_in_generate=True,
            output_scores=True,
        )

    # Decodificación del texto predicho
    generated_ids = outputs.sequences
    texto = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

    # Cálculo de la confianza global documentado
    confianza = 0.0
    if outputs.scores and len(outputs.scores) > 0:
        probabilidades_pasos = []
        for step_logits in outputs.scores:
            # step_logits tiene dimensión [batch_size, vocab_size]
            probabilidades = torch.softmax(step_logits, dim=-1)
            prob_max = torch.max(probabilidades, dim=-1).values.item()
            probabilidades_pasos.append(prob_max)

        if probabilidades_pasos:
            confianza = sum(probabilidades_pasos) / len(probabilidades_pasos)

    tiempo_segundos = time.perf_counter() - t_inicio

    return {
        "texto": texto,
        "confianza": round(float(confianza), 5),
        "tiempo_segundos": round(float(tiempo_segundos), 4),
    }
