"""Registro de fuentes: lee pipeline/config/fuentes.toml."""

import tomllib
from pathlib import Path

from municipios.comun.modelos import Fuente
from municipios.config import DIR_CONFIG


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
