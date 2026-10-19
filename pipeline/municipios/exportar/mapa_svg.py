"""Mapas en SVG a partir de contornos en Web Mercator.

Cada mapa es un SVG autónomo con un <path> por entidad. Los colores no van en el archivo: la web
los asigna con CSS según `data-codigo`, así el mismo SVG sirve para cualquier capa de datos.

Los territorios muy alejados no caben a buena escala en un solo marco. Para ellos hay dos
recursos: un **recuadro** (por ejemplo, San Andrés en el mapa nacional) y los **paneles**
(cada entidad en su propio marco, como las islas de San Andrés y Providencia).
"""

from collections.abc import Collection
from dataclasses import dataclass, replace
from xml.sax.saxutils import escape, quoteattr

from municipios.comun.geometria import Poligono, area, caja, simplificar

ANCHO = 1000  # ancho del viewBox; el alto sale de la proporción del territorio
MARGEN = 10
TAM_RECUADRO = 200  # lado del recuadro, en unidades del viewBox
FRACCION_ISLA_PRINCIPAL = 0.05  # en un recuadro se omiten islotes menores al 5 % del mayor
RELLENO = 6  # aire entre el borde de un recuadro o panel y el dibujo
TOLERANCIA_PX = 0.6  # error máximo de la simplificación, en unidades del viewBox
AREA_MINIMA_PX = 2.0  # islotes y huecos más chicos que esto (en unidades²) se descartan
DECIMALES = 1

# Aspecto por defecto (por ejemplo, al abrir el SVG suelto). `:where` tiene especificidad cero,
# así que cualquier regla de la web lo reemplaza sin pelear.
# Estilo base acotado al propio mapa: un <style> dentro de un SVG en línea es global en la página,
# y una regla suelta sobre `path` pintaba también los íconos de la interfaz.
_MAPA = 'svg[aria-labelledby="titulo-mapa"]'
ESTILO_BASE = (
    f":where({_MAPA} path){{fill:#cfd5dc;stroke:#fff;stroke-width:.6;"
    "vector-effect:non-scaling-stroke;stroke-linejoin:round}"
    f":where({_MAPA} .recuadro){{fill:none;stroke:#a4abb5;stroke-width:1;"
    "vector-effect:non-scaling-stroke}"
)


@dataclass(frozen=True, slots=True)
class Forma:
    codigo: str
    nombre: str
    slug: str
    poligonos: list[Poligono]
    sufijo: str = ""  # para el id cuando una entidad se dibuja en varias piezas («-1», «-2»)


@dataclass(frozen=True, slots=True)
class Marco:
    """Rectángulo del viewBox donde se dibuja un grupo de formas."""

    x: float
    y: float
    ancho: float
    alto: float


@dataclass(frozen=True, slots=True)
class Transformacion:
    """Lleva metros (Web Mercator) a unidades del viewBox, con el eje Y hacia abajo."""

    xmin: float
    ymax: float
    escala: float
    dx: float
    dy: float

    def aplicar(self, x: float, y: float) -> tuple[float, float]:
        return (x - self.xmin) * self.escala + self.dx, (self.ymax - y) * self.escala + self.dy


def _proporcion(formas: list[Forma]) -> float:
    """Alto / ancho del conjunto."""
    xmin, ymin, xmax, ymax = caja([p for f in formas for p in f.poligonos])
    return (ymax - ymin) / (xmax - xmin)


def transformacion_para(formas: list[Forma], marco: Marco) -> Transformacion:
    """Escala las formas para que quepan en el marco, centradas y sin deformar."""
    xmin, ymin, xmax, ymax = caja([p for f in formas for p in f.poligonos])
    escala = min(marco.ancho / (xmax - xmin), marco.alto / (ymax - ymin))
    dx = marco.x + (marco.ancho - (xmax - xmin) * escala) / 2
    dy = marco.y + (marco.alto - (ymax - ymin) * escala) / 2
    return Transformacion(xmin=xmin, ymax=ymax, escala=escala, dx=dx, dy=dy)


def _numero(valor: float) -> str:
    texto = f"{valor:.{DECIMALES}f}".rstrip("0").rstrip(".")
    return "0" if texto in ("-0", "") else texto


def trazo(poligonos: list[Poligono], t: Transformacion) -> str:
    """Atributo `d` con coordenadas relativas (más compacto que absolutas)."""
    partes: list[str] = []
    for poligono in poligonos:
        for anillo in poligono:
            abierto = anillo[:-1] if len(anillo) > 1 and anillo[0] == anillo[-1] else anillo
            puntos = [t.aplicar(x, y) for x, y in abierto]  # la «z» final cierra el anillo
            redondeados = [(round(x, DECIMALES), round(y, DECIMALES)) for x, y in puntos]
            x0, y0 = redondeados[0]
            segmento = [f"M{_numero(x0)} {_numero(y0)}"]
            relativos = []
            px, py = x0, y0
            for x, y in redondeados[1:]:
                dx, dy = round(x - px, DECIMALES), round(y - py, DECIMALES)
                if dx or dy:
                    relativos.append(f"{_numero(dx)} {_numero(dy)}")
                px, py = x, y
            if relativos:
                segmento.append("l" + " ".join(relativos))
            segmento.append("z")
            partes.append("".join(segmento))
    return "".join(partes)


def _camino(forma: Forma, t: Transformacion) -> str:
    poligonos = simplificar(forma.poligonos, TOLERANCIA_PX / t.escala, AREA_MINIMA_PX / t.escala**2)
    return (
        f"<path id={quoteattr('e-' + forma.codigo + forma.sufijo)}"
        f" data-codigo={quoteattr(forma.codigo)} data-slug={quoteattr(forma.slug)}"
        f" d={quoteattr(trazo(poligonos, t))}><title>{escape(forma.nombre)}</title></path>"
    )


def _islas_principales(forma: Forma) -> list[Forma]:
    """Una forma por cada polígono de al menos FRACCION_ISLA_PRINCIPAL del área del mayor.

    En un recuadro, los cayos lejanos agrandan el encuadre y la distancia entre islas las achica
    hasta volverlas ilegibles. Por eso cada isla principal va en su propia celda, de oeste a este,
    y los cayos se omiten (a esa escala no se verían de todos modos).
    """
    mayor = max(area(p[0]) for p in forma.poligonos)
    islas = [p for p in forma.poligonos if area(p[0]) >= FRACCION_ISLA_PRINCIPAL * mayor]
    islas.sort(key=lambda p: min(x for x, _ in p[0]))
    if len(islas) == 1:
        return [replace(forma, poligonos=islas)]
    return [replace(forma, poligonos=[p], sufijo=f"-{i}") for i, p in enumerate(islas, 1)]


def _con_relleno(marco: Marco) -> Marco:
    """Marco interior de un recuadro o panel, para que el dibujo no toque el borde."""
    return Marco(
        marco.x + RELLENO, marco.y + RELLENO, marco.ancho - 2 * RELLENO, marco.alto - 2 * RELLENO
    )


def _rectangulo(marco: Marco) -> str:
    return (
        f'<rect class="recuadro" x="{_numero(marco.x)}" y="{_numero(marco.y)}"'
        f' width="{_numero(marco.ancho)}" height="{_numero(marco.alto)}" rx="6"/>'
    )


def svg(
    formas: list[Forma],
    titulo: str,
    clase: str,
    recuadro: Collection[str] = (),
    paneles: bool = False,
) -> str:
    """Genera el SVG completo.

    - `clase` va en el <g> (por ejemplo 'municipios').
    - `recuadro`: códigos que se dibujan en un recuadro arriba a la izquierda, a su propia escala
      (cada isla principal en su celda; ver `_islas_principales`).
    - `paneles`: cada forma en su propio marco, una al lado de la otra.
    """
    ordenadas = sorted(formas, key=lambda f: f.codigo)
    dibujos: list[tuple[list[Forma], Marco]] = []
    bordes: list[Marco] = []

    if paneles:
        ancho_panel = (ANCHO - MARGEN * (len(ordenadas) + 1)) / len(ordenadas)
        alto = max(ancho_panel * _proporcion([f]) for f in ordenadas)
        for i, forma in enumerate(ordenadas):
            marco = Marco(MARGEN + i * (ancho_panel + MARGEN), MARGEN, ancho_panel, alto)
            dibujos.append(([forma], _con_relleno(marco)))
            bordes.append(marco)
    else:
        principales = [f for f in ordenadas if f.codigo not in recuadro]
        ancho_util = ANCHO - 2 * MARGEN
        alto = ancho_util * _proporcion(principales)
        dibujos.append((principales, Marco(MARGEN, MARGEN, ancho_util, alto)))
        islas = [isla for f in ordenadas if f.codigo in recuadro for isla in _islas_principales(f)]
        if islas:
            bordes.append(Marco(MARGEN, MARGEN, TAM_RECUADRO, TAM_RECUADRO))
            ancho_celda = TAM_RECUADRO / len(islas)
            for i, isla in enumerate(islas):
                celda = Marco(MARGEN + i * ancho_celda, MARGEN, ancho_celda, TAM_RECUADRO)
                dibujos.append(([isla], _con_relleno(celda)))

    alto_total = round(alto + 2 * MARGEN)
    contenido = [_rectangulo(marco) for marco in bordes]
    for grupo, marco in dibujos:
        t = transformacion_para(grupo, marco)
        contenido.extend(_camino(f, t) for f in grupo)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ANCHO} {alto_total}"'
        f' role="img" aria-labelledby="titulo-mapa">'
        f'<title id="titulo-mapa">{escape(titulo)}</title>'
        f"<style>{ESTILO_BASE}</style>"
        f'<g class={quoteattr(clase)} fill-rule="evenodd">\n'
        + "\n".join(contenido)
        + "\n</g></svg>\n"
    )
