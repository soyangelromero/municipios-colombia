"""Punto de entrada del pipeline: `python -m municipios <comando>`."""

import argparse
import logging
import os
import sys
from collections import Counter

from municipios.comun.modelos import Municipio
from municipios.comun.registro import cargar_fuentes
from municipios.comun.salida import ahora_iso, escribir_json, leer_json
from municipios.comun.socrata import ClienteSocrata
from municipios.config import DIR_CRUDOS, DIR_INTERMEDIOS, RAIZ, cargar_env
from municipios.exportar import mapas
from municipios.fuentes import divipola, mgn, poblacion, seguridad

log = logging.getLogger("municipios")

RUTA_MUNICIPIOS = DIR_INTERMEDIOS / "municipios.json"
RUTA_SEGURIDAD = DIR_INTERMEDIOS / "seguridad.json"
RUTA_POBLACION = DIR_INTERMEDIOS / "poblacion.json"
RUTA_TERRITORIO = DIR_INTERMEDIOS / "territorio.json"
DIR_MAPAS = RAIZ / "web" / "data" / "mapas"


def comando_fuentes(_: ClienteSocrata, __: bool) -> None:
    for fuente in cargar_fuentes().values():
        print(f"{fuente.clave:28} {fuente.organismo} · {fuente.titulo}\n{'':28} {fuente.url}")


def comando_divipola(cliente: ClienteSocrata, refrescar: bool) -> list[Municipio]:
    """Descarga DIVIPOLA. Va primero en `todo` porque las demás fuentes cruzan con ella."""
    municipios = divipola.normalizar(divipola.descargar(cliente, refrescar))
    escribir_json(
        RUTA_MUNICIPIOS,
        {"generado": ahora_iso(), "fuente": divipola.FUENTE, "municipios": municipios},
    )
    tipos = Counter(m.tipo for m in municipios)
    log.info("DIVIPOLA: %d registros %s → %s", len(municipios), dict(tipos), RUTA_MUNICIPIOS)
    return municipios


def _municipios(cliente: ClienteSocrata, refrescar: bool) -> dict[str, Municipio]:
    """Municipios por código: del archivo intermedio si existe, si no los descarga."""
    if RUTA_MUNICIPIOS.exists() and not refrescar:
        lista = [Municipio(**m) for m in leer_json(RUTA_MUNICIPIOS)["municipios"]]
    else:
        lista = comando_divipola(cliente, refrescar)
    return {m.divipola: m for m in lista}


def _avisar_sin_cruce(que: str, codigos: dict[str, object]) -> None:
    if codigos:
        detalle = ", ".join(f"{c} ({v})" for c, v in sorted(codigos.items())[:10])
        log.warning("%s: %d códigos sin cruce con DIVIPOLA: %s", que, len(codigos), detalle)


def comando_poblacion(cliente: ClienteSocrata, refrescar: bool) -> None:
    codigos = set(_municipios(cliente, refrescar=False))
    ruta = poblacion.descargar(DIR_CRUDOS / "dane", refrescar)
    observaciones, sin_cruce = poblacion.normalizar(poblacion.leer_filas(ruta), codigos)
    _avisar_sin_cruce("Población", sin_cruce)
    cubiertos = {o.divipola for o in observaciones}
    faltantes = sorted(codigos - cubiertos)
    if faltantes:
        log.warning("Población: %d municipios sin dato: %s", len(faltantes), faltantes)
    escribir_json(
        RUTA_POBLACION,
        {
            "generado": ahora_iso(),
            "sin_cruce": sin_cruce,
            "sin_dato": faltantes,
            "observaciones": observaciones,
        },
    )
    log.info("Población: %d observaciones → %s", len(observaciones), RUTA_POBLACION)


def comando_mapas(cliente: ClienteSocrata, refrescar: bool) -> None:
    municipios = _municipios(cliente, refrescar=False)
    cache = DIR_CRUDOS / "mgn"
    resultado = mapas.construir(
        mgn.leer(mgn.descargar(mgn.MUNICIPIOS, cache, refrescar), mgn.MUNICIPIOS),
        mgn.leer(mgn.descargar(mgn.DEPARTAMENTOS, cache, refrescar), mgn.DEPARTAMENTOS),
        municipios,
        DIR_MAPAS,
    )
    _avisar_sin_cruce("MGN", resultado.sin_divipola)
    if resultado.sin_geometria:
        sin_geo = [f"{c} {municipios[c].nombre}" for c in resultado.sin_geometria]
        log.warning("Sin contorno en el MGN (no aparecen en el mapa): %s", ", ".join(sin_geo))
    escribir_json(
        RUTA_TERRITORIO,
        {
            "generado": ahora_iso(),
            "sin_geometria": resultado.sin_geometria,
            "sin_divipola": resultado.sin_divipola,
            "observaciones": resultado.superficie,
        },
    )
    log.info("%d mapas → %s (vista previa: index.html)", len(resultado.archivos), DIR_MAPAS)


def comando_seguridad(cliente: ClienteSocrata, refrescar: bool) -> None:
    codigos = set(_municipios(cliente, refrescar=False))

    observaciones, sin_cruce, ultimas = [], {}, {}
    for delito in seguridad.DELITOS:
        filas, ultima = seguridad.descargar(cliente, delito, refrescar)
        obs, faltantes = seguridad.normalizar(filas, delito, ultima, codigos)
        observaciones.extend(obs)
        ultimas[delito.indicador] = ultima.isoformat()
        if faltantes:
            sin_cruce[delito.indicador] = faltantes
            _avisar_sin_cruce(delito.indicador, faltantes)
        log.info("%s: %d observaciones, datos hasta %s", delito.indicador, len(obs), ultima)

    escribir_json(
        RUTA_SEGURIDAD,
        {
            "generado": ahora_iso(),
            "datos_hasta": ultimas,
            "sin_cruce": sin_cruce,
            "observaciones": observaciones,
        },
    )
    log.info("Seguridad → %s", RUTA_SEGURIDAD)


def comando_todo(cliente: ClienteSocrata, refrescar: bool) -> None:
    comando_divipola(cliente, refrescar)
    for comando in (comando_poblacion, comando_mapas, comando_seguridad):
        comando(cliente, refrescar)


COMANDOS = {
    "fuentes": (comando_fuentes, "Lista las fuentes registradas"),
    "divipola": (comando_divipola, "Descarga y normaliza la lista oficial de municipios"),
    "poblacion": (comando_poblacion, "Descarga las proyecciones de población del DANE"),
    "mapas": (comando_mapas, "Descarga el MGN y genera los mapas SVG (≈180 MB la primera vez)"),
    "seguridad": (comando_seguridad, "Descarga homicidios y hurtos por municipio y año"),
    "todo": (comando_todo, "Corre todas las fuentes disponibles"),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="municipios", description=__doc__)
    parser.add_argument("--refrescar", action="store_true", help="ignora la caché y descarga")
    parser.add_argument("-v", "--detalle", action="store_true", help="muestra más mensajes")
    sub = parser.add_subparsers(dest="comando", required=True, metavar="comando")
    for nombre, (_, ayuda) in COMANDOS.items():
        sub.add_parser(nombre, help=ayuda)
    args = parser.parse_args(argv)

    # La consola de Windows usa cp1252 por defecto; los nombres llevan tildes.
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")

    logging.basicConfig(
        level=logging.DEBUG if args.detalle else logging.INFO,
        format="%(levelname)s %(message)s",
    )
    # Scrapling registra cada petición en INFO; el pipeline ya informa su propio avance.
    logging.getLogger("scrapling").setLevel(logging.WARNING)
    cargar_env()

    cliente = ClienteSocrata(
        token=os.environ.get("SOCRATA_APP_TOKEN") or None,
        dir_cache=DIR_CRUDOS / "socrata",
    )
    funcion, _ = COMANDOS[args.comando]
    funcion(cliente, args.refrescar)
    return 0
