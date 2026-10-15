import pytest

from municipios.comun.textos import nombre_legible, sin_tildes, slug


@pytest.mark.parametrize(
    ("oficial", "esperado"),
    [
        ("MEDELLÍN", "Medellín"),
        ("SAN ANDRÉS DE TUMACO", "San Andrés de Tumaco"),
        ("EL CARMEN DE VIBORAL", "El Carmen de Viboral"),
        ("BOGOTÁ, D.C.", "Bogotá, D.C."),
        ("MIRITÍ - PARANÁ", "Mirití - Paraná"),
        ("SAN JOSÉ DE CÚCUTA", "San José de Cúcuta"),
        ("LA PLATA", "La Plata"),
        ("  PUERTO   NARIÑO ", "Puerto Nariño"),
    ],
)
def test_nombre_legible(oficial, esperado):
    assert nombre_legible(oficial) == esperado


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("El Carmen de Viboral", "el-carmen-de-viboral"),
        ("Nariño", "narino"),
        ("Mirití - Paraná", "miriti-parana"),
        ("Bogotá, D.C.", "bogota-d-c"),
    ],
)
def test_slug(texto, esperado):
    assert slug(texto) == esperado


def test_sin_tildes_conserva_mayusculas():
    assert sin_tildes("ÁÉÍÓÚÑ ü") == "AEIOUN u"
