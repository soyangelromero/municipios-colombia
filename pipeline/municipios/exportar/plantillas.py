"""Plantillas HTML del sitio: esqueleto común y fragmentos reutilizables.

Sin motor de plantillas: funciones que devuelven texto, con todo valor externo escapado. Cada
página conoce su `raiz` (la ruta relativa hasta la carpeta del sitio, por ejemplo «../../»), así
el sitio funciona igual en un dominio propio o en una subcarpeta (GitHub Pages).
"""

from dataclasses import dataclass
from html import escape

NAVEGACION = (
    ("", "Inicio"),
    ("ranking/", "Ranking"),
    ("comparar/", "Comparar"),
    ("metodologia/", "Metodología"),
    ("fuentes/", "Fuentes"),
    ("acerca/", "Acerca"),
)

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


def documento(pagina: Pagina, sitio: dict, activo: str | None = None) -> str:
    raiz = pagina.raiz
    url = sitio["url_base"] + pagina.ruta.removesuffix("index.html")
    titulo = (
        f"{pagina.titulo} · {sitio['nombre']}"
        if pagina.titulo != sitio["nombre"]
        else pagina.titulo
    )
    enlaces = "".join(
        f'<a href="{raiz}{ruta}"{' aria-current="page"' if ruta == activo else ""}>{escape(texto)}</a>'
        for ruta, texto in NAVEGACION
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
<meta name="theme-color" content="#0a0d12">
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
<a class="saltar" href="#contenido">Saltar al contenido</a>
<header class="cabecera">
  <div class="cabecera__fila contenedor">
    <a class="marca" href="{raiz}" aria-label="{escape(sitio["nombre"])}, inicio">
      <img src="{raiz}assets/img/icono.svg" alt="" width="28" height="28">
      <span>Municipios <strong>Colombia</strong></span>
    </a>
    <nav class="nav" aria-label="Principal">{enlaces}</nav>
    <button type="button" class="tema" data-tema-boton hidden aria-label="Cambiar entre modo oscuro y claro">
      <span aria-hidden="true">◐</span></button>
    <div class="busqueda" data-busqueda>
      <label class="visualmente-oculto" for="buscar-global">Buscar municipio</label>
      <input id="buscar-global" type="search" placeholder="Busca tu municipio" autocomplete="off"
        role="combobox" aria-expanded="false" aria-controls="buscar-global-lista">
      <ul id="buscar-global-lista" class="busqueda__lista" role="listbox" hidden></ul>
    </div>
  </div>
</header>
<main id="contenido" class="contenedor">
{pagina.contenido}
</main>
<footer class="pie">
  <div class="contenedor pie__fila">
    <p><strong>{escape(sitio["nombre"])}</strong> · Datos oficiales con su fuente.
      Código <a href="{escape(sitio["repositorio"])}">abierto (MIT)</a> y datos propios CC BY 4.0.</p>
    <p><a href="{raiz}metodologia/">Metodología</a> · <a href="{raiz}fuentes/">Fuentes</a> ·
      <a href="{raiz}acerca/">Acerca y privacidad</a> ·
      <a href="{escape(sitio["repositorio"])}/issues/new/choose">Reportar un error</a></p>
    <p class="pie__fecha">Datos actualizados el {escape(sitio["actualizado"])}.</p>
    <p class="pie__credito">Creado y mantenido por <a href="mailto:{escape(sitio["correo"])}">Angel Romero</a>.</p>
  </div>
</footer>
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


def miga(raiz: str, pasos: list[tuple[str, str]]) -> str:
    """Migas de pan: [(ruta relativa a la raíz o '', texto)]; el último no es enlace."""
    partes = [f'<a href="{raiz}{ruta}">{escape(t)}</a>' for ruta, t in pasos[:-1]]
    partes.append(f'<span aria-current="page">{escape(pasos[-1][1])}</span>')
    return f'<nav class="miga" aria-label="Ruta">{" / ".join(partes)}</nav>'
