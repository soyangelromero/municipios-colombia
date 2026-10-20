"""Cruce del relevamiento con fuentes oficiales nacionales (sin buscadores).

Si el sitio de la alcaldía no deja ver un criterio pero una fuente oficial sí muestra que el
municipio publica o reporta ese dato, el criterio no queda como «no hallado» sin más: pasa a
`fuente_oficial`, con la URL de la fuente y un detalle. Sigue siendo una revisión automática,
sin verificación humana: que una fuente nacional tenga el dato no prueba que la alcaldía lo
publique en su propio sitio, solo que existe.

Fuentes usadas (todas en datos.gov.co, sin raspar páginas):
- SECOP II (Colombia Compra Eficiente) -> contratación; sale de datos/intermedios/contratacion.json.
- SIGEP II (Función Pública), «Caracterización del Empleo Público» -> directorio y salarios.
- Catálogo de datos.gov.co -> los conjuntos que la propia alcaldía publica como entidad
  (datos abiertos, y los criterios cuyo nombre aparezca en el título de un conjunto).

No se cruza con el Kit de Planeación Territorial (DNP): no tiene API ni datos abiertos por
municipio que se puedan leer sin raspar su portal. Ver docs/metodologia.md.
"""

import logging
import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from municipios.comun.contexto import Contexto
from municipios.comun.cruce import clave
from municipios.comun.salida import escribir_json, leer_json
from municipios.fuentes import ita
from municipios.relevamiento.criterios import CRITERIOS, clasificar

log = logging.getLogger(__name__)

URL_SECOP = "https://www.datos.gov.co/d/jbjy-vk9h"
CONJUNTO_SIGEP = "h8rs-jxum"
URL_SIGEP = f"https://www.datos.gov.co/d/{CONJUNTO_SIGEP}"
URL_CATALOGO = "https://api.us.socrata.com/api/catalog/v1"
TAM_PAGINA_CATALOGO = 1000

ES_ENTIDAD_MUNICIPAL = re.compile(r"^(ALCALDIA (?!LOCAL)|MUNICIPIO DE |DISTRITO )")


@dataclass(frozen=True, slots=True)
class Evidencia:
    url: str
    detalle: str
    metodo: str  # «cruce_secop», «cruce_sigep» o «cruce_datos_gov_co»


# Por municipio (DIVIPOLA) y criterio.
Cruces = dict[str, dict[str, Evidencia]]


def _codigo(texto: Any) -> str:
    digitos = re.sub(r"\D", "", str(texto or ""))
    return digitos.zfill(5) if digitos else ""


def _moneda(valor: float) -> str:
    return "$" + f"{round(valor):,}".replace(",", ".")


def cruces_secop(observaciones: Iterable[dict[str, Any]], anio_actual: int) -> Cruces:
    """Contratación: alcaldías con contratos firmados en SECOP II el año pasado o este."""
    ultimo: dict[str, tuple[str, float]] = {}
    for o in observaciones:
        if o.get("indicador") != "contratos_numero" or not o.get("valor"):
            continue
        periodo = str(o["periodo"])
        if not periodo.isdigit() or int(periodo) < anio_actual - 1:
            continue
        if o["divipola"] not in ultimo or periodo > ultimo[o["divipola"]][0]:
            ultimo[o["divipola"]] = (periodo, o["valor"])
    return {
        codigo: {
            "contratacion": Evidencia(
                URL_SECOP,
                f"SECOP II: {int(valor):,} contratos firmados en {periodo}".replace(",", "."),
                "cruce_secop",
            )
        }
        for codigo, (periodo, valor) in ultimo.items()
    }


def cruces_sigep(filas: Iterable[dict[str, Any]], nits: dict[str, str]) -> Cruces:
    """Directorio y salarios: alcaldías con servidores registrados en SIGEP II.

    SIGEP casi nunca trae el código del municipio, así que se cruza por NIT (el mapa
    NIT → DIVIPOLA del ITA). Si la fila trae el código, se usa con el nombre de la entidad.
    """
    resultado: Cruces = {}
    for f in filas:
        codigo = nits.get(ita.nit(str(f.get("nit", ""))), "")
        if not codigo:
            if not ES_ENTIDAD_MUNICIPAL.match(clave(f.get("nombre_de_la_entidad", "")) + " "):
                continue
            codigo = _codigo(f.get("c_digo_divipola_municipio"))
        servidores = sum(
            int(float(f.get(k) or 0))
            for k in ("genero_hombre", "genero_mujer", "genero_no_binario")
        )
        if not codigo or servidores <= 0:
            continue
        salario = float(f.get("salario_mensual_promedio") or 0)
        corte = f"{f.get('mes', '')}/{f.get('a_o', '')}".strip("/")
        detalle = f"SIGEP II ({corte}): {servidores} servidores registrados"
        if salario > 0:
            detalle += f", salario mensual promedio {_moneda(salario)}"
        resultado[codigo] = {"directorio": Evidencia(URL_SIGEP, detalle, "cruce_sigep")}
    return resultado


def cruces_catalogo(conjuntos: Iterable[dict[str, str]]) -> Cruces:
    """Conjuntos que la alcaldía publica en datos.gov.co: datos abiertos y criterios por título.

    Cada conjunto es {divipola, entidad, nombre, url}. Solo cuentan los publicados por la
    alcaldía o el distrito mismo (no por la gobernación ni otra entidad, aunque traten el
    municipio).
    """
    por_municipio: dict[str, list[dict[str, str]]] = defaultdict(list)
    for c in conjuntos:
        if c["divipola"] and ES_ENTIDAD_MUNICIPAL.match(clave(c["entidad"]) + " "):
            por_municipio[c["divipola"]].append(c)
    resultado: Cruces = {}
    for codigo, lista in por_municipio.items():
        evidencias = {
            "datos_abiertos": Evidencia(
                lista[0]["url"],
                f"datos.gov.co: la alcaldía publica {len(lista)} conjunto(s) de datos abiertos",
                "cruce_datos_gov_co",
            )
        }
        for criterio, url in clasificar((c["nombre"], c["url"]) for c in lista).items():
            if url and criterio != "datos_abiertos":
                nombre = next(c["nombre"] for c in lista if c["url"] == url)
                evidencias[criterio] = Evidencia(
                    url, f"datos.gov.co: conjunto «{nombre}»", "cruce_datos_gov_co"
                )
        resultado[codigo] = evidencias
    return resultado


def combinar(*fuentes: Cruces) -> Cruces:
    """Une los cruces; ante el mismo criterio gana la fuente que va primero."""
    resultado: Cruces = defaultdict(dict)
    for fuente in fuentes:
        for codigo, por_criterio in fuente.items():
            for criterio, evidencia in por_criterio.items():
                resultado[codigo].setdefault(criterio, evidencia)
    return dict(resultado)


def aplicar(filas: list[dict[str, str]], cruces: dict[str, Evidencia]) -> list[dict[str, str]]:
    """Pasa a `fuente_oficial` los criterios que el sitio no mostró y una fuente oficial sí.

    No toca los `enlace_encontrado`. Los demás estados (no hallado, menú no legible, sitio
    no encontrado…) se reemplazan solo en los criterios con evidencia; el resto queda igual.
    """
    resultado = []
    for fila in filas:
        evidencia = cruces.get(fila["criterio"])
        if evidencia and fila["resultado"] != "enlace_encontrado":
            fila = {
                **fila,
                "resultado": "fuente_oficial",
                "evidencia": evidencia.url,
                "detalle": evidencia.detalle,
                "metodo": evidencia.metodo,
            }
        resultado.append(fila)
    return resultado


# --- descarga (con red) ---------------------------------------------------------------------


def _valor_metadato(clasificacion: dict[str, Any], sufijo: str) -> str:
    for m in clasificacion.get("domain_metadata", []):
        if m.get("key", "").endswith(sufijo):
            return str(m.get("value", ""))
    return ""


def conjuntos_del_catalogo(contexto: Contexto) -> list[dict[str, str]]:
    """Todo el catálogo de datos.gov.co, reducido a lo que importa (se guarda en caché)."""
    ruta = Path(contexto.dir_crudos) / "catalogo_datos_gov" / "conjuntos.json"
    if ruta.exists() and not contexto.refrescar:
        return leer_json(ruta)["conjuntos"]
    conjuntos: list[dict[str, str]] = []
    desde = 0
    while True:
        pagina = contexto.cliente.transporte(
            URL_CATALOGO,
            {
                "domains": contexto.cliente.dominio,
                "only": "datasets",
                "limit": str(TAM_PAGINA_CATALOGO),
                "offset": str(desde),
            },
            {},
        )
        resultados = pagina.get("results", [])
        for r in resultados:
            clasif = r.get("classification", {})
            conjuntos.append(
                {
                    "divipola": _codigo(_valor_metadato(clasif, "_DIVIPOLA-Municipio")),
                    "entidad": _valor_metadato(clasif, "_Nombre-de-la-Entidad"),
                    "nombre": r["resource"]["name"],
                    "url": r["permalink"],
                }
            )
        log.info("Catálogo de datos.gov.co: %d conjuntos leídos", len(conjuntos))
        if len(resultados) < TAM_PAGINA_CATALOGO:
            break
        desde += TAM_PAGINA_CATALOGO
    escribir_json(ruta, {"conjuntos": conjuntos})
    return conjuntos


def descargar_cruces(contexto: Contexto, ruta_contratacion: Path, anio_actual: int) -> Cruces:
    """Cruces de las tres fuentes. Una que falle se registra y no detiene a las demás."""
    partes: list[Cruces] = []
    try:
        partes.append(cruces_secop(leer_json(ruta_contratacion)["observaciones"], anio_actual))
    except (OSError, KeyError, ValueError):
        log.warning("Sin cruce con SECOP: falta %s (corre `contratacion`)", ruta_contratacion)
    try:
        filas = contexto.cliente.consultar(
            CONJUNTO_SIGEP,
            select="nombre_de_la_entidad, nit, c_digo_divipola_municipio, a_o, mes,"
            " genero_hombre, genero_mujer, genero_no_binario, salario_mensual_promedio",
            where="orden = 'TERRITORIAL' AND nivel = 'CENTRAL'",
            refrescar=contexto.refrescar,
        )
        partes.append(cruces_sigep(filas, ita.mapa_nits(contexto)))
    except Exception:
        log.exception("Sin cruce con SIGEP: no se pudo descargar")
    try:
        partes.append(cruces_catalogo(conjuntos_del_catalogo(contexto)))
    except Exception:
        log.exception("Sin cruce con datos.gov.co: no se pudo leer el catálogo")
    cruces = combinar(*partes)
    cubiertos = {c.id: sum(c.id in v for v in cruces.values()) for c in CRITERIOS}
    log.info("Cruces oficiales: %d municipios; por criterio %s", len(cruces), cubiertos)
    return cruces
