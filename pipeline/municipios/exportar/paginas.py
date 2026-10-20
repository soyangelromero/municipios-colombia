"""Contenido de cada página del sitio. Todas se generan con las cifras ya escritas en el HTML."""

from html import escape
from pathlib import Path

from municipios.comun.modelos import Municipio
from municipios.exportar import formato
from municipios.exportar.aligerar import aligerar_svg
from municipios.exportar.datos_web import NOMBRES_GRUPOS, DatosSitio, url_reporte
from municipios.exportar.plantillas import (
    Pagina,
    anillo,
    bar2,
    barra,
    chip,
    color_puntaje,
    kpi,
    medidor,
    miga,
    semaforo,
    sin_dato,
)
from municipios.exportar.silueta import Siluetas
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


def _fecha_corta(iso: str) -> str:
    """'2026-10-18' -> '18/10/2026'."""
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}"


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


def titular(nombre: str) -> str:
    """Nombre con pesos mezclados: las primeras palabras livianas, la última negra y de acento."""
    palabras = nombre.split()
    if len(palabras) == 1:
        return f'<span class="t-negro acento">{escape(nombre)}</span>'
    return (
        f'<span class="t-liviano">{escape(" ".join(palabras[:-1]))}</span> '
        f'<span class="t-negro acento">{escape(palabras[-1])}</span>'
    )


def foto_img(
    datos: DatosSitio, codigo: str, raiz: str, *, primera: bool, tamanos: str, alt: str = ""
) -> str:
    """<img> de la foto del municipio con srcset, o cadena vacía si no hay foto libre."""
    if codigo not in datos.fotos:
        return ""
    base = f"{raiz}assets/fotos/{codigo}"
    carga = 'fetchpriority="high"' if primera else 'loading="lazy" decoding="async"'
    return (
        f'<img class="foto" src="{base}-1080.webp" '
        f'srcset="{base}-480.webp 480w, {base}-1080.webp 1080w" sizes="{tamanos}" alt="{escape(alt)}" {carga}>'
    )


def credito_foto(datos: DatosSitio, codigo: str) -> str:
    """Crédito y licencia de la foto (siempre visibles junto a ella)."""
    f = datos.fotos.get(codigo)
    if not f:
        return ""
    autor = f["autor"] if len(f["autor"]) <= 70 else f["autor"][:67] + "…"
    licencia = escape(f["licencia"])
    if f["url_licencia"]:
        licencia = f'<a href="{escape(f["url_licencia"])}" rel="noopener">{licencia}</a>'
    return (
        f'<p class="credito">Foto: {escape(autor)} · {licencia} · '
        f'<a href="{escape(f["url_pagina"])}" rel="noopener">Wikimedia Commons</a></p>'
    )


def formulario(
    tipo: str,
    datos: DatosSitio,
    *,
    titulo: str,
    ayuda: str,
    municipio: str = "",
    asunto: bool = False,
) -> str:
    """Formulario opcional: con PHP envía a la API; sin PHP cae a GitHub o al correo."""
    repo = escape(datos.sitio["repositorio"])
    correo = escape(datos.sitio["correo"])
    campo_asunto = (
        '<label>Asunto <input type="text" name="asunto" maxlength="160" required></label>'
        if asunto
        else ""
    )
    oculto_municipio = (
        f'<input type="hidden" name="municipio" value="{escape(municipio)}">' if municipio else ""
    )
    return f"""
<details class="enviar">
  <summary>{escape(titulo)}</summary>
  <form class="formulario" data-formulario="{tipo}" data-repo="{repo}" data-correo="{correo}">
    <input type="hidden" name="t" data-tiempo value="">
    <p class="visualmente-oculto" aria-hidden="true">
      <label>No llenar este campo <input type="text" name="web" tabindex="-1" autocomplete="off"></label>
    </p>
    {oculto_municipio}{campo_asunto}
    <label>Mensaje <textarea name="mensaje" rows="4" minlength="5" required></textarea></label>
    <label>Tu correo (opcional) <input type="email" name="contacto" maxlength="120"></label>
    <button type="submit" class="boton">Enviar</button>
    <p class="formulario__aviso" role="status" data-aviso></p>
    <p class="nota">{escape(ayuda)}</p>
  </form>
</details>"""


def leyenda_escala() -> str:
    pasos = [("e1", "menos de 40"), ("e2", "40 a 49"), ("e3", "50 a 59"), ("e4", "60 a 69"), ("e5", "70 o más"), ("sin", "sin dato")]  # fmt: skip
    items = "".join(f'<li><span class="muestra muestra--{c}"></span>{t}</li>' for c, t in pasos)
    return f'<ul class="leyenda" aria-label="Escala de colores">{items}</ul>'


def mapa_en_linea(ruta_svg: Path, colores: dict[str, str], etiqueta: str) -> str:
    """Inserta el SVG del mapa con una regla de color por entidad (funciona sin JavaScript)."""
    if not ruta_svg.exists():
        return '<p class="nota">El mapa no está disponible en esta versión.</p>'
    tolerancia = 0.8 if ruta_svg.stem == "colombia" else 0.35
    svg = aligerar_svg(ruta_svg.read_text(encoding="utf-8"), tolerancia)
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


# --- datos estructurados (schema.org) -------------------------------------------------------
def _ld_migas(datos: DatosSitio, pasos: list[tuple[str, str]]) -> dict:
    """BreadcrumbList: pasos = [(ruta relativa a la raíz, nombre)]."""
    base = datos.sitio["url_base"]
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": nombre, "item": base + ruta}
            for i, (ruta, nombre) in enumerate(pasos, 1)
        ],
    }


def _ld_sitio(datos: DatosSitio) -> list[dict]:
    """Organización, sitio y conjunto de datos abiertos (aparece en Google Dataset Search)."""
    s = datos.sitio
    base = s["url_base"]
    return [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": s["nombre"],
            "url": base,
            "inLanguage": s["idioma"],
            "description": s["descripcion"],
        },
        {
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "Índice municipal de Colombia",
            "description": (
                "Índice de transparencia, servicios y seguridad, gestión y control de los "
                "municipios de Colombia, con la fuente oficial de cada dato."
            ),
            "url": base,
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "isAccessibleForFree": True,
            "inLanguage": s["idioma"],
            "dateModified": s["actualizado"],
            "spatialCoverage": {"@type": "Country", "name": "Colombia"},
            "creator": {"@type": "Organization", "name": s["nombre"], "url": base},
            "distribution": [
                {
                    "@type": "DataDownload",
                    "encodingFormat": "application/json",
                    "contentUrl": base + "data/pais.json",
                }
            ],
        },
    ]


# --- inicio ---------------------------------------------------------------------------------
def _dato(fila: dict, clave: str) -> dict | None:
    return fila.get("datos", {}).get(clave)


def linea_portada(datos: DatosSitio, fila: dict) -> str:
    """«137.624 habitantes · 876 km² · 157 hab./km²», sin los datos que falten."""
    partes = []
    if _dato(fila, "poblacion") is not None:
        partes.append(f"{_valor_dato(datos, fila, 'poblacion')} habitantes")
    partes += [
        _valor_dato(datos, fila, clave)
        for clave in ("superficie_km2", "densidad")
        if _dato(fila, clave) is not None
    ]
    return " · ".join(partes)


def _valor_dato(datos: DatosSitio, fila: dict, clave: str, unidad: str | None = None) -> str:
    """Valor formateado de un indicador de contexto (o «—»)."""
    dato = _dato(fila, clave)
    if dato is None:
        return "—"
    u = (
        unidad
        if unidad is not None
        else (datos.indicadores[clave].unidad if clave in datos.indicadores else "")
    )
    return formato.segun_unidad(dato["valor"], u)


def tarjeta_carrusel(datos: DatosSitio, codigo: str, siluetas: Siluetas, puesto: int) -> str:
    """Tarjeta 9:15 de foto (o silueta) para el carrusel de la portada."""
    m, f = datos.municipios[codigo], datos.indice[codigo]
    foto = foto_img(datos, codigo, "", primera=puesto <= 3, tamanos="(max-width:620px) 56vw, 240px")
    fondo = foto or (siluetas.de(m.departamento_slug, codigo) or "")
    clase = "" if foto else " card__fondo--silueta"
    indice = f.get("indice")
    chip_txt = f"Índice {_num(indice, 0)}" if indice is not None else "Sin índice"
    poblacion = _dato(f, "poblacion")
    t, s = datos.valor(codigo, "T"), datos.valor(codigo, "S")
    meta = (
        f"{escape(m.departamento)} · {formato.numero(poblacion['valor'] if poblacion else None)} hab"
        f" · trans {_num(t, 0)} · seg {_num(s, 0)}"
    )
    gasto = _dato(f, "gasto_por_habitante")
    if gasto is not None:
        info = (
            '<span class="card__info-etq">Gasto por habitante</span>'
            f'<span class="card__info-val">{formato.segun_unidad(gasto["valor"], "pesos por habitante")}</span>'
        )
    else:
        info = '<span class="card__info-etq">Dato informativo</span><span class="card__info-val">—</span>'
    return (
        f'<a class="card" href="m/{m.slug}/" data-foto="{puesto}" data-dep="{m.departamento_codigo}"'
        f' data-grupo="{escape(f.get("grupo") or "")}">'
        f'<span class="card__fondo{clase}" aria-hidden="true">{fondo}</span>'
        f'<span class="card__chip">{chip(chip_txt, f.get("semaforo"))}</span>'
        f'<span class="card__puesto mono">{puesto:02d}</span>'
        '<span class="card__cuerpo">'
        f'<span class="card__nombre">{escape(m.nombre)}</span>'
        f'<span class="card__meta">{meta}</span>'
        f'<span class="card__info">{info}</span>'
        "</span></a>"
    )


def _fila_ranking(datos: DatosSitio, codigo: str, raiz: str) -> str:
    """Una fila de la lista de ranking (.rk)."""
    m, f = datos.municipios[codigo], datos.indice[codigo]
    iniciales = "".join(p[0] for p in m.nombre.split()[:2]).upper()
    valor = f.get("indice")
    return (
        '<li class="rk__fila">'
        f'<a class="rk__enlace" href="{raiz}m/{m.slug}/" data-historia="{codigo}">'
        f'<span class="rk__puesto mono">{f["puesto"]["nacional"]:02d}</span>'
        f'<span class="rk__cara" aria-hidden="true">{escape(iniciales)}</span>'
        f'<span class="rk__texto"><b>{escape(m.nombre)}</b>'
        f"<small>{escape(m.departamento)} · {escape(NOMBRES_GRUPOS.get(f.get('grupo') or '', 'sin grupo'))}</small></span>"
        f'<span class="rk__valor">{_num(valor, 0)}</span>'
        "</a>"
        f'<span class="rk__barra">{bar2(valor)}</span></li>'
    )


def _señales(datos: DatosSitio, codigo: str) -> list[tuple[str, str, str]]:
    """(color, texto, valor) de las señales del resumen, ordenadas por gravedad."""
    f = datos.indice[codigo]
    señales: list[tuple[str, str, str]] = []
    for pid, nombre in (
        ("T", "Transparencia"),
        ("S", "Servicios y seguridad"),
        ("G", "Gestión"),
        ("C", "Control"),
    ):
        v = datos.valor(codigo, pid)
        if v is None:
            señales.append(("rojo", f"{nombre} sin datos suficientes", "sin dato"))
            continue
        señales.append((color_puntaje(v), nombre, _num(v, 0)))
    if f.get("tope"):
        señales.insert(0, ("rojo", "No publica su ejecución presupuestal (índice topado)", "39,9"))
    gasto = _dato(f, "gasto_por_habitante")
    if gasto is not None:
        señales.append(
            (
                "info",
                "Gasto por habitante (contexto, no puntúa)",
                formato.segun_unidad(gasto["valor"], "pesos"),
            )
        )
    return señales


def inicio(datos: DatosSitio, dir_mapas: Path) -> Pagina:
    ranking = datos.ranking()
    conteo = {s: sum(1 for c in ranking if datos.indice[c]["semaforo"] == s) for s in ("verde", "amarillo", "rojo")}  # fmt: skip
    por_dep = datos.por_departamento()
    colores = {
        cod: tramo(datos.promedio([m.divipola for m in por_dep.get(cod, [])]))
        for cod in DEPARTAMENTOS
    }
    siluetas = Siluetas(dir_mapas)
    total = sum(1 for m in datos.municipios.values() if m.tipo in ("municipio", "isla"))

    pilares = "".join(
        f'<li class="tarjeta"><h3>{escape(p.nombre)} <small>{p.peso:g} %</small></h3>'
        f"<p>{escape(p.descripcion)}</p></li>"
        for p in datos.config.pilares
    )
    botones_capa = "".join(
        f'<button type="button" data-capa="{c}" aria-pressed="{"true" if c == "indice" else "false"}">{t}</button>'
        for c, t in CAPAS
    )
    # Histograma de la leyenda: una barra por departamento, según el índice promedio.
    histograma = "".join(
        f'<i class="hist__b hist__b--{colores[cod]}" style="height:{max(6, min(100, datos.promedio([m.divipola for m in por_dep.get(cod, [])]) or 0)):.0f}%"></i>'
        for cod in DEPARTAMENTOS
    )
    promedios = [
        datos.promedio([m.divipola for m in por_dep.get(cod, [])]) for cod in DEPARTAMENTOS
    ]
    promedios = [v for v in promedios if v is not None]

    def opciones_dep() -> str:
        return "".join(
            f'<option value="{cod}">{escape(nombre)}</option>'
            for cod, (nombre, _) in sorted(DEPARTAMENTOS.items(), key=lambda kv: kv[1][0])
        )

    grupos = "".join(f'<option value="{g}">{escape(n)}</option>' for g, n in NOMBRES_GRUPOS.items())

    intro = f"""
<div class="intro" id="intro" data-intro role="dialog" aria-modal="true" aria-label="Presentación del proyecto">
  <div class="intro__fondo" aria-hidden="true"></div>
  <div class="intro__prog" aria-hidden="true"><span><i></i></span><span><i></i></span><span><i></i></span></div>
  <div class="intro__mapa" data-intro-mapa aria-hidden="true"></div>
  <button type="button" class="pill intro__salto" data-intro-salto>Saltar</button>
  <div class="intro__contenido">
    <p class="intro__marca"><span class="logo logo--grande" aria-hidden="true"><i></i><i></i><i></i><i></i></span></p>
    <p class="intro__h1"><span class="o">Municipios</span> <span class="lt">Colombia</span></p>
    <p class="lede">Transparencia, servicios, seguridad, gestión y control de cada alcaldía, con la fuente oficial de cada dato.</p>
    <div class="intro__cifras">
      <div><strong data-contar="{total}">{formato.numero(total)}</strong>municipios</div>
      <div><strong data-contar="{len(ranking)}">{formato.numero(len(ranking))}</strong>con índice</div>
      <div><strong data-contar="{conteo["verde"]}">{formato.numero(conteo["verde"])}</strong>en verde</div>
    </div>
    <button type="button" class="pill pill--claro intro__explorar" data-intro-salto>Explorar el mapa</button>
  </div>
</div>
"""
    carrusel = "".join(
        tarjeta_carrusel(datos, c, siluetas, i + 1) for i, c in enumerate(ranking[:40])
    )
    filas_rank = "".join(_fila_ranking(datos, c, "") for c in ranking[:20])
    contenido = f"""
{intro}
<section class="hero" data-mapa-pais>
  <div class="hero__texto">
    <h1 class="hero__h1"><span class="lt">¿Tu municipio</span> <span class="o">muestra</span> <span class="lt">sus</span> <span class="acc">cuentas</span><span class="o">?</span></h1>
    <p class="lede">{escape(datos.sitio["descripcion"])}</p>
    <form class="buscador" data-busqueda action="ranking/" role="search">
      <svg class="buscador__ico" aria-hidden="true"><use href="#i-lupa"/></svg>
      <label class="visualmente-oculto" for="buscar-portada">Busca tu municipio</label>
      <input id="buscar-portada" name="q" type="search" placeholder="Busca tu municipio"
        autocomplete="off" role="combobox" aria-expanded="false" aria-controls="buscar-portada-lista">
      <ul id="buscar-portada-lista" class="busqueda__lista" role="listbox" hidden></ul>
    </form>
  </div>
  <div class="hero__mapa" data-mapa>
    <div class="mseg" role="group" aria-label="Qué mostrar en el mapa">
      <span class="mseg__th" aria-hidden="true"></span>{botones_capa}
    </div>
    {mapa_en_linea(dir_mapas / "colombia.svg", colores, "Mapa de Colombia por departamento, coloreado según el índice promedio")}
    <div class="leyenda-card" aria-hidden="true">
      <p class="leyenda-card__tit">Índice municipal · promedio por departamento</p>
      <div class="hist">{histograma}</div>
      <div class="leyenda-card__extremos mono"><span>{_num(min(promedios), 0)}</span><span>peor — mejor</span><span>{_num(max(promedios), 0)}</span></div>
      {leyenda_escala()}
      <p class="leyenda-card__pie f">Fuente: cálculo propio a partir de fuentes oficiales.</p>
    </div>
    <div class="mapa__velo" aria-hidden="true"></div>
  </div>
</section>

<section class="rail revela">
  <div class="rail-h">
    <h2>Elige un municipio</h2>
    <p class="mono">{formato.numero(total)} municipios · los 40 primeros</p>
  </div>
  <div class="rail__filtros">
    <label class="sel">
      <span class="visualmente-oculto">Departamento</span>
      <select data-filtro-dep><option value="">Todos los departamentos</option>{opciones_dep()}</select>
    </label>
    <label class="sel">
      <span class="visualmente-oculto">Grupo de capacidades</span>
      <select data-filtro-grupo><option value="">Todos los grupos</option>{grupos}</select>
    </label>
  </div>
  <div class="rail__track" data-carrusel>
    {carrusel}
  </div>
</section>

<section class="rank-sec revela">
  <h2 class="rank-h"><span class="lt">Quién muestra sus cuentas</span> <span class="o">y da mejores servicios</span></h2>
  <ol class="rk" data-rk>{filas_rank}</ol>
  <p><a class="pill" href="ranking/">Ver el ranking completo <span class="mono">+{max(0, len(ranking) - 20)}</span></a></p>
</section>

<section class="vp revela" id="vecinos-piden" data-vecinos aria-labelledby="vp-t">
  <p class="vp-k"><span class="vp-vivo" aria-hidden="true"></span>En vivo</p>
  <h2 id="vp-t"><span class="lt">Lo que más le piden</span> <span class="o">los vecinos</span></h2>
  <p class="vp-sub">Municipios con más pedidos de datos que no encontramos en su sitio web. Cada vecino cuenta una vez. No mide calidad ni acusa a nadie: muestra qué información quiere ver la gente.</p>
  <label class="vp-filtro"><span>Departamento</span><select data-vp-dep><option value="">Todo el país</option></select></label>
  <div class="vp-tk" data-vp-cinta aria-live="polite" hidden></div>
  <div data-vp-cuerpo><p class="nota">Elige un municipio, mira qué datos no encontramos en su sitio y súmate al pedido. <a href="ranking/">Ver el ranking completo</a>.</p></div>
</section>

<section class="revela bloque-pilares">
  <h2><span class="lt">Qué mide</span> <span class="o">el índice</span></h2>
  <p class="lede">Un número de 0 a 100 con cuatro pilares. Cada municipio se compara con los de su <a href="metodologia/#pares">grupo de capacidades</a> del DNP: un municipio pequeño no se mide contra Medellín.</p>
  <ul class="rejilla">{pilares}</ul>
  <p><a class="pill pill--claro" href="metodologia/">Cómo se calcula, paso a paso</a> <a class="pill" href="ranking/">Ver el ranking completo</a></p>
</section>
<a class="chip-datos chip-datos--fijo mono" href="fuentes/" data-fecha="Datos oficiales · {_fecha_corta(datos.sitio["actualizado"])}">Datos oficiales · actualizado el {_fecha_corta(datos.sitio["actualizado"])}</a>
"""
    return Pagina(
        "",
        datos.sitio["nombre"],
        datos.sitio["descripcion"],
        contenido,
        ("inicio.js", "carrusel.js"),
        "pagina-inicio",
        titulo_seo=f"Municipios Colombia: transparencia y servicios de los {formato.numero(total)} municipios",
        jsonld=tuple(_ld_sitio(datos)),
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
    mensajes = {
        "sitio_no_encontrado": "No se encontró el sitio web oficial.",
        "no_permitido": "El sitio no permite la revisión automática (robots.txt).",
        "error": "No se pudo abrir el menú de transparencia.",
        "menu_no_legible": "El menú de transparencia no se pudo leer de forma automática: no se sabe qué publica.",
    }
    estados = {f["resultado"] for f in filas}
    lee_el_sitio = bool(estados & {"enlace_encontrado", "no_encontrado"})
    problema = (
        next((m for e, m in mensajes.items() if e in estados), None) if not lee_el_sitio else None
    )
    items = []
    for f in filas:
        if f["resultado"] == "enlace_encontrado":
            estado = f'<a href="{escape(f["evidencia"])}" rel="noopener">Enlace encontrado</a>'
        elif f["resultado"] == "fuente_oficial":
            estado = (
                f'<a href="{escape(f["evidencia"])}" rel="noopener">Fuente oficial</a>: '
                f"{escape(f.get('detalle', ''))}"
            )
        elif f["resultado"] == "no_encontrado":
            estado = "No se encontró un enlace en las páginas revisadas"
        else:
            continue
        items.append(
            f"<li><span>{escape(nombres.get(f['criterio'], f['criterio']))}</span> <small>{estado}</small></li>"
        )
    sitio = filas[0]["sitio"]
    origen = (
        f' Sitio revisado: <a href="{escape(sitio)}" rel="noopener">{escape(sitio)}</a>.'
        if sitio
        else ""
    )
    cuerpo = (f'<p class="nota">{problema}</p>' if problema else "") + (
        f'<ul class="revision">{"".join(items)}</ul>' if items else ""
    )
    return (
        '<aside class="revision-auto"><h3>Revisión automática del sitio web '
        "<small>sin verificación humana, no puntúa</small></h3>"
        f"{cuerpo}"
        f'<p class="nota">Un robot buscó estos criterios el {escape(filas[0]["fecha"])} en el menú de transparencia y hasta dos niveles de sus secciones, y los cruzó con fuentes oficiales (SECOP, SIGEP, datos.gov.co). '
        f"Que no halle un enlace no prueba que no se publique, y que haya uno no prueba que el documento esté completo ni al día.{origen}</p></aside>"
    )


TITULOS_CAP = {
    "T": ('<span class="lt">¿Muestra</span> <span class="o">sus cuentas?</span>', "01"),
    "S": ('<span class="lt">De cada 100 hogares,</span> <span class="o">qué llega</span>', "02"),
    "G": ('<span class="lt">Cómo gestiona</span> <span class="o">su presupuesto</span>', "03"),
    "C": ('<span class="o">Qué dice</span> <span class="lt">el control</span>', "04"),
}
# Etiqueta corta de cada pilar, para los anillos de la portada de la ficha.
CORTOS_PILAR = {"T": "Transp.", "S": "Servicios", "G": "Gestión", "C": "Control"}


def _cap_pilar(datos: DatosSitio, codigo: str, p) -> str:
    """Un capítulo de la historia por pilar: medidor, descripción y componentes."""
    fila = datos.indice[codigo]
    info = fila.get("pilares", {}).get(p.id, {})
    titulo, numero = TITULOS_CAP.get(p.id, (escape(p.nombre), "00"))
    filas = []
    for c in p.componentes:
        valor, periodo, fuentes = _valor_componente(datos, fila, c.id, c.si_falta)
        comp = fila.get("componentes", {}).get(c.id, {}).get("puntaje")
        filas.append(
            '<li class="comp">'
            f'<p class="comp__nombre">{escape(c.nombre)}</p>'
            f'<p class="comp__valor">{valor}</p>'
            f'<p class="comp__pie mono">{periodo} · {fuentes}</p>'
            f"{bar2(comp, etiqueta=c.nombre)}</li>"
        )
    extra = bloque_revision_automatica(datos, codigo) if p.id == "T" else ""
    return (
        f'<section class="cap cap--pilar" data-capitulo="{escape(p.nombre)}">'
        f'<p class="ojo mono"><span class="acc">{numero}</span> {escape(p.nombre)}</p>'
        f'<h2 class="h">{titulo}</h2>'
        '<div class="cap__fila">'
        f"{medidor(info.get('puntaje'), p.nombre)}"
        f'<p class="lede">{escape(p.descripcion)}</p></div>'
        f'<ul class="comp-grid">{"".join(filas)}</ul>{extra}</section>'
    )


def _cap_contexto(datos: DatosSitio, codigo: str) -> str:
    fila = datos.indice[codigo]
    gasto = _dato(fila, "gasto_por_habitante")
    if gasto is not None:
        cifra = f'<p class="big money">{formato.segun_unidad(gasto["valor"], "pesos")}</p>'
        pie = (
            f'<p class="mono">{escape(formato.periodo(gasto["periodo"]))} · '
            f"{enlaces_fuente(datos, gasto['fuentes'])}</p>"
        )
    else:
        cifra = sin_dato("gasto por habitante", "se buscó en CUIPO (Contraloría)")
        pie = ""
    kpis = []
    for ind in datos.config.contexto:
        if ind == "gasto_por_habitante":
            continue
        dato, ficha_ind = _dato(fila, ind), datos.indicadores.get(ind)
        if dato is None or ficha_ind is None:
            continue
        kpis.append(
            kpi(
                ficha_ind.etiqueta,
                escape(formato.segun_unidad(dato["valor"], ficha_ind.unidad)),
                f'<span class="mono">{escape(formato.periodo(dato["periodo"]))}</span> · '
                f"{enlaces_fuente(datos, dato['fuentes'])}",
            )
        )
    return (
        '<section class="cap cap--contexto" data-capitulo="Contexto">'
        '<p class="ojo mono"><span class="acc">05</span> Contexto · no puntúa</p>'
        '<h2 class="h"><span class="lt">Gastó por vecino</span> <span class="q-info">(contexto)</span></h2>'
        f"{cifra}{pie}"
        f'<div class="kpi-grid">{"".join(kpis) or "<p>Sin datos de contexto.</p>"}</div></section>'
    )


def _cap_resumen(datos: DatosSitio, codigo: str) -> str:
    señales = _señales(datos, codigo)
    rojos = sum(1 for c, _, _ in señales if c == "rojo")
    amarillos = sum(1 for c, _, _ in señales if c == "amarillo")
    if rojos:
        titulo = f'Hay <span class="o">{rojos} señal{"es" if rojos > 1 else ""}</span> para mirar de cerca'
    elif amarillos:
        titulo = f'Hay <span class="o">{amarillos} aspecto{"s" if amarillos > 1 else ""}</span> para mejorar'
    else:
        titulo = '<span class="o">Buenos resultados</span> frente a sus pares'
    filas = "".join(
        f'<li class="veredicto__fila"><span class="chip__punto chip__punto--{("info" if c == "info" else c)}"></span>'
        f'<span class="veredicto__texto">{escape(t)}</span>'
        f'<span class="veredicto__valor">{escape(v)}</span></li>'
        for c, t, v in señales
    )
    return (
        '<section class="cap cap--resumen" data-capitulo="Resumen">'
        '<p class="ojo mono"><span class="acc">06</span> En resumen</p>'
        f'<h2 class="h">{titulo}</h2>'
        f'<ul class="veredicto">{filas}</ul>'
        '<p class="lede sm">Lo que pesa es la transparencia y los servicios; el gasto por habitante es '
        "contexto: no es bueno ni malo por sí solo.</p></section>"
    )


def _titulo_ficha(datos: DatosSitio, codigo: str) -> str:
    """Título de la pestaña y de los buscadores: nombre, índice y puesto (hasta ~70 caracteres)."""
    m, f = datos.municipios[codigo], datos.indice[codigo]
    nombre = datos.sitio["nombre"]
    if f.get("indice") is None:
        return f"{m.nombre} ({m.departamento}): transparencia, servicios y gestión | {nombre}"
    p = f["puesto"]
    completo = (
        f"{m.nombre} ({m.departamento}): índice {_num(f['indice'])}/100, "
        f"puesto {p['nacional']} de {formato.numero(p['nacional_de'])} | {nombre}"
    )
    if len(completo) <= 72:
        return completo
    # Los buscadores cortan hacia los 60-70 caracteres: se quita primero el puesto, luego la marca.
    medio = f"{m.nombre} ({m.departamento}): índice {_num(f['indice'])}/100 | {nombre}"
    return (
        medio
        if len(medio) <= 72
        else f"{m.nombre} ({m.departamento}): índice {_num(f['indice'])}/100"
    )


def ficha(datos: DatosSitio, codigo: str, dir_mapas: Path | None = None) -> Pagina:
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
            f'<section class="tarjeta" id="pilar-{p.id}">'
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

    reportar = url_reporte(datos, codigo)
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
    foto = foto_img(
        datos,
        codigo,
        raiz,
        primera=True,
        tamanos="100vw",
        alt=f"Vista de {m.nombre}, {m.departamento}",
    )
    fondo = foto or (
        Siluetas(dir_mapas).de(m.departamento_slug, codigo) if dir_mapas is not None else None
    )
    capitulos = "".join(_cap_pilar(datos, codigo, p) for p in datos.config.pilares)
    capitulos += _cap_contexto(datos, codigo) + _cap_resumen(datos, codigo)
    anillos = "".join(
        anillo(
            datos.valor(codigo, p.id),
            color_puntaje(datos.valor(codigo, p.id)),
            CORTOS_PILAR.get(p.id, p.nombre),
        )
        for p in datos.config.pilares
    )
    largo = "corto" if len(m.nombre) <= 12 else "medio" if len(m.nombre) <= 18 else "largo"
    anexo = (
        f'<h3>Los cuatro pilares</h3><ul class="pilares">{resumen_pilares}</ul>'
        f"{''.join(secciones)}"
        "<h3>Contexto <small>no puntúa</small></h3>"
        f'<dl class="contexto">{"".join(contexto) or "<p>Sin datos de contexto.</p>"}</dl>'
    )
    contenido = f"""
{miga(raiz, [("", "Inicio"), (f"d/{m.departamento_slug}/", m.departamento), ("", m.nombre)])}
<article class="ficha" data-codigo="{codigo}" data-slug="{m.slug}" data-nombre="{escape(m.nombre)}"
  data-indice="{"" if fila.get("indice") is None else fila["indice"]}" data-semaforo="{fila.get("semaforo") or ""}"
  data-reportar="{escape(reportar)}"{f' data-foto="{raiz}assets/fotos/{codigo}-1080.webp"' if foto else ""}>
<header class="ficha__heroe heroe{" sin-foto" if not foto else ""}" data-capitulo="Portada">
  <div class="heroe__fondo{"" if foto else " heroe__fondo--silueta"}" aria-hidden="true">{fondo or ""}</div>
  <div class="st-shade" aria-hidden="true"></div>
  <div class="heroe__cuerpo">
    <p class="etiqueta mono">{escape(m.departamento)} · {escape(grupo)}</p>
    <h1 class="big ficha__nombre ficha__nombre--{largo}">{escape(m.nombre)}</h1>
    <p class="lede">{linea_portada(datos, fila)}</p>
    {medidor(fila.get("indice"), "Índice municipal", fila.get("semaforo"))}
    <div class="anillos">{anillos}</div>
    {puesto_html}
    <p class="ficha__resumen">{_resumen(m, fila)}</p>
    {credito_foto(datos, codigo)}
    <div class="acciones">
      <button type="button" class="pill pill--claro" data-historia hidden>Empezar →</button>
      <a class="pill" href="{raiz}comparar/?a={codigo}">Comparar</a>
      <button type="button" class="pill" data-compartir hidden>Compartir</button>
      <a class="pill" href="{raiz}d/{m.departamento_slug}/">Ver en el mapa</a>
      <a class="pill" href="{escape(reportar)}" rel="noopener">Reportar</a>
    </div>
  </div>
</header>

{capitulos}

<section class="tarjeta mapa-seccion">
  <h2>{escape(m.nombre)} en el mapa de {escape(m.departamento)}</h2>
  <div class="mapa mapa--ficha" data-mapa="{m.departamento_slug}" data-resaltar="{codigo}">
    <p class="nota"><a href="{raiz}d/{m.departamento_slug}/">Ver el mapa y el ranking de {escape(m.departamento)}</a></p>
  </div>
</section>

<section class="anexo">
  <details><summary class="pill">Ver los datos técnicos y las fuentes</summary>{anexo}</details>
</section>

<section class="tarjeta reportes" id="reportar">
  <h2>¿Ves algo mal o falta un dato?</h2>
  <p class="nota">Tu aviso se publica con su fecha en el registro de correcciones. Si una alcaldía quiere responder, este es su derecho de réplica.</p>
  {formulario("reporte", datos, titulo="Reportar un error en un dato", ayuda="Si el sitio no tiene servidor, se abre un issue en GitHub con tu mensaje.", municipio=f"{m.nombre}, {m.departamento} ({codigo})")}
  {formulario("pedido", datos, titulo="Pedir un dato que no encontramos publicado", ayuda="Nos ayuda a completar la ficha y a ejercer el derecho de petición.", municipio=f"{m.nombre}, {m.departamento} ({codigo})", asunto=True)}
</section>
</article>
<footer class="nota-final contenedor">
  <p>Cada cifra tiene su fuente oficial. Los puntajes «entre pares» son el percentil del municipio dentro de su grupo de capacidades del DNP (0 = el peor del grupo, 100 = el mejor). <a href="{raiz}metodologia/">Ver la metodología</a>.</p>
</footer>
"""
    descripcion = (
        f"{m.nombre} ({m.departamento}): índice municipal {_num(fila.get('indice'))}/100. "
        "Transparencia, servicios, seguridad, gestión y control, con fuentes oficiales."
    )
    return Pagina(
        ruta,
        f"{m.nombre}, {m.departamento}",
        descripcion,
        contenido,
        ("ficha.js", "formularios.js"),
        "pagina-ficha",
        f"assets/fotos/{codigo}-1080.webp" if codigo in datos.fotos else "",
        titulo_seo=_titulo_ficha(datos, codigo),
        jsonld=(
            _ld_migas(
                datos,
                [
                    ("", "Inicio"),
                    (f"d/{m.departamento_slug}/", m.departamento),
                    (ruta, m.nombre),
                ],
            ),
            {
                "@context": "https://schema.org",
                "@type": "AdministrativeArea",
                "name": m.nombre,
                "containedInPlace": {"@type": "AdministrativeArea", "name": m.departamento},
                "url": datos.sitio["url_base"] + ruta,
            },
        ),
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
        titulo_seo=f"Municipios de {nombre}: índice de transparencia y servicios | {datos.sitio['nombre']}",
        jsonld=(_ld_migas(datos, [("", "Inicio"), (f"d/{slug}/", nombre)]),),
    )


# --- ranking --------------------------------------------------------------------------------
def _fila_pagina(datos: DatosSitio, codigo: str, raiz: str) -> str:
    """Fila del ranking completo: lleva los cinco puntajes para ordenar y filtrar sin servidor."""
    m, f = datos.municipios[codigo], datos.indice[codigo]
    iniciales = "".join(p[0] for p in m.nombre.split()[:2]).upper()
    valores = {c: datos.valor(codigo, c) for c in ("indice", "T", "S", "G", "C")}
    attrs = "".join(f' data-{c.lower()}="{v:.1f}"' for c, v in valores.items() if v is not None)
    valor = valores["indice"]
    clase = color_puntaje(valor) or "sin"
    return (
        f'<li class="rk__fila" data-dep="{m.departamento_codigo}" data-grupo="{escape(f.get("grupo") or "")}"'
        f' data-semaforo="{f.get("semaforo") or ""}"{attrs}>'
        f'<a class="rk__enlace" href="{raiz}m/{m.slug}/" data-historia="{codigo}">'
        f'<span class="rk__puesto mono">{f["puesto"]["nacional"]:02d}</span>'
        f'<span class="rk__cara" aria-hidden="true">{escape(iniciales)}</span>'
        f'<span class="rk__texto"><b>{escape(m.nombre)}</b>'
        f"<small>{escape(m.departamento)} · {escape(NOMBRES_GRUPOS.get(f.get('grupo') or '', 'sin grupo'))}</small></span>"
        f'<span class="rk__valor">{_num(valor, 0)}</span>'
        "</a>"
        '<span class="rk__barra"><span class="bar2"><i class="bar2__f bar2__f--'
        f'{clase}" style="width:{max(valor or 0, 1):.1f}%"></i></span></span></li>'
    )


def ranking(datos: DatosSitio) -> Pagina:
    codigos = datos.ranking()
    raiz = "../"
    deps = "".join(
        f'<option value="{cod}">{escape(nombre)}</option>'
        for cod, (nombre, _) in sorted(DEPARTAMENTOS.items(), key=lambda kv: kv[1][0])
    )
    grupos = "".join(f'<option value="{g}">{escape(n)}</option>' for g, n in NOMBRES_GRUPOS.items())
    tabs = "".join(
        f'<button type="button" class="pill" data-campo="{c}" aria-pressed="{"true" if c == "indice" else "false"}">{t}</button>'
        for c, t in CAPAS
    )
    # Histograma del índice: 20 tramos de 5 puntos (altura = municipios en el tramo).
    cuentas = [0] * 20
    for c in codigos:
        cuentas[min(19, int(datos.indice[c]["indice"] // 5))] += 1
    mayor = max(cuentas) or 1
    hist = "".join(
        f'<i class="hist__b hist__b--{tramo(5 * i + 2.5)}" style="height:{max(4, 100 * n / mayor):.0f}%"'
        f' title="{5 * i} a {5 * i + 5}: {n} municipios"></i>'
        for i, n in enumerate(cuentas)
    )
    filas = "".join(_fila_pagina(datos, c, raiz) for c in codigos)
    contenido = f"""
{miga(raiz, [("", "Inicio"), ("", "Ranking")])}
<section class="rank-pagina">
  <h1 class="rank-h"><span class="lt">Quién muestra sus cuentas</span> <span class="o">y da mejores servicios</span></h1>
  <p class="entradilla">{formato.numero(len(codigos))} municipios ordenados por el índice municipal (v{escape(datos.config.version)}). Transparencia, servicios y seguridad, gestión y control, comparados con municipios de capacidades parecidas.</p>
  <div class="rk-controles" data-rk-controles hidden>
    <div class="rk-tabs" role="group" aria-label="Ordenar por">{tabs}</div>
    <div class="rk-filtros">
      <label class="visualmente-oculto" for="rk-texto">Buscar por nombre</label>
      <input id="rk-texto" class="rk-buscar" type="search" placeholder="Busca por nombre" autocomplete="off" data-rk-texto>
      <label class="sel"><span class="visualmente-oculto">Departamento</span><select data-rk-dep><option value="">Todos los departamentos</option>{deps}</select></label>
      <label class="sel"><span class="visualmente-oculto">Grupo de capacidades</span><select data-rk-grupo><option value="">Todos los grupos</option>{grupos}</select></label>
      <div class="rk-sem" role="group" aria-label="Semáforo">
        <button type="button" class="pill" data-sem="" aria-pressed="true">Todos</button>
        <button type="button" class="pill" data-sem="verde" aria-pressed="false">Verde</button>
        <button type="button" class="pill" data-sem="amarillo" aria-pressed="false">Amarillo</button>
        <button type="button" class="pill" data-sem="rojo" aria-pressed="false">Rojo</button>
      </div>
    </div>
  </div>
  <div class="rk-resumen">
    <div class="hist" aria-hidden="true">{hist}</div>
    <p class="rk-leyenda mono"><span>peor</span><i class="rk-grad" aria-hidden="true"></i><span>mejor</span></p>
    <p class="mono rk-conteo" aria-live="polite" data-rk-conteo>{formato.numero(len(codigos))} municipios</p>
  </div>
  <ol class="rk rk--pagina" data-rk>{filas}</ol>
  <button type="button" class="mas" data-rk-mas hidden>Ver más <small class="mono"></small></button>
</section>
"""
    return Pagina(
        "ranking/",
        "Ranking de municipios",
        "Ranking de los municipios de Colombia según el índice municipal, con filtros por departamento y grupo.",
        contenido,
        ("ranking.js",),
        "pagina-ranking",
    )


# --- comparar -------------------------------------------------------------------------------
def comparar(datos: DatosSitio) -> Pagina:
    raiz = "../"
    contenido = f"""
{miga(raiz, [("", "Inicio"), ("", "Comparar")])}
<div id="cmp">
  <h1 class="visualmente-oculto">Comparar municipios</h1>
  <a class="cmp-cerrar pill pill--icono" href="{raiz}" aria-label="Cerrar y volver al inicio">&times;</a>
  <div class="cmp-top">
    <div class="cmp-lado" data-lado="a">
      <div class="cmp-fondo" data-fondo="a" aria-hidden="true"></div>
      <div class="cmp-info">
        <div class="busqueda cmp-buscar" data-busqueda data-busqueda-campo="a">
          <label class="visualmente-oculto" for="cmp-a">Municipio A</label>
          <input id="cmp-a" type="search" placeholder="Elige un municipio" autocomplete="off"
            role="combobox" aria-expanded="false" aria-controls="cmp-a-lista">
          <ul id="cmp-a-lista" class="busqueda__lista" role="listbox" hidden></ul>
        </div>
        <p class="cmp-dep mono" data-dep="a"></p>
      </div>
    </div>
    <div class="cmp-vs" aria-hidden="true">VS</div>
    <div class="cmp-lado" data-lado="b">
      <div class="cmp-fondo" data-fondo="b" aria-hidden="true"></div>
      <div class="cmp-info">
        <div class="busqueda cmp-buscar" data-busqueda data-busqueda-campo="b">
          <label class="visualmente-oculto" for="cmp-b">Municipio B</label>
          <input id="cmp-b" type="search" placeholder="Elige otro municipio" autocomplete="off"
            role="combobox" aria-expanded="false" aria-controls="cmp-b-lista">
          <ul id="cmp-b-lista" class="busqueda__lista" role="listbox" hidden></ul>
        </div>
        <p class="cmp-dep mono" data-dep="b"></p>
      </div>
    </div>
  </div>
  <div class="cmp-body" data-cmp-resultado aria-live="polite">
    <p class="nota">Elige los dos municipios para ver el duelo, rubro por rubro.</p>
  </div>
</div>
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
  <p>Este sitio no usa cookies, no usa herramientas de analítica ni publicidad y no carga recursos de terceros, salvo el servicio que cuenta los pedidos de datos cuando está activo (corre en Cloudflare Workers: al ver «Lo que más le piden los vecinos» o usar «Súmate al pedido», tu navegador lo consulta y Cloudflare ve tu IP). No recopila datos personales. Si usas «Súmate al pedido» (solo cuando el sitio tiene servidor), se guarda el municipio, el dato y una huella cifrada de tu conexión (no la IP) para que cuentes una sola vez; se borra al año. Si escribes por correo o abres un issue, esos datos los gestiona tu proveedor de correo o GitHub.</p>
</section>
<section>
  <h2>Código y datos abiertos</h2>
  <p>El código está en <a href="{escape(s["repositorio"])}">GitHub</a> bajo licencia MIT. Los datos propios (relevamientos, cálculos e índice) se publican bajo CC BY 4.0. Los datos de terceros conservan la licencia de su fuente.</p>
  <p>¿Quieres ayudar? Lee la <a href="{escape(s["repositorio"])}/blob/main/CONTRIBUTING.md">guía para contribuir</a>.</p>
</section>
<section id="contacto">
  <h2>Escríbenos</h2>
  {formulario("contacto", datos, titulo="Enviar un mensaje", ayuda="Si el sitio no tiene servidor, se abre tu correo con el mensaje listo.", asunto=True)}
</section>
"""
    return Pagina(
        "acerca/",
        "Acerca y privacidad",
        "Qué es el proyecto, cómo corregir un dato, privacidad y licencias.",
        contenido,
        ("formularios.js",),
        "pagina-texto",
    )


def no_encontrada(datos: DatosSitio) -> Pagina:
    contenido = """
<header class="encabezado">
  <h1>No encontramos esa página</h1>
  <p class="entradilla">Puede que el enlace esté mal escrito o que la página haya cambiado de lugar. Busca tu municipio arriba o vuelve al <a href="./">inicio</a>.</p>
</header>
"""
    return Pagina(
        "404.html",
        "Página no encontrada",
        "Página no encontrada.",
        contenido,
        clase="pagina-texto",
        indexar=False,
    )
