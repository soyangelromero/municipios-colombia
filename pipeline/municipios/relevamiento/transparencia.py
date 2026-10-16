"""Revisión automática del menú de transparencia de cada alcaldía (Ley 1712, Res. MinTIC 1519).

Para cada municipio:
1. Encuentra el sitio oficial: lista manual verificada (datos/manual/sitios.csv), o el patrón de
   MinTIC «www.<municipio>-<departamento>.gov.co», o «www.<municipio>.gov.co».
2. Abre la sección de transparencia con un navegador real (los portales de MinTIC se dibujan con
   JavaScript) y reúne los enlaces que publica.
3. Busca, por texto y dirección de cada enlace, los 10 criterios del proyecto.

El resultado es una **revisión automática**: dice si hay un enlace con ese nombre, no si el
documento está completo o al día. Por eso no puntúa en el índice hasta que una persona lo revise
(datos/manual/transparencia.csv). Se respeta robots.txt, se hace una pausa entre sitios y el
rastreador se identifica.
"""

import csv
import logging
import os
import time
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from scrapling.fetchers import DynamicFetcher, Fetcher

from municipios.comun.cruce import clave
from municipios.comun.modelos import Municipio
from municipios.relevamiento.criterios import CRITERIOS, candidatos, clasificar

log = logging.getLogger(__name__)

ENLACES_MINIMOS = 15  # menos enlaces: el menú no se pudo leer (JavaScript, bloqueo)
PAUSA = 3.0  # segundos entre sitios
AGENTE = "MunicipiosColombiaBot/0.1 (+https://github.com/soyangelromero/municipios-colombia)"


CAMPOS_SALIDA = (
    "divipola",
    "municipio",
    "sitio",
    "pagina_transparencia",
    "fecha",
    "criterio",
    "resultado",
    "evidencia",
    "metodo",
)


def _permitido(url: str) -> bool:
    partes = urlparse(url)
    robots = RobotFileParser()
    try:
        respuesta = Fetcher.get(f"{partes.scheme}://{partes.netloc}/robots.txt", timeout=20)
        if respuesta.status != 200:
            return True  # sin robots.txt: se permite
        robots.parse(respuesta.body.decode("utf-8", "replace").splitlines())
    except Exception:
        return True
    return robots.can_fetch(AGENTE, url)


def _responde(url: str) -> bool:
    try:
        return Fetcher.get(url, timeout=25, retries=1).status < 400
    except Exception:
        return False


def _enlaces(url: str, agente: str) -> tuple[str, list[tuple[str, str]]]:
    """Abre la página con un navegador y devuelve (URL final, [(texto, URL absoluta)])."""
    pagina = DynamicFetcher.fetch(
        url, headless=True, network_idle=True, timeout=60000, useragent=agente
    )
    enlaces = [
        (
            " ".join(a.text.split()) or a.attrib.get("title", ""),
            urljoin(pagina.url, a.attrib.get("href", "")),
        )
        for a in pagina.css("a")
        if a.attrib.get("href") and not a.attrib["href"].startswith(("javascript:", "mailto:", "#"))
    ]
    return pagina.url, enlaces


def revisar(m: Municipio, manuales: dict[str, str]) -> list[dict[str, str]]:
    """Filas de resultado (una por criterio) para un municipio."""
    contacto = os.environ.get("CONTACTO_RASTREO")
    agente = f"{AGENTE} {contacto}" if contacto else AGENTE
    hoy = date.today().isoformat()
    base = {"divipola": m.divipola, "municipio": m.nombre, "fecha": hoy, "metodo": "automatico"}

    sitio = next((u for u in candidatos(m, manuales) if _responde(u)), None)
    if sitio is None:
        return [
            {
                **base,
                "sitio": "",
                "pagina_transparencia": "",
                "criterio": c.id,
                "resultado": "sitio_no_encontrado",
                "evidencia": "",
            }
            for c in CRITERIOS
        ]

    destino = urljoin(sitio, "transparencia")
    if not _permitido(destino):
        log.info("%s: robots.txt no permite revisar %s", m.nombre, destino)
        return [
            {
                **base,
                "sitio": sitio,
                "pagina_transparencia": destino,
                "criterio": c.id,
                "resultado": "no_permitido",
                "evidencia": "",
            }
            for c in CRITERIOS
        ]
    try:
        final, enlaces = _enlaces(destino, agente)
        if len(enlaces) < ENLACES_MINIMOS:
            # Sitio propio (no la plantilla de MinTIC): buscar el enlace de transparencia
            # en la portada.
            _, portada = _enlaces(sitio, agente)
            otra = next((u for t, u in portada if "TRANSPARENCIA" in clave(t + " " + u)), None)
            if otra:
                final, enlaces = _enlaces(otra, agente)
    except Exception as error:
        log.warning("%s: no se pudo abrir %s (%s)", m.nombre, destino, error)
        return [
            {
                **base,
                "sitio": sitio,
                "pagina_transparencia": destino,
                "criterio": c.id,
                "resultado": "error",
                "evidencia": "",
            }
            for c in CRITERIOS
        ]

    if len(enlaces) < ENLACES_MINIMOS:
        log.warning("%s: el menú de %s trae solo %d enlaces", m.nombre, final, len(enlaces))
        return [
            {
                **base,
                "sitio": sitio,
                "pagina_transparencia": final,
                "criterio": c.id,
                "resultado": "menu_no_legible",
                "evidencia": "",
            }
            for c in CRITERIOS
        ]
    encontrados = clasificar(enlaces)
    if not any(encontrados.values()):
        # Ni un solo criterio: casi seguro el menú se arma en un componente que no se lee
        # (iframe, shadow DOM). Afirmar que no publica nada sería un falso negativo.
        log.warning("%s: %d enlaces, ninguno coincide", m.nombre, len(enlaces))
        return [
            {
                **base,
                "sitio": sitio,
                "pagina_transparencia": final,
                "criterio": c.id,
                "resultado": "menu_no_legible",
                "evidencia": "",
            }
            for c in CRITERIOS
        ]
    return [
        {
            **base,
            "sitio": sitio,
            "pagina_transparencia": final,
            "criterio": c.id,
            "resultado": "enlace_encontrado" if encontrados[c.id] else "no_encontrado",
            "evidencia": encontrados[c.id] or "",
        }
        for c in CRITERIOS
    ]


def relevar(municipios: list[Municipio], manuales: dict[str, str], salida: Path) -> int:
    """Revisa los municipios y reescribe sus filas en `salida` (conserva las de los demás)."""
    previas: list[dict[str, str]] = []
    if salida.exists():
        with salida.open(encoding="utf-8", newline="") as f:
            codigos = {m.divipola for m in municipios}
            previas = [fila for fila in csv.DictReader(f) if fila["divipola"] not in codigos]
    nuevas: list[dict[str, str]] = []
    for i, m in enumerate(municipios, 1):
        filas = revisar(m, manuales)
        nuevas.extend(filas)
        hallados = sum(f["resultado"] == "enlace_encontrado" for f in filas)
        log.info(
            "[%d/%d] %s: %s (%d/10)",
            i,
            len(municipios),
            m.nombre,
            filas[0]["resultado"] if hallados == 0 else "ok",
            hallados,
        )
        time.sleep(PAUSA)
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS_SALIDA, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(
            sorted(previas + nuevas, key=lambda fila: (fila["divipola"], fila["criterio"]))
        )
    return len(municipios)
