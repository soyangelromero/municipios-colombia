"""Silueta de un municipio, sacada de su trazado en el mapa del departamento.

Sirve de fondo en las fichas y tarjetas que no tienen foto con licencia libre. Los mapas se dibujan
con `M x y` absolutos y `l dx dy …` relativos (ver `mapa_svg.trazo`); aquí se leen, se adelgazan
y se reescriben a una escala fija para que pesen poco, sin importar el tamaño del municipio.
"""

import re
from pathlib import Path

LADO = 200  # unidades del lado mayor de la silueta
PUNTOS_MAXIMOS = 450  # en total, entre todos los anillos

_NUMERO = re.compile(r"-?\d+(?:\.\d+)?")


def _anillos(trazo: str) -> list[list[tuple[float, float]]]:
    """Lee `M x y l dx dy … z` (varias veces) y devuelve los anillos en coordenadas absolutas."""
    salida: list[list[tuple[float, float]]] = []
    for pieza in re.split(r"[zZ]", trazo):
        partes = pieza.split("l")
        if not partes[0].strip().startswith("M"):
            continue
        x, y = (float(n) for n in _NUMERO.findall(partes[0])[:2])
        puntos = [(x, y)]
        for bloque in partes[1:]:
            numeros = [float(n) for n in _NUMERO.findall(bloque)]
            for dx, dy in zip(numeros[0::2], numeros[1::2], strict=False):
                x, y = x + dx, y + dy
                puntos.append((x, y))
        if len(puntos) >= 3:
            salida.append(puntos)
    return salida


def _trazo_de(svg: str, codigo: str) -> str | None:
    coincidencia = re.search(rf'<path id="e-{re.escape(codigo)}"[^>]*? d="([^"]+)"', svg)
    return coincidencia.group(1) if coincidencia else None


def silueta(svg_departamento: str, codigo: str) -> str | None:
    """SVG de la silueta del municipio `codigo`, o None si no está en el mapa."""
    trazo = _trazo_de(svg_departamento, codigo)
    anillos = _anillos(trazo) if trazo else []
    if not anillos:
        return None
    total = sum(len(a) for a in anillos)
    paso = max(1, -(-total // PUNTOS_MAXIMOS))  # techo de la división
    anillos = [a[::paso] if len(a) > 8 else a for a in anillos]
    xs = [x for a in anillos for x, _ in a]
    ys = [y for a in anillos for _, y in a]
    x0, y0 = min(xs), min(ys)
    ancho, alto = max(xs) - x0, max(ys) - y0
    escala = LADO / max(ancho, alto, 1e-9)
    caminos = []
    for anillo in anillos:
        puntos = [f"{round((x - x0) * escala)} {round((y - y0) * escala)}" for x, y in anillo]
        caminos.append("M" + "L".join(puntos) + "z")
    return (
        f'<svg class="silueta" viewBox="0 0 {round(ancho * escala)} {round(alto * escala)}" '
        'aria-hidden="true" focusable="false"><path fill-rule="evenodd" d="'
        + "".join(caminos)
        + '"/></svg>'
    )


class Siluetas:
    """Lee cada mapa departamental una sola vez."""

    def __init__(self, dir_mapas: Path) -> None:
        self.dir_mapas = dir_mapas
        self._svg: dict[str, str] = {}

    def de(self, departamento_slug: str, codigo: str) -> str | None:
        if departamento_slug not in self._svg:
            ruta = self.dir_mapas / f"{departamento_slug}.svg"
            self._svg[departamento_slug] = ruta.read_text("utf-8") if ruta.exists() else ""
        return silueta(self._svg[departamento_slug], codigo)
