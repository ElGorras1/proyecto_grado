import os
import time
from typing import List
from google import genai
from pydantic import ValidationError
from PIL import Image

from app.core.config import settings
from app.schemas.kardex import ExtraccionKardexHoja

# Prompt Maestro basado en los requerimientos del usuario
PROMPT_MAESTRO = """Actúa como un auditor experto en digitalización de kárdex de almacén. 
Tu tarea es extraer la información del artículo y su tabla de movimientos a partir de la imagen adjunta utilizando el modelo gemini-3.5-flash-lite.

REGLAS CRÍTICAS DE EXTRACCIÓN:
1. Identifica el nombre del artículo principal en la parte superior.
2. Extrae todas las filas de la tabla respetando el orden secuencial de arriba hacia abajo.
3. Normaliza rigurosamente todas las fechas al formato estándar YYYY-MM-DD. Si el año tiene formato de dos dígitos como '10', interprétalo como '2010'. Si es '13', como '2013'.
4. Si una celda de la columna 'INGRESOS' o 'SALIDAS' está vacía o contiene una línea horizontal, asígnale el valor null en el JSON.
5. Limpia el texto de la columna 'DETALLE' conservando su significado original, sin alterar nombres de eventos o ferias.
6. Ignora por completo las marcas de verificación manuscritas (checks, firmas) situadas fuera de los límites de las celdas de la tabla.
7. Devuelve la información estrictamente bajo la estructura del esquema JSON solicitado.
"""

def get_genai_client() -> genai.Client:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY no configurada")
    return genai.Client(api_key=api_key)

def procesar_imagen_kardex(imagen_path: str) -> ExtraccionKardexHoja:
    """
    Procesa una única imagen de Kardex llamando a Gemini 3.5 Flash Lite
    y forzando Structured Outputs (JSON Estricto).
    Incluye un mecanismo de reintento automático (Exponential Backoff) 
    para lidiar con el error 429 RESOURCE_EXHAUSTED del Tier Gratuito.
    """
    client = get_genai_client()
    
    if not os.path.exists(imagen_path):
        raise FileNotFoundError(f"Imagen no encontrada en disco: {imagen_path}")
        
    img = Image.open(imagen_path)
    
    max_retries = 3
    base_delay = 32  # Esperamos al menos 32s como pide el error "retry in 29s"
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=[img, PROMPT_MAESTRO],
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtraccionKardexHoja,
                    temperature=0.1
                )
            )
            
            # Parsear y retornar el objeto estructurado
            return ExtraccionKardexHoja.model_validate_json(response.text)
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Se excedió la cuota de la API después de {max_retries} intentos. Espera unos minutos antes de volver a escanear.")
                print(f"⚠️ Cuota excedida (429). La IA está descansando... reintentando en {base_delay}s (Intento {attempt + 1}/{max_retries})")
                time.sleep(base_delay)
                base_delay *= 2  # Exponential backoff (32s, 64s, 128s...)
            else:
                # Si es un error de validación u otro tipo, lo lanzamos directamente
                if isinstance(e, ValidationError):
                    raise ValueError(f"El LLM devolvió un JSON con esquema inválido: {e}")
                raise e

def procesar_lote_imagenes(imagenes_paths: List[str]) -> List[ExtraccionKardexHoja]:
    """
    Procesa un lote de N imágenes respetando el Free Tier rate limit.
    Aplica Throttling (ej. 4 segundos de pausa) para no chocar con las 15 RPM.
    """
    resultados = []
    for i, path in enumerate(imagenes_paths):
        resultado = procesar_imagen_kardex(path)
        resultados.append(resultado)
        
        # Throttling preventivo más conservador (6 segundos -> 10 RPM max)
        if i < len(imagenes_paths) - 1:
            time.sleep(6.0)
            
    return resultados
