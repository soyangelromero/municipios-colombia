"""Marco Geoestadístico Nacional (DANE), versión 2025: contornos de municipios y departamentos.

Se descarga del servicio WFS oficial, que entrega GML en Web Mercator (EPSG:3857) a resolución
completa (unos 180 MB para los municipios). Las páginas se guardan en caché y se leen de a una.

Notas sobre el servicio:
- El servicio ArcGIS REST del mismo MGN no devuelve geometrías; por eso se usa el WFS.
- Su firewall rechaza filtros genéricos (`1=1`) y filtros XML en la URL, así que se pagina la
  capa completa con `count` y `startIndex`.
"""

import logging
import re
import time
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from scrapling.fetchers import Fetcher

from municipios.comun.geometria import Poligono

log = logging.getLogger(__name__)

FUENTE = "dane_mgn"
URL_WFS = (
    "https://portalgis.dane.gov.co/mparcgis/services/MGN2025/Serv_CapasMGN_2025/MapServer/WFSServer"
)
PAUSA = 1.0  # segundos entre páginas, por cortesía con el servidor


@dataclass(frozen=True, slots=True)
class Capa:
    nombre: str  # nombre del tipo en el WFS
    campo_codigo: str
    campo_nombre: str
    campo_area: str  # km²
    tam_pagina: int


MUNICIPIOS = Capa(
    nombre="Municipio",
    campo_codigo="Código_DANE_concatenado_departamento_y_municipio",
    campo_nombre="Nombre_municipio",
    # El servicio rotula mal este campo: contiene el área del municipio, no la del departamento.
    campo_area="Área_departamento_en_kilómetros_cuadrados",
    tam_pagina=40,
)
DEPARTAMENTOS = Capa(
    nombre="Departamento",
    campo_codigo="Código_DANE_departamento",
    campo_nombre="Nombre_departamento",
    campo_area="Área_departamento_en_kilómetros_cuadrados",
    tam_pagina=40,
)


@dataclass(frozen=True, slots=True)
class Entidad:
    codigo: str
    nombre: str
    area_km2: float | None
    anio_version: str | None
    poligonos: list[Poligono]


def descargar(capa: Capa, directorio: Path, refrescar: bool = False) -> list[Path]:
    """Descarga todas las páginas de una capa y devuelve las rutas en caché."""
    carpeta = directorio / capa.nombre.lower()
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas: list[Path] = []
    total: int | None = None
    inicio = 0
    while total is None or inicio < total:
        ruta = carpeta / f"pagina-{inicio:05d}.gml"
        if refrescar or not ruta.exists():
            ruta.write_bytes(_pedir_pagina(capa, inicio))
            time.sleep(PAUSA)
        if total is None:
            total = _total_de_entidades(ruta)
            log.info("MGN %s: %d entidades", capa.nombre, total)
        rutas.append(ruta)
        inicio += capa.tam_pagina
        log.info("MGN %s: %d/%d", capa.nombre, min(inicio, total), total)
    return rutas


def _pedir_pagina(capa: Capa, inicio: int) -> bytes:
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": f"Serv_CapasMGN_2025:{capa.nombre}",
        "srsName": "EPSG:3857",
        "count": str(capa.tam_pagina),
        "startIndex": str(inicio),
    }
    respuesta = Fetcher.get(URL_WFS, params=params, timeout=600, retries=3)
    if respuesta.status != 200 or b"FeatureCollection" not in respuesta.body[:2000]:
        raise RuntimeError(f"WFS respondió {respuesta.status} para {capa.nombre} desde {inicio}")
    return respuesta.body


def _total_de_entidades(ruta: Path) -> int:
    with ruta.open("rb") as f:
        cabecera = f.read(4000).decode("utf-8", "replace")
    encontrado = re.search(r'numberMatched="(\d+)"', cabecera)
    if not encontrado:
        raise ValueError(f"No se encontró numberMatched en {ruta}")
    return int(encontrado.group(1))


def _local(etiqueta: str) -> str:
    """'{espacio}Nombre' -> 'Nombre'."""
    return etiqueta.rsplit("}", 1)[-1]


def _coordenadas(texto: str) -> list[tuple[float, float]]:
    valores = [float(v) for v in texto.split()]
    return list(zip(valores[0::2], valores[1::2], strict=True))


def leer(rutas: list[Path], capa: Capa) -> Iterator[Entidad]:
    """Lee entidades de páginas GML (WFS 2.0, GML 3.2), una por una, sin cargar todo a memoria."""
    for ruta in rutas:
        for _, elemento in ET.iterparse(ruta, events=("end",)):
            if _local(elemento.tag) != capa.nombre:
                continue
            yield _entidad(elemento, capa)
            elemento.clear()


def _entidad(elemento: ET.Element, capa: Capa) -> Entidad:
    atributos = {_local(hijo.tag): (hijo.text or "").strip() for hijo in elemento if len(hijo) == 0}
    poligonos: list[Poligono] = []
    for poligono in elemento.iter():
        if _local(poligono.tag) != "Polygon":
            continue
        anillos = [
            _coordenadas(lista.text or "")
            for lista in poligono.iter()
            if _local(lista.tag) == "posList"
        ]
        if anillos:
            poligonos.append(anillos)
    area = atributos.get(capa.campo_area)
    return Entidad(
        codigo=atributos[capa.campo_codigo],
        nombre=atributos.get(capa.campo_nombre, ""),
        area_km2=float(area) if area else None,
        anio_version=atributos.get("Año_versión_DANE") or None,
        poligonos=poligonos,
    )
