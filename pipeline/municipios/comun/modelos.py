"""Tipos de datos del pipeline. Ver docs/modelo-de-datos.md."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Fuente:
    clave: str
    organismo: str
    titulo: str
    url: str
    conjunto: str | None
    licencia: str
    oficial: bool


@dataclass(frozen=True, slots=True)
class Municipio:
    divipola: str
    nombre: str
    nombre_oficial: str
    departamento_codigo: str
    departamento: str
    departamento_slug: str
    tipo: str
    slug: str
    lat: float | None
    lon: float | None


@dataclass(frozen=True, slots=True)
class Observacion:
    divipola: str
    indicador: str
    valor: float | int | str
    periodo: str
    fuente: str
