"""Educación preescolar, básica y media (Ministerio de Educación), por municipio y año."""

from typing import Any

from municipios.comun.contexto import Contexto, Resultado
from municipios.comun.modelos import Observacion

FUENTE = "men_estadisticas_educacion"
CONJUNTO = "nudc-7mev"
ANIO_INICIAL = 2018
CAMPOS = {
    "cobertura_neta": "educacion_cobertura_neta",
    "cobertura_bruta": "educacion_cobertura_bruta",
    "deserci_n": "educacion_desercion",
    "reprobaci_n": "educacion_reprobacion",
}
INDICADORES = tuple(CAMPOS.values())


def descargar(contexto: Contexto) -> list[dict[str, Any]]:
    return contexto.cliente.consultar(
        CONJUNTO,
        select=", ".join(["a_o", "c_digo_municipio", *CAMPOS]),
        where=f"a_o >= '{ANIO_INICIAL}'",
        order="c_digo_municipio, a_o",
        refrescar=contexto.refrescar,
    )


def normalizar(filas: list[dict[str, Any]], codigos: set[str]) -> Resultado:
    observaciones: list[Observacion] = []
    sin_cruce: dict[str, str] = {}
    for fila in filas:
        codigo = str(fila["c_digo_municipio"]).strip().zfill(5)
        if codigo not in codigos:
            sin_cruce[codigo] = fila["a_o"]
            continue
        for campo, indicador in CAMPOS.items():
            if fila.get(campo) not in (None, ""):
                observaciones.append(
                    Observacion(
                        codigo, indicador, round(float(fila[campo]), 2), fila["a_o"], FUENTE
                    )
                )
    return Resultado(observaciones, sin_cruce=sin_cruce)


def ejecutar(contexto: Contexto) -> Resultado:
    return normalizar(descargar(contexto), contexto.codigos)
