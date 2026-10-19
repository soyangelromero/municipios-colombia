"""Punto de entrada del pipeline: `python -m municipios <comando>`."""

import argparse
import logging
import os
import sys
from collections import Counter
from datetime import date
from types import ModuleType

from municipios.comun.contexto import Contexto, Resultado
from municipios.comun.modelos import Municipio
from municipios.comun.registro import cargar_fuentes, cargar_indicadores
from municipios.comun.salida import ahora_iso, escribir_json, leer_json
from municipios.comun.socrata import ClienteSocrata
from municipios.config import DIR_CRUDOS, DIR_INTERMEDIOS, RAIZ, cargar_env
from municipios.exportar import enlaces, mapas, sitio
from municipios.exportar.datos_web import DatosSitio
from municipios.fotos import commons as fotos
from municipios.fuentes import (
    cuipo,
    divipola,
    educacion,
    furag,
    gobierno_digital,
    grupos,
    ita,
    mgn,
    poblacion,
    salud,
    secop,
    seguridad,
)
from municipios.indice.almacen import Almacen
from municipios.indice.calculo import calcular as calcular_indice
from municipios.indice.calculo import cargar_config
from municipios.indice.derivados import Calculadora
from municipios.relevamiento import transparencia as relevamiento
from municipios.relevamiento.criterios import leer_sitios_manuales

log = logging.getLogger("municipios")

RUTA_MUNICIPIOS = DIR_INTERMEDIOS / "municipios.json"
RUTA_INDICE = DIR_INTERMEDIOS / "indice.json"
RUTA_RELEVAMIENTO = RAIZ / "datos" / "relevamiento" / "transparencia_automatica.csv"
DIR_FOTOS = RAIZ / "datos" / "fotos"
RUTA_SITIOS = RAIZ / "datos" / "manual" / "sitios.csv"
# Capitales de departamento (Bogotá incluida): alcance inicial del relevamiento.
CAPITALES = (
    "05001", "08001", "11001", "13001", "15001", "17001", "18001", "19001", "20001", "23001",
    "27001", "41001", "44001", "47001", "50001", "52001", "54001", "63001", "66001", "68001",
    "70001", "73001", "76001", "81001", "85001", "86001", "91001", "94001", "95001", "97001",
    "99001",
)  # fmt: skip
DIR_WEB = RAIZ / "web"
DIR_DIST = RAIZ / "dist"
DIR_MAPAS = DIR_DIST / "data" / "mapas"

# Fuentes que siguen el patrón `ejecutar(contexto) -> Resultado`. Cada una se guarda en
# datos/intermedios/<nombre>.json. El orden es el de `todo`.
FUENTES: dict[str, tuple[ModuleType, str]] = {
    "poblacion": (poblacion, "Proyecciones de población del DANE"),
    "grupos": (grupos, "Grupos de capacidades iniciales del DNP (pares del índice)"),
    "seguridad": (seguridad, "Homicidios y hurtos por municipio y año (MinDefensa)"),
    "transparencia": (ita, "Índice de Transparencia y Acceso a la Información (Procuraduría)"),
    "gobierno_digital": (gobierno_digital, "Índice de Gobierno Digital (MinTIC)"),
    "desempeno_institucional": (furag, "FURAG: desempeño institucional (Función Pública)"),
    "finanzas": (cuipo, "Ejecución presupuestal CUIPO (Contraloría)"),
    "contratacion": (secop, "Contratos de las alcaldías en SECOP II"),
    "educacion": (educacion, "Cobertura y deserción escolar (MEN)"),
    "salud": (salud, "Afiliados al sistema de salud (ADRES)"),
}


def comando_fuentes(_: Contexto) -> None:
    for fuente in cargar_fuentes().values():
        print(f"{fuente.clave:28} {fuente.organismo} · {fuente.titulo}\n{'':28} {fuente.url}")


def comando_divipola(contexto: Contexto) -> None:
    """Descarga DIVIPOLA. Va primero en `todo` porque las demás fuentes cruzan con ella."""
    municipios = divipola.normalizar(divipola.descargar(contexto.cliente, contexto.refrescar))
    escribir_json(
        RUTA_MUNICIPIOS,
        {"generado": ahora_iso(), "fuente": divipola.FUENTE, "municipios": municipios},
    )
    contexto.reemplazar_municipios({m.divipola: m for m in municipios})
    tipos = Counter(m.tipo for m in municipios)
    log.info("DIVIPOLA: %d registros %s → %s", len(municipios), dict(tipos), RUTA_MUNICIPIOS)


def comando_mapas(contexto: Contexto) -> None:
    cache = contexto.dir_crudos / "mgn"
    resultado = mapas.construir(
        mgn.leer(mgn.descargar(mgn.MUNICIPIOS, cache, contexto.refrescar), mgn.MUNICIPIOS),
        mgn.leer(mgn.descargar(mgn.DEPARTAMENTOS, cache, contexto.refrescar), mgn.DEPARTAMENTOS),
        contexto.municipios,
        DIR_MAPAS,
    )
    _guardar(
        "territorio",
        Resultado(
            resultado.superficie,
            sin_cruce=resultado.sin_divipola,
            notas={"sin_geometria": resultado.sin_geometria},
        ),
    )
    log.info("%d mapas → %s (vista previa: index.html)", len(resultado.archivos), DIR_MAPAS)


def _guardar(nombre: str, resultado: Resultado) -> None:
    ruta = DIR_INTERMEDIOS / f"{nombre}.json"
    escribir_json(
        ruta,
        {
            "generado": ahora_iso(),
            "notas": resultado.notas,
            "sin_cruce": resultado.sin_cruce,
            "observaciones": resultado.observaciones,
        },
    )
    if resultado.sin_cruce:
        muestra = ", ".join(str(c) for c in list(resultado.sin_cruce)[:8])
        log.warning("%s: %d sin cruce con DIVIPOLA: %s", nombre, len(resultado.sin_cruce), muestra)
    cubiertos = len({o.divipola for o in resultado.observaciones})
    log.info(
        "%s: %d observaciones de %d municipios → %s",
        nombre,
        len(resultado.observaciones),
        cubiertos,
        ruta.name,
    )


def _verificar_indicadores(nombre: str, resultado: Resultado) -> None:
    """Todo indicador producido debe tener ficha en config/indicadores.toml."""
    sin_ficha = {o.indicador for o in resultado.observaciones} - set(cargar_indicadores())
    if sin_ficha:
        raise ValueError(f"{nombre}: indicadores sin ficha en indicadores.toml: {sin_ficha}")


def comando_fuente(nombre: str):
    modulo, _ = FUENTES[nombre]

    def ejecutar(contexto: Contexto) -> None:
        resultado = modulo.ejecutar(contexto)
        _verificar_indicadores(nombre, resultado)
        _guardar(nombre, resultado)

    return ejecutar


def comando_indice(contexto: Contexto) -> None:
    """Calcula el índice con lo que haya en datos/intermedios/ y lo guarda en indice.json."""
    config = cargar_config()
    almacen = Almacen.desde_directorio(DIR_INTERMEDIOS)
    grupos = {
        codigo: str(o.valor)
        for codigo in contexto.municipios
        if (o := almacen.ultimo(codigo, "grupo_capacidades")) is not None
    }
    calculadora = Calculadora(
        almacen,
        contexto.municipios,
        grupos,
        anio_actual=date.today().year,
        antiguedad_maxima=int(config.reglas["antiguedad_maxima_anios"]),
        suavizado_poblacion=float(config.reglas["suavizado_poblacion"]),
    )
    datos = calculadora.calcular()
    resultado = calcular_indice(datos, contexto.municipios, grupos, config)
    for codigo, fila in resultado.items():
        fila["datos"] = datos[codigo]
    escribir_json(
        RUTA_INDICE,
        {
            "generado": ahora_iso(),
            "version": config.version,
            "anios_referencia": calculadora.ref,
            "municipios": resultado,
        },
    )
    con_indice = [f for f in resultado.values() if f["indice"] is not None]
    semaforos = Counter(f["semaforo"] for f in con_indice)
    log.info(
        "Índice v%s: %d municipios con índice %s → %s",
        config.version,
        len(con_indice),
        dict(semaforos),
        RUTA_INDICE.name,
    )


def comando_relevamiento(contexto: Contexto) -> None:
    """Revisión automática del menú de transparencia (necesita `scrapling install`).

    Por defecto revisa las capitales; con --alcance todos, los 1.104 municipios (varias horas).
    """
    codigos = (
        CAPITALES
        if contexto.alcance == "capitales"
        else sorted(c for c, m in contexto.municipios.items() if m.tipo == "municipio")
    )
    lista = [contexto.municipios[c] for c in codigos]
    manuales = leer_sitios_manuales(RUTA_SITIOS)
    total = relevamiento.relevar(lista, manuales, RUTA_RELEVAMIENTO)
    log.info("Relevamiento: %d municipios → %s", total, RUTA_RELEVAMIENTO)


def comando_fotos(contexto: Contexto) -> None:
    """Descarga la foto con licencia libre de cada municipio (Wikidata y Commons)."""
    total = fotos.descargar(contexto.codigos, DIR_FOTOS)
    log.info("Fotos con licencia libre: %d → %s", total, DIR_FOTOS)


def comando_sitio(_: Contexto) -> None:
    """Arma dist/: páginas HTML, datos JSON y recursos de web/. Requiere `indice` y `mapas`."""
    if not RUTA_INDICE.exists():
        raise SystemExit(
            "Falta datos/intermedios/indice.json: corre antes `python -m municipios indice`."
        )
    datos = DatosSitio.cargar(DIR_INTERMEDIOS, generado=date.today().isoformat())
    sitio.construir(datos, DIR_WEB, DIR_DIST)


def comando_enlaces(_: Contexto) -> None:
    """Revisa que los enlaces internos de dist/ apunten a algo que exista (no está en `todo`)."""
    rotos = enlaces.revisar(DIR_DIST)
    for pagina, enlace, motivo in rotos[:200]:
        log.error("%s → %s (%s)", pagina, enlace, motivo)
    if rotos:
        raise SystemExit(f"{len(rotos)} enlaces rotos en dist/")
    log.info("Enlaces internos de dist/: sin rotos")


def comando_todo(contexto: Contexto) -> None:
    """Corre todo en orden. Con --tolerante, una fuente que falla no detiene a las demás."""
    comando_divipola(contexto)
    fallidas: dict[str, str] = {}
    for nombre in FUENTES:
        try:
            comando_fuente(nombre)(contexto)
        except Exception as error:
            if not contexto.tolerante:
                raise
            log.exception("%s falló; se continúa con las demás fuentes", nombre)
            fallidas[nombre] = repr(error)[:300]
    comando_indice(contexto)
    comando_mapas(contexto)
    comando_sitio(contexto)
    escribir_json(DIR_INTERMEDIOS / "estado.json", {"generado": ahora_iso(), "fallidas": fallidas})
    if fallidas:
        log.warning("Fuentes que fallaron: %s", ", ".join(fallidas))


COMANDOS = {
    "fuentes": (comando_fuentes, "Lista las fuentes registradas"),
    "divipola": (comando_divipola, "Descarga y normaliza la lista oficial de municipios"),
    **{nombre: (comando_fuente(nombre), ayuda) for nombre, (_, ayuda) in FUENTES.items()},
    "indice": (comando_indice, "Calcula el índice municipal con los datos descargados"),
    "mapas": (comando_mapas, "Descarga el MGN y genera los mapas SVG (≈240 MB la primera vez)"),
    "relevamiento": (
        comando_relevamiento,
        "Revisión automática del menú de transparencia de las alcaldías (no está en `todo`)",
    ),
    "fotos": (
        comando_fotos,
        "Descarga la foto con licencia libre de cada municipio (no está en `todo`)",
    ),
    "enlaces": (comando_enlaces, "Revisa los enlaces internos de dist/ (no está en `todo`)"),
    "sitio": (comando_sitio, "Arma el sitio publicable en dist/ (páginas y datos)"),
    "todo": (comando_todo, "Corre todo, en orden"),
}


def _municipios(cliente: ClienteSocrata) -> dict[str, Municipio]:
    """Municipios ya descargados; si no hay, descarga DIVIPOLA (las fuentes cruzan con ella)."""
    if not RUTA_MUNICIPIOS.exists():
        municipios = divipola.normalizar(divipola.descargar(cliente))
        escribir_json(
            RUTA_MUNICIPIOS,
            {"generado": ahora_iso(), "fuente": divipola.FUENTE, "municipios": municipios},
        )
    return {m["divipola"]: Municipio(**m) for m in leer_json(RUTA_MUNICIPIOS)["municipios"]}


def main(argv: list[str] | None = None) -> int:
    # La consola de Windows usa cp1252 por defecto; los nombres llevan tildes.
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="municipios", description=__doc__)
    parser.add_argument("--refrescar", action="store_true", help="ignora la caché y descarga")
    parser.add_argument("-v", "--detalle", action="store_true", help="muestra más mensajes")
    parser.add_argument(
        "--alcance",
        choices=("capitales", "todos"),
        default="capitales",
        help="en `relevamiento`: qué municipios revisar (por defecto, las capitales)",
    )
    parser.add_argument(
        "--tolerante",
        action="store_true",
        help="en `todo`, si una fuente falla se registra y se sigue con las demás",
    )
    sub = parser.add_subparsers(dest="comando", required=True, metavar="comando")
    for nombre, (_, ayuda) in COMANDOS.items():
        sub.add_parser(nombre, help=ayuda)
    args = parser.parse_args(argv)

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
    contexto = Contexto(
        cliente=cliente,
        municipios=_municipios(cliente) if args.comando != "fuentes" else {},
        dir_crudos=DIR_CRUDOS,
        refrescar=args.refrescar,
        tolerante=args.tolerante,
        alcance=args.alcance,
    )
    funcion, _ = COMANDOS[args.comando]
    funcion(contexto)
    return 0
