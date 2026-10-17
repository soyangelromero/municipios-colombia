"""Reúne lo que necesita el sitio (municipios, índice, fichas, fuentes) y exporta los JSON.

JSON publicados en dist/data/ (los lee el JavaScript; las páginas HTML ya traen las cifras):
- pais.json: resumen liviano de todos los municipios, para buscador, mapa y ranking.
- m/<codigo>.json: ficha completa de un municipio, para el comparador.
- indice.json: configuración del índice, fichas de indicadores y fuentes.
"""

import csv
import tomllib
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any

from municipios.comun.modelos import Fuente, Indicador, Municipio
from municipios.comun.registro import cargar_fuentes, cargar_indicadores
from municipios.comun.salida import escribir_json, leer_json
from municipios.config import DIR_CONFIG, RAIZ
from municipios.fuentes.divipola import DEPARTAMENTOS
from municipios.indice.calculo import Config, cargar_config

NOMBRES_GRUPOS = {
    "C": "Ciudades",
    "G1": "Grupo 1 (capacidades altas)",
    "G2": "Grupo 2 (medio-altas)",
    "G3": "Grupo 3 (medias)",
    "G4": "Grupo 4 (medio-bajas)",
    "G5": "Grupo 5 (bajas)",
}


RUTA_TRANSPARENCIA_AUTO = RAIZ / "datos" / "relevamiento" / "transparencia_automatica.csv"
DIR_FOTOS = RAIZ / "datos" / "fotos"


def leer_transparencia_auto(ruta: Path) -> dict[str, list[dict[str, str]]]:
    """Lee el relevamiento automático agrupado por código DIVIPOLA ({} si no existe)."""
    if not ruta.exists():
        return {}
    por_municipio: dict[str, list[dict[str, str]]] = defaultdict(list)
    with ruta.open(encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            por_municipio[fila["divipola"]].append(fila)
    return dict(por_municipio)


def leer_fotos(dir_fotos: Path) -> dict[str, dict[str, str]]:
    """Crédito de las fotos con licencia libre, por código DIVIPOLA ({} si no hay)."""
    ruta = dir_fotos / "fotos.csv"
    if not ruta.exists():
        return {}
    with ruta.open(encoding="utf-8", newline="") as f:
        return {
            fila["divipola"]: fila
            for fila in csv.DictReader(f)
            if (dir_fotos / f"{fila['divipola']}-1080.webp").exists()
        }


@dataclass
class DatosSitio:
    sitio: dict[str, Any]
    config: Config
    indicadores: dict[str, Indicador]
    fuentes: dict[str, Fuente]
    municipios: dict[str, Municipio]
    indice: dict[str, dict[str, Any]]
    anios_referencia: dict[str, int | None]
    # Revisión automática del menú de transparencia: código -> filas (una por criterio).
    transparencia_auto: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    # Fotos con licencia libre: código -> {autor, licencia, url_licencia, url_pagina, …}.
    fotos: dict[str, dict[str, str]] = field(default_factory=dict)

    @classmethod
    def cargar(cls, dir_intermedios: Path, generado: str) -> "DatosSitio":
        with (DIR_CONFIG / "sitio.toml").open("rb") as f:
            sitio = tomllib.load(f)
        sitio["actualizado"] = generado
        municipios = {
            m["divipola"]: Municipio(**m)
            for m in leer_json(dir_intermedios / "municipios.json")["municipios"]
        }
        indice = leer_json(dir_intermedios / "indice.json")
        return cls(
            sitio=sitio,
            config=cargar_config(),
            indicadores=cargar_indicadores(),
            fuentes=cargar_fuentes(),
            municipios=municipios,
            indice=indice["municipios"],
            anios_referencia=indice["anios_referencia"],
            transparencia_auto=leer_transparencia_auto(RUTA_TRANSPARENCIA_AUTO),
            fotos=leer_fotos(DIR_FOTOS),
        )

    # --- consultas útiles para las páginas -------------------------------------------------
    def por_departamento(self) -> dict[str, list[Municipio]]:
        grupos: dict[str, list[Municipio]] = defaultdict(list)
        for m in sorted(self.municipios.values(), key=lambda m: m.nombre):
            grupos[m.departamento_codigo].append(m)
        return grupos

    def promedio(self, codigos: list[str], campo: str = "indice") -> float | None:
        valores = [v for c in codigos if (v := self.valor(c, campo)) is not None]
        return round(mean(valores), 1) if valores else None

    def valor(self, codigo: str, campo: str) -> float | None:
        """Índice ('indice') o puntaje de un pilar ('T', 'S', 'G', 'C')."""
        fila = self.indice.get(codigo, {})
        if campo == "indice":
            return fila.get("indice")
        pilar = fila.get("pilares", {}).get(campo)
        return pilar["puntaje"] if pilar and pilar.get("valido") else None

    def ranking(self) -> list[str]:
        con = [c for c, f in self.indice.items() if f.get("indice") is not None]
        return sorted(con, key=lambda c: (self.indice[c]["puesto"]["nacional"], c))


def _ficha_json(datos: DatosSitio, codigo: str) -> dict[str, Any]:
    m = datos.municipios[codigo]
    fila = datos.indice[codigo]
    return {
        "codigo": codigo,
        "nombre": m.nombre,
        "slug": m.slug,
        "departamento": m.departamento,
        "departamento_slug": m.departamento_slug,
        "tipo": m.tipo,
        "grupo": fila.get("grupo"),
        "indice": fila.get("indice"),
        "semaforo": fila.get("semaforo"),
        "tope": fila.get("tope"),
        "motivo_sin_indice": fila.get("motivo_sin_indice"),
        "puesto": fila.get("puesto"),
        "rango_puestos": fila.get("rango_puestos"),
        "pilares": fila.get("pilares", {}),
        "componentes": fila.get("componentes", {}),
        "datos": fila.get("datos", {}),
    }


def exportar(datos: DatosSitio, destino: Path) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    campos = [
        "codigo", "nombre", "slug", "dep", "grupo", "indice", "semaforo", "puesto",
        "T", "S", "G", "C", "poblacion",
    ]  # fmt: skip
    filas = []
    for codigo, m in sorted(datos.municipios.items()):
        f = datos.indice.get(codigo, {})
        poblacion = f.get("datos", {}).get("poblacion", {}).get("valor")
        filas.append(
            [
                codigo,
                m.nombre,
                m.slug,
                m.departamento_codigo,
                f.get("grupo"),
                f.get("indice"),
                f.get("semaforo"),
                (f.get("puesto") or {}).get("nacional"),
                *(datos.valor(codigo, p) for p in "TSGC"),
                poblacion,
            ]
        )
    por_dep = datos.por_departamento()
    departamentos = {
        cod: {
            "nombre": nombre,
            "slug": slug,
            "municipios": len(por_dep.get(cod, [])),
            **{
                campo: datos.promedio([m.divipola for m in por_dep.get(cod, [])], campo)
                for campo in ("indice", "T", "S", "G", "C")
            },
        }
        for cod, (nombre, slug) in DEPARTAMENTOS.items()
    }
    escribir_json(
        destino / "pais.json",
        {
            "generado": datos.sitio["actualizado"],
            "version": datos.config.version,
            "campos": campos,
            "municipios": filas,
            "departamentos": departamentos,
            "grupos": NOMBRES_GRUPOS,
        },
        compacto=True,
    )
    escribir_json(
        destino / "indice.json",
        {
            "version": datos.config.version,
            "semaforo": datos.config.semaforo,
            "pilares": [
                {
                    "id": p.id,
                    "nombre": p.nombre,
                    "peso": p.peso,
                    "descripcion": p.descripcion,
                    "componentes": [asdict(c) for c in p.componentes],
                }
                for p in datos.config.pilares
            ],
            "contexto": list(datos.config.contexto),
            "indicadores": {k: asdict(v) for k, v in datos.indicadores.items()},
            "fuentes": {k: asdict(v) for k, v in datos.fuentes.items()},
            "anios_referencia": datos.anios_referencia,
        },
        compacto=True,
    )
    for codigo in datos.municipios:
        escribir_json(destino / "m" / f"{codigo}.json", _ficha_json(datos, codigo), compacto=True)
