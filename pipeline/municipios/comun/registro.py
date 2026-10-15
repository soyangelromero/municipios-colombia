"""Registros de fuentes e indicadores: leen pipeline/config/*.toml."""

import tomllib
from pathlib import Path

from municipios.comun.modelos import Fuente, Indicador
from municipios.config import DIR_CONFIG

SENTIDOS = frozenset({"mayor_mejor", "menor_mejor", "contexto"})


def cargar_indicadores(ruta: Path = DIR_CONFIG / "indicadores.toml") -> dict[str, Indicador]:
    with ruta.open("rb") as f:
        crudo = tomllib.load(f)
    indicadores = {
        clave: Indicador(
            clave=clave,
            etiqueta=datos["etiqueta"],
            unidad=datos["unidad"],
            sentido=datos["sentido"],
            fuente=datos["fuente"],
            descripcion=datos.get("descripcion", ""),
        )
        for clave, datos in crudo.items()
    }
    invalidos = sorted(c for c, i in indicadores.items() if i.sentido not in SENTIDOS)
    if invalidos:
        raise ValueError(f"Sentido inválido en: {invalidos}")
    return indicadores


def cargar_fuentes(ruta: Path = DIR_CONFIG / "fuentes.toml") -> dict[str, Fuente]:
    with ruta.open("rb") as f:
        crudo = tomllib.load(f)
    return {
        clave: Fuente(
            clave=clave,
            organismo=datos["organismo"],
            titulo=datos["titulo"],
            url=datos["url"],
            conjunto=datos.get("conjunto"),
            licencia=datos["licencia"],
            oficial=bool(datos["oficial"]),
        )
        for clave, datos in crudo.items()
    }
