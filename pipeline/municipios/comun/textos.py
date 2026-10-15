"""Normalización de textos: slugs para URL y nombres legibles a partir de los oficiales."""

import re
import unicodedata

# Palabras que van en minúscula dentro de un nombre propio («San Andrés de Tumaco»).
CONECTORES = frozenset({"a", "de", "del", "e", "el", "en", "la", "las", "los", "y"})

_PALABRA = re.compile(r"[^\W\d_]+(?:\.[^\W\d_]+)*\.?")
_SIGLA_CON_PUNTOS = re.compile(r"^(?:[^\W\d_]\.)+$")


def sin_tildes(texto: str) -> str:
    """Quita tildes y diéresis; la ñ pasa a n."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def slug(texto: str) -> str:
    """'El Carmen de Viboral' -> 'el-carmen-de-viboral'."""
    base = sin_tildes(texto).lower()
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


def nombre_legible(oficial: str) -> str:
    """'SAN ANDRÉS DE TUMACO' -> 'San Andrés de Tumaco'; 'BOGOTÁ, D.C.' -> 'Bogotá, D.C.'."""
    texto = " ".join(oficial.split()).lower()

    def formatear(m: re.Match[str]) -> str:
        palabra = m.group(0)
        if _SIGLA_CON_PUNTOS.match(palabra):
            return palabra.upper()
        if m.start() > 0 and palabra in CONECTORES:
            return palabra
        return palabra[0].upper() + palabra[1:]

    return _PALABRA.sub(formatear, texto)
