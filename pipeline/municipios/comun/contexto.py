"""Contexto compartido por las fuentes y el resultado que cada una devuelve."""

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any

from municipios.comun.cruce import Cruce
from municipios.comun.modelos import Municipio, Observacion
from municipios.comun.socrata import ClienteSocrata


@dataclass
class Contexto:
    cliente: ClienteSocrata
    municipios: dict[str, Municipio]  # por código DIVIPOLA
    dir_crudos: Path
    refrescar: bool = False
    tolerante: bool = False  # en `todo`, seguir aunque una fuente falle

    @property
    def codigos(self) -> set[str]:
        return set(self.municipios)

    @cached_property
    def cruce(self) -> Cruce:
        return Cruce(self.municipios.values())

    def reemplazar_municipios(self, municipios: dict[str, Municipio]) -> None:
        """Cambia la lista de municipios y descarta el cruce por nombre ya calculado."""
        self.municipios = municipios
        self.__dict__.pop("cruce", None)


@dataclass
class Resultado:
    """Lo que devuelve `ejecutar()` de cada fuente."""

    observaciones: list[Observacion]
    sin_cruce: dict[str, Any] = field(default_factory=dict)  # códigos o nombres sin DIVIPOLA
    notas: dict[str, Any] = field(default_factory=dict)  # datos útiles para revisar la fuente
