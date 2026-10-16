"""Descubre y descarga la foto de cada municipio.

1. Wikidata (SPARQL): el código DANE (P7325) y la imagen principal (P18) de cada municipio.
2. Commons (API): licencia, autor y miniatura de cada imagen. Solo pasan las licencias libres.
3. Se guardan dos WebP por municipio (480 y 1080 px de ancho) y un CSV con el crédito.

Las fotos y `fotos.csv` se versionan (datos/fotos/): el despliegue no depende de la red.
"""

import csv
import io
import logging
import time
from datetime import date
from pathlib import Path
from urllib.parse import quote

from PIL import Image
from scrapling.fetchers import Fetcher

from municipios.fotos.licencias import licencia_libre, limpiar_html, nombre_de_archivo

log = logging.getLogger(__name__)

AGENTE = "MunicipiosColombiaBot/0.1 (+https://github.com/soyangelromero/municipios-colombia)"
URL_SPARQL = "https://query.wikidata.org/sparql"
URL_COMMONS = "https://commons.wikimedia.org/w/api.php"
CONSULTA = """
SELECT ?dane ?img WHERE {
  ?m wdt:P7325 ?dane . ?m wdt:P18 ?img . FILTER(STRLEN(?dane) = 5)
}"""
ANCHOS = (480, 1080)
CALIDAD = 62
PAUSA = 1.0
CAMPOS = ("divipola", "archivo", "autor", "licencia", "url_licencia", "url_pagina", "fecha")


def imagenes_de_wikidata() -> dict[str, str]:
    """{código DANE: nombre de archivo en Commons}; si un municipio tiene varias, la primera."""
    r = Fetcher.get(
        URL_SPARQL,
        params={"query": CONSULTA, "format": "json"},
        headers={"User-Agent": AGENTE},
        timeout=120,
    )
    filas = r.json()["results"]["bindings"]
    salida: dict[str, str] = {}
    for fila in sorted(filas, key=lambda f: (f["dane"]["value"], f["img"]["value"])):
        salida.setdefault(fila["dane"]["value"], nombre_de_archivo(fila["img"]["value"]))
    return salida


def info_commons(archivos: list[str]) -> dict[str, dict]:
    """Licencia, autor y URL de la miniatura de hasta 50 archivos por consulta."""
    r = Fetcher.get(
        URL_COMMONS,
        params={
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|size|mime",
            "iiurlwidth": max(ANCHOS),
            "titles": "|".join(f"File:{a}" for a in archivos),
        },
        headers={"User-Agent": AGENTE},
        timeout=60,
    )
    salida: dict[str, dict] = {}
    for pagina in r.json().get("query", {}).get("pages", {}).values():
        info = (pagina.get("imageinfo") or [None])[0]
        if not info or not info.get("mime", "").startswith("image/"):
            continue
        meta = info.get("extmetadata", {})
        titulo = pagina["title"].removeprefix("File:").replace(" ", "_")
        salida[titulo] = {
            "autor": limpiar_html(meta.get("Artist", {}).get("value")),
            "licencia": limpiar_html(meta.get("LicenseShortName", {}).get("value")),
            "url_licencia": meta.get("LicenseUrl", {}).get("value", ""),
            "url_pagina": info.get("descriptionurl", ""),
            "miniatura": info.get("thumburl") or info.get("url"),
            "ancho": info.get("width", 0),
        }
    return salida


def guardar_webp(contenido: bytes, destino: Path, codigo: str) -> None:
    """Guarda `<codigo>-<ancho>.webp` por cada ancho (sin agrandar la imagen)."""
    with Image.open(io.BytesIO(contenido)) as original:
        imagen = original.convert("RGB")
    for ancho in ANCHOS:
        copia = imagen.copy()
        if copia.width > ancho:
            copia = copia.resize((ancho, round(copia.height * ancho / copia.width)), Image.LANCZOS)
        copia.save(destino / f"{codigo}-{ancho}.webp", "WEBP", quality=CALIDAD, method=6)


def descargar(codigos: set[str], destino: Path) -> int:
    """Busca y guarda las fotos con licencia libre. Devuelve cuántas hay en total."""
    destino.mkdir(parents=True, exist_ok=True)
    ruta_csv = destino / "fotos.csv"
    previas: dict[str, dict] = {}
    if ruta_csv.exists():
        with ruta_csv.open(encoding="utf-8", newline="") as f:
            previas = {fila["divipola"]: fila for fila in csv.DictReader(f)}

    candidatas = {c: a for c, a in imagenes_de_wikidata().items() if c in codigos}
    log.info("Wikidata: %d municipios con imagen", len(candidatas))
    pendientes = [c for c in sorted(candidatas) if c not in previas]
    for i in range(0, len(pendientes), 40):
        lote = pendientes[i : i + 40]
        info = info_commons([candidatas[c] for c in lote])
        for codigo in lote:
            dato = info.get(candidatas[codigo].replace(" ", "_"))
            if dato is None or not licencia_libre(dato["licencia"]) or not dato["autor"]:
                log.info(
                    "%s: sin licencia libre o sin autor (%s)", codigo, dato and dato["licencia"]
                )
                continue
            try:
                respuesta = Fetcher.get(
                    dato["miniatura"], headers={"User-Agent": AGENTE}, timeout=90
                )
                guardar_webp(respuesta.body, destino, codigo)
            except Exception as error:
                log.warning("%s: no se pudo guardar la foto (%s)", codigo, error)
                continue
            previas[codigo] = {
                "divipola": codigo,
                "archivo": candidatas[codigo],
                "autor": dato["autor"],
                "licencia": dato["licencia"],
                "url_licencia": dato["url_licencia"],
                "url_pagina": dato["url_pagina"]
                or f"https://commons.wikimedia.org/wiki/File:{quote(candidatas[codigo])}",
                "fecha": date.today().isoformat(),
            }
            time.sleep(PAUSA)
        _escribir(ruta_csv, previas)
    _escribir(ruta_csv, previas)
    return len(previas)


def _escribir(ruta: Path, filas: dict[str, dict]) -> None:
    with ruta.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas[c] for c in sorted(filas))
