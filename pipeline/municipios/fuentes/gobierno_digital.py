"""Índice de Gobierno Digital (MinTIC), por alcaldía y vigencia.

Además de su puntaje, este conjunto es la llave para cruzar FURAG: trae el código SIGEP de cada
alcaldía junto con su código DIVIPOLA (FURAG solo trae el código SIGEP).
"""

from typing import Any

from municipios.comun.contexto import Contexto, Resultado
from municipios.comun.modelos import Observacion
from municipios.comun.textos import sin_separador_miles

FUENTE = "mintic_gobierno_digital"
CONJUNTO = "rtai-k9uh"
# id del índice en la fuente -> indicador del proyecto. POL07 es el índice actual (desde 2025);
# POL06 es el puntaje de la política medido en FURAG en vigencias anteriores.
INDICES = {"POL07": "indice_gobierno_digital", "POL06": "politica_gobierno_digital"}
INDICADORES = tuple(INDICES.values())


def codigo_sigep(texto: str) -> str:
    """Código SIGEP comparable entre conjuntos: '6,418' -> '6418'; '0039' -> '39'."""
    return sin_separador_miles(texto).lstrip("0") or "0"


def descargar(contexto: Contexto) -> list[dict[str, Any]]:
    ids = ", ".join(f"'{i}'" for i in INDICES)
    return contexto.cliente.consultar(
        CONJUNTO,
        select="c_digo_sigep, id_municipio, vigencia, id_ndice, puntaje_entidad",
        where=f"naturaleza_jur_dica = 'ALCALDÍA' AND id_ndice IN ({ids})",
        refrescar=contexto.refrescar,
        order="c_digo_sigep, vigencia, id_ndice",
    )


def normalizar(filas: list[dict[str, Any]], codigos: set[str]) -> tuple[Resultado, dict[str, str]]:
    observaciones: list[Observacion] = []
    sigep: dict[str, str] = {}
    sin_cruce: dict[str, str] = {}
    for fila in filas:
        codigo = str(fila["id_municipio"]).strip().zfill(5)
        if codigo not in codigos:
            sin_cruce[codigo] = codigo_sigep(fila["c_digo_sigep"])
            continue
        sigep[codigo_sigep(fila["c_digo_sigep"])] = codigo
        if fila.get("puntaje_entidad") not in (None, ""):
            observaciones.append(
                Observacion(
                    divipola=codigo,
                    indicador=INDICES[fila["id_ndice"]],
                    valor=round(float(fila["puntaje_entidad"]), 2),
                    periodo=sin_separador_miles(fila["vigencia"]),
                    fuente=FUENTE,
                )
            )
    observaciones.sort(key=lambda o: (o.divipola, o.indicador, o.periodo))
    return Resultado(observaciones, sin_cruce=sin_cruce), sigep


def ejecutar(contexto: Contexto) -> Resultado:
    resultado, _ = normalizar(descargar(contexto), contexto.codigos)
    return resultado


def mapa_sigep(contexto: Contexto) -> dict[str, str]:
    """Código SIGEP de cada alcaldía → DIVIPOLA (para cruzar FURAG)."""
    _, sigep = normalizar(descargar(contexto), contexto.codigos)
    return sigep
