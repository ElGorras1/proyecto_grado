"""Límites de una gestión institucional según el calendario de Bolivia."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def limites_gestion(gestion: int) -> tuple[datetime, datetime]:
    zona = ZoneInfo("America/La_Paz")
    return (
        datetime(gestion, 1, 1, tzinfo=zona).astimezone(UTC),
        datetime(gestion + 1, 1, 1, tzinfo=zona).astimezone(UTC),
    )
