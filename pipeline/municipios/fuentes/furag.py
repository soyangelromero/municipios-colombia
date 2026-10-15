"""FURAG (Función Pública): Índice de Desempeño Institucional y componentes, por alcaldía.

El conjunto solo trae el código SIGEP de la entidad; se cruza con DIVIPOLA mediante el mapa que
arma `gobierno_digital.mapa_sigep`.
"""

from typing import Any

from municipios.comun.contexto import Contexto, Resultado
from municipios.comun.modelos import Observacion
from municipios.comun.textos import sin_separador_miles
from municipios.fuentes.gobierno_digital import codigo_sigep, mapa_sigep

FUENTE = "funcion_publica_furag"
CONJUNTO = "daed-z4fw"
INDICES = {
    "IDI": "furag_desempeno_institucional",
    "D7": "furag_control_interno",
    "I09": "furag_publicacion_contractual",
    "I18": "furag_estado_abierto",
}
INDICADORES = tuple(INDICES.values())


def descargar(contexto: Contexto) -> list[dict[str, Any]]:
    ids = ", ".join(f"'{i}'" for i in INDICES)
    return contexto.cliente.consultar(
        CONJUNTO,
        select="c_digo_sigep, entidad, vigencia, id_indice, puntaje_entidad",
        where=f"orden = 'TERRITORIAL' AND upper(entidad) LIKE 'ALCALD%' AND id_indice IN ({ids})",
        order="c_digo_sigep, vigencia, id_indice",
        refrescar=contexto.refrescar,
    )


def normalizar(filas: list[dict[str, Any]], sigep: dict[str, str]) -> Resultado:
    observaciones: list[Observacion] = []
    sin_cruce: dict[str, str] = {}
    for fila in filas:
        codigo = sigep.get(codigo_sigep(fila["c_digo_sigep"]))
        if codigo is None:
            sin_cruce[codigo_sigep(fila["c_digo_sigep"])] = fila["entidad"]
            continue
        if fila.get("puntaje_entidad") in (None, ""):
            continue
        observaciones.append(
            Observacion(
                divipola=codigo,
                indicador=INDICES[fila["id_indice"]],
                valor=round(float(fila["puntaje_entidad"]), 2),
                periodo=sin_separador_miles(fila["vigencia"]),
                fuente=FUENTE,
            )
        )
    observaciones.sort(key=lambda o: (o.divipola, o.indicador, o.periodo))
    return Resultado(observaciones, sin_cruce=sin_cruce)


def ejecutar(contexto: Contexto) -> Resultado:
    return normalizar(descargar(contexto), mapa_sigep(contexto))
