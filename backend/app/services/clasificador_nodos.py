from dataclasses import dataclass
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session
from thefuzz import fuzz

logger = logging.getLogger(__name__)

UMBRAL_FUZZY = 80

AREA_RESUELTA_AUTOMATICAMENTE = "RESUELTA_AUTOMATICAMENTE"
AREA_RESUELTA_POR_HUMANO = "RESUELTA_POR_HUMANO"
AREA_SIN_REGISTRAR = "SIN_AREA_REGISTRADA"
AREA_NO_CATALOGADA = "AREA_NO_CATALOGADA"
AREA_PENDIENTE_HIL = "PENDIENTE_HIL"
AREA_NO_APLICA = "NO_APLICA"

REFERENCIA_PRESENTE = "PRESENTE"
REFERENCIA_AUSENTE = "AUSENTE"
REFERENCIA_ILEGIBLE = "ILEGIBLE"
REFERENCIA_INCIERTA = "INCIERTA"

NODO_ORIGEN_NO_ESPECIFICADO = "Origen no especificado"
NODO_DESTINO_NO_ESPECIFICADO = "Destino no especificado"
NODO_AREA_NO_CATALOGADA = "Área no catalogada"
NODO_PENDIENTE_CLASIFICACION = "Pendiente de clasificación"

NODOS_LEGACY_NO_RESUELTOS = frozenset(
    {
        "Desconocido / Sin Asignar",
        "Sin catalogar",
        "Área: Sin asignar",
        "Área: Sin catalogar",
    }
)

ESTADOS_AREA_PENDIENTES = frozenset({AREA_NO_CATALOGADA, AREA_PENDIENTE_HIL})
ESTADOS_REFERENCIA_PENDIENTES = frozenset({REFERENCIA_ILEGIBLE, REFERENCIA_INCIERTA})


@dataclass(frozen=True)
class ClasificacionMovimiento:
    nodo_grafo: str
    area_estado: str
    referencia_estado: str
    requiere_auditoria_nodo: bool
    requiere_auditoria_referencia: bool


def _texto_normalizado(valor: str | None) -> str:
    return (valor or "").strip()


def _parece_ilegible(texto: str) -> bool:
    if not texto:
        return False
    if "�" in texto:
        return True
    return not any(caracter.isalnum() for caracter in texto)


def clasificar_estado_referencia(referencia: str | None) -> tuple[str, bool]:
    texto = _texto_normalizado(referencia)
    if not texto or texto.upper() in {"-", "--", "N/A", "S/R", "SIN REF"}:
        return REFERENCIA_AUSENTE, False
    if _parece_ilegible(texto):
        return REFERENCIA_ILEGIBLE, True

    caracteres_utiles = sum(caracter.isalnum() for caracter in texto)
    if caracteres_utiles / len(texto) < 0.35:
        return REFERENCIA_INCIERTA, True
    return REFERENCIA_PRESENTE, False


def normalizar_nodo_grafo(
    nodo: str | None,
    ingresos: int = 0,
    salidas: int = 0,
) -> tuple[str, bool]:
    """Normaliza valores antiguos sin convertirlos en una ubicación real."""
    valor = _texto_normalizado(nodo)
    if valor and valor not in NODOS_LEGACY_NO_RESUELTOS:
        return valor, valor in {
            NODO_AREA_NO_CATALOGADA,
            NODO_PENDIENTE_CLASIFICACION,
        }

    if salidas > 0 and ingresos == 0:
        return NODO_DESTINO_NO_ESPECIFICADO, False
    if ingresos > 0 and salidas == 0:
        return NODO_ORIGEN_NO_ESPECIFICADO, False
    return NODO_PENDIENTE_CLASIFICACION, True


def estado_area_para_nodo_manual(nodo: str) -> tuple[str, bool]:
    if nodo in {NODO_ORIGEN_NO_ESPECIFICADO, NODO_DESTINO_NO_ESPECIFICADO}:
        return AREA_SIN_REGISTRAR, False
    if nodo == NODO_AREA_NO_CATALOGADA:
        return AREA_NO_CATALOGADA, True
    if nodo == NODO_PENDIENTE_CLASIFICACION:
        return AREA_PENDIENTE_HIL, True
    return AREA_RESUELTA_POR_HUMANO, False


def _clasificar_operacion(
    detalle: str,
    referencia: str,
    area: str,
    ingreso: int,
) -> str | None:
    if any(marca in texto for marca in ("FIL", "FERIA") for texto in (detalle, referencia)):
        if "DEV" in referencia or "DEV" in detalle or ingreso > 0:
            return "Entrada: Devolución Feria"
        return "Salida: Feria del Libro (FIL)"

    if any(
        marca in texto
        for marca in ("OBS", "DONA", "OBSEQUIO")
        for texto in (detalle, referencia, area)
    ):
        return "Salida: Obsequios y Donaciones"

    if "VENTA" in detalle or "VENTA" in referencia:
        return "Salida: Ventas"

    if any(
        marca in texto for marca in ("CONSIG", "CONIG") for texto in (detalle, referencia, area)
    ):
        return "Salida: Consignación"
    return None


def _clasificar_entrada_catalogo(
    nombre: str,
    tipo: str,
    confirmado: bool,
    ingreso: int,
    salida: int,
) -> tuple[str, str, bool]:
    """El tipo del catálogo determina el nodo; una operación no es una unidad."""
    if tipo == "departamento":
        return (f"Área: {nombre}",
                AREA_RESUELTA_AUTOMATICAMENTE if confirmado else AREA_PENDIENTE_HIL,
                not confirmado)
    if tipo != "operacion":
        return NODO_PENDIENTE_CLASIFICACION, AREA_PENDIENTE_HIL, True

    operaciones = {
        "Ventas": ("Salida: Ventas", "salida"),
        "Obsequios y Donaciones": ("Salida: Obsequios y Donaciones", "salida"),
        "Consignación": ("Salida: Consignación", "salida"),
        "Inventario / Compra": ("Entrada: Inventario / Compra", "ingreso"),
        "Baja / Pérdida": ("Salida: Baja / Pérdida", "salida"),
        "Salida a Feria": ("Salida: Feria del Libro (FIL)", "salida"),
    }
    nodo, direccion = operaciones.get(nombre, (nombre, None))
    if ((direccion == "salida" and not (salida > 0 and ingreso == 0))
            or (direccion == "ingreso" and not (ingreso > 0 and salida == 0))):
        return NODO_PENDIENTE_CLASIFICACION, AREA_PENDIENTE_HIL, True
    return nodo, AREA_NO_APLICA if confirmado else AREA_PENDIENTE_HIL, not confirmado


def _resolver_area_con_catalogo(
    area_texto: str,
    db: Session | None,
    ingreso: int = 0,
    salida: int = 0,
) -> tuple[str, str, bool]:
    texto_area = area_texto.strip().upper()
    if _parece_ilegible(texto_area):
        return NODO_PENDIENTE_CLASIFICACION, AREA_PENDIENTE_HIL, True
    if not db:
        return NODO_AREA_NO_CATALOGADA, AREA_NO_CATALOGADA, True

    try:
        coincidencia = db.execute(
            text(
                """
                SELECT nombre_oficial, tipo
                FROM catalogo_areas
                WHERE UPPER(nombre_oficial) = :texto
                   OR UPPER(abreviatura) = :texto
                """
            ),
            {"texto": texto_area},
        ).fetchone()
        if coincidencia:
            return _clasificar_entrada_catalogo(
                coincidencia[0], coincidencia[1], True, ingreso, salida,
            )

        coincidencia = db.execute(
            text(
                """
                SELECT ca.nombre_oficial, sa.confirmado, ca.tipo, sa.activa
                FROM sinonimos_area sa
                JOIN catalogo_areas ca ON sa.area_oficial_id = ca.id
                WHERE UPPER(sa.texto_sucio) = :texto
                """
            ),
            {"texto": texto_area},
        ).fetchone()
        if coincidencia:
            if not coincidencia[3]:
                return NODO_PENDIENTE_CLASIFICACION, AREA_PENDIENTE_HIL, True
            confirmado = bool(coincidencia[1])
            return _clasificar_entrada_catalogo(
                coincidencia[0], coincidencia[2], confirmado, ingreso, salida,
            )

        areas = db.execute(
            text("SELECT id, nombre_oficial, abreviatura, tipo FROM catalogo_areas")
        ).fetchall()
        mejor_score = 0
        mejor_area = None
        mejor_id = None
        mejor_tipo = None

        for area_id, nombre, abreviatura, tipo in areas:
            score_nombre = fuzz.ratio(texto_area, nombre.upper())
            score_abreviatura = fuzz.ratio(texto_area, abreviatura.upper()) if abreviatura else 0
            score = max(score_nombre, score_abreviatura)
            if score > mejor_score:
                mejor_score = score
                mejor_area = nombre
                mejor_id = area_id
                mejor_tipo = tipo

        if mejor_score >= UMBRAL_FUZZY:
            try:
                with db.begin_nested():
                    db.execute(
                        text(
                            """
                            INSERT INTO sinonimos_area
                                (texto_sucio, area_oficial_id, confirmado)
                            VALUES (:texto, :area_id, FALSE)
                            ON CONFLICT (texto_sucio) DO NOTHING
                            """
                        ),
                        {"texto": texto_area, "area_id": mejor_id},
                    )
            except Exception as exc:
                logger.warning("No se guardó la sugerencia de área; requiere revisión (%s)", type(exc).__name__)
            return _clasificar_entrada_catalogo(
                mejor_area, mejor_tipo, False, ingreso, salida,
            )

        return NODO_AREA_NO_CATALOGADA, AREA_NO_CATALOGADA, True
    except Exception as exc:
        logger.warning("Catálogo de áreas no disponible; clasificación pendiente HIL (%s)", type(exc).__name__)
        return NODO_PENDIENTE_CLASIFICACION, AREA_PENDIENTE_HIL, True


def clasificar_movimiento(
    detalle: str | None,
    ref: str | None,
    area: str | None,
    ingreso: int | None,
    salida: int | None,
    db: Session | None = None,
) -> ClasificacionMovimiento:
    detalle_normalizado = _texto_normalizado(detalle).upper()
    referencia_normalizada = _texto_normalizado(ref).upper()
    area_normalizada = _texto_normalizado(area).upper()
    cantidad_ingreso = ingreso or 0
    cantidad_salida = salida or 0
    referencia_estado, auditoria_referencia = clasificar_estado_referencia(ref)

    nodo_operacion = _clasificar_operacion(
        detalle_normalizado,
        referencia_normalizada,
        area_normalizada,
        cantidad_ingreso,
    )
    if nodo_operacion:
        return ClasificacionMovimiento(
            nodo_grafo=nodo_operacion,
            area_estado=AREA_NO_APLICA,
            referencia_estado=referencia_estado,
            requiere_auditoria_nodo=False,
            requiere_auditoria_referencia=auditoria_referencia,
        )

    if area_normalizada:
        nodo, area_estado, auditoria_nodo = _resolver_area_con_catalogo(
            area_normalizada,
            db,
            cantidad_ingreso,
            cantidad_salida,
        )
    elif cantidad_salida > 0 and cantidad_ingreso == 0:
        nodo = NODO_DESTINO_NO_ESPECIFICADO
        area_estado = AREA_SIN_REGISTRAR
        auditoria_nodo = False
    elif cantidad_ingreso > 0 and cantidad_salida == 0:
        nodo = NODO_ORIGEN_NO_ESPECIFICADO
        area_estado = AREA_SIN_REGISTRAR
        auditoria_nodo = False
    else:
        nodo = NODO_PENDIENTE_CLASIFICACION
        area_estado = AREA_PENDIENTE_HIL
        auditoria_nodo = True

    return ClasificacionMovimiento(
        nodo_grafo=nodo,
        area_estado=area_estado,
        referencia_estado=referencia_estado,
        requiere_auditoria_nodo=auditoria_nodo,
        requiere_auditoria_referencia=auditoria_referencia,
    )


def clasificar_nodo_movimiento(
    detalle: str | None,
    ref: str | None,
    area: str | None,
    ingreso: int | None,
    salida: int | None,
    db: Session | None = None,
) -> tuple[str, bool]:
    """Compatibilidad temporal para consumidores que solo conocen nodo y HIL."""
    clasificacion = clasificar_movimiento(detalle, ref, area, ingreso, salida, db)
    return clasificacion.nodo_grafo, clasificacion.requiere_auditoria_nodo
