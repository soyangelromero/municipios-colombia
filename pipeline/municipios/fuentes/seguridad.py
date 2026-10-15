"""Seguridad (Ministerio de Defensa / Policía Nacional): delitos por municipio y año.

Los conjuntos traen una fila por hecho (o por día y municipio) con una columna «cantidad».
Se agregan en la API por municipio y año para descargar poco.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any

from municipios.comun import periodos
from municipios.comun.contexto import Contexto, Resultado
from municipios.comun.modelos import Observacion
from municipios.comun.socrata import ClienteSocrata

ANIO_INICIAL = 2018


@dataclass(frozen=True, slots=True)
class Delito:
    indicador: str
    conjunto: str
    fuente: str


DELITOS = (
    Delito("homicidios", "m8fd-ahd9", "mindefensa_homicidios"),
    Delito("hurto_personas", "4rxi-8m8d", "mindefensa_hurto_personas"),
)
INDICADORES = tuple(d.indicador for d in DELITOS)


def descargar(
    cliente: ClienteSocrata, delito: Delito, refrescar: bool = False
) -> tuple[list[dict[str, Any]], date]:
    """Devuelve (filas agregadas por municipio y año, fecha del último hecho registrado)."""
    filas = cliente.consultar(
        delito.conjunto,
        select="cod_muni, date_extract_y(fecha_hecho) AS anio, sum(cantidad) AS total",
        where=f"fecha_hecho >= '{ANIO_INICIAL}-01-01T00:00:00'",
        group="cod_muni, anio",
        order="cod_muni, anio",
        refrescar=refrescar,
    )
    ultima = cliente.consultar(
        delito.conjunto, select="max(fecha_hecho) AS ultima", refrescar=refrescar
    )
    return filas, date.fromisoformat(ultima[0]["ultima"][:10])


def periodo(anio: int, ultima_fecha: date) -> str:
    """Año completo ('2025') o rango parcial del año en curso ('2026-01/2026-08')."""
    if anio == ultima_fecha.year and (ultima_fecha.month, ultima_fecha.day) != (12, 31):
        return periodos.anual(anio, ultima_fecha.month)
    return periodos.anual(anio)


def normalizar(
    filas: list[dict[str, Any]],
    delito: Delito,
    ultima_fecha: date,
    divipolas: set[str],
) -> tuple[list[Observacion], dict[str, int]]:
    """Observaciones por municipio y año, con ceros explícitos.

    En un registro policial, que un municipio no aparezca en un año significa cero hechos
    reportados, así que se completa con 0 para cada municipio de `divipolas`.
    Devuelve también los códigos que no cruzan con DIVIPOLA y cuántos hechos suman.
    """
    totales: dict[tuple[str, int], int] = {}
    sin_cruce: dict[str, int] = {}
    for fila in filas:
        codigo = str(fila["cod_muni"]).strip().zfill(5)
        cantidad = int(float(fila["total"]))
        if codigo not in divipolas:
            sin_cruce[codigo] = sin_cruce.get(codigo, 0) + cantidad
            continue
        clave = (codigo, int(fila["anio"]))
        totales[clave] = totales.get(clave, 0) + cantidad

    observaciones = [
        Observacion(
            divipola=codigo,
            indicador=delito.indicador,
            valor=totales.get((codigo, anio), 0),
            periodo=periodo(anio, ultima_fecha),
            fuente=delito.fuente,
        )
        for codigo in sorted(divipolas)
        for anio in range(ANIO_INICIAL, ultima_fecha.year + 1)
    ]
    return observaciones, sin_cruce


def ejecutar(contexto: Contexto) -> Resultado:
    resultado = Resultado([])
    for delito in DELITOS:
        filas, ultima = descargar(contexto.cliente, delito, contexto.refrescar)
        observaciones, sin_cruce = normalizar(filas, delito, ultima, contexto.codigos)
        resultado.observaciones.extend(observaciones)
        if sin_cruce:
            resultado.sin_cruce[delito.indicador] = sin_cruce
        resultado.notas[f"{delito.indicador}_datos_hasta"] = ultima.isoformat()
    return resultado
