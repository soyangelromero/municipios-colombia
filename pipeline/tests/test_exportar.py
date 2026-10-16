import pytest

from municipios.exportar import formato
from municipios.exportar.paginas import sigla, tramo
from municipios.exportar.plantillas import Pagina, barra, semaforo


@pytest.mark.parametrize(
    ("valor", "decimales", "esperado"),
    [(1234567.89, 0, "1.234.568"), (1234.5, 1, "1.234,5"), (None, 0, "—")],
)
def test_numero_en_formato_colombiano(valor, decimales, esperado):
    assert formato.numero(valor, decimales) == esperado


@pytest.mark.parametrize(
    ("valor", "unidad", "esperado"),
    [
        (1.2e12, "pesos corrientes", "$ 1,2 billones"),
        (345e9, "pesos corrientes", "$ 345 mil millones"),
        (2650826, "pesos por habitante", "$ 2.650.826"),
        (87.04, "% del gasto comprometido", "87,0 %"),
        (100, "sí/no", "Sí"),
        (0, "sí/no", "No"),
        (670.4, "habitantes por km²", "670 hab./km²"),
        (207.3, "km²", "207 km²"),
        (138796, "personas (proyección)", "138.796"),
    ],
)
def test_segun_unidad(valor, unidad, esperado):
    assert formato.segun_unidad(valor, unidad) == esperado


def test_periodo_legible():
    assert formato.periodo("2026-01/2026-08") == "ene-ago 2026"
    assert formato.periodo("2019-S2") == "2.º sem. 2019"
    assert formato.periodo("2026-10") == "oct 2026"
    assert formato.periodo("2025") == "2025"


@pytest.mark.parametrize(
    ("ruta", "raiz"),
    [("", ""), ("ranking/", "../"), ("m/boyaca--samaca/", "../../"), ("404.html", "")],
)
def test_raiz_relativa_de_cada_pagina(ruta, raiz):
    assert Pagina(ruta, "t", "d", "").raiz == raiz


def test_fragmentos_y_escala():
    assert "semaforo--verde" in semaforo("verde", 81.4) and "81,4" in semaforo("verde", 81.4)
    assert "Sin índice" in semaforo(None)
    assert "sin dato" in barra(None)
    assert "width:55.0%" in barra(55)
    assert [tramo(v) for v in (None, 10, 45, 55, 65, 95)] == ["sin", "e1", "e2", "e3", "e4", "e5"]
    assert sigla("cgr_cuipo_gastos") == "Contraloría (CUIPO)"


def test_leer_transparencia_auto_agrupa_por_municipio(tmp_path):
    from municipios.exportar.datos_web import leer_transparencia_auto

    ruta = tmp_path / "t.csv"
    ruta.write_text(
        "divipola,criterio,resultado\n05001,pqrsd,enlace_encontrado\n05001,datos_abiertos,no_encontrado\n08001,pqrsd,error\n",
        encoding="utf-8",
    )
    datos = leer_transparencia_auto(ruta)
    assert len(datos["05001"]) == 2
    assert datos["08001"][0]["resultado"] == "error"
    assert leer_transparencia_auto(tmp_path / "no.csv") == {}
