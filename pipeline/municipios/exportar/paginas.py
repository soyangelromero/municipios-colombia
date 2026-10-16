"""Contenido de cada página del sitio. Todas se generan con las cifras ya escritas en el HTML."""

from html import escape
from pathlib import Path
from urllib.parse import urlencode

from municipios.comun.modelos import Municipio
from municipios.exportar import formato
from municipios.exportar.datos_web import NOMBRES_GRUPOS, DatosSitio
from municipios.exportar.plantillas import Pagina, barra, miga, semaforo
from municipios.fuentes.divipola import DEPARTAMENTOS
from municipios.relevamiento.criterios import CRITERIOS

# Nombre corto de cada organismo, para los enlaces «Fuente».
SIGLAS = {
    "dane_": "DANE",
    "mindefensa_": "MinDefensa",
    "pgn_": "Procuraduría",
    "mintic_": "MinTIC",
    "funcion_publica_": "Función Pública",
    "cgr_": "Contraloría (CUIPO)",
    "cce_": "SECOP II",
    "men_": "MinEducación",
    "adres_": "ADRES",
    "dnp_": "DNP",
}
# Escala de color de los mapas (cinco tramos del índice o del puntaje del pilar).
TRAMOS = ((40, "e1"), (50, "e2"), (60, "e3"), (70, "e4"), (101, "e5"))
CAPAS = (("indice", "Índice"), ("T", "Transparencia"), ("S", "Servicios"), ("G", "Gestión"), ("C", "Control"))  # fmt: skip


def sigla(clave: str) -> str:
    return next((s for prefijo, s in SIGLAS.items() if clave.startswith(prefijo)), clave)


def tramo(valor: float | None) -> str:
    if valor is None:
        return "sin"
    return next(t for limite, t in TRAMOS if valor < limite)


def _num(valor: float | None, decimales: int = 1) -> str:
    return formato.numero(valor, decimales) if valor is not None else "—"


# --- piezas compartidas ---------------------------------------------------------------------
def enlaces_fuente(datos: DatosSitio, claves: list[str] | tuple[str, ...]) -> str:
    """Un enlace por organismo (dos conjuntos de ADRES dan un solo «ADRES»)."""
    por_sigla: dict[str, list] = {}
    for clave in dict.fromkeys(claves):
        if fuente := datos.fuentes.get(clave):
            por_sigla.setdefault(sigla(clave), []).append(fuente)
    enlaces = [
        f'<a href="{escape(fuentes[0].url)}" title="{escape(fuentes[0].organismo)}: '
        f'{escape("; ".join(f.titulo for f in fuentes))}" rel="noopener">{escape(s)}</a>'
        for s, fuentes in por_sigla.items()
    ]
    return " · ".join(enlaces) or "—"


def leyenda_escala() -> str:
    pasos = [("e1", "menos de 40"), ("e2", "40 a 49"), ("e3", "50 a 59"), ("e4", "60 a 69"), ("e5", "70 o más"), ("sin", "sin dato")]  # fmt: skip
    items = "".join(f'<li><span class="muestra muestra--{c}"></span>{t}</li>' for c, t in pasos)
    return f'<ul class="leyenda" aria-label="Escala de colores">{items}</ul>'


def mapa_en_linea(ruta_svg: Path, colores: dict[str, str], etiqueta: str) -> str:
    """Inserta el SVG del mapa con una regla de color por entidad (funciona sin JavaScript)."""
    if not ruta_svg.exists():
        return '<p class="nota">El mapa no está disponible en esta versión.</p>'
    svg = ruta_svg.read_text(encoding="utf-8")
    svg = svg.replace("<svg ", '<svg class="mapa__svg" focusable="false" ', 1)
    reglas = "".join(f'[data-codigo="{c}"]{{fill:var(--escala-{t})}}' for c, t in colores.items())
    return (
        f'<figure class="mapa" aria-label="{escape(etiqueta)}"><style>{reglas}</style>'
        f'{svg}<figcaption class="mapa__ayuda">Toca o pasa el cursor sobre el mapa para ver el dato.'
        f"</figcaption></figure>"
    )


def tabla_ranking(datos: DatosSitio, codigos: list[str], raiz: str, con_departamento: bool) -> str:
    filas = []
    for c in codigos:
        m, f = datos.municipios[c], datos.indice[c]
        pilares = "".join(
            f'<td class="num" data-v="{datos.valor(c, p) or ""}">{_num(datos.valor(c, p), 0)}</td>'
            for p in "TSGC"
        )
        poblacion = f.get("datos", {}).get("poblacion", {}).get("valor")
        dep = f"<td>{escape(m.departamento)}</td>" if con_departamento else ""
        filas.append(
            f'<tr data-dep="{m.departamento_codigo}" data-grupo="{escape(f.get("grupo") or "")}"'
            f' data-semaforo="{f.get("semaforo") or ""}" data-nombre="{escape(m.nombre.lower())}">'
            f'<td class="num" data-v="{f["puesto"]["nacional"]}">{f["puesto"]["nacional"]}</td>'
            f'<th scope="row"><a href="{raiz}m/{m.slug}/">{escape(m.nombre)}</a></th>{dep}'
            f"<td>{escape(f.get('grupo') or '')}</td>"
            f'<td class="num" data-v="{f["indice"]}">{semaforo(f["semaforo"], f["indice"])}</td>'
            f'{pilares}<td class="num" data-v="{poblacion or 0}">{formato.numero(poblacion)}</td></tr>'
        )
    cabecera_dep = '<th scope="col">Departamento</th>' if con_departamento else ""
    return (
        '<div class="tabla-contenedor"><table class="tabla tabla--ranking" data-ordenable>'
        '<thead><tr><th scope="col" data-orden="num">Puesto</th><th scope="col">Municipio</th>'
        f'{cabecera_dep}<th scope="col" title="Grupo de capacidades del DNP">Grupo</th>'
        '<th scope="col" data-orden="num">Índice</th>'
        '<th scope="col" data-orden="num" title="Transparencia">T</th>'
        '<th scope="col" data-orden="num" title="Servicios y seguridad">S</th>'
        '<th scope="col" data-orden="num" title="Gestión fiscal y contratación">G</th>'
        '<th scope="col" data-orden="num" title="Control e institucionalidad">C</th>'
        '<th scope="col" data-orden="num">Población</th></tr></thead>'
        f"<tbody>{''.join(filas)}</tbody></table></div>"
    )


# --- inicio ---------------------------------------------------------------------------------
def inicio(datos: DatosSitio, dir_mapas: Path) -> Pagina:
    ranking = datos.ranking()
    conteo = {s: sum(1 for c in ranking if datos.indice[c]["semaforo"] == s) for s in ("verde", "amarillo", "rojo")}  # fmt: skip
    por_dep = datos.por_departamento()
    colores = {
        cod: tramo(datos.promedio([m.divipola for m in por_dep.get(cod, [])]))
        for cod in DEPARTAMENTOS
    }

    def lista(codigos: list[str]) -> str:
        items = "".join(
            f'<li><a href="m/{datos.municipios[c].slug}/"><span>{escape(datos.municipios[c].nombre)}'
            f"<small>{escape(datos.municipios[c].departamento)}</small></span>"
            f"{semaforo(datos.indice[c]['semaforo'], datos.indice[c]['indice'])}</a></li>"
            for c in codigos
        )
        return f'<ol class="lista-municipios">{items}</ol>'

    pilares = "".join(
        f'<li class="tarjeta"><h3>{escape(p.nombre)} <small>{p.peso:g} %</small></h3>'
        f"<p>{escape(p.descripcion)}</p></li>"
        for p in datos.config.pilares
    )
    botones_capa = "".join(
        f'<button type="button" data-capa="{c}" aria-pressed="{"true" if c == "indice" else "false"}">{t}</button>'
        for c, t in CAPAS
    )
    contenido = f"""
<section class="portada">
  <div class="portada__texto">
    <p class="etiqueta">Observatorio ciudadano · datos oficiales</p>
    <h1>¿Tu municipio muestra sus <span class="acento">cuentas</span>?</h1>
    <p class="entradilla">{escape(datos.sitio["descripcion"])}</p>
    <form class="busqueda busqueda--grande" data-busqueda action="ranking/" role="search">
      <label class="visualmente-oculto" for="buscar-portada">Busca tu municipio</label>
      <input id="buscar-portada" name="q" type="search" placeholder="Escribe el nombre de tu municipio"
        autocomplete="off" role="combobox" aria-expanded="false" aria-controls="buscar-portada-lista">
      <ul id="buscar-portada-lista" class="busqueda__lista" role="listbox" hidden></ul>
    </form>
    <ul class="cifras">
      <li><strong>{formato.numero(len(ranking))}</strong> municipios con índice</li>
      <li class="cifras--verde"><strong>{conteo["verde"]}</strong> en verde</li>
      <li class="cifras--amarillo"><strong>{conteo["amarillo"]}</strong> en amarillo</li>
      <li class="cifras--rojo"><strong>{conteo["rojo"]}</strong> en rojo</li>
    </ul>
  </div>
  <div class="portada__mapa" data-mapa-pais>
    <div class="capas" role="group" aria-label="Qué mostrar en el mapa">{botones_capa}</div>
    {mapa_en_linea(dir_mapas / "colombia.svg", colores, "Mapa de Colombia por departamento, coloreado según el índice promedio")}
    {leyenda_escala()}
    <p class="nota">Promedio de los municipios de cada departamento. Toca un departamento para ver sus municipios.</p>
  </div>
</section>

<section class="dos-columnas">
  <div>
    <h2>Mejor índice</h2>
    {lista(ranking[:10])}
  </div>
  <div>
    <h2>Más por mejorar</h2>
    {lista(list(reversed(ranking[-10:])))}
  </div>
</section>
<p class="centrado"><a class="boton" href="ranking/">Ver el ranking completo</a></p>

<section>
  <h2>Qué mide el índice</h2>
  <p>Un número de 0 a 100 con cuatro pilares. Cada municipio se compara con los de su <a href="metodologia/#pares">grupo de capacidades</a> del DNP: un municipio pequeño no se mide contra Medellín.</p>
  <ul class="rejilla">{pilares}</ul>
  <p><a href="metodologia/">Cómo se calcula, paso a paso</a></p>
</section>
"""
    return Pagina(
        "",
        datos.sitio["nombre"],
        datos.sitio["descripcion"],
        contenido,
        ("inicio.js",),
        "pagina-inicio",
    )


# --- ficha de municipio ---------------------------------------------------------------------
def _valor_componente(
    datos: DatosSitio, fila: dict, comp_id: str, si_falta: float | None
) -> tuple[str, str, str]:
    """(valor para mostrar, período, fuentes) de un componente."""
    dato = fila.get("datos", {}).get(comp_id)
    ficha = datos.indicadores.get(comp_id)
    if dato is None:
        texto = "No reportó" if si_falta is not None else "Sin dato"
        fuente = enlaces_fuente(datos, [ficha.fuente]) if ficha else "—"
        return f'<span class="sin-dato">{texto}</span>', "—", fuente
    unidad = ficha.unidad if ficha else ""
    return (
        escape(formato.segun_unidad(dato["valor"], unidad)),
        escape(formato.periodo(dato["periodo"])),
        enlaces_fuente(datos, dato["fuentes"]),
    )


def _resumen(m: Municipio, fila: dict) -> str:
    if fila.get("indice") is None:
        return escape(fila.get("motivo_sin_indice") or "Este municipio no tiene índice.")
    p = fila["puesto"]
    rango = fila.get("rango_puestos") or [p["nacional"], p["nacional"]]
    texto = (
        f"{m.nombre} tiene un índice de {_num(fila['indice'])} sobre 100 ({fila['semaforo']}). "
        f"Es el puesto {p['nacional']} de {formato.numero(p['nacional_de'])} en el país, "
        f"{p['departamento']} de {p['departamento_de']} en {m.departamento} y "
        f"{p['grupo']} de {p['grupo_de']} entre los municipios de su grupo. "
        f"Si se mueven ±10 puntos los pesos de los pilares, su puesto va del {rango[0]} al {rango[1]}."
    )
    if fila.get("tope"):
        texto += " Su índice está topado en 39,9 porque no reportó su ejecución presupuestal."
    return escape(texto)


def bloque_revision_automatica(datos: DatosSitio, codigo: str) -> str:
    """Resultado del relevamiento automático del sitio de la alcaldía (no puntúa)."""
    filas = datos.transparencia_auto.get(codigo)
    if not filas:
        return ""
    nombres = {c.id: c.nombre for c in CRITERIOS}
    problema = {
        "sitio_no_encontrado": "No se encontró el sitio web oficial.",
        "no_permitido": "El sitio no permite la revisión automática (robots.txt).",
        "error": "No se pudo abrir el menú de transparencia.",
        "menu_no_legible": "El menú de transparencia no se pudo leer de forma automática: no se sabe qué publica.",
    }.get(filas[0]["resultado"])
    items = []
    for f in filas:
        if f["resultado"] == "enlace_encontrado":
            estado = f'<a href="{escape(f["evidencia"])}" rel="noopener">Enlace encontrado</a>'
        else:
            estado = "No se encontró un enlace en esa página"
        items.append(
            f"<li><span>{escape(nombres.get(f['criterio'], f['criterio']))}</span> <small>{estado}</small></li>"
        )
    sitio = filas[0]["sitio"]
    origen = (
        f' Sitio revisado: <a href="{escape(sitio)}" rel="noopener">{escape(sitio)}</a>.'
        if sitio
        else ""
    )
    cuerpo = (
        f'<p class="nota">{problema}</p>'
        if problema
        else f'<ul class="revision">{"".join(items)}</ul>'
    )
    return (
        '<aside class="revision-auto"><h3>Revisión automática del sitio web '
        "<small>sin verificación humana, no puntúa</small></h3>"
        f"{cuerpo}"
        f'<p class="nota">Un robot buscó estos criterios en el menú de transparencia el {escape(filas[0]["fecha"])}. '
        f"Solo lee la página principal del menú, no sus subpáginas: que falte un enlace no prueba que no se publique, y que haya uno no prueba que el documento esté completo ni al día.{origen}</p></aside>"
    )


def ficha(datos: DatosSitio, codigo: str) -> Pagina:
    m = datos.municipios[codigo]
    fila = datos.indice[codigo]
    ruta = f"m/{m.slug}/"
    raiz = "../../"
    grupo = NOMBRES_GRUPOS.get(fila.get("grupo") or "", "sin grupo")

    resumen_pilares = "".join(
        f'<li><a href="#pilar-{p.id}">{escape(p.nombre)}</a> <small>{p.peso:g} %</small>'
        f"{barra(datos.valor(codigo, p.id), p.nombre)}</li>"
        for p in datos.config.pilares
    )
    secciones = []
    for p in datos.config.pilares:
        info = fila.get("pilares", {}).get(p.id, {})
        filas_comp = []
        for c in p.componentes:
            valor, periodo, fuentes = _valor_componente(datos, fila, c.id, c.si_falta)
            puntaje = fila.get("componentes", {}).get(c.id, {}).get("puntaje")
            como = "entre pares" if c.puntaje == "pares" else "escala absoluta"
            filas_comp.append(
                f'<tr><th scope="row">{escape(c.nombre)}<small>{como}</small></th>'
                f'<td class="num">{valor}</td><td>{periodo}</td>'
                f"<td>{barra(puntaje, c.nombre)}</td><td>{fuentes}</td></tr>"
            )
        cobertura = info.get("cobertura")
        aviso = (
            f'<p class="nota">Este pilar tiene datos para el {formato.numero(100 * cobertura)} % de su peso'
            + (" y no alcanza el mínimo para contar." if not info.get("valido") else ".")
            + "</p>"
            if cobertura is not None and cobertura < 1
            else ""
        )
        secciones.append(
            f'<section class="tarjeta" id="pilar-{p.id}" data-capitulo="{escape(p.nombre)}">'
            f'<header class="tarjeta__cabecera"><h2>{escape(p.nombre)} <small>{p.peso:g} % del índice</small></h2>'
            f"{barra(datos.valor(codigo, p.id), p.nombre)}</header>"
            f"<p>{escape(p.descripcion)}</p>{aviso}"
            '<div class="tabla-contenedor"><table class="tabla tabla--ficha"><thead><tr><th scope="col">Indicador</th>'
            '<th scope="col">Valor</th><th scope="col">Período</th><th scope="col">Puntaje</th>'
            f'<th scope="col">Fuente</th></tr></thead><tbody>{"".join(filas_comp)}</tbody></table></div>'
            f"{bloque_revision_automatica(datos, codigo) if p.id == 'T' else ''}</section>"
        )

    contexto = []
    for ind in datos.config.contexto:
        dato = fila.get("datos", {}).get(ind)
        ficha_ind = datos.indicadores.get(ind)
        if dato is None or ficha_ind is None:
            continue
        contexto.append(
            f"<div><dt>{escape(ficha_ind.etiqueta)}</dt>"
            f"<dd>{escape(formato.segun_unidad(dato['valor'], ficha_ind.unidad))}"
            f"<small>{escape(formato.periodo(dato['periodo']))} · {enlaces_fuente(datos, dato['fuentes'])}</small></dd></div>"
        )

    reportar = (
        datos.sitio["repositorio"]
        + "/issues/new?"
        + urlencode(
            {
                "template": "error-en-dato.yml",
                "title": f"[Dato] {m.nombre} ({m.departamento}): ",
                "municipio": f"{m.nombre}, {m.departamento} ({codigo})",
            }
        )
    )
    puesto_html = ""
    if fila.get("puesto"):
        p = fila["puesto"]
        puesto_html = (
            '<dl class="puestos">'
            f"<div><dt>En el país</dt><dd>{p['nacional']}<small> de {formato.numero(p['nacional_de'])}</small></dd></div>"
            f"<div><dt>En {escape(m.departamento)}</dt><dd>{p['departamento']}<small> de {p['departamento_de']}</small></dd></div>"
            f"<div><dt>En su grupo</dt><dd>{p['grupo']}<small> de {p['grupo_de']}</small></dd></div>"
            "</dl>"
        )
    contenido = f"""
{miga(raiz, [("", "Inicio"), (f"d/{m.departamento_slug}/", m.departamento), ("", m.nombre)])}
<article class="ficha" data-codigo="{codigo}" data-nombre="{escape(m.nombre)}">
<header class="ficha__cabecera" data-capitulo="Portada">
  <p class="etiqueta">{escape(m.departamento)} · {escape(grupo)}</p>
  <h1>{escape(m.nombre)}</h1>
  <div class="ficha__indice">
    <p class="indice-grande indice-grande--{fila.get("semaforo") or "sin"}">
      <span class="indice-grande__valor">{_num(fila.get("indice"))}</span>
      <span class="indice-grande__de">de 100</span></p>
    {semaforo(fila.get("semaforo"))}
    {puesto_html}
  </div>
  <p class="ficha__resumen">{_resumen(m, fila)}</p>
  <div class="acciones">
    <button type="button" class="boton" data-historia hidden>Ver como historia</button>
    <a class="boton boton--secundario" href="{raiz}comparar/?a={codigo}">Comparar</a>
    <button type="button" class="boton boton--secundario" data-compartir hidden>Compartir</button>
    <a class="boton boton--secundario" href="{escape(reportar)}" rel="noopener">Reportar un error</a>
  </div>
</header>

<section class="tarjeta" data-capitulo="Resumen">
  <h2>Los cuatro pilares</h2>
  <ul class="pilares">{resumen_pilares}</ul>
</section>

{"".join(secciones)}

<section class="tarjeta" data-capitulo="Contexto">
  <h2>Contexto <small>no puntúa</small></h2>
  <dl class="contexto">{"".join(contexto) or "<p>Sin datos de contexto.</p>"}</dl>
</section>

<section class="tarjeta">
  <h2>{escape(m.nombre)} en el mapa de {escape(m.departamento)}</h2>
  <div class="mapa mapa--ficha" data-mapa="{m.departamento_slug}" data-resaltar="{codigo}">
    <p class="nota"><a href="{raiz}d/{m.departamento_slug}/">Ver el mapa y el ranking de {escape(m.departamento)}</a></p>
  </div>
</section>

<section class="nota-final">
  <p>Cada cifra tiene su fuente oficial. Los puntajes «entre pares» son el percentil del municipio dentro de su grupo de capacidades del DNP (0 = el peor del grupo, 100 = el mejor). <a href="{raiz}metodologia/">Ver la metodología</a>.</p>
</section>
</article>
"""
    descripcion = (
        f"{m.nombre} ({m.departamento}): índice municipal {_num(fila.get('indice'))}/100. "
        "Transparencia, servicios, seguridad, gestión y control, con fuentes oficiales."
    )
    return Pagina(
        ruta, f"{m.nombre}, {m.departamento}", descripcion, contenido, ("ficha.js",), "pagina-ficha"
    )


# --- departamento ---------------------------------------------------------------------------
def departamento(datos: DatosSitio, cod: str, dir_mapas: Path) -> Pagina:
    nombre, slug = DEPARTAMENTOS[cod]
    municipios = datos.por_departamento().get(cod, [])
    codigos = [m.divipola for m in municipios]
    con_indice = sorted(
        (c for c in codigos if datos.indice[c].get("indice") is not None),
        key=lambda c: datos.indice[c]["puesto"]["nacional"],
    )
    sin_indice = [c for c in codigos if c not in con_indice]
    conteo = {s: sum(1 for c in con_indice if datos.indice[c]["semaforo"] == s) for s in ("verde", "amarillo", "rojo")}  # fmt: skip
    colores = {c: tramo(datos.indice[c].get("indice")) for c in codigos}
    raiz = "../../"
    lista_sin = ""
    if sin_indice:
        items = "".join(
            f'<li><a href="{raiz}m/{datos.municipios[c].slug}/">{escape(datos.municipios[c].nombre)}</a>'
            f" — {escape(datos.indice[c].get('motivo_sin_indice') or '')}</li>"
            for c in sin_indice
        )
        lista_sin = f"<h2>Sin índice</h2><ul>{items}</ul>"
    contenido = f"""
{miga(raiz, [("", "Inicio"), ("", nombre)])}
<header class="encabezado">
  <p class="etiqueta">Departamento</p>
  <h1>{escape(nombre)}</h1>
  <ul class="cifras">
    <li><strong>{len(codigos)}</strong> {"municipio" if len(codigos) == 1 else "municipios y áreas"}</li>
    <li><strong>{_num(datos.promedio(codigos))}</strong> índice promedio</li>
    <li class="cifras--verde"><strong>{conteo["verde"]}</strong> en verde</li>
    <li class="cifras--amarillo"><strong>{conteo["amarillo"]}</strong> en amarillo</li>
    <li class="cifras--rojo"><strong>{conteo["rojo"]}</strong> en rojo</li>
  </ul>
</header>
<section class="tarjeta" data-mapa-departamento>
  {mapa_en_linea(dir_mapas / f"{slug}.svg", colores, f"Mapa de los municipios de {nombre}, coloreado según el índice")}
  {leyenda_escala()}
</section>
<section>
  <h2>Ranking de {escape(nombre)}</h2>
  <p class="nota">El puesto es el nacional. Ordena la tabla tocando los encabezados.</p>
  {tabla_ranking(datos, con_indice, raiz, con_departamento=False) if con_indice else "<p>Ningún municipio tiene índice.</p>"}
  {lista_sin}
</section>
"""
    return Pagina(
        f"d/{slug}/",
        f"Municipios de {nombre}",
        f"Índice municipal de los municipios de {nombre}: transparencia, servicios, seguridad, gestión y control.",
        contenido,
        ("departamento.js", "tablas.js"),
        "pagina-departamento",
    )


# --- ranking --------------------------------------------------------------------------------
def ranking(datos: DatosSitio) -> Pagina:
    codigos = datos.ranking()
    raiz = "../"
    deps = "".join(
        f'<option value="{cod}">{escape(nombre)}</option>'
        for cod, (nombre, _) in sorted(DEPARTAMENTOS.items(), key=lambda kv: kv[1][0])
    )
    grupos = "".join(f'<option value="{g}">{escape(n)}</option>' for g, n in NOMBRES_GRUPOS.items())
    contenido = f"""
{miga(raiz, [("", "Inicio"), ("", "Ranking")])}
<header class="encabezado">
  <h1>Ranking de municipios</h1>
  <p class="entradilla">{formato.numero(len(codigos))} municipios ordenados por el índice municipal (v{escape(datos.config.version)}). T = transparencia, S = servicios y seguridad, G = gestión fiscal y contratación, C = control.</p>
</header>
<form class="filtros" data-filtros hidden>
  <label>Buscar <input type="search" name="texto" placeholder="Nombre del municipio"></label>
  <label>Departamento <select name="dep"><option value="">Todos</option>{deps}</select></label>
  <label>Grupo <select name="grupo"><option value="">Todos</option>{grupos}</select></label>
  <label>Semáforo <select name="semaforo"><option value="">Todos</option>
    <option value="verde">Verde</option><option value="amarillo">Amarillo</option><option value="rojo">Rojo</option></select></label>
  <p class="filtros__conteo" aria-live="polite"></p>
</form>
{tabla_ranking(datos, codigos, raiz, con_departamento=True)}
"""
    return Pagina(
        "ranking/",
        "Ranking de municipios",
        "Ranking de los municipios de Colombia según el índice municipal, con filtros por departamento y grupo.",
        contenido,
        ("tablas.js",),
        "pagina-ranking",
    )


# --- comparar -------------------------------------------------------------------------------
def comparar(datos: DatosSitio) -> Pagina:
    raiz = "../"
    contenido = f"""
{miga(raiz, [("", "Inicio"), ("", "Comparar")])}
<header class="encabezado">
  <h1>Comparar dos municipios</h1>
  <p class="entradilla">Elige dos municipios para verlos lado a lado, pilar por pilar y dato por dato.</p>
</header>
<form class="comparar__elegir" data-comparar>
  <div class="busqueda" data-busqueda data-busqueda-campo="a">
    <label for="comparar-a">Municipio A</label>
    <input id="comparar-a" type="search" placeholder="Escribe un municipio" autocomplete="off"
      role="combobox" aria-expanded="false" aria-controls="comparar-a-lista">
    <ul id="comparar-a-lista" class="busqueda__lista" role="listbox" hidden></ul>
  </div>
  <div class="busqueda" data-busqueda data-busqueda-campo="b">
    <label for="comparar-b">Municipio B</label>
    <input id="comparar-b" type="search" placeholder="Escribe otro municipio" autocomplete="off"
      role="combobox" aria-expanded="false" aria-controls="comparar-b-lista">
    <ul id="comparar-b-lista" class="busqueda__lista" role="listbox" hidden></ul>
  </div>
</form>
<div class="comparar__resultado" data-comparar-resultado aria-live="polite"></div>
<noscript><p class="nota">El comparador necesita JavaScript. Puedes ver cada municipio en su ficha desde el <a href="{raiz}ranking/">ranking</a>.</p></noscript>
"""
    return Pagina(
        "comparar/",
        "Comparar municipios",
        "Compara dos municipios de Colombia lado a lado: índice, pilares y cada dato con su fuente.",
        contenido,
        ("comparar.js",),
        "pagina-comparar",
    )


# --- metodología ----------------------------------------------------------------------------
def metodologia(datos: DatosSitio) -> Pagina:
    c = datos.config
    r = c.reglas
    pilares = []
    for p in c.pilares:
        total = sum(x.peso for x in p.componentes)
        filas = "".join(
            f'<tr><th scope="row">{escape(x.nombre)}</th><td class="num">{formato.numero(100 * x.peso / total, 0)} %</td>'
            f"<td>{'entre pares' if x.puntaje == 'pares' else 'escala absoluta'}</td>"
            f"<td>{'más alto es mejor' if x.sentido == 'mayor_mejor' else 'más bajo es mejor'}</td>"
            f"<td>{'no reportar cuenta como 0' if x.si_falta is not None else 'si falta, su peso se reparte'}</td></tr>"
            for x in p.componentes
        )
        pilares.append(
            f'<section class="tarjeta" id="pilar-{p.id}"><h3>{escape(p.nombre)} <small>{p.peso:g} % del índice</small></h3>'
            f"<p>{escape(p.descripcion)}</p>"
            '<div class="tabla-contenedor"><table class="tabla"><thead><tr><th scope="col">Componente</th>'
            '<th scope="col">Peso en el pilar</th><th scope="col">Puntaje</th><th scope="col">Sentido</th>'
            f'<th scope="col">Si no hay dato</th></tr></thead><tbody>{filas}</tbody></table></div></section>'
        )
    derivados = "".join(
        f"<li><strong>{escape(i.etiqueta)}:</strong> {escape(i.descripcion)}</li>"
        for i in datos.indicadores.values()
        if i.descripcion and any(i.clave == x.id for p in c.pilares for x in p.componentes)
    )
    grupos = "".join(
        f"<li><strong>{g}</strong>: {escape(n)}</li>" for g, n in NOMBRES_GRUPOS.items()
    )
    refs = ", ".join(f"{k}: {v}" for k, v in datos.anios_referencia.items() if v)
    contenido = f"""
{miga("../", [("", "Inicio"), ("", "Metodología")])}
<header class="encabezado">
  <h1>Metodología del índice municipal <small>v{escape(c.version)}</small></h1>
  <p class="entradilla">Un número de 0 a 100 que resume si la alcaldía muestra sus cuentas, qué servicios y seguridad recibe su población, cómo gestiona su presupuesto y su contratación, y qué capacidad institucional tiene. Esta página se genera desde el mismo archivo de configuración que usa el cálculo, <a href="{escape(datos.sitio["repositorio"])}/blob/main/pipeline/config/indice.toml"><code>indice.toml</code></a>.</p>
</header>

<section id="pares">
  <h2>Con quién se compara cada municipio</h2>
  <p>Con su <strong>grupo de capacidades iniciales</strong> del Departamento Nacional de Planeación (Medición de Desempeño Municipal). Es la agrupación oficial para comparar municipios con condiciones de partida parecidas:</p>
  <ul>{grupos}</ul>
  <p>En los componentes «entre pares», el puntaje es el <strong>percentil dentro del grupo</strong>: 0 es el peor del grupo y 100 el mejor; los empates comparten percentil. Los grupos con menos de {r["pares_minimos"]:g} municipios se comparan con todo el país.</p>
</section>

<section>
  <h2>Pilares y componentes</h2>
  {"".join(pilares)}
</section>

<section>
  <h2>Reglas</h2>
  <ol>
    <li><strong>Obligaciones no reportadas cuentan como 0.</strong> Si una alcaldía no diligencia el ITA o el FURAG, ese componente vale 0 y su peso no se reparte.</li>
    <li><strong>Lo que no depende del municipio sí se reparte.</strong> La auditoría del ITA depende del muestreo de la Procuraduría: si no la hay, su peso se reparte dentro del pilar.</li>
    <li>Un pilar cuenta si tiene datos para al menos el {formato.numero(100 * r["cobertura_minima_pilar"])} % de su peso.</li>
    <li>El índice exige el pilar de transparencia y al menos {r["pilares_minimos"]:g} de los {len(c.pilares)} pilares.</li>
    <li><strong>Tope sin cuentas:</strong> si la alcaldía no reportó su ejecución presupuestal (CUIPO) del último año completo, su índice no pasa de {formato.numero(r["tope_sin_cuentas"], 1)}.</li>
    <li>No entran datos de más de {r["antiguedad_maxima_anios"]:g} años atrás.</li>
    <li>Cada indicador anual se compara en el mismo año para todos ({escape(refs)}): el último año completo con datos de al menos la mitad de los municipios.</li>
    <li><strong>Tasas de delitos suavizadas:</strong> promedio de 3 años, suavizado hacia la tasa de su grupo con una población ficticia de {formato.numero(r["suavizado_poblacion"])} habitantes, para que en un municipio muy pequeño un hecho aislado no lo convierta en el peor del país. La ficha muestra la tasa sin suavizar.</li>
  </ol>
</section>

<section>
  <h2>Semáforo</h2>
  <p>{semaforo("rojo")} menos de {c.semaforo["rojo_menor_a"]:g} · {semaforo("amarillo")} de {c.semaforo["rojo_menor_a"]:g} a {c.semaforo["verde_desde"] - 0.1:g} · {semaforo("verde")} {c.semaforo["verde_desde"]:g} o más.</p>
</section>

<section>
  <h2>Qué tan estable es el puesto</h2>
  <p>Se recalcula el índice moviendo ±{r["sensibilidad_puntos"]:g} puntos el peso de cada pilar (y re-escalando los demás). Cada ficha muestra el rango de puestos resultante: un rango amplio significa que el puesto depende mucho de cómo se ponderen los pilares.</p>
</section>

<section>
  <h2>Cómo se calculan los indicadores derivados</h2>
  <ul>{derivados}</ul>
</section>

<section>
  <h2>Limitaciones de esta versión</h2>
  <ul>
    <li>El autodiagnóstico del ITA lo reporta la propia alcaldía y la mayoría declara 99 o 100; por eso pesa poco frente a la auditoría de la Procuraduría.</li>
    <li>Todavía no hay datos de acueducto, alcantarillado ni calidad del agua (no tienen conjunto de datos abierto con API).</li>
    <li>Contratación: solo SECOP II. Una alcaldía que publica solo en SECOP I aparece como «no publica».</li>
    <li>Los grupos del DNP son de la medición 2020, la última en datos abiertos. Nuevo Belén de Bajirá toma el grupo de Riosucio (del que se segregó) y Barrancominas el G5.</li>
    <li>Las áreas no municipalizadas y San Andrés (administrado por el departamento) no tienen índice.</li>
  </ul>
  <p>¿Ves un error o tienes una propuesta? <a href="{escape(datos.sitio["repositorio"])}/issues/new/choose">Abre un issue</a> o escribe a <a href="mailto:{escape(datos.sitio["correo"])}">{escape(datos.sitio["correo"])}</a>.</p>
</section>
"""
    return Pagina(
        "metodologia/",
        "Metodología",
        "Cómo se calcula el índice municipal: pilares, pesos, comparación entre pares, reglas y limitaciones.",
        contenido,
        clase="pagina-texto",
    )


# --- fuentes --------------------------------------------------------------------------------
def fuentes(datos: DatosSitio) -> Pagina:
    usa: dict[str, list[str]] = {}
    for ind in datos.indicadores.values():
        usa.setdefault(ind.fuente, []).append(ind.etiqueta)
    filas = "".join(
        f'<tr><th scope="row">{escape(f.organismo)}</th><td><a href="{escape(f.url)}" rel="noopener">{escape(f.titulo)}</a></td>'
        f"<td>{escape(', '.join(usa.get(f.clave, [])) or '—')}</td><td>{escape(f.licencia)}</td></tr>"
        for f in datos.fuentes.values()
    )
    contenido = f"""
{miga("../", [("", "Inicio"), ("", "Fuentes")])}
<header class="encabezado">
  <h1>Fuentes de datos</h1>
  <p class="entradilla">Todas las cifras salen de fuentes oficiales y abiertas. Cada dato del sitio enlaza a su fuente. El detalle técnico de cada una (cómo se descarga, cómo se cruza con el código DIVIPOLA y sus problemas de calidad) está en el <a href="{escape(datos.sitio["repositorio"])}/blob/main/docs/fuentes.md">repositorio</a>.</p>
</header>
<div class="tabla-contenedor"><table class="tabla">
<thead><tr><th scope="col">Organismo</th><th scope="col">Conjunto de datos</th><th scope="col">Qué aporta</th><th scope="col">Licencia</th></tr></thead>
<tbody>{filas}</tbody></table></div>
"""
    return Pagina(
        "fuentes/",
        "Fuentes de datos",
        "Fuentes oficiales y abiertas de cada dato del índice municipal.",
        contenido,
        clase="pagina-texto",
    )


# --- acerca ---------------------------------------------------------------------------------
def acerca(datos: DatosSitio) -> Pagina:
    s = datos.sitio
    contenido = f"""
{miga("../", [("", "Inicio"), ("", "Acerca")])}
<header class="encabezado"><h1>Acerca del proyecto</h1></header>
<section>
  <p><strong>{escape(s["nombre"])}</strong> es un observatorio ciudadano, abierto y neutral. Muestra, para cada municipio de Colombia, si su alcaldía publica sus cuentas, qué servicios y seguridad recibe su población, cómo gestiona su presupuesto y su contratación, y qué dicen las mediciones oficiales de control. Cada cifra lleva su fuente.</p>
  <p>No toma partido político ni recibe financiación de partidos o campañas. La metodología es pública y cualquier cambio queda registrado en el repositorio.</p>
</section>
<section>
  <h2>Correcciones y derecho de réplica</h2>
  <p>Si una alcaldía o una persona encuentra un dato equivocado, puede reportarlo con el botón «Reportar un error» de cada ficha, en <a href="{escape(s["repositorio"])}/issues/new/choose">GitHub</a> o escribiendo a <a href="mailto:{escape(s["correo"])}">{escape(s["correo"])}</a>. Las correcciones se publican con su fecha.</p>
</section>
<section id="privacidad">
  <h2>Privacidad</h2>
  <p>Este sitio no usa cookies, no usa herramientas de analítica ni publicidad y no carga recursos de terceros. No recopila datos personales. Si escribes por correo o abres un issue, esos datos los gestiona tu proveedor de correo o GitHub.</p>
</section>
<section>
  <h2>Código y datos abiertos</h2>
  <p>El código está en <a href="{escape(s["repositorio"])}">GitHub</a> bajo licencia MIT. Los datos propios (relevamientos, cálculos e índice) se publican bajo CC BY 4.0. Los datos de terceros conservan la licencia de su fuente.</p>
  <p>¿Quieres ayudar? Lee la <a href="{escape(s["repositorio"])}/blob/main/CONTRIBUTING.md">guía para contribuir</a>.</p>
</section>
"""
    return Pagina(
        "acerca/",
        "Acerca y privacidad",
        "Qué es el proyecto, cómo corregir un dato, privacidad y licencias.",
        contenido,
        clase="pagina-texto",
    )


def no_encontrada(datos: DatosSitio) -> Pagina:
    contenido = """
<header class="encabezado">
  <h1>No encontramos esa página</h1>
  <p class="entradilla">Puede que el enlace esté mal escrito o que la página haya cambiado de lugar. Busca tu municipio arriba o vuelve al <a href="./">inicio</a>.</p>
</header>
"""
    return Pagina(
        "404.html", "Página no encontrada", "Página no encontrada.", contenido, clase="pagina-texto"
    )
