import xml.etree.ElementTree as ET

import pytest

from municipios.exportar.mapa_svg import (
    ANCHO,
    MARGEN,
    RELLENO,
    TAM_RECUADRO,
    Forma,
    Marco,
    svg,
    transformacion_para,
    trazo,
)

SVG_NS = "{http://www.w3.org/2000/svg}"


def cuadrado(x, y, lado):
    return [[(x, y), (x + lado, y), (x + lado, y + lado), (x, y + lado), (x, y)]]


FORMAS = [
    Forma("15002", "Almeida", "boyaca--almeida", [cuadrado(100.0, 0.0, 100.0)]),
    Forma("15001", "Tunja & <Centro>", "boyaca--tunja", [cuadrado(0.0, 0.0, 100.0)]),
]


def leer(documento):
    raiz = ET.fromstring(documento)
    return raiz, raiz.findall(f".//{SVG_NS}path")


def test_transformacion_ajusta_al_marco_e_invierte_y():
    t = transformacion_para(FORMAS, Marco(10, 10, 980, 490))
    assert t.aplicar(0, 100) == pytest.approx((10, 10))  # esquina superior izquierda
    assert t.aplicar(200, 0) == pytest.approx((990, 500))  # inferior derecha


def test_transformacion_centra_si_sobra_espacio():
    t = transformacion_para(FORMAS, Marco(0, 0, 400, 400))  # escala 2; sobra alto
    assert t.aplicar(0, 100) == pytest.approx((0, 100))


def test_trazo_usa_coordenadas_relativas():
    t = transformacion_para(FORMAS, Marco(10, 10, 980, 490))
    assert trazo([cuadrado(0.0, 0.0, 100.0)], t) == "M10 500l490 0 0 -490 -490 0z"


def test_svg_valido_ordenado_y_escapado():
    raiz, caminos = leer(svg(FORMAS, "Municipios de Boyacá", "municipios"))
    assert raiz.get("viewBox") == f"0 0 {ANCHO} 510"  # 100 m x escala 4,9 + 2 márgenes
    assert [c.get("data-codigo") for c in caminos] == ["15001", "15002"]
    assert caminos[0].get("data-slug") == "boyaca--tunja"
    assert caminos[0].find(f"{SVG_NS}title").text == "Tunja & <Centro>"
    assert raiz.find(f"{SVG_NS}title").text == "Municipios de Boyacá"


def test_recuadro_saca_la_forma_lejana_del_marco_principal():
    lejana = Forma("88001", "San Andrés", "san-andres--san-andres", [cuadrado(-5000, 0, 10)])
    raiz, caminos = leer(svg([*FORMAS, lejana], "Colombia", "departamentos", recuadro={"88001"}))
    # Sin la isla, el continente ocupa todo el ancho y la proporción no cambia.
    assert raiz.get("viewBox") == f"0 0 {ANCHO} 510"
    rect = raiz.find(f".//{SVG_NS}rect")
    assert rect.get("width") == str(TAM_RECUADRO)
    assert {c.get("data-codigo") for c in caminos} == {"15001", "15002", "88001"}


def test_recuadro_omite_cayos_lejanos():
    isla = cuadrado(-5000, 0, 100)
    cayo = cuadrado(-9000, 9000, 1)  # 1 m², lejísimos: agrandaría el encuadre
    archipielago = Forma("88", "San Andrés", "san-andres", [isla, cayo])
    _, caminos = leer(svg([*FORMAS, archipielago], "Colombia", "d", recuadro={"88"}))
    d = next(c for c in caminos if c.get("data-codigo") == "88").get("d")
    assert d.count("M") == 1  # solo la isla principal
    # La isla llena el recuadro (menos el relleno interior), no queda reducida a un punto.
    assert d.startswith(f"M{MARGEN + RELLENO} {MARGEN + TAM_RECUADRO - RELLENO}")


def test_recuadro_pone_cada_isla_principal_en_su_celda():
    islas = Forma(
        "88", "San Andrés", "san-andres", [cuadrado(-5000, 0, 10), cuadrado(-4000, 900, 8)]
    )
    raiz, caminos = leer(svg([*FORMAS, islas], "Colombia", "d", recuadro={"88"}))
    piezas = [c for c in caminos if c.get("data-codigo") == "88"]
    assert [c.get("id") for c in piezas] == ["e-88-1", "e-88-2"]
    assert len(raiz.findall(f".//{SVG_NS}rect")) == 1


def test_paneles_dibuja_cada_forma_en_su_marco():
    raiz, caminos = leer(svg(FORMAS, "Islas", "municipios", paneles=True))
    assert len(raiz.findall(f".//{SVG_NS}rect")) == 2
    ancho_panel = (ANCHO - 3 * MARGEN) / 2
    assert raiz.get("viewBox") == f"0 0 {ANCHO} {round(ancho_panel + 2 * MARGEN)}"
    assert len(caminos) == 2
