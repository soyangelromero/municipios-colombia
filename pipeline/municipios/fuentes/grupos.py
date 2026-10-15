"""Grupos de capacidades iniciales del DNP (Medición de Desempeño Municipal, MDM).

El DNP agrupa a los municipios en Ciudades y G1 a G5 según sus «dotaciones iniciales» (población
urbana, densidad, recursos propios…). Es la agrupación oficial para comparar municipios
parecidos, y el índice la usa para definir los pares. Se toma la última medición publicada en
datos abiertos (2020), con su puntaje MDM como dato de contexto.
"""

from typing import Any

from municipios.comun.contexto import Contexto, Resultado
from municipios.comun.modelos import Observacion

FUENTE = "dnp_mdm"
CONJUNTO = "nkjx-rsq7"
INDICADORES = ("grupo_capacidades", "mdm_puntaje")
PERIODO_MDM = "2020"  # última medición en datos abiertos; se usa también para los asignados

# Etiqueta del DNP -> código corto del grupo.
GRUPOS = {
    "Ciudades": "C",
    "G1- Nivel Alto": "G1",
    "G2- Nivel Medio Alto": "G2",
    "G3- Nivel Medio": "G3",
    "G4- Nivel Medio Bajo": "G4",
    "G5- Nivel Bajo": "G5",
}

# Municipios creados después de la medición: toman el grupo del municipio del que se segregaron
# (o G5 si se formaron con áreas no municipalizadas). Se marcan como asignados por el proyecto.
ORIGEN_DE_MUNICIPIOS_NUEVOS = {
    "27493": "27615",  # Nuevo Belén de Bajirá, segregado de Riosucio (Chocó)
}
GRUPO_POR_DEFECTO_NUEVOS = {
    "94343": "G5",  # Barrancominas, formado con áreas no municipalizadas de Guainía
}


def descargar(contexto: Contexto) -> list[dict[str, Any]]:
    return contexto.cliente.consultar(
        CONJUNTO,
        select="codigo_entidad, anio, indicador, etiqueta, dato",
        where="indicador IN ('Grupo de dotaciones iniciales', 'MDM')",
        order="codigo_entidad, anio, indicador",
        refrescar=contexto.refrescar,
    )


def normalizar(filas: list[dict[str, Any]], codigos: set[str]) -> Resultado:
    """Grupo y puntaje MDM de la medición más reciente de cada municipio."""
    ultimas: dict[tuple[str, str], dict[str, Any]] = {}
    for fila in filas:
        codigo = str(fila["codigo_entidad"]).strip().zfill(5)
        clave = (codigo, fila["indicador"])
        if clave not in ultimas or fila["anio"] > ultimas[clave]["anio"]:
            ultimas[clave] = fila

    observaciones: list[Observacion] = []
    sin_cruce: dict[str, str] = {}
    grupos: dict[str, tuple[str, str]] = {}
    for (codigo, indicador), fila in sorted(ultimas.items()):
        if codigo not in codigos:
            sin_cruce[codigo] = fila["indicador"]
            continue
        if indicador == "MDM" and fila.get("dato"):
            observaciones.append(
                Observacion(
                    codigo, "mdm_puntaje", round(float(fila["dato"]), 2), fila["anio"], FUENTE
                )
            )
        elif fila.get("etiqueta") in GRUPOS:
            grupos[codigo] = (GRUPOS[fila["etiqueta"]], fila["anio"])

    asignados = {}
    for nuevo, origen in ORIGEN_DE_MUNICIPIOS_NUEVOS.items():
        if nuevo in codigos and nuevo not in grupos and origen in grupos:
            grupos[nuevo] = grupos[origen]
            asignados[nuevo] = f"grupo de {origen}"
    for nuevo, grupo in GRUPO_POR_DEFECTO_NUEVOS.items():
        if nuevo in codigos and nuevo not in grupos:
            grupos[nuevo] = (grupo, PERIODO_MDM)
            asignados[nuevo] = grupo

    observaciones.extend(
        Observacion(codigo, "grupo_capacidades", grupo, periodo, FUENTE)
        for codigo, (grupo, periodo) in sorted(grupos.items())
    )
    return Resultado(observaciones, sin_cruce=sin_cruce, notas={"asignados": asignados})


def ejecutar(contexto: Contexto) -> Resultado:
    return normalizar(descargar(contexto), contexto.codigos)
