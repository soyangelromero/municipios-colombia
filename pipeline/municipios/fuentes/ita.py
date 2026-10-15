"""ITA: Índice de Transparencia y Acceso a la Información (Procuraduría General de la Nación).

Cada alcaldía diligencia un autodiagnóstico; la Procuraduría audita una parte. El conjunto trae
una fila por entidad, período, dimensión y categoría, así que se agrega en la API a un valor por
alcaldía y período. Solo trae nombres de departamento y municipio, y el NIT de la entidad: el
cruce con DIVIPOLA es por nombre, y de paso se arma el mapa NIT → DIVIPOLA que usa SECOP.
"""

import re
from typing import Any

from municipios.comun.contexto import Contexto, Resultado
from municipios.comun.cruce import Cruce, clave
from municipios.comun.modelos import Observacion

FUENTE = "pgn_ita"
CONJUNTO = "im79-n45d"
INDICADORES = ("ita_autodiagnostico", "ita_auditoria")


def descargar(contexto: Contexto) -> list[dict[str, Any]]:
    return contexto.cliente.consultar(
        CONJUNTO,
        select=(
            "periodo_medicion, departamento, municipio, sujeto_obligado, numero_documento,"
            " max(indicador_autodiagnostico::number) AS autodiagnostico,"
            " max(indicador_auditoria::number) AS auditoria"
        ),
        # Bogotá y los distritos figuran como «DISTRITAL», y algunos con naturaleza «NA»: por eso
        # no se filtra por naturaleza jurídica sino, después, por el nombre del sujeto obligado.
        where="tipo_orden IN ('MUNICIPAL', 'DISTRITAL')",
        group="periodo_medicion, departamento, municipio, sujeto_obligado, numero_documento",
        refrescar=contexto.refrescar,
    )


def periodo(texto: str) -> str:
    """'2019 SEMESTRE 2' -> '2019-S2'; '2026' -> '2026'."""
    semestre = re.fullmatch(r"(\d{4})\s+SEMESTRE\s+([12])", texto.strip().upper())
    return f"{semestre.group(1)}-S{semestre.group(2)}" if semestre else texto.strip()


def nit(texto: str) -> str:
    """NIT de 9 dígitos, sin dígito de verificación ni puntos ('8180013419' -> '818001341')."""
    return re.sub(r"\D", "", texto)[:9]


# La alcaldía (o su secretaría general, en Bogotá), no concejos, empresas ni alcaldías locales.
ES_ALCALDIA = re.compile(r"^(ALCALDIA (?!LOCAL)|MUNICIPIO DE |SECRETARIA GENERAL ALCALDIA MAYOR)")


def es_alcaldia(sujeto: str) -> bool:
    return bool(ES_ALCALDIA.match(clave(sujeto) + " "))


def normalizar(filas: list[dict[str, Any]], cruce: Cruce) -> tuple[Resultado, dict[str, str]]:
    """Observaciones de la alcaldía de cada municipio, por período, y el mapa NIT → DIVIPOLA.

    Solo cuentan los sujetos obligados que son la alcaldía (ver `ES_ALCALDIA`). Si una alcaldía
    reporta dos veces en un período, se toma el mayor puntaje.
    """
    elegidas: dict[tuple[str, str], dict[str, Any]] = {}
    nits: dict[str, str] = {}
    sin_cruce: dict[str, str] = {}
    for fila in filas:
        if not es_alcaldia(fila["sujeto_obligado"]):
            continue
        codigo = cruce.municipio(fila["departamento"], fila["municipio"])
        if codigo is None:
            sin_cruce[f"{fila['departamento']} / {fila['municipio']}"] = fila["sujeto_obligado"]
            continue
        nits[nit(fila["numero_documento"])] = codigo
        llave = (codigo, periodo(fila["periodo_medicion"]))
        actual = elegidas.get(llave)
        if actual is None or float(fila.get("autodiagnostico") or 0) > float(
            actual.get("autodiagnostico") or 0
        ):
            elegidas[llave] = fila

    observaciones = [
        Observacion(codigo, indicador, round(float(fila[campo]), 2), per, FUENTE)
        for (codigo, per), fila in sorted(elegidas.items())
        for indicador, campo in zip(INDICADORES, ("autodiagnostico", "auditoria"), strict=True)
        if fila.get(campo) not in (None, "")
    ]
    return Resultado(observaciones, sin_cruce=sin_cruce, notas={"nits": len(nits)}), nits


def ejecutar(contexto: Contexto) -> Resultado:
    resultado, _ = normalizar(descargar(contexto), contexto.cruce)
    return resultado


def mapa_nits(contexto: Contexto) -> dict[str, str]:
    """NIT de cada alcaldía → DIVIPOLA (para cruzar SECOP). Usa la misma descarga en caché."""
    _, nits = normalizar(descargar(contexto), contexto.cruce)
    return nits
