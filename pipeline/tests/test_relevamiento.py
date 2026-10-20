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


def test_unir_junta_las_partes_y_reemplaza_solo_a_los_municipios_revisados(tmp_path):
    from municipios.relevamiento.transparencia import CAMPOS_SALIDA, unir

    def escribir(ruta, filas):
        cabecera = ",".join(CAMPOS_SALIDA)
        lineas = [",".join(f.get(c, "") for c in CAMPOS_SALIDA) for f in filas]
        ruta.write_text("\n".join([cabecera, *lineas]) + "\n", encoding="utf-8")

    def fila(codigo, criterio, resultado, fecha="2026-10-19"):
        return {"divipola": codigo, "criterio": criterio, "resultado": resultado, "fecha": fecha}

    salida = tmp_path / "final.csv"
    escribir(
        salida,
        [
            fila("05001", "pqrsd", "no_encontrado", "2026-10-16"),
            fila("08001", "pqrsd", "no_encontrado"),
        ],
    )
    partes = tmp_path / "parciales"
    partes.mkdir()
    escribir(partes / "transparencia_0.csv", [fila("05001", "pqrsd", "enlace_encontrado")])
    escribir(partes / "transparencia_1.csv", [fila("11001", "pqrsd", "menu_no_legible")])
    assert unir(partes, salida) == 2
    texto = salida.read_text(encoding="utf-8").splitlines()
    assert len(texto) == 1 + 3  # 05001 reemplazado, 08001 conservado, 11001 agregado
    assert any("05001" in t and "enlace_encontrado" in t for t in texto)
    assert any("08001" in t for t in texto)


def test_particion_de_la_linea_de_comandos():
    import pytest

    from municipios.cli import _particion

    assert _particion(None) is None
    assert _particion("2/6") == (2, 6)
    for malo in ("6/6", "a/b", "3"):
        with pytest.raises(SystemExit):
            _particion(malo)


def _fila_csv(criterio, resultado, evidencia="", detalle=""):
    return {
        "divipola": "05001",
        "sitio": "https://www.medellin.gov.co/",
        "fecha": "2026-10-19",
        "criterio": criterio,
        "resultado": resultado,
        "evidencia": evidencia,
        "detalle": detalle,
    }


def test_ficha_muestra_la_fuente_oficial_y_no_dice_que_no_publica():
    from types import SimpleNamespace

    from municipios.exportar.paginas import bloque_revision_automatica

    filas = [
        _fila_csv(
            "contratacion",
            "fuente_oficial",
            "https://www.datos.gov.co/d/jbjy-vk9h",
            "SECOP II: 9 contratos",
        ),
        _fila_csv("pqrsd", "menu_no_legible"),
    ]
    html = bloque_revision_automatica(SimpleNamespace(transparencia_auto={"05001": filas}), "05001")
    assert "Fuente oficial" in html and "SECOP II: 9 contratos" in html
    assert "no se pudo leer de forma automática" in html  # el menú sigue sin leerse
    assert "sin verificación humana" in html
    assert "no publica" not in html.replace("no prueba que no se publique", "")


def test_json_de_la_ficha_lleva_el_detalle_de_cada_criterio():
    from types import SimpleNamespace

    from municipios.exportar.datos_web import _auto_json

    filas = [_fila_csv("contratacion", "fuente_oficial", "https://x", "SECOP II: 9 contratos")]
    auto = _auto_json(SimpleNamespace(transparencia_auto={"05001": filas}), "05001")
    assert auto["criterios"] == [
        ["contratacion", "fuente_oficial", "https://x", "SECOP II: 9 contratos"]
    ]
