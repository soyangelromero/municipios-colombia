"""Nombres de período con notación ISO 8601 (ver docs/modelo-de-datos.md)."""


def anual(anio: int, ultimo_mes: int = 12) -> str:
    """Año completo ('2025') o acumulado parcial del año ('2026-01/2026-06')."""
    if not 1 <= ultimo_mes <= 12:
        raise ValueError(f"Mes inválido: {ultimo_mes}")
    return str(anio) if ultimo_mes == 12 else f"{anio}-01/{anio}-{ultimo_mes:02d}"
