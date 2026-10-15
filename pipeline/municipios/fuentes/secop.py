"""SECOP II (Colombia Compra Eficiente): contratos firmados por cada alcaldía, por año.

Se agrega en la API por NIT de la entidad, año y modalidad. Para saber qué NIT es de cada
alcaldía se combinan dos fuentes:
1. SECOP mismo: entidades cuyo nombre indica alcaldía o municipio (y no concejo,
   personería, hospital, empresa…), cruzadas por departamento y ciudad, o por el nombre.
2. El ITA, que trae el NIT de cada alcaldía (complementa los casos que SECOP no resuelve).
Solo cuenta la administración central, no los entes descentralizados.

Limitación: SECOP II no incluye lo que algunas entidades todavía publican solo en SECOP I.
"""

import re
from collections import defaultdict
from datetime import date
from typing import Any

from municipios.comun import periodos
from municipios.comun.contexto import Contexto, Resultado
from municipios.comun.cruce import Cruce, clave
from municipios.comun.modelos import Observacion
from municipios.fuentes import ita

ES_ALCALDIA = re.compile(r"\b(ALCALDIA|MUNICIPIO|DISTRITO)\b")
NO_ES_ALCALDIA = re.compile(
    r"\b(CONCEJO|PERSONERIA|CONTRALORIA|HOSPITAL|ESE|E S E|INSTITUTO|INSTITUCION|EMPRESA|"
    r"EMPRESAS|ESP|E S P|COLEGIO|UNIVERSIDAD|TERMINAL|AREA METROPOLITANA|ASOCIACION|"
    r"CORPORACION|FONDO|BOMBEROS|ACUEDUCTO|TRANSITO|LOTERIA|CAJA|CENTRO)\b"
)
PREFIJO_ALCALDIA = re.compile(
    r"^(ALCALDIA|MUNICIPIO|DISTRITO)( (MUNICIPAL|DISTRITAL|ESPECIAL))?( DE| DEL)? "
)

FUENTE = "cce_secop2_contratos"
CONJUNTO = "jbjy-vk9h"
ANIO_INICIAL = 2020
MODALIDADES_DIRECTAS = frozenset({"Contratación directa", "Contratación Directa (con ofertas)"})
INDICADORES = (
    "contratos_numero",
    "contratos_valor",
    "contratos_directa_numero",
    "contratos_directa_valor",
)


def _rango_de_fechas(hoy: date) -> str:
    # Sin filtrar por «orden»: SECOP clasifica algunas alcaldías como «Nacional» (p. ej. Toledo).
    return (
        f"fecha_de_firma >= '{ANIO_INICIAL}-01-01T00:00:00'"
        f" AND fecha_de_firma < '{hoy.year + 1}-01-01T00:00:00'"
    )


def descargar(contexto: Contexto, hoy: date) -> list[dict[str, Any]]:
    return contexto.cliente.consultar(
        CONJUNTO,
        select="nit_entidad, date_extract_y(fecha_de_firma) AS anio,"
        " modalidad_de_contratacion AS modalidad, count(*) AS contratos,"
        " sum(valor_del_contrato) AS valor",
        where=_rango_de_fechas(hoy),
        group="nit_entidad, anio, modalidad",
        refrescar=contexto.refrescar,
    )


def descargar_entidades(contexto: Contexto, hoy: date) -> list[dict[str, Any]]:
    """Entidades con contratos: NIT, nombre, departamento y ciudad."""
    return contexto.cliente.consultar(
        CONJUNTO,
        select="nit_entidad, nombre_entidad, departamento, ciudad, count(*) AS contratos",
        where=_rango_de_fechas(hoy),
        group="nit_entidad, nombre_entidad, departamento, ciudad",
        refrescar=contexto.refrescar,
    )


def alcaldias_por_nombre(entidades: list[dict[str, Any]], cruce: Cruce) -> dict[str, str]:
    """NIT → DIVIPOLA de las entidades de SECOP que son alcaldías.

    Se identifica la alcaldía por el nombre y el municipio por la ciudad declarada; si la ciudad
    no está definida, por el nombre sin el prefijo («ALCALDIA MUNICIPAL DE …»).
    """
    nits: dict[str, str] = {}
    for entidad in entidades:
        nombre = clave(entidad.get("nombre_entidad", ""))
        if not ES_ALCALDIA.search(nombre) or NO_ES_ALCALDIA.search(nombre):
            continue
        departamento = entidad.get("departamento", "")
        ciudad = entidad.get("ciudad", "")
        codigo = None
        if ciudad and clave(ciudad) != "NO DEFINIDO":
            codigo = cruce.municipio(departamento, ciudad)
        if codigo is None:
            codigo = cruce.municipio(departamento, PREFIJO_ALCALDIA.sub("", nombre))
        if codigo is not None:
            nits[ita.nit(entidad["nit_entidad"])] = codigo
    return nits


def normalizar(filas: list[dict[str, Any]], nits: dict[str, str], hoy: date) -> Resultado:
    """Totales por alcaldía y año; el año en curso va como acumulado parcial hasta `hoy`."""
    valores: dict[tuple[str, str, str], float] = defaultdict(float)
    alcaldias = set()
    for fila in filas:
        codigo = nits.get(ita.nit(fila["nit_entidad"]))
        if codigo is None:
            continue  # otra entidad territorial (gobernación, hospital, instituto…)
        alcaldias.add(codigo)
        anio = int(fila["anio"])
        per = periodos.anual(anio, hoy.month) if anio == hoy.year else periodos.anual(anio)
        numero, valor = float(fila["contratos"]), float(fila.get("valor") or 0)
        valores[(codigo, "contratos_numero", per)] += numero
        valores[(codigo, "contratos_valor", per)] += valor
        if fila.get("modalidad") in MODALIDADES_DIRECTAS:
            valores[(codigo, "contratos_directa_numero", per)] += numero
            valores[(codigo, "contratos_directa_valor", per)] += valor

    observaciones = [
        Observacion(codigo, indicador, round(valor), per, FUENTE)
        for (codigo, indicador, per), valor in sorted(valores.items())
    ]
    return Resultado(observaciones, notas={"alcaldias_con_contratos": len(alcaldias)})


def ejecutar(contexto: Contexto) -> Resultado:
    hoy = date.today()
    por_secop = alcaldias_por_nombre(descargar_entidades(contexto, hoy), contexto.cruce)
    # Lo que identifica SECOP manda: el ITA a veces trae NIT mal digitados.
    nits = {**ita.mapa_nits(contexto), **por_secop}
    resultado = normalizar(descargar(contexto, hoy), nits, hoy)
    resultado.notas["nits_por_secop"] = len(por_secop)
    resultado.notas["nits_total"] = len(nits)
    return resultado
