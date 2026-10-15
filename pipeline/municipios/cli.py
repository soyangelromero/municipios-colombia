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
from municipios.config import DIR_CRUDOS, DIR_INTERMEDIOS, cargar_env
from municipios.fuentes import divipola, seguridad

log = logging.getLogger("municipios")

RUTA_MUNICIPIOS = DIR_INTERMEDIOS / "municipios.json"
RUTA_SEGURIDAD = DIR_INTERMEDIOS / "seguridad.json"


def comando_fuentes(_: ClienteSocrata, __: bool) -> None:
    for fuente in cargar_fuentes().values():
        print(f"{fuente.clave:28} {fuente.organismo} · {fuente.titulo}\n{'':28} {fuente.url}")


def comando_divipola(cliente: ClienteSocrata, refrescar: bool) -> list[Municipio]:
    municipios = divipola.normalizar(divipola.descargar(cliente, refrescar))
    escribir_json(
        RUTA_MUNICIPIOS,
        {"generado": ahora_iso(), "fuente": divipola.FUENTE, "municipios": municipios},
    )
    tipos = Counter(m.tipo for m in municipios)
    log.info("DIVIPOLA: %d registros %s → %s", len(municipios), dict(tipos), RUTA_MUNICIPIOS)
    return municipios


def comando_seguridad(cliente: ClienteSocrata, refrescar: bool) -> None:
    if RUTA_MUNICIPIOS.exists() and not refrescar:
        codigos = {m["divipola"] for m in leer_json(RUTA_MUNICIPIOS)["municipios"]}
    else:
        codigos = {m.divipola for m in comando_divipola(cliente, refrescar)}

    observaciones, sin_cruce, ultimas = [], {}, {}
    for delito in seguridad.DELITOS:
        filas, ultima = seguridad.descargar(cliente, delito, refrescar)
        obs, faltantes = seguridad.normalizar(filas, delito, ultima, codigos)
        observaciones.extend(obs)
        ultimas[delito.indicador] = ultima.isoformat()
        if faltantes:
            sin_cruce[delito.indicador] = faltantes
            log.warning(
                "%s: %d códigos sin cruce con DIVIPOLA (%d hechos): %s",
                delito.indicador,
                len(faltantes),
                sum(faltantes.values()),
                ", ".join(sorted(faltantes)[:10]),
            )
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
    comando_seguridad(cliente, refrescar=False)


COMANDOS = {
    "fuentes": (comando_fuentes, "Lista las fuentes registradas"),
    "divipola": (comando_divipola, "Descarga y normaliza la lista oficial de municipios"),
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
