"""Criterios de transparencia y reglas puras (sin red) del relevamiento automático."""

import csv
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from municipios.comun.cruce import clave
from municipios.comun.modelos import Municipio
from municipios.comun.textos import sin_tildes


@dataclass(frozen=True, slots=True)
class Criterio:
    id: str
    nombre: str
    patrones: tuple[str, ...]  # expresiones sobre el texto normalizado del enlace + su URL


CRITERIOS = (
    Criterio(
        "presupuesto",
        "Presupuesto vigente",
        (
            r"PRESUPUESTO (GENERAL|APROBADO|VIGENTE|DE (RENTAS|INGRESOS))",
            r"\bPRESUPUESTO\b(?! PARTICIPATIVO)",
        ),
    ),
    Criterio(
        "ejecucion",
        "Ejecución presupuestal",
        (
            r"EJECUCION(ES)? PRESUPUESTAL",
            r"EJECUCION DEL PRESUPUESTO",
            r"EJECUCION.*(INGRESOS|GASTOS)",
        ),
    ),
    Criterio(
        "plan_desarrollo",
        "Plan de desarrollo y su seguimiento",
        (r"PLAN DE DESARROLLO", r"PLAN(ES)? DE ACCION", r"PLAN INDICATIVO"),
    ),
    Criterio(
        "plan_adquisiciones",
        "Plan anual de adquisiciones",
        (r"PLAN ANUAL DE ADQUISICIONES", r"\bPAA\b"),
    ),
    Criterio(
        "contratacion",
        "Contratación (SECOP)",
        (r"\bSECOP\b", r"CONTRATACION", r"PROCESOS CONTRACTUALES"),
    ),
    Criterio(
        "directorio",
        "Directorio de servidores y escalas salariales",
        (
            r"DIRECTORIO DE (SERVIDORES|FUNCIONARIOS|CONTRATISTAS)",
            r"ESCALA(S)? SALARIAL",
        ),
    ),
    Criterio(
        "control",
        "Informes de control y planes de mejoramiento",
        (
            r"CONTROL INTERNO",
            r"PLAN(ES)? DE MEJORAMIENTO",
            r"INFORMES? DE (GESTION|AUDITORIA|CONTROL)",
        ),
    ),
    Criterio(
        "pqrsd",
        "Atención de peticiones (PQRSD) e informes",
        (r"\bPQR", r"PETICIONES,? QUEJAS", r"INFORME(S)? DE (PQR|PETICIONES|SOLICITUDES)"),
    ),
    Criterio("datos_abiertos", "Datos abiertos", (r"DATOS ABIERTOS", r"DATOS GOV CO")),
    Criterio(
        "declaraciones",
        "Declaración de bienes y conflictos de interés del alcalde (Ley 2013)",
        (r"LEY 2013", r"DECLARACION(ES)? DE BIENES", r"CONFLICTO(S)? DE INTERES"),
    ),
)


def dominio(texto: str) -> str:
    """'San José del Guaviare' -> 'sanjosedelguaviare'."""
    return re.sub(r"[^a-z0-9]", "", sin_tildes(texto).lower())


def candidatos(m: Municipio, manuales: dict[str, str]) -> list[str]:
    """URLs posibles del sitio oficial, en orden de confianza."""
    if m.divipola in manuales:
        return [manuales[m.divipola]]
    nombre, departamento = dominio(m.nombre), dominio(m.departamento)
    return [f"https://www.{nombre}-{departamento}.gov.co/", f"https://www.{nombre}.gov.co/"]


def leer_sitios_manuales(ruta: Path) -> dict[str, str]:
    if not ruta.exists():
        return {}
    with ruta.open(encoding="utf-8", newline="") as f:
        return {fila["divipola"]: fila["sitio"] for fila in csv.DictReader(f) if fila.get("sitio")}


def clasificar(enlaces: Iterable[tuple[str, str]]) -> dict[str, str | None]:
    """Para cada criterio, la URL del primer enlace que lo cumple (o None).

    `enlaces` son pares (texto visible, URL). Se compara el texto normalizado y la URL con
    guiones y barras convertidos en espacios.
    """
    normalizados = [
        (clave(texto) + " " + clave(re.sub(r"[-_/.]", " ", url)), url) for texto, url in enlaces
    ]
    resultado: dict[str, str | None] = {}
    for criterio in CRITERIOS:
        resultado[criterio.id] = next(
            (
                url
                for texto, url in normalizados
                if any(re.search(p, texto) for p in criterio.patrones)
            ),
            None,
        )
    return resultado


# Secciones del menú de transparencia (estructura de la Resolución MinTIC 1519 de 2020, anexo 2)
# donde suelen estar los criterios. Cada patrón se compara con el texto del enlace y dice qué
# criterios podrían esconderse detrás: solo se abre una sección si puede aportar algo que aún no
# se halló.
SECCIONES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        r"INFORMACION DE LA ENTIDAD|ESTRUCTURA ORGANICA|TALENTO HUMANO|MECANISMOS? DE CONTACTO",
        ("directorio", "declaraciones", "pqrsd"),
    ),
    (
        r"PLANEACION|PLANES? ESTRATEGICO|PLAN DE ACCION|PROGRAMAS Y PROYECTOS|METAS",
        ("plan_desarrollo", "plan_adquisiciones", "presupuesto", "ejecucion", "control"),
    ),
    (
        r"PRESUPUESTO|INFORMACION FINANCIERA|HACIENDA",
        ("presupuesto", "ejecucion"),
    ),
    (r"CONTRATACION|ADQUISICIONES|COMPRAS", ("contratacion", "plan_adquisiciones")),
    (
        r"CONTROL|AUDITORIA|ORGANOS DE CONTROL|INFORMES? DE GESTION",
        ("control", "plan_desarrollo"),
    ),
    (
        r"PARTICIPA|ATENCION (AL|A LA) CIUDADAN|SERVICIO AL CIUDADANO|PQR|TRAMITES",
        ("pqrsd", "declaraciones"),
    ),
    (r"DATOS ABIERTOS", ("datos_abiertos",)),
    (r"NORMATIVA|TRANSPARENCIA|ACCESO A LA INFORMACION|LEY 1712", tuple(c.id for c in CRITERIOS)),
)

_ARCHIVOS = (
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar", ".csv",
    ".jpg", ".jpeg", ".png", ".gif", ".mp3", ".mp4",
)  # fmt: skip


def raiz_del_sitio(url: str) -> str:
    """'www.x-y.gov.co' y 'transparencia.x-y.gov.co' -> 'x-y.gov.co' (para no salirse del sitio)."""
    etiquetas = (urlparse(url).hostname or "").lower().split(".")
    return ".".join(etiquetas[-3:] if etiquetas[-2:] == ["gov", "co"] else etiquetas[-2:])


def es_archivo(url: str) -> bool:
    return urlparse(url).path.lower().endswith(_ARCHIVOS)


def secciones_a_abrir(
    enlaces: Iterable[tuple[str, str]],
    sitio: str,
    faltan: set[str],
    visitadas: set[str],
    maximo: int,
) -> list[str]:
    """URLs de las secciones del menú que podrían contener criterios que aún faltan.

    Solo enlaces del mismo sitio, que no sean archivos ni páginas ya leídas. Van primero las
    secciones que podrían aportar más criterios faltantes. Sin red.
    """
    raiz = raiz_del_sitio(sitio)
    puntos: dict[str, int] = {}
    for texto, url in enlaces:
        url = url.split("#")[0]
        if url in visitadas or es_archivo(url) or raiz_del_sitio(url) != raiz:
            continue
        if not urlparse(url).scheme.startswith("http"):
            continue
        ruta = re.sub(r"[-_/.]", " ", urlparse(url).path)
        normal = clave(f"{texto} {ruta}")
        aporte = max(
            (
                len(faltan & set(criterios))
                for patron, criterios in SECCIONES
                if re.search(patron, normal)
            ),
            default=0,
        )
        if aporte:
            puntos[url] = max(puntos.get(url, 0), aporte)
    orden = sorted(puntos, key=lambda u: -puntos[u])  # estable: conserva el orden del menú
    return orden[:maximo]
