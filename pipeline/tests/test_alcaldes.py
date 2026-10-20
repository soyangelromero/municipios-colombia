from datetime import date
from types import SimpleNamespace

from municipios.exportar.paginas import linea_alcalde
from municipios.fuentes.alcaldes import elegir, titulo

ENTIDADES = [
    {"nombre_de_la_entidad": "ALCALDIA DE SOPO", "nit": "899999468"},
    {"nombre_de_la_entidad": "ALCALDIA DE APARTADO ANTIOQUIA", "nit": "890907215"},
    {"nombre_de_la_entidad": "ALCALDIA DE APARTADO CORDOBA", "nit": "800000001"},
    {"nombre_de_la_entidad": "EMPRESA SIN NIT EN EL MAPA", "nit": "111111111"},
]
NITS = {"899999468": "25758", "890907215": "05045", "800000001": "23182"}


def _p(nombre, entidad, desde, hasta="", cargo="ALCALDE"):
    p = {
        "nombre_pep": nombre,
        "denominacion_cargo": cargo,
        "nombre_entidad": entidad,
        "fecha_vinculacion": desde,
    }
    if hasta:
        p["fecha_desvinculacion"] = hasta
    return p


def test_titulo_pasa_a_mayusculas_iniciales_y_deja_las_particulas():
    assert titulo("MARIA DE LOS ANGELES PEREZ") == "Maria de los Angeles Perez"
    assert titulo("JUAN CARLOS ORTIZ-LOPEZ") == "Juan Carlos Ortiz-Lopez"


def test_elige_al_unico_alcalde_vigente_del_periodo():
    personas = [
        _p("ALBA MUÑOZ", "ALCALDIA DE SOPO", "1/01/2024"),
        _p("ANTIGUO ALCALDE", "ALCALDIA DE SOPO", "1/01/2020", "31/12/2023"),
    ]
    elegidos, notas = elegir(personas, ENTIDADES, NITS)
    assert elegidos["25758"]["nombre"] == "Alba Muñoz"
    assert elegidos["25758"]["desde"] == "2024-01-01"
    assert notas == {"con_alcalde": 1, "dudosos": 0}


def test_no_muestra_a_nadie_si_hay_dos_vigentes_o_es_de_antes_del_periodo():
    personas = [
        _p("PERSONA UNO", "ALCALDIA DE SOPO", "1/01/2024"),
        _p("PERSONA DOS", "ALCALDIA DE SOPO", "5/03/2025"),  # ¿encargado? no se sabe
        _p("ALCALDE VIEJO", "ALCALDIA DE APARTADO ANTIOQUIA", "1/01/2020"),  # sin cerrar
    ]
    elegidos, notas = elegir(personas, ENTIDADES, NITS)
    assert elegidos == {}
    assert notas["dudosos"] == 1


def test_la_misma_persona_posesionada_dos_veces_cuenta_una_vez_con_la_primera_fecha():
    personas = [
        _p("ASTRID ARROYO", "ALCALDIA DE SOPO", "6/05/2025"),
        _p("ASTRID ARROYO", "ALCALDIA DE SOPO", "7/02/2025"),
    ]
    elegidos, _ = elegir(personas, ENTIDADES, NITS)
    assert elegidos["25758"]["desde"] == "2025-02-07"


def test_municipios_con_el_mismo_nombre_no_se_confunden_y_otros_cargos_no_cuentan():
    personas = [
        _p("DEL CORDOBA", "ALCALDIA DE APARTADO CORDOBA", "1/01/2024"),
        _p("DE ANTIOQUIA", "ALCALDIA DE APARTADO ANTIOQUIA", "1/01/2024"),
        _p("SECRETARIO", "ALCALDIA DE SOPO", "1/01/2024", cargo="ALCALDE LOCAL"),
        _p("NO CRUZA", "ENTIDAD QUE NO EXISTE", "1/01/2024"),
        _p("SIN NIT", "EMPRESA SIN NIT EN EL MAPA", "1/01/2024"),
    ]
    elegidos, _ = elegir(personas, ENTIDADES, NITS)
    assert elegidos["23182"]["nombre"] == "Del Cordoba"
    assert elegidos["05045"]["nombre"] == "De Antioquia"
    assert set(elegidos) == {"23182", "05045"}


def test_el_inicio_del_periodo_se_puede_cambiar():
    personas = [_p("ALCALDE VIEJO", "ALCALDIA DE SOPO", "1/01/2020")]
    assert elegir(personas, ENTIDADES, NITS, inicio=date(2020, 1, 1))[0]["25758"]


def test_la_ficha_muestra_el_nombre_con_su_fuente_o_nada():
    alcalde = {
        "nombre": "Alba Muñoz",
        "desde": "2024-01-01",
        "fuente": "https://www.datos.gov.co/d/x",
    }
    datos = SimpleNamespace(alcaldes={"25758": alcalde})
    html = linea_alcalde(datos, "25758")
    assert "Alba Muñoz" in html and "SIGEP II" in html and "01/01/2024" in html
    assert linea_alcalde(datos, "05001") == ""
