"""
Script CLI para procesar un documento físico del Kardex histórico mediante OpenCV + TrOCR.

Flujo:
  1. Recibe la ruta de la imagen original.
  2. Calcula su checksum SHA-256.
  3. Aplica preprocesamiento (escala de grises, reducción de ruido, deskew, binarización).
  4. Ejecuta el motor TrOCR sobre la imagen preprocesada.
  5. Registra o recupera el documento en `documento_legacy` y guarda la extracción.
  6. Muestra un resumen legible en consola.

Uso:
  python -m scripts.procesar_documento_legacy ruta/a/imagen.png
  python -m scripts.procesar_documento_legacy --imagen ruta/a/imagen.png
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import UTC, datetime
from pathlib import Path

# Asegurar que el directorio raíz de backend esté en sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.append(str(backend_root))

from app.db.session import SessionLocal  # noqa: E402
from app.models.legacy import DocumentoLegacy, ExtraccionLegacy  # noqa: E402
from app.services.legacy_ocr.ocr_engine import DEFAULT_MODELO, ejecutar_ocr  # noqa: E402
from app.services.legacy_ocr.preprocessing import preprocesar_imagen  # noqa: E402


def calcular_sha256(ruta_archivo: Path) -> str:
    """Calcula el hash SHA-256 de un archivo en disco."""
    sha = hashlib.sha256()
    with open(ruta_archivo, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def procesar_documento(
    ruta_imagen: str | Path,
    ruta_salida_preprocesada: str | Path | None = None,
    nombre_modelo: str = DEFAULT_MODELO,
) -> dict:
    """
    Ejecuta el pipeline completo de preprocesamiento, OCR y persistencia en base de datos.
    """
    path_in = Path(ruta_imagen).resolve()
    if not path_in.exists():
        raise FileNotFoundError(f"El archivo de imagen no existe: {path_in}")

    if ruta_salida_preprocesada is None:
        dir_procesadas = backend_root / "storage" / "legacy_processed"
        dir_procesadas.mkdir(parents=True, exist_ok=True)
        path_out = dir_procesadas / f"{path_in.stem}_preprocessed.png"
    else:
        path_out = Path(ruta_salida_preprocesada).resolve()

    # 1. Checksum del archivo original
    checksum = calcular_sha256(path_in)

    # 2. Preprocesamiento OpenCV
    print("\n[1/3] Preprocesando imagen con OpenCV...")
    metricas_prep = preprocesar_imagen(path_in, path_out)
    print(f"      - Dimensiones originales : {metricas_prep['ancho']}x{metricas_prep['alto']} px")
    print(f"      - Ángulo de deskew       : {metricas_prep['angulo_correccion']}°")
    print(f"      - Tiempo preproceso      : {metricas_prep['tiempo_procesamiento']:.4f} s")
    print(f"      - Imagen guardada en     : {path_out}")

    # 3. Reconocimiento OCR con TrOCR
    print(f"\n[2/3] Ejecutando OCR con TrOCR ({nombre_modelo})...")
    resultado_ocr = ejecutar_ocr(path_out, nombre_modelo=nombre_modelo)
    print(f"      - Texto extraído         : \"{resultado_ocr['texto']}\"")
    print(f"      - Confianza estimada     : {resultado_ocr['confianza'] * 100:.2f}%")
    print(f"      - Tiempo inferencia      : {resultado_ocr['tiempo_segundos']:.4f} s")

    # 4. Persistencia en Base de Datos
    print("\n[3/3] Registrando en base de datos...")
    db = SessionLocal()
    try:
        codigo_sugerido = f"DOC-LEGACY-{path_in.stem}"
        doc = (
            db.query(DocumentoLegacy)
            .filter(
                (DocumentoLegacy.checksum_original == checksum)
                | (DocumentoLegacy.codigo_documento == codigo_sugerido)
            )
            .first()
        )

        if doc is None:
            doc = DocumentoLegacy(
                codigo_documento=codigo_sugerido,
                periodo_documental="Historico",
                ruta_original=str(path_in),
                checksum_original=checksum,
                estado="historico",
                observacion="Importado vía pipeline CLI de legacy_ocr",
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            print(f"      - Nuevo DocumentoLegacy creado (ID: {doc.id})")
            print(f"        Código: {doc.codigo_documento}")
        else:
            print(f"      - DocumentoLegacy reutilizado (ID: {doc.id})")
            print(f"        Código: {doc.codigo_documento}")

        extraccion = ExtraccionLegacy(
            documento_legacy_id=doc.id,
            motor="TrOCR",
            modelo_version=nombre_modelo,
            texto_extraido=resultado_ocr["texto"],
            confianza_global=resultado_ocr["confianza"],
            procesado_at=datetime.now(UTC),
            estado="activo",
            observacion=(
                f"Deskew: {metricas_prep['angulo_correccion']}°; "
                f"T_prep: {metricas_prep['tiempo_procesamiento']}s; "
                f"T_ocr: {resultado_ocr['tiempo_segundos']}s"
            ),
        )
        db.add(extraccion)
        db.commit()
        extraccion_id = extraccion.id
        doc_id = doc.id
        doc_codigo = doc.codigo_documento
        texto_guardado = extraccion.texto_extraido
        confianza_guardada = float(extraccion.confianza_global or 0.0)
        print(f"      - Nueva ExtraccionLegacy registrada (ID: {extraccion_id})")

    finally:
        db.close()

    tiempo_total = metricas_prep["tiempo_procesamiento"] + resultado_ocr["tiempo_segundos"]
    print("\n========================================================")
    print("           RESUMEN DE PROCESAMIENTO LEGACY              ")
    print("========================================================")
    print(f" Documento ID        : {doc_id} ({doc_codigo})")
    print(f" Extracción ID       : {extraccion_id}")
    print(f" Texto detectado     : {texto_guardado}")
    print(f" Confianza           : {confianza_guardada * 100:.2f}%")
    print(f" Tiempo total        : {tiempo_total:.4f} s")
    print("========================================================\n")

    return {
        "documento_id": doc_id,
        "extraccion_id": extraccion_id,
        "texto": resultado_ocr["texto"],
        "confianza": resultado_ocr["confianza"],
        "metricas_prep": metricas_prep,
        "tiempo_ocr": resultado_ocr["tiempo_segundos"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Procesa una imagen del Kardex histórico con OpenCV y TrOCR."
    )
    parser.add_argument(
        "imagen_posicional",
        nargs="?",
        help="Ruta a la imagen física a procesar (opcional si se usa --imagen).",
    )
    parser.add_argument(
        "--imagen",
        "-i",
        dest="imagen_flag",
        help="Ruta a la imagen física a procesar.",
    )
    parser.add_argument(
        "--salida-preprocesada",
        "-o",
        dest="salida_preprocesada",
        default=None,
        help="Ruta de guardado para la imagen preprocesada con OpenCV.",
    )
    parser.add_argument(
        "--modelo",
        "-m",
        dest="modelo",
        default=DEFAULT_MODELO,
        help=f"Modelo TrOCR de HuggingFace (por defecto: {DEFAULT_MODELO}).",
    )

    args = parser.parse_args()
    ruta = args.imagen_flag or args.imagen_posicional

    if not ruta:
        parser.print_help()
        sys.exit(1)

    try:
        procesar_documento(
            ruta_imagen=ruta,
            ruta_salida_preprocesada=args.salida_preprocesada,
            nombre_modelo=args.modelo,
        )
    except Exception as exc:
        print(f"\n[ERROR] Falló el procesamiento del documento: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
