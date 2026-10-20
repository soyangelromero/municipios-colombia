"""Formato de números y períodos para mostrar (español de Colombia: 1.234.567,8)."""

import re


def numero(valor: float | int | None, decimales: int = 0) -> str:
    if valor is None:
        return "—"
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def pesos(valor: float | None) -> str:
    """Pesos abreviados: $ 1,2 billones, $ 345 mil millones, $ 1 millón, $ 12 millones."""
    if valor is None:
        return "—"
    if abs(valor) >= 1e12:
        return f"$ {_cantidad(valor / 1e12, 'billón', 'billones')}"
    if abs(valor) >= 1e9:
        return f"$ {numero(valor / 1e9, 0)} mil millones"
    if abs(valor) >= 1e6:
        return f"$ {_cantidad(valor / 1e6, 'millón', 'millones')}"
    return f"$ {numero(valor)}"


def _cantidad(valor: float, singular: str, plural: str) -> str:
    """«1 millón» (singular), «1,4 millones», «12 millones»: un decimal solo por debajo de 10."""
    redondo = round(valor, 1) if abs(valor) < 10 else round(valor)
    if redondo == 1:
        return f"1 {singular}"
    decimales = 1 if abs(valor) < 10 and redondo != int(redondo) else 0
    return f"{numero(redondo, decimales)} {plural}"


def segun_unidad(valor: float | int | str | None, unidad: str) -> str:
    """Formatea un valor de acuerdo con la unidad de su ficha de indicador."""
    if valor is None:
        return "—"
    if isinstance(valor, str):
        return valor
    u = unidad.lower()
    if u == "sí/no":
        return "Sí" if valor >= 50 else "No"
    if "peso" in u:
        return pesos(valor) if "por habitante" not in u else f"$ {numero(valor)}"
    if u.startswith("%") or "porcentaje" in u:
        return f"{numero(valor, 1)} %"
    if "puntos" in u:
        return numero(valor, 1)
    if "100.000" in u:
        return numero(valor, 1)
    if "por km²" in u:
        return f"{numero(valor, 0)} hab./km²"
    if "km²" in u:
        return f"{numero(valor, 0)} km²"
    if float(valor).is_integer():
        return numero(valor)
    return numero(valor, 1)


MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def periodo(texto: str) -> str:
    """Período legible.

    '2026-01/2026-08' -> 'ene-ago 2026'; '2019-S2' -> '2.º sem. 2019'; '2026-10' -> 'oct 2026'.
    """
    if m := re.fullmatch(r"(\d{4})-(\d{2})/\1-(\d{2})", texto):
        return f"{MESES[int(m.group(2)) - 1]}-{MESES[int(m.group(3)) - 1]} {m.group(1)}"
    if m := re.fullmatch(r"(\d{4})-S([12])", texto):
        return f"{m.group(2)}.º sem. {m.group(1)}"
    if m := re.fullmatch(r"(\d{4})-(\d{2})", texto):
        return f"{MESES[int(m.group(2)) - 1]} {m.group(1)}"
    return texto
