"""Aligera los mapas SVG antes de incrustarlos en el HTML.

Los trazados salen del pipeline con más vértices de los que se ven en pantalla. Aquí se
vuelven a simplificar (Douglas-Peucker, con tolerancia en unidades del propio SVG) y se
reescriben con coordenadas relativas de un decimal. El mapa se ve igual y pesa mucho menos.
"""

import re

from municipios.comun.geometria import douglas_peucker
from municipios.exportar.silueta import _anillos

_TRAZO = re.compile(r'(<path\b[^>]*?\sd=")([^"]+)(")')


def _numero(valor: float) -> str:
    texto = f"{valor:.1f}".rstrip("0").rstrip(".")
    return "0" if texto in ("-0", "") else texto


def _trazo(d: str, tolerancia: float) -> str:
    anillos = _anillos(d)
    if not anillos:
        return d
    partes: list[str] = []
    for anillo in anillos:
        simple = douglas_peucker(anillo, tolerancia)
        if len(simple) < 3:
            simple = anillo
        x0, y0 = round(simple[0][0], 1), round(simple[0][1], 1)
        partes.append(f"M{_numero(x0)} {_numero(y0)}")
        deltas: list[str] = []
        ax, ay = x0, y0
        for x, y in simple[1:]:
            nx, ny = round(x, 1), round(y, 1)
            deltas.append(f"{_numero(nx - ax)} {_numero(ny - ay)}")
            ax, ay = nx, ny
        partes.append("l" + " ".join(deltas) + "z")
    return "".join(partes)


def aligerar_svg(svg: str, tolerancia: float = 0.4) -> str:
    """Re-simplifica todos los trazados `d="M… l… z"` de un SVG del pipeline."""
    return _TRAZO.sub(lambda m: m.group(1) + _trazo(m.group(2), tolerancia) + m.group(3), svg)
