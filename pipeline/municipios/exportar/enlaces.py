"""Revisa los enlaces internos de dist/: cada href/src relativo debe apuntar a algo que exista.

Comprueba archivos, carpetas con index.html y anclas (`#id`) dentro de las páginas del sitio.
Los enlaces externos, `mailto:` y `javascript:` no se tocan (no hay red en esta revisión).
"""

import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

# Anclas que abren una historia (`#departamento--municipio` o `#<código DANE>`), no un id del HTML.
HISTORIA = re.compile(r"[0-9a-z-]+--[0-9a-z-]+|\d{5}")
EXTERNOS = ("http:", "https:", "mailto:", "tel:", "javascript:", "data:", "//")


class _Lector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.enlaces: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, atributos: list[tuple[str, str | None]]) -> None:
        for nombre, valor in atributos:
            if valor is None:
                continue
            if nombre == "id":
                self.ids.add(valor)
            elif nombre in ("href", "src") and tag != "base":
                self.enlaces.append(valor)
            elif nombre == "srcset":
                self.enlaces += [p.strip().split()[0] for p in valor.split(",") if p.strip()]


def _leer(ruta: Path) -> _Lector:
    lector = _Lector()
    lector.feed(ruta.read_text(encoding="utf-8", errors="replace"))
    return lector


def _destino(pagina: Path, raiz: Path, enlace: str) -> Path | None:
    """Archivo al que apunta el enlace (None si no es interno)."""
    if enlace.startswith(EXTERNOS):
        return None
    ruta = unquote(urlsplit(enlace).path)
    if ruta == "":
        return pagina
    base = raiz if ruta.startswith("/") else pagina.parent
    destino = (base / ruta.lstrip("/")).resolve()
    return destino / "index.html" if destino.is_dir() else destino


def revisar(raiz: Path) -> list[tuple[str, str, str]]:
    """Devuelve (página, enlace, motivo) por cada enlace roto de dist/."""
    raiz = raiz.resolve()
    rotos: list[tuple[str, str, str]] = []
    ids: dict[Path, set[str]] = {}
    vistos: dict[tuple[Path, str], str | None] = {}
    paginas = [p for p in raiz.rglob("*.html") if p.name != "index.html" or "mapas" not in p.parts]
    por_destino: dict[Path, list[tuple[Path, str]]] = defaultdict(list)
    for pagina in paginas:
        lector = _leer(pagina)
        ids[pagina.resolve()] = lector.ids
        for enlace in lector.enlaces:
            if enlace.startswith(EXTERNOS):
                continue
            por_destino[pagina.resolve()].append((pagina, enlace))
    for origen, lista in por_destino.items():
        for pagina, enlace in lista:
            clave = (origen, enlace)
            if clave in vistos:
                continue
            vistos[clave] = None
            destino = _destino(origen, raiz, enlace)
            if destino is None:
                continue
            nombre = str(pagina.relative_to(raiz)).replace("\\", "/")
            if not destino.exists():
                rotos.append((nombre, enlace, "no existe"))
                continue
            ancla = unquote(urlsplit(enlace).fragment)
            if ancla and destino.suffix == ".html":
                if destino not in ids:
                    ids[destino] = _leer(destino).ids
                if ancla not in ids[destino] and not HISTORIA.fullmatch(ancla):
                    rotos.append((nombre, enlace, "el ancla no existe"))
    return sorted(set(rotos))
