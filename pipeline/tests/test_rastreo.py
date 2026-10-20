from municipios.relevamiento.criterios import es_archivo, raiz_del_sitio, secciones_a_abrir
from municipios.relevamiento.rastreo import rastrear
from municipios.relevamiento.transparencia import filas_del_rastro

SITIO = "https://www.sopo-cundinamarca.gov.co/"
MENU = "https://www.sopo-cundinamarca.gov.co/transparencia"


def _url(ruta: str) -> str:
    return f"{SITIO}{ruta}"


# Un sitio ficticio: el menú solo tiene secciones; los criterios están un nivel más abajo.
PAGINAS = {
    _url("planeacion"): [
        ("Presupuesto general 2026", _url("p.pdf")),
        ("Plan anual de adquisiciones", _url("paa")),
        ("Plan de desarrollo 2024-2027", _url("pd")),
        ("Banco de proyectos", _url("planeacion/proyectos")),
    ],
    _url("planeacion/proyectos"): [("Informe de empalme", _url("empalme.pdf"))],
    _url("entidad"): [
        ("Directorio de servidores públicos", _url("dir")),
        ("Datos abiertos", _url("planeacion/proyectos")),
    ],
}
MENU_ENLACES = [
    ("Planeación", _url("planeacion")),
    ("Información de la entidad", _url("entidad")),
    ("Noticias", _url("noticias")),
    ("Facebook", "https://www.facebook.com/alcaldiasopo"),
    ("Manual", _url("manual.pdf")),
]


def _leer(registro: list[str]):
    def leer(url: str):
        registro.append(url)
        return PAGINAS.get(url)

    return leer


def test_rastrear_halla_criterios_en_secciones_del_menu():
    rastro = rastrear(MENU_ENLACES, MENU, SITIO, _leer([]))
    assert rastro.encontrados["presupuesto"].nivel == 1
    assert rastro.encontrados["presupuesto"].pagina == _url("planeacion")
    assert rastro.encontrados["plan_desarrollo"].evidencia == _url("pd")
    assert rastro.encontrados["directorio"].evidencia == _url("dir")
    assert rastro.encontrados["datos_abiertos"].nivel == 1
    assert "pqrsd" not in rastro.encontrados  # no hallado: no se inventa
    # El menú, las dos secciones y «planeacion/proyectos» (nivel 2); /paa no está en el sitio.
    assert (rastro.paginas_leidas, rastro.paginas_omitidas) == (4, 1)


def test_rastrear_baja_hasta_el_segundo_nivel():
    paginas = {
        _url("planeacion"): [("Gestión por procesos", _url("gestion"))],
        _url("entidad"): [("Contratación", _url("contratos"))],
        _url("contratos"): [("Plan anual de adquisiciones", _url("paa"))],
    }
    rastro = rastrear(MENU_ENLACES, MENU, SITIO, paginas.get)
    # «Contratación» se abre en el nivel 1 y su enlace ya cumple el criterio de contratación.
    assert rastro.encontrados["contratacion"].nivel == 1
    # El plan de adquisiciones está un nivel más abajo (nivel 2).
    assert rastro.encontrados["plan_adquisiciones"].nivel == 2
    assert rastro.encontrados["plan_adquisiciones"].pagina == _url("contratos")


def test_rastrear_no_sale_del_sitio_ni_abre_archivos_ni_repite_paginas():
    leidas: list[str] = []
    rastrear(MENU_ENLACES, MENU, SITIO, _leer(leidas))
    assert all(raiz_del_sitio(u) == "sopo-cundinamarca.gov.co" for u in leidas)
    assert not any(es_archivo(u) for u in leidas)
    assert len(leidas) == len(set(leidas))


def test_rastrear_respeta_el_tope_de_paginas_y_la_profundidad():
    leidas: list[str] = []
    rastrear(MENU_ENLACES, MENU, SITIO, _leer(leidas), max_paginas=1)
    assert len(leidas) == 1
    leidas = []
    rastrear(MENU_ENLACES, MENU, SITIO, _leer(leidas), profundidad=0)
    assert leidas == []


def test_rastrear_cuenta_las_paginas_omitidas():
    rastro = rastrear(MENU_ENLACES, MENU, SITIO, lambda url: None)
    assert rastro.paginas_leidas == 1
    assert rastro.paginas_omitidas == 2
    assert rastro.encontrados == {}


def test_rastrear_se_detiene_cuando_ya_no_falta_nada():
    todos = [
        (texto, _url(f"c{i}"))
        for i, texto in enumerate(
            [
                "Presupuesto general",
                "Ejecución presupuestal",
                "Plan de desarrollo",
                "Plan anual de adquisiciones",
                "SECOP",
                "Directorio de servidores",
                "Control interno",
                "PQRSD",
                "Datos abiertos",
                "Declaración de bienes",
            ]
        )
    ] + MENU_ENLACES
    leidas: list[str] = []
    rastro = rastrear(todos, MENU, SITIO, _leer(leidas))
    assert leidas == []
    assert all(h.nivel == 0 for h in rastro.encontrados.values())


def test_secciones_a_abrir_prioriza_las_que_aportan_mas_faltantes():
    enlaces = [
        ("Datos abiertos", _url("da")),
        ("Planeación", _url("pl")),
        ("Contratación", _url("co")),
    ]
    faltan = {"presupuesto", "ejecucion", "plan_desarrollo", "contratacion"}
    assert secciones_a_abrir(enlaces, SITIO, faltan, set(), 5) == [_url("pl"), _url("co")]
    assert secciones_a_abrir(enlaces, SITIO, faltan, {_url("pl")}, 5) == [_url("co")]
    assert secciones_a_abrir(enlaces, SITIO, faltan, set(), 1) == [_url("pl")]
    assert secciones_a_abrir(enlaces, SITIO, set(), set(), 5) == []


def test_raiz_del_sitio_acepta_subdominios_de_la_misma_alcaldia():
    assert raiz_del_sitio("https://transparencia.sopo-cundinamarca.gov.co/x") == (
        "sopo-cundinamarca.gov.co"
    )
    assert raiz_del_sitio("https://www.sopo-cundinamarca.gov.co/") == "sopo-cundinamarca.gov.co"
    assert raiz_del_sitio("https://www.facebook.com/x") == "facebook.com"


def test_filas_del_rastro_explican_donde_se_hallo_y_donde_se_busco():
    rastro = rastrear(MENU_ENLACES, MENU, SITIO, _leer([]))
    base = {"divipola": "25758", "municipio": "Sopó", "fecha": "2026-10-19", "metodo": "automatico"}
    filas = {f["criterio"]: f for f in filas_del_rastro(base, SITIO, MENU, rastro)}
    assert len(filas) == 10
    assert filas["presupuesto"]["resultado"] == "enlace_encontrado"
    assert filas["presupuesto"]["detalle"].startswith("Nivel 1:")
    assert filas["pqrsd"]["resultado"] == "no_encontrado"
    assert "Se leyeron 4 páginas del sitio, 1 omitidas" in filas["pqrsd"]["detalle"]
    assert filas["pqrsd"]["evidencia"] == ""
