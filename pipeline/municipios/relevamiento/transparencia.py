"""Revisión automática del menú de transparencia de cada alcaldía (Ley 1712, Res. MinTIC 1519).

Para cada municipio:
1. Encuentra el sitio oficial: lista manual verificada (datos/manual/sitios.csv), o el patrón de
   MinTIC «www.<municipio>-<departamento>.gov.co», o «www.<municipio>.gov.co».
2. Abre la sección de transparencia con un navegador real (los portales de MinTIC se dibujan con
   JavaScript) y reúne los enlaces que publica.
3. Busca, por texto y dirección de cada enlace, los 10 criterios del proyecto.
4. Si faltan criterios, abre hasta 2 niveles de las secciones del menú que podrían tenerlos
   (planeación, contratación, información de la entidad…), sin salir del sitio (ver `rastreo.py`).
5. Los criterios que el sitio no muestra se cruzan con fuentes oficiales nacionales (SECOP,
   SIGEP, datos.gov.co; ver `cruces.py`). No se usan buscadores.

El resultado es una **revisión automática**: dice si hay un enlace con ese nombre, no si el
documento está completo o al día; «no hallado» nunca significa «no publica». Por eso no puntúa en
el índice hasta que una persona lo revise (datos/manual/transparencia.csv). Se respeta robots.txt
(y su Crawl-delay), se hace una pausa entre sitios y entre páginas, y el rastreador se identifica.
"""

import csv
import logging
import os
import time
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from scrapling.fetchers import DynamicSession, Fetcher

from municipios.comun.cruce import clave
from municipios.comun.modelos import Municipio
from municipios.relevamiento.criterios import CRITERIOS, candidatos
from municipios.relevamiento.cruces import Cruces, aplicar
from municipios.relevamiento.rastreo import Enlaces, Rastro, rastrear

log = logging.getLogger(__name__)

ENLACES_MINIMOS = 15  # menos enlaces: el menú no se pudo leer (JavaScript, bloqueo)
PAUSA = 3.0  # segundos entre sitios
PAUSA_PAGINA = 2.0  # segundos mínimos entre páginas del mismo sitio
PAUSA_MAXIMA = 10.0  # tope al Crawl-delay que pida un robots.txt
ENLACES_SECCION_MINIMOS = 5  # una sección con menos enlaces se vuelve a abrir con navegador
GUARDAR_CADA = 25  # municipios entre guardados parciales
TIEMPO_NAVEGADOR = 40000  # milisegundos para abrir una página con el navegador
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
    "detalle",
)


class Rastreador:
    """Lee páginas respetando robots.txt (con su Crawl-delay) y una pausa entre páginas."""

    def __init__(self, agente: str, navegador: DynamicSession) -> None:
        self.agente = agente
        self.navegador = navegador
        self._robots: dict[str, RobotFileParser | None] = {}
        self._ultima: dict[str, float] = {}

    def _robots_de(self, url: str) -> RobotFileParser | None:
        partes = urlparse(url)
        origen = f"{partes.scheme}://{partes.netloc}"
        if origen not in self._robots:
            robots: RobotFileParser | None = RobotFileParser()
            try:
                respuesta = Fetcher.get(
                    f"{origen}/robots.txt", timeout=20, headers={"User-Agent": self.agente}
                )
                if respuesta.status == 200 and robots is not None:
                    robots.parse(respuesta.body.decode("utf-8", "replace").splitlines())
                else:
                    robots = None  # sin robots.txt: se permite
            except Exception:
                robots = None
            self._robots[origen] = robots
        return self._robots[origen]

    def permitido(self, url: str) -> bool:
        robots = self._robots_de(url)
        return robots is None or robots.can_fetch(AGENTE, url)

    def _esperar(self, url: str) -> None:
        sitio = urlparse(url).netloc
        robots = self._robots_de(url)
        pedida = robots.crawl_delay(AGENTE) if robots else None
        espera = min(max(float(pedida or 0), PAUSA_PAGINA), PAUSA_MAXIMA)
        falta = self._ultima.get(sitio, 0.0) + espera - time.monotonic()
        if falta > 0:
            time.sleep(falta)
        self._ultima[sitio] = time.monotonic()

    def leer(self, url: str) -> Enlaces | None:
        """Enlaces de una sección, o None si robots.txt no lo permite o no se pudo abrir."""
        if not self.permitido(url):
            log.info("robots.txt no permite revisar %s", url)
            return None
        try:
            self._esperar(url)
            pagina = Fetcher.get(url, timeout=25, retries=1, headers={"User-Agent": self.agente})
            enlaces = _extraer(pagina) if pagina.status < 400 else []
            if len(enlaces) < ENLACES_SECCION_MINIMOS:
                self._esperar(url)
                _, enlaces = _enlaces(url, self.navegador)
            return enlaces
        except Exception as error:
            log.info("no se pudo abrir %s (%s)", url, error)
            return None


def _responde(url: str) -> bool:
    try:
        return Fetcher.get(url, timeout=25, retries=1).status < 400
    except Exception:
        return False


def _extraer(pagina) -> Enlaces:
    return [
        (
            " ".join(a.get_all_text().split())
            or a.attrib.get("title", "")
            or a.attrib.get("aria-label", ""),
            urljoin(pagina.url, a.attrib.get("href", "")),
        )
        for a in pagina.css("a")
        if a.attrib.get("href") and not a.attrib["href"].startswith(("javascript:", "mailto:", "#"))
    ]


def _abrir_navegador(agente: str) -> DynamicSession:
    """Un navegador por municipio: abrirlo una vez por página costaba ~10 s cada vez."""
    return DynamicSession(
        headless=True, useragent=agente, retries=1, disable_resources=True, timeout=TIEMPO_NAVEGADOR
    )


def _enlaces(url: str, navegador: DynamicSession) -> tuple[str, Enlaces]:
    """Abre la página con el navegador y devuelve (URL final, [(texto, URL absoluta)]).

    Primero espera a que la red se calme (los menús de MinTIC se dibujan con JavaScript); si la
    página nunca se calma (anuncios, chats), la vuelve a abrir esperando un tiempo fijo.
    """
    try:
        pagina = navegador.fetch(url, network_idle=True)
    except Exception:
        pagina = navegador.fetch(url, network_idle=False, wait=4000)
    return pagina.url, _extraer(pagina)


def _filas(
    base: dict[str, str], sitio: str, pagina: str, resultado: str, detalle: str = ""
) -> list[dict[str, str]]:
    """Una fila por criterio con el mismo resultado (sitio ausente, error, menú ilegible…)."""
    return [
        {
            **base,
            "sitio": sitio,
            "pagina_transparencia": pagina,
            "criterio": c.id,
            "resultado": resultado,
            "evidencia": "",
            "detalle": detalle,
        }
        for c in CRITERIOS
    ]


def filas_del_rastro(
    base: dict[str, str], sitio: str, pagina: str, rastro: Rastro
) -> list[dict[str, str]]:
    """Una fila por criterio: enlace hallado (con su nivel) o no hallado (con páginas leídas)."""
    omitidas = f", {rastro.paginas_omitidas} omitidas" if rastro.paginas_omitidas else ""
    sin_hallar = f"Se leyeron {rastro.paginas_leidas} páginas del sitio{omitidas}; sin enlace"
    filas = []
    for c in CRITERIOS:
        h = rastro.encontrados.get(c.id)
        if h is None:
            detalle = sin_hallar
        elif h.nivel == 0:
            detalle = "En el menú de transparencia"
        else:
            detalle = f"Nivel {h.nivel}: {h.pagina}"
        filas.append(
            {
                **base,
                "sitio": sitio,
                "pagina_transparencia": pagina,
                "criterio": c.id,
                "resultado": "enlace_encontrado" if h else "no_encontrado",
                "evidencia": h.evidencia if h else "",
                "detalle": detalle,
            }
        )
    return filas


def revisar(m: Municipio, manuales: dict[str, str]) -> list[dict[str, str]]:
    """Filas de resultado (una por criterio) para un municipio, solo con lo que muestra su sitio."""
    contacto = os.environ.get("CONTACTO_RASTREO")
    agente = f"{AGENTE} {contacto}" if contacto else AGENTE
    hoy = date.today().isoformat()
    base = {"divipola": m.divipola, "municipio": m.nombre, "fecha": hoy, "metodo": "automatico"}

    sitio = next((u for u in candidatos(m, manuales) if _responde(u)), None)
    if sitio is None:
        return _filas(base, "", "", "sitio_no_encontrado")

    with _abrir_navegador(agente) as navegador:
        return _revisar_sitio(m, sitio, base, agente, navegador)


def _revisar_sitio(
    m: Municipio, sitio: str, base: dict[str, str], agente: str, navegador: DynamicSession
) -> list[dict[str, str]]:
    rastreador = Rastreador(agente, navegador)
    destino = urljoin(sitio, "transparencia")
    if not rastreador.permitido(destino):
        log.info("%s: robots.txt no permite revisar %s", m.nombre, destino)
        return _filas(base, sitio, destino, "no_permitido")
    try:
        final, enlaces = _enlaces(destino, navegador)
        if len(enlaces) < ENLACES_MINIMOS:
            # Sitio propio (no la plantilla de MinTIC): buscar el enlace de transparencia
            # en la portada.
            _, portada = _enlaces(sitio, navegador)
            otra = next((u for t, u in portada if "TRANSPARENCIA" in clave(t + " " + u)), None)
            if otra and rastreador.permitido(otra):
                final, enlaces = _enlaces(otra, navegador)
    except Exception as error:
        log.warning("%s: no se pudo abrir %s (%s)", m.nombre, destino, error)
        return _filas(base, sitio, destino, "error")

    if len(enlaces) < ENLACES_MINIMOS:
        log.warning("%s: el menú de %s trae solo %d enlaces", m.nombre, final, len(enlaces))
        return _filas(base, sitio, final, "menu_no_legible")
    rastro = rastrear(enlaces, final, final, rastreador.leer)
    if not rastro.encontrados:
        # Ni un solo criterio: casi seguro el menú se arma en un componente que no se lee
        # (iframe, shadow DOM). Afirmar que no publica nada sería un falso negativo.
        log.warning("%s: %d enlaces, ninguno coincide", m.nombre, len(enlaces))
        return _filas(base, sitio, final, "menu_no_legible")
    return filas_del_rastro(base, sitio, final, rastro)


def _leer_csv(ruta: Path) -> list[dict[str, str]]:
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _escribir_csv(ruta: Path, filas: list[dict[str, str]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS_SALIDA, restval="", lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(sorted(filas, key=lambda fila: (fila["divipola"], fila["criterio"])))


def relevar(
    municipios: list[Municipio],
    manuales: dict[str, str],
    salida: Path,
    cruces: Cruces | None = None,
    reanudar: bool = False,
) -> int:
    """Revisa los municipios y reescribe sus filas en `salida` (conserva las de los demás).

    Con `reanudar`, se saltan los municipios ya revisados hoy (para retomar una corrida larga).
    Guarda cada `GUARDAR_CADA` municipios para no perder horas de trabajo si se interrumpe.
    """
    cruces = cruces or {}
    hoy = date.today().isoformat()
    existentes = _leer_csv(salida)
    if reanudar:
        hechos = {f["divipola"] for f in existentes if f["fecha"] == hoy}
        municipios = [m for m in municipios if m.divipola not in hechos]
    codigos = {m.divipola for m in municipios}
    conservadas = [f for f in existentes if f["divipola"] not in codigos]
    nuevas: list[dict[str, str]] = []
    for i, m in enumerate(municipios, 1):
        filas = aplicar(revisar(m, manuales), cruces.get(m.divipola, {}))
        nuevas.extend(filas)
        hallados = sum(f["resultado"] == "enlace_encontrado" for f in filas)
        oficiales = sum(f["resultado"] == "fuente_oficial" for f in filas)
        log.info(
            "[%d/%d] %s: %s (%d/10 en el sitio, %d en fuentes oficiales)",
            i,
            len(municipios),
            m.nombre,
            filas[0]["resultado"] if hallados + oficiales == 0 else "ok",
            hallados,
            oficiales,
        )
        if i % GUARDAR_CADA == 0:
            _escribir_csv(salida, conservadas + nuevas)
        time.sleep(PAUSA)
    _escribir_csv(salida, conservadas + nuevas)
    return len(municipios)


def reaplicar_cruces(salida: Path, cruces: Cruces) -> int:
    """Aplica los cruces oficiales al CSV existente sin volver a rastrear ningún sitio."""
    por_municipio: dict[str, list[dict[str, str]]] = {}
    for fila in _leer_csv(salida):
        por_municipio.setdefault(fila["divipola"], []).append(fila)
    resultado = [
        f for codigo, grupo in por_municipio.items() for f in aplicar(grupo, cruces.get(codigo, {}))
    ]
    _escribir_csv(salida, resultado)
    return len(por_municipio)


def unir(directorio: Path, salida: Path) -> int:
    """Junta los CSV parciales en `salida`; las filas de cada municipio sustituyen a las previas."""
    nuevas = [f for ruta in sorted(directorio.glob("transparencia_*.csv")) for f in _leer_csv(ruta)]
    codigos = {f["divipola"] for f in nuevas}
    _escribir_csv(salida, [f for f in _leer_csv(salida) if f["divipola"] not in codigos] + nuevas)
    return len(codigos)
