"""Reglas puras (sin red) para decidir si una foto de Commons se puede mostrar y cómo citarla."""

import html
import re
from urllib.parse import unquote, urlparse

# Licencias aceptadas: Creative Commons de atribución (con o sin compartir igual), CC0 y dominio
# público. Se descartan las NC (no comercial), ND (sin derivadas), GFDL sola y «uso legítimo».
_LIBRES = (
    r"^CC BY( SA)?( \d(\.\d)?)?( [A-Z]{2,3})?$",
    r"^CC0",
    r"^PUBLIC DOMAIN",
    r"^PD\b",
    r"^CC ZERO",
)


def licencia_libre(nombre: str | None) -> bool:
    """True si `LicenseShortName` de Commons es una licencia libre aceptada."""
    if not nombre:
        return False
    limpio = " ".join(nombre.replace("-", " ").split()).upper()
    if {"NC", "ND"} & set(limpio.split()):
        return False
    return any(re.search(p, limpio) for p in _LIBRES)


def limpiar_html(texto: str | None) -> str:
    """Quita etiquetas y entidades de campos como `Artist` (Commons los entrega en HTML)."""
    if not texto:
        return ""
    sin_etiquetas = re.sub(r"<[^>]+>", " ", texto)
    return " ".join(html.unescape(sin_etiquetas).split())


def nombre_de_archivo(url_commons: str) -> str:
    """'http://commons.wikimedia.org/wiki/Special:FilePath/Casa%20x.JPG' -> 'Casa x.JPG'."""
    return unquote(urlparse(url_commons).path.rsplit("/", 1)[-1])
