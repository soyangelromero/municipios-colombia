"""Rastreo de la sección de transparencia: sigue 1 o 2 niveles de enlaces.

La lógica no toca la red: recibe una función `leer(url)` que devuelve los enlaces de una página
(o None si no se pudo o no se debe leer: robots.txt, error, tiempo agotado). Así se prueba con
un sitio ficticio. La red real está en `transparencia.py`.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from municipios.relevamiento.criterios import CRITERIOS, clasificar, secciones_a_abrir

Enlaces = list[tuple[str, str]]
Lector = Callable[[str], Enlaces | None]

PROFUNDIDAD = 2  # niveles de enlaces que se siguen desde el menú de transparencia
MAX_PAGINAS = 6  # páginas adicionales por municipio (tope de cortesía)
MAX_POR_NIVEL = 6


@dataclass
class Hallazgo:
    evidencia: str  # URL del enlace que cumple el criterio
    pagina: str  # página donde estaba el enlace
    nivel: int  # 0 = menú de transparencia; 1 y 2 = secciones que se abrieron


@dataclass
class Rastro:
    encontrados: dict[str, Hallazgo] = field(default_factory=dict)
    paginas_leidas: int = 0  # incluye el menú
    paginas_omitidas: int = 0  # robots.txt, errores o tiempo agotado


def _anotar(rastro: Rastro, enlaces: Enlaces, pagina: str, nivel: int) -> None:
    for criterio, url in clasificar(enlaces).items():
        if url and criterio not in rastro.encontrados:
            rastro.encontrados[criterio] = Hallazgo(url, pagina, nivel)


def rastrear(
    menu: Enlaces,
    pagina_menu: str,
    sitio: str,
    leer: Lector,
    *,
    profundidad: int = PROFUNDIDAD,
    max_paginas: int = MAX_PAGINAS,
    max_por_nivel: int = MAX_POR_NIVEL,
) -> Rastro:
    """Busca los criterios en el menú y, si faltan, en las secciones que podrían tenerlos."""
    rastro = Rastro(paginas_leidas=1)
    _anotar(rastro, menu, pagina_menu, 0)
    visitadas = {pagina_menu.split("#")[0]}
    actuales: Enlaces = list(menu)
    adicionales = 0
    for nivel in range(1, profundidad + 1):
        faltan = {c.id for c in CRITERIOS} - set(rastro.encontrados)
        if not faltan or adicionales >= max_paginas:
            break
        urls = secciones_a_abrir(actuales, sitio, faltan, visitadas, max_por_nivel)
        siguientes: Enlaces = []
        for url in urls:
            if adicionales >= max_paginas:
                break
            adicionales += 1
            visitadas.add(url)
            enlaces = leer(url)
            if enlaces is None:
                rastro.paginas_omitidas += 1
                continue
            rastro.paginas_leidas += 1
            _anotar(rastro, enlaces, url, nivel)
            siguientes.extend(enlaces)
        actuales = siguientes
    return rastro
