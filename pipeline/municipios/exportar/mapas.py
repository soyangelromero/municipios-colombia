"""Arma los mapas del sitio: Colombia por departamentos y cada departamento por municipios."""

import logging
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

from municipios.comun.geometria import simplificar
from municipios.comun.modelos import Municipio, Observacion
from municipios.comun.textos import nombre_legible
from municipios.exportar.mapa_svg import Forma, svg
from municipios.fuentes import mgn
from municipios.fuentes.divipola import DEPARTAMENTOS

log = logging.getLogger(__name__)

# Simplificación previa al leer cada entidad, para no tener millones de puntos en memoria.
# 10 m está muy por debajo del error visible incluso en el departamento más chico.
PRESIMPLIFICACION_M = 10.0

# San Andrés y Providencia queda a unos 700 km del continente: va en recuadro en el mapa
# nacional, y sus dos islas (separadas unos 80 km) van en paneles en el mapa departamental.
DEPARTAMENTOS_EN_RECUADRO = {"88"}
DEPARTAMENTOS_EN_PANELES = {"88"}


@dataclass
class ResultadoMapas:
    archivos: list[Path] = field(default_factory=list)
    superficie: list[Observacion] = field(default_factory=list)
    sin_geometria: list[str] = field(default_factory=list)  # en DIVIPOLA, no en el MGN
    sin_divipola: dict[str, str] = field(default_factory=dict)  # en el MGN, no en DIVIPOLA


def _presimplificada(entidad: mgn.Entidad) -> mgn.Entidad:
    poligonos = simplificar(entidad.poligonos, PRESIMPLIFICACION_M, area_minima=0)
    return mgn.Entidad(
        entidad.codigo, entidad.nombre, entidad.area_km2, entidad.anio_version, poligonos
    )


def construir(
    entidades_municipios: Iterable[mgn.Entidad],
    entidades_departamentos: Iterable[mgn.Entidad],
    municipios: dict[str, Municipio],
    destino: Path,
) -> ResultadoMapas:
    resultado = ResultadoMapas()
    destino.mkdir(parents=True, exist_ok=True)

    por_departamento: dict[str, list[Forma]] = defaultdict(list)
    for entidad in map(_presimplificada, entidades_municipios):
        municipio = municipios.get(entidad.codigo)
        if municipio is None:
            resultado.sin_divipola[entidad.codigo] = entidad.nombre
            nombre, slug = nombre_legible(entidad.nombre), ""
        else:
            nombre, slug = municipio.nombre, municipio.slug
        por_departamento[entidad.codigo[:2]].append(
            Forma(entidad.codigo, nombre, slug, entidad.poligonos)
        )
        if municipio is not None and entidad.area_km2 is not None:
            resultado.superficie.append(
                Observacion(
                    divipola=entidad.codigo,
                    indicador="superficie_km2",
                    valor=round(entidad.area_km2, 2),
                    periodo=entidad.anio_version or "2025",
                    fuente=mgn.FUENTE,
                )
            )

    con_geometria = {f.codigo for formas in por_departamento.values() for f in formas}
    resultado.sin_geometria = sorted(set(municipios) - con_geometria)

    for codigo, formas in sorted(por_departamento.items()):
        nombre_dep, slug_dep = DEPARTAMENTOS[codigo]
        archivo = destino / f"{slug_dep}.svg"
        documento = svg(
            formas,
            f"Municipios de {nombre_dep}",
            "municipios",
            paneles=codigo in DEPARTAMENTOS_EN_PANELES,
        )
        archivo.write_text(documento, "utf-8")
        resultado.archivos.append(archivo)
        log.info("Mapa %s: %d municipios, %d KB", slug_dep, len(formas), _kb(archivo))

    departamentos = [
        Forma(e.codigo, *DEPARTAMENTOS[e.codigo], e.poligonos)
        for e in map(_presimplificada, entidades_departamentos)
    ]
    archivo = destino / "colombia.svg"
    documento = svg(
        departamentos,
        "Departamentos de Colombia",
        "departamentos",
        recuadro=DEPARTAMENTOS_EN_RECUADRO,
    )
    archivo.write_text(documento, "utf-8")
    resultado.archivos.insert(0, archivo)
    log.info("Mapa colombia: %d departamentos, %d KB", len(departamentos), _kb(archivo))

    _escribir_vista_previa(destino, resultado.archivos)
    return resultado


def _kb(ruta: Path) -> int:
    return round(ruta.stat().st_size / 1024)


def _escribir_vista_previa(destino: Path, archivos: list[Path]) -> None:
    """Página de revisión (generada, no versionada) con todos los mapas."""
    figuras = "\n".join(
        f'<figure><img src="{escape(a.name)}" alt="" loading="lazy">'
        f"<figcaption>{escape(a.stem)} · {_kb(a)} KB</figcaption></figure>"
        for a in archivos
    )
    (destino / "index.html").write_text(
        "<!doctype html><html lang='es-CO'><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Mapas generados</title><style>"
        "body{font-family:system-ui,sans-serif;margin:16px;background:#f7f7f5}"
        "main{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr))}"
        "figure{margin:0;background:#fff;border:1px solid #d9dce1;border-radius:12px;padding:8px}"
        "img{width:100%;height:260px;object-fit:contain}figcaption{font-size:.85rem;color:#4b5159}"
        f"</style><h1>Mapas generados</h1><main>{figuras}</main></html>\n",
        "utf-8",
    )
