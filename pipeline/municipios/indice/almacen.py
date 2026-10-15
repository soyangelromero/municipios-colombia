"""Lectura de las observaciones de todas las fuentes (datos/intermedios/*.json)."""

import re
from collections import defaultdict
from pathlib import Path

from municipios.comun.modelos import Observacion
from municipios.comun.salida import leer_json

ANUAL = re.compile(r"\d{4}")


def clave_periodo(periodo: str) -> tuple[int, int]:
    """(año, mes final) para ordenar períodos de distinto tipo.

    '2025' -> (2025, 12) · '2026-01/2026-08' -> (2026, 8) · '2019-S2' -> (2019, 12) ·
    '2026-10' -> (2026, 10).
    """
    if ANUAL.fullmatch(periodo):
        return int(periodo), 12
    if m := re.fullmatch(r"(\d{4})-S([12])", periodo):
        return int(m.group(1)), 6 * int(m.group(2))
    if m := re.fullmatch(r"\d{4}-\d{2}/(\d{4})-(\d{2})", periodo):
        return int(m.group(1)), int(m.group(2))
    if m := re.fullmatch(r"(\d{4})-(\d{2})", periodo):
        return int(m.group(1)), int(m.group(2))
    raise ValueError(f"Período no reconocido: {periodo!r}")


class Almacen:
    """Observaciones indexadas por (municipio, indicador), ordenadas por período."""

    def __init__(self, observaciones: list[Observacion]) -> None:
        self._datos: dict[tuple[str, str], list[Observacion]] = defaultdict(list)
        for o in observaciones:
            self._datos[(o.divipola, o.indicador)].append(o)
        for lista in self._datos.values():
            lista.sort(key=lambda o: clave_periodo(o.periodo))

    @classmethod
    def desde_directorio(cls, directorio: Path) -> "Almacen":
        observaciones = []
        for ruta in sorted(directorio.glob("*.json")):
            contenido = leer_json(ruta)
            if isinstance(contenido, dict) and "observaciones" in contenido:
                observaciones.extend(Observacion(**o) for o in contenido["observaciones"])
        return cls(observaciones)

    def serie(self, divipola: str, indicador: str) -> list[Observacion]:
        return self._datos.get((divipola, indicador), [])

    def ultimo(self, divipola: str, indicador: str) -> Observacion | None:
        serie = self.serie(divipola, indicador)
        return serie[-1] if serie else None

    def anual(self, divipola: str, indicador: str, anio: int) -> Observacion | None:
        """Observación del año completo `anio` (no los acumulados parciales)."""
        for o in self.serie(divipola, indicador):
            if o.periodo == str(anio):
                return o
        return None

    def anio_referencia(self, indicador: str, cobertura_minima: float = 0.5) -> int | None:
        """Último año completo con datos para al menos esa fracción de los municipios con datos.

        Así todos los municipios se comparan con el mismo año, aunque algunos ya hayan reportado
        uno más reciente.
        """
        por_anio: dict[int, int] = defaultdict(int)
        municipios = set()
        for (codigo, ind), serie in self._datos.items():
            if ind != indicador:
                continue
            municipios.add(codigo)
            for o in serie:
                if ANUAL.fullmatch(o.periodo):
                    por_anio[int(o.periodo)] += 1
        candidatos = [a for a, n in por_anio.items() if n >= cobertura_minima * len(municipios)]
        return max(candidatos) if candidatos else None
