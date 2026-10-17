"""Arma el sitio publicable en dist/: copia web/ (CSS, JS, imágenes, PHP) y genera las páginas.

dist/ no se versiona: es lo que se sube a GitHub Pages o a cualquier hosting.
"""

import logging
import shutil
from html import escape
from pathlib import Path

from municipios.exportar import paginas
from municipios.exportar.datos_web import DIR_FOTOS, DatosSitio, exportar
from municipios.exportar.plantillas import Pagina, documento

log = logging.getLogger(__name__)


# Página activa en la navegación, según la primera parte de la ruta.
def _escribir(destino: Path, pagina: Pagina, sitio: dict) -> None:
    ruta = destino / (
        pagina.ruta + "index.html" if pagina.ruta.endswith("/") or not pagina.ruta else pagina.ruta
    )
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(documento(pagina, sitio), encoding="utf-8")


def construir(datos: DatosSitio, dir_web: Path, destino: Path) -> int:
    """Genera dist/ completo y devuelve el número de páginas escritas."""
    destino.mkdir(parents=True, exist_ok=True)
    for viejo in ("m", "d"):  # fichas de municipios que ya no existan no deben quedar publicadas
        shutil.rmtree(destino / viejo, ignore_errors=True)
    shutil.copytree(dir_web, destino, dirs_exist_ok=True)
    exportar(datos, destino / "data")
    _copiar_fotos(datos, destino / "assets" / "fotos")

    dir_mapas = destino / "data" / "mapas"
    lista = [
        paginas.inicio(datos, dir_mapas),
        paginas.ranking(datos),
        paginas.comparar(datos),
        paginas.metodologia(datos),
        paginas.fuentes(datos),
        paginas.acerca(datos),
        paginas.no_encontrada(datos),
        *(paginas.departamento(datos, cod, dir_mapas) for cod in datos.por_departamento()),
        *(paginas.ficha(datos, codigo, dir_mapas) for codigo in datos.municipios),
    ]
    for pagina in lista:
        _escribir(destino, pagina, datos.sitio)

    _sitemap(destino, [p.ruta for p in lista if p.ruta != "404.html"], datos.sitio)
    (destino / ".nojekyll").write_text("", encoding="utf-8")  # GitHub Pages: servir tal cual
    log.info("Sitio: %d páginas → %s", len(lista), destino)
    return len(lista)


def _copiar_fotos(datos: DatosSitio, destino: Path) -> None:
    shutil.rmtree(destino, ignore_errors=True)
    destino.mkdir(parents=True)
    for codigo in datos.fotos:
        for archivo in DIR_FOTOS.glob(f"{codigo}-*.webp"):
            shutil.copy2(archivo, destino / archivo.name)


def _sitemap(destino: Path, rutas: list[str], sitio: dict) -> None:
    base = sitio["url_base"]
    urls = "".join(
        f"<url><loc>{escape(base + r)}</loc><lastmod>{sitio['actualizado'][:10]}</lastmod></url>"
        for r in rutas
    )
    (destino / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n',
        encoding="utf-8",
    )
    (destino / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: {base}sitemap.xml\n", encoding="utf-8"
    )
