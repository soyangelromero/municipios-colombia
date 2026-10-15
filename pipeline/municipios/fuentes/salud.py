"""Afiliación al sistema de salud (ADRES, Base de Datos Única de Afiliados), por municipio.

Es una foto del momento: el período es la fecha de la última actualización del conjunto. Trae
solo nombres de departamento y municipio, así que se cruza por nombre.
"""

from collections import defaultdict
from typing import Any

from municipios.comun.contexto import Contexto, Resultado
from municipios.comun.cruce import Cruce
from municipios.comun.modelos import Observacion

# conjunto -> (indicador, fuente)
CONJUNTOS = {
    "d7a5-cnra": ("afiliados_subsidiado", "adres_bdua_subsidiado"),
    "tq4m-hmg2": ("afiliados_contributivo", "adres_bdua_contributivo"),
}
INDICADORES = tuple(indicador for indicador, _ in CONJUNTOS.values())


def descargar(contexto: Contexto, conjunto: str) -> tuple[list[dict[str, Any]], str]:
    """Filas agregadas por municipio y fecha de actualización del conjunto."""
    filas = contexto.cliente.consultar(
        conjunto,
        select="dpr_nombre, mnc_nombre, sum(cantidad::number) AS afiliados",
        where="tps_est_afl_nombre = 'Activo'",
        group="dpr_nombre, mnc_nombre",
        refrescar=contexto.refrescar,
    )
    return filas, contexto.cliente.fecha_actualizacion(conjunto)


def normalizar(filas: list[dict[str, Any]], conjunto: str, fecha: str, cruce: Cruce) -> Resultado:
    indicador, fuente = CONJUNTOS[conjunto]
    totales: dict[str, int] = defaultdict(int)
    sin_cruce: dict[str, int] = {}
    for fila in filas:
        codigo = cruce.municipio(fila["dpr_nombre"], fila["mnc_nombre"])
        afiliados = round(float(fila["afiliados"]))
        if codigo is None:
            sin_cruce[f"{fila['dpr_nombre']} / {fila['mnc_nombre']}"] = afiliados
        else:
            totales[codigo] += afiliados
    periodo = fecha[:7]  # AAAA-MM
    observaciones = [
        Observacion(codigo, indicador, total, periodo, fuente)
        for codigo, total in sorted(totales.items())
    ]
    return Resultado(observaciones, sin_cruce=sin_cruce)


def ejecutar(contexto: Contexto) -> Resultado:
    resultado = Resultado([])
    for conjunto in CONJUNTOS:
        filas, fecha = descargar(contexto, conjunto)
        parcial = normalizar(filas, conjunto, fecha, contexto.cruce)
        resultado.observaciones.extend(parcial.observaciones)
        resultado.sin_cruce.update(parcial.sin_cruce)
    return resultado
