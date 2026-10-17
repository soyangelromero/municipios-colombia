"""Plantillas HTML del sitio: esqueleto común y fragmentos reutilizables.

Sin motor de plantillas: funciones que devuelven texto, con todo valor externo escapado. Cada
página conoce su `raiz` (la ruta relativa hasta la carpeta del sitio, por ejemplo «../../»), así
el sitio funciona igual en un dominio propio o en una subcarpeta (GitHub Pages).
"""

import math
from dataclasses import dataclass
from html import escape

SEMAFORO_TEXTO = {"verde": "Verde", "amarillo": "Amarillo", "rojo": "Rojo"}


@dataclass(frozen=True)
class Pagina:
    ruta: str  # relativa a la raíz del sitio, termina en «/» o en «.html»
    titulo: str
    descripcion: str
    contenido: str
    scripts: tuple[str, ...] = ()
    clase: str = ""
    imagen: str = ""  # ruta (desde la raíz del sitio) de la imagen para redes sociales

    @property
    def raiz(self) -> str:
        """'' en la raíz, '../' en 'ranking/', '../../' en 'm/slug/'."""
        profundidad = self.ruta.rstrip("/").count("/") + (1 if self.ruta.endswith("/") else 0)
        return "../" * profundidad


def documento(pagina: Pagina, sitio: dict) -> str:
    raiz = pagina.raiz
    url = sitio["url_base"] + pagina.ruta.removesuffix("index.html")
    titulo = (
        f"{pagina.titulo} · {sitio['nombre']}"
        if pagina.titulo != sitio["nombre"]
        else pagina.titulo
    )
    imagen = sitio["url_base"] + pagina.imagen if pagina.imagen else ""
    og_imagen = (
        f'<meta property="og:image" content="{escape(imagen)}">\n'
        '<meta name="twitter:card" content="summary_large_image">'
        if imagen
        else '<meta name="twitter:card" content="summary">'
    )
    intro = (
        "if(!localStorage.getItem('intro-vista')&&!matchMedia('(prefers-reduced-motion: reduce)')."
        "matches){d.classList.add('con-intro');setTimeout(function(){d.classList.remove('con-intro')},9000)}"
        if "pagina-inicio" in pagina.clase
        else ""
    )
    scripts = "".join(
        f'<script type="module" src="{raiz}assets/js/{escape(s)}"></script>' for s in pagina.scripts
    )
    # La página 404 se sirve en cualquier URL inexistente: sus rutas relativas parten de la base.
    base = f'<base href="{escape(sitio["url_base"])}">\n' if pagina.ruta == "404.html" else ""
    return f"""<!doctype html>
<html lang="{sitio["idioma"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{base}<title>{escape(titulo)}</title>
<meta name="description" content="{escape(pagina.descripcion)}">
<link rel="canonical" href="{escape(url)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{escape(sitio["nombre"])}">
<meta property="og:title" content="{escape(titulo)}">
<meta property="og:description" content="{escape(pagina.descripcion)}">
<meta property="og:url" content="{escape(url)}">
{og_imagen}
<meta name="theme-color" content="#0b0d10">
<meta name="raiz" content="{raiz}">
<link rel="icon" href="{raiz}assets/img/icono.svg" type="image/svg+xml">
<link rel="preload" href="{raiz}assets/fonts/Geist-Variable.woff2" as="font" type="font/woff2" crossorigin>
<script>var d=document.documentElement;d.classList.add('js');try{{var t=localStorage.getItem('tema');if(t==='claro'||t==='oscuro')d.dataset.tema=t;{intro}}}catch(e){{}}</script>
<link rel="stylesheet" href="{raiz}assets/css/tokens.css">
<link rel="stylesheet" href="{raiz}assets/css/base.css">
<link rel="stylesheet" href="{raiz}assets/css/componentes.css">
<link rel="stylesheet" href="{raiz}assets/css/editorial.css">
</head>
<body class="{escape(pagina.clase)}">
<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">
  <symbol id="i-mapa" viewBox="0 0 20 20"><path d="M10 2 3 6v8l7 4 7-4V6z"/><path d="M10 2v14M3 6l7 4 7-4"/></symbol>
  <symbol id="i-comparar" viewBox="0 0 20 20"><path d="M4 4v12M10 2v16M16 6v8"/></symbol>
  <symbol id="i-contacto" viewBox="0 0 20 20"><rect x="3" y="5" width="14" height="10" rx="2"/><path d="m3 6 7 5 7-5"/></symbol>
  <symbol id="i-lupa" viewBox="0 0 20 20"><circle cx="9" cy="9" r="5"/><path d="m13 13 4 4"/></symbol>
  <symbol id="i-cerrar" viewBox="0 0 20 20"><path d="m5 5 10 10M15 5 5 15"/></symbol>
</svg>
<a class="saltar" href="#contenido">Saltar al contenido</a>
<header class="top" data-top>
  <a class="top__marca" href="{raiz}" aria-label="{escape(sitio["nombre"])}, inicio">
    <span class="logo" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
    <span class="top__nombre"><b>Municipios</b> <span>Colombia</span></span>
  </a>
  <div class="top__acciones">
    <a class="pill" href="{raiz}"><svg class="ico"><use href="#i-mapa"/></svg><span>Mapa</span></a>
    <a class="pill" href="{raiz}comparar/"><svg class="ico"><use href="#i-comparar"/></svg><span>Comparar</span></a>
    <a class="pill" href="{raiz}acerca/#contacto"><svg class="ico"><use href="#i-contacto"/></svg><span>Contacto</span></a>
    <button type="button" class="pill pill--icono" data-tema-boton hidden
      aria-label="Cambiar entre modo oscuro y claro"><span aria-hidden="true">◐</span></button>
  </div>
</header>
<main id="contenido" class="contenedor">
{pagina.contenido}
</main>
<footer class="pie">
  <div class="pie__fila contenedor">
    <div class="pie__contacto">
      <p class="lede sm">¿Trabajas en una alcaldía o encuentras un dato equivocado? Escríbenos y lo corregimos con su fuente.</p>
      <a class="pill pill--claro" href="{raiz}acerca/#contacto">Contacto</a>
    </div>
    <nav class="pie__enlaces" aria-label="Pie de página">
      <a href="{raiz}metodologia/">Metodología</a>
      <a href="{raiz}fuentes/">Fuentes</a>
      <a href="{raiz}acerca/">Acerca y privacidad</a>
      <a href="{escape(sitio["repositorio"])}">Código abierto (MIT)</a>
      <a href="{escape(sitio["repositorio"])}/issues/new/choose">Reportar un error</a>
    </nav>
    <p class="mono pie__fecha">Datos actualizados el {escape(sitio["actualizado"])}.</p>
    <p class="pie__credito">Creado y mantenido por <a href="mailto:{escape(sitio["correo"])}">Angel Romero</a>.</p>
  </div>
</footer>
<script>addEventListener('scroll',function(){{var t=document.querySelector('[data-top]');if(t)t.classList.toggle('solid',scrollY>40)}},{{passive:true}})</script>
<script type="module" src="{raiz}assets/js/tema.js"></script>
<script type="module" src="{raiz}assets/js/busqueda.js"></script>
{scripts}
</body>
</html>
"""


def semaforo(color: str | None, valor: float | None = None) -> str:
    if color is None:
        return '<span class="semaforo semaforo--sin">Sin índice</span>'
    numero = "" if valor is None else f"{valor:.1f}".replace(".", ",") + " · "
    return f'<span class="semaforo semaforo--{color}">{numero}{SEMAFORO_TEXTO[color]}</span>'


def barra(puntaje: float | None, etiqueta: str = "") -> str:
    """Barra horizontal 0-100 con su valor (o «sin dato»)."""
    if puntaje is None:
        return '<span class="barra barra--vacia" title="Sin dato">sin dato</span>'
    color = "rojo" if puntaje < 40 else "verde" if puntaje >= 70 else "amarillo"
    texto = f"{puntaje:.0f}"
    return (
        f'<span class="barra" role="img" aria-label="{escape(etiqueta)} {texto} de 100">'
        f'<span class="barra__relleno barra__relleno--{color}" style="width:{max(puntaje, 1):.1f}%"></span>'
        f'<span class="barra__valor">{texto}</span></span>'
    )


def color_puntaje(valor: float | None) -> str | None:
    """Color del semáforo para un puntaje 0-100 (mismos cortes que el índice)."""
    if valor is None:
        return None
    return "rojo" if valor < 40 else "verde" if valor >= 70 else "amarillo"


def _dec(valor: float, decimales: int = 1) -> str:
    return f"{valor:.{decimales}f}".replace(".", ",")


def medidor(
    valor: float | None, etiqueta: str = "Índice municipal", color: str | None = None
) -> str:
    """Medidor semicircular (gauge) con aguja. Sin dato: aviso plano."""
    color = color or color_puntaje(valor)
    if valor is None:
        return '<figure class="gauge gauge--vacio"><p class="gauge__sin">Sin dato</p></figure>'
    fraccion = max(0.0, min(1.0, valor / 100))
    angulo = math.pi - fraccion * math.pi
    aguja_x = 100 + 76 * math.cos(angulo)
    aguja_y = 100 - 76 * math.sin(angulo)
    return (
        f'<figure class="gauge" role="img" aria-label="{escape(etiqueta)}: {_dec(valor)} de 100, '
        f'estado {SEMAFORO_TEXTO.get(color or "", "sin dato")}">'
        '<svg viewBox="0 0 200 108" aria-hidden="true">'
        '<path class="gauge__pista" d="M20 100 A80 80 0 0 1 180 100" pathLength="100"></path>'
        f'<path class="gauge__arco gauge__arco--{color}" d="M20 100 A80 80 0 0 1 180 100" '
        f'pathLength="100" style="stroke-dasharray:{fraccion * 100:.2f} 100"></path>'
        f'<circle class="gauge__aguja" cx="{aguja_x:.1f}" cy="{aguja_y:.1f}" r="7"></circle>'
        "</svg>"
        f'<figcaption><span class="gauge__valor">{_dec(valor)}</span>'
        f'<span class="gauge__de">de 100</span>{semaforo(color)}</figcaption>'
        "</figure>"
    )


def anillo(valor: float | None, color: str | None, etiqueta: str, *, unidad: str = "%") -> str:
    """Anillo de progreso 0-100 con la etiqueta debajo."""
    if valor is None:
        return (
            '<div class="ring ring--vacio"><span class="ring__sin">s/d</span>'
            f'<span class="ring__etiq">{escape(etiqueta)}</span></div>'
        )
    circ = 2 * math.pi * 34
    offset = circ * (1 - max(0.0, min(100.0, valor)) / 100)
    return (
        f'<div class="ring ring--{color or color_puntaje(valor)}">'
        f'<svg viewBox="0 0 80 80" role="img" aria-label="{escape(etiqueta)}: {_dec(valor)}{unidad}">'
        '<circle class="ring__pista" cx="40" cy="40" r="34"></circle>'
        f'<circle class="ring__arco" cx="40" cy="40" r="34" '
        f'stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"></circle>'
        "</svg>"
        f'<span class="ring__valor">{_dec(valor)}<small>{unidad}</small></span>'
        f'<span class="ring__etiq">{escape(etiqueta)}</span>'
        "</div>"
    )


def bar2(puntaje: float | None, color: str | None = None, etiqueta: str = "") -> str:
    """Barra fina (10 px) que crece de izquierda a derecha según el puntaje."""
    if puntaje is None:
        return '<span class="bar2 bar2--vacio" title="Sin dato"></span>'
    color = color or color_puntaje(puntaje)
    return (
        f'<span class="bar2" role="img" aria-label="{escape(etiqueta)} {_dec(puntaje)} de 100">'
        f'<i class="bar2__f bar2__f--{color}" style="width:{max(puntaje, 1):.1f}%"></i></span>'
    )


def chip(texto: str, color: str | None = None, *, activo: bool = False) -> str:
    punto = f'<span class="chip__punto chip__punto--{color}"></span>' if color else ""
    clase = "chip chip--on" if activo else "chip"
    return f'<span class="{clase}">{punto}{escape(texto)}</span>'


def kpi(etiqueta: str, valor: str, detalle: str = "", color: str | None = None) -> str:
    """Tarjeta de dato: etiqueta, valor grande y una línea de contexto con su fuente."""
    clase = f" kpi__valor--{color}" if color else ""
    detalle_html = f'<p class="kpi__detalle">{detalle}</p>' if detalle else ""
    return (
        f'<div class="kpi"><p class="kpi__etiqueta">{escape(etiqueta)}</p>'
        f'<p class="kpi__valor{clase}">{valor}</p>{detalle_html}</div>'
    )


def sin_dato(texto: str, buscado: str = "") -> str:
    """Aviso rojo de dato faltante (con dónde se buscó, si se indica)."""
    extra = f' <span class="nd-red__donde">{escape(buscado)}</span>' if buscado else ""
    return f'<p class="nd-red"><span class="nd-red__ico" aria-hidden="true">!</span>Sin dato de {escape(texto)}.{extra}</p>'


def miga(raiz: str, pasos: list[tuple[str, str]]) -> str:
    """Migas de pan: [(ruta relativa a la raíz o '', texto)]; el último no es enlace."""
    partes = [f'<a href="{raiz}{ruta}">{escape(t)}</a>' for ruta, t in pasos[:-1]]
    partes.append(f'<span aria-current="page">{escape(pasos[-1][1])}</span>')
    return f'<nav class="miga" aria-label="Ruta">{" / ".join(partes)}</nav>'
