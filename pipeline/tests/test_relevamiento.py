from municipios.comun.modelos import Municipio
from municipios.relevamiento.criterios import (
    CRITERIOS,
    candidatos,
    clasificar,
    dominio,
    leer_sitios_manuales,
)


def _municipio(nombre: str, departamento: str) -> Municipio:
    return Municipio(
        divipola="99999",
        nombre=nombre,
        nombre_oficial=nombre.upper(),
        departamento_codigo="99",
        departamento=departamento,
        departamento_slug="y",
        tipo="municipio",
        slug="x",
        lat=None,
        lon=None,
    )


def test_dominio_quita_tildes_espacios_y_signos():
    assert dominio("San José del Guaviare") == "sanjosedelguaviare"
    assert dominio("Bogotá, D.C.") == "bogotadc"


def test_candidatos_sigue_el_patron_de_mintic():
    m = _municipio("Sopó", "Cundinamarca")
    assert candidatos(m, {}) == [
        "https://www.sopo-cundinamarca.gov.co/",
        "https://www.sopo.gov.co/",
    ]


def test_candidatos_prefiere_el_sitio_manual():
    m = _municipio("Medellín", "Antioquia")
    assert candidatos(m, {"99999": "https://www.medellin.gov.co/"}) == [
        "https://www.medellin.gov.co/"
    ]


def test_clasificar_encuentra_por_texto_y_por_url():
    enlaces = [
        ("Ejecución presupuestal 2026", "https://x.gov.co/a.pdf"),
        ("Plan Anual de Adquisiciones", "https://x.gov.co/b"),
        ("Documentos", "https://x.gov.co/datos-abiertos/inicio"),
        ("Contacto", "https://x.gov.co/contacto"),
    ]
    r = clasificar(enlaces)
    assert r["ejecucion"] == "https://x.gov.co/a.pdf"
    assert r["plan_adquisiciones"] == "https://x.gov.co/b"
    assert r["datos_abiertos"] == "https://x.gov.co/datos-abiertos/inicio"
    assert r["pqrsd"] is None
    assert set(r) == {c.id for c in CRITERIOS}


def test_clasificar_sin_enlaces_no_encuentra_nada():
    assert all(v is None for v in clasificar([]).values())


def test_leer_sitios_manuales(tmp_path):
    ruta = tmp_path / "sitios.csv"
    ruta.write_text("divipola,sitio\n05001,https://a.gov.co/\n05002,\n", encoding="utf-8")
    assert leer_sitios_manuales(ruta) == {"05001": "https://a.gov.co/"}
    assert leer_sitios_manuales(tmp_path / "no_existe.csv") == {}


def test_presupuesto_participativo_no_es_presupuesto():
    r = clasificar([("Presupuesto participativo", "https://x.gov.co/pp")])
    assert r["presupuesto"] is None
    assert clasificar([("Presupuesto General 2026", "https://x.gov.co/p")])["presupuesto"]
