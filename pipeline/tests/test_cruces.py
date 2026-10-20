from municipios.relevamiento.cruces import (
    aplicar,
    combinar,
    cruces_catalogo,
    cruces_secop,
    cruces_sigep,
)


def _fila(criterio: str, resultado: str, evidencia: str = "") -> dict[str, str]:
    return {
        "divipola": "25758",
        "municipio": "Sopó",
        "sitio": "https://www.sopo.gov.co/",
        "pagina_transparencia": "https://www.sopo.gov.co/transparencia",
        "fecha": "2026-10-19",
        "criterio": criterio,
        "resultado": resultado,
        "evidencia": evidencia,
        "metodo": "automatico",
        "detalle": "",
    }


def _contratos(codigo: str, valor: int, periodo: str = "2026") -> dict:
    return {"divipola": codigo, "indicador": "contratos_numero", "valor": valor, "periodo": periodo}


def test_secop_exige_contratos_recientes():
    obs = [
        _contratos("25758", 300, "2025"),
        _contratos("25758", 120, "2026"),
        _contratos("05001", 900, "2020"),
        _contratos("05002", 0),
        {"divipola": "05003", "indicador": "contratos_valor", "valor": 5, "periodo": "2026"},
    ]
    r = cruces_secop(obs, 2026)
    assert set(r) == {"25758"}  # 2020 es viejo; 0 contratos y otros indicadores no cuentan
    e = r["25758"]["contratacion"]
    assert "120 contratos firmados en 2026" in e.detalle
    assert e.metodo == "cruce_secop"
    assert e.url.startswith("https://www.datos.gov.co/")


def test_sigep_solo_cuenta_alcaldias_con_servidores():
    filas = [
        {
            "nombre_de_la_entidad": "ALCALDIA DE SOPO",
            "nit": "899999468",
            "a_o": "2026",
            "mes": "6",
            "genero_hombre": "40",
            "genero_mujer": "60",
            "genero_no_binario": "0",
            "salario_mensual_promedio": "2016593",
        },
        {  # empresa del municipio: no es la alcaldía
            "nombre_de_la_entidad": "EMPRESA DE SERVICIOS PUBLICOS DE SOPO",
            "nit": "800111222",
            "c_digo_divipola_municipio": "25758",
            "genero_hombre": "5",
        },
        {  # sin servidores
            "nombre_de_la_entidad": "ALCALDIA DE X",
            "nit": "800000001",
            "genero_hombre": "0",
        },
    ]
    r = cruces_sigep(filas, {"899999468": "25758", "800000001": "05001"})
    assert set(r) == {"25758"}
    assert "100 servidores" in r["25758"]["directorio"].detalle
    assert "$2.016.593" in r["25758"]["directorio"].detalle


def test_sigep_completa_el_codigo_con_ceros():
    r = cruces_sigep(
        [
            {
                "nombre_de_la_entidad": "ALCALDIA DE MEDELLIN",
                "c_digo_divipola_municipio": "5001",
                "genero_mujer": "10",
            }
        ],
        {},
    )
    assert "05001" in r


def _conjunto(entidad: str, nombre: str, id_: str, divipola: str = "25758") -> dict[str, str]:
    return {
        "divipola": divipola,
        "entidad": entidad,
        "nombre": nombre,
        "url": f"https://www.datos.gov.co/d/{id_}",
    }


def test_catalogo_cuenta_solo_lo_que_publica_la_alcaldia():
    conjuntos = [
        _conjunto(
            "Alcaldía de Sopó, Cundinamarca", "Ejecución presupuestal de gastos", "aaaa-1111"
        ),
        _conjunto("Alcaldía de Sopó, Cundinamarca", "Eventos culturales", "bbbb-2222"),
        _conjunto("Gobernación de Cundinamarca", "Presupuesto departamental", "cccc-3333"),
        _conjunto("Alcaldía Local de Usaquén", "Directorio de servidores", "dddd-4444", "11001"),
    ]
    r = cruces_catalogo(conjuntos)
    assert set(r) == {"25758"}
    assert r["25758"]["datos_abiertos"].url == "https://www.datos.gov.co/d/aaaa-1111"
    assert "2 conjunto(s)" in r["25758"]["datos_abiertos"].detalle
    assert r["25758"]["ejecucion"].url == "https://www.datos.gov.co/d/aaaa-1111"
    assert "presupuesto" not in r["25758"]  # el de la gobernación no cuenta


def test_combinar_da_prioridad_a_la_primera_fuente():
    secop = cruces_secop([_contratos("1", 3)], 2026)
    catalogo = cruces_catalogo([_conjunto("Alcaldía de X", "Contratación 2025", "eeee-5555", "1")])
    r = combinar(secop, catalogo)
    assert r["1"]["contratacion"].metodo == "cruce_secop"
    assert r["1"]["datos_abiertos"].metodo == "cruce_datos_gov_co"


def test_aplicar_no_toca_lo_que_el_sitio_si_mostro():
    cruces = cruces_secop([_contratos("25758", 9)], 2026)["25758"]
    filas = [
        _fila("contratacion", "enlace_encontrado", "https://www.sopo.gov.co/secop"),
        _fila("presupuesto", "no_encontrado"),
    ]
    assert aplicar(filas, cruces) == filas  # contratación ya estaba en el sitio
    filas = [_fila("contratacion", "no_encontrado"), _fila("presupuesto", "no_encontrado")]
    r = aplicar(filas, cruces)
    assert r[0]["resultado"] == "fuente_oficial"
    assert r[0]["evidencia"].startswith("https://www.datos.gov.co/")
    assert r[0]["metodo"] == "cruce_secop"
    assert "9 contratos" in r[0]["detalle"]
    assert r[1]["resultado"] == "no_encontrado"  # sin evidencia, sigue igual (y no es «no publica»)
    assert filas[0]["resultado"] == "no_encontrado"  # no muta la entrada


def test_aplicar_cubre_tambien_el_menu_no_legible():
    cruces = cruces_secop([_contratos("25758", 9)], 2026)["25758"]
    filas = [_fila("contratacion", "menu_no_legible"), _fila("pqrsd", "menu_no_legible")]
    assert [f["resultado"] for f in aplicar(filas, cruces)] == ["fuente_oficial", "menu_no_legible"]
