"""Alcalde vigente de cada municipio, de las «Personas Expuestas Políticamente» de SIGEP II.

La Función Pública publica en datos.gov.co (conjunto 3qxn-uc22) las personas que la ley obliga a
declararse expuestas políticamente, entre ellas los alcaldes: nombre, cargo, entidad y fecha de
posesión. No trae el código del municipio, así que se une por el nombre de la entidad con el
conjunto de caracterización del empleo público (h8rs-jxum), que sí trae el NIT, y el NIT con
DIVIPOLA por el mapa del ITA.

Solo se publica un nombre cuando no hay duda: una única persona vigente (sin fecha de
desvinculación) posesionada desde el inicio del período. Si hay dos o más (encargados, suspensiones
sin cerrar) o ninguna, el municipio queda sin alcalde en la ficha: es mejor no mostrar nada que
mostrar a la persona equivocada. No es una fuente de indicadores, no puntúa.
"""

from collections.abc import Iterable
from datetime import date
from typing import Any

from municipios.comun.contexto import Contexto
from municipios.comun.salida import ahora_iso, escribir_json
from municipios.fuentes import ita

CONJUNTO_PEP = "3qxn-uc22"
CONJUNTO_ENTIDADES = "h8rs-jxum"
URL_FUENTE = f"https://www.datos.gov.co/d/{CONJUNTO_PEP}"
INICIO_PERIODO = date(2024, 1, 1)  # período 2024-2027; cambiar en las elecciones de 2027
CARGOS = frozenset({"ALCALDE", "ALCALDE MAYOR"})
MINUSCULAS = frozenset({"de", "del", "la", "las", "los", "y", "e", "da", "dos", "van", "von"})


def titulo(nombre: str) -> str:
    """'MARIA DE LOS ANGELES PEREZ' -> 'María de los Angeles Perez' (sin inventar tildes)."""
    palabras = nombre.lower().split()
    return " ".join(
        p if i and p in MINUSCULAS else "-".join(t.capitalize() for t in p.split("-"))
        for i, p in enumerate(palabras)
    )


def _fecha(texto: str) -> date | None:
    """'1/01/2024' -> date(2024, 1, 1)."""
    try:
        dia, mes, anio = (int(x) for x in texto.split("/"))
        return date(anio, mes, dia)
    except ValueError:
        return None


def elegir(
    personas: Iterable[dict[str, Any]],
    entidades: Iterable[dict[str, Any]],
    nits: dict[str, str],
    inicio: date = INICIO_PERIODO,
) -> tuple[dict[str, dict[str, str]], dict[str, int]]:
    """Alcalde vigente por DIVIPOLA y un conteo de lo que quedó sin resolver."""
    por_nombre: dict[str, str] = {}
    for e in entidades:
        codigo = nits.get(ita.nit(str(e.get("nit", ""))))
        if codigo:
            por_nombre[e["nombre_de_la_entidad"]] = codigo

    vigentes: dict[str, list[tuple[date, str]]] = {}
    for p in personas:
        if p.get("denominacion_cargo") not in CARGOS or p.get("fecha_desvinculacion"):
            continue
        codigo = por_nombre.get(p.get("nombre_entidad", ""))
        desde = _fecha(p.get("fecha_vinculacion", ""))
        if codigo and desde and desde >= inicio:
            vigentes.setdefault(codigo, []).append((desde, p["nombre_pep"]))

    elegidos: dict[str, dict[str, str]] = {}
    dudosos = 0
    for codigo, lista in vigentes.items():
        nombres = {nombre for _, nombre in lista}
        if len(nombres) > 1:
            dudosos += 1
            continue
        elegidos[codigo] = {
            "nombre": titulo(nombres.pop()),
            "desde": min(d for d, _ in lista).isoformat(),
            "fuente": URL_FUENTE,
        }
    return elegidos, {"con_alcalde": len(elegidos), "dudosos": dudosos}


def ejecutar(contexto: Contexto, salida) -> int:
    """Descarga, elige y guarda datos/intermedios/alcaldes.json. Devuelve cuántos municipios."""
    personas = contexto.cliente.consultar(
        CONJUNTO_PEP,
        select="nombre_pep, denominacion_cargo, nombre_entidad, fecha_vinculacion,"
        " fecha_desvinculacion",
        where="denominacion_cargo in ('ALCALDE', 'ALCALDE MAYOR')",
        refrescar=contexto.refrescar,
    )
    entidades = contexto.cliente.consultar(
        CONJUNTO_ENTIDADES,
        select="nombre_de_la_entidad, nit",
        where="orden = 'TERRITORIAL' AND nivel = 'CENTRAL'",
        refrescar=contexto.refrescar,
    )
    elegidos, notas = elegir(personas, entidades, ita.mapa_nits(contexto))
    corte = contexto.cliente.fecha_actualizacion(CONJUNTO_PEP)
    escribir_json(
        salida,
        {"generado": ahora_iso(), "corte": corte, "fuente": URL_FUENTE, "notas": notas,
         "alcaldes": elegidos},
    )  # fmt: skip
    return len(elegidos)
