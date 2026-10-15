import pytest

from municipios.comun.cruce import Cruce, clave
from municipios.comun.modelos import Municipio


def municipio(divipola, nombre, oficial, departamento):
    return Municipio(
        divipola=divipola,
        nombre=nombre,
        nombre_oficial=oficial,
        departamento_codigo=divipola[:2],
        departamento=departamento,
        departamento_slug="x",
        tipo="municipio",
        slug="x",
        lat=None,
        lon=None,
    )


CRUCE = Cruce(
    [
        municipio("11001", "Bogotá D.C.", "BOGOTÁ, D.C.", "Bogotá D.C."),
        municipio("13001", "Cartagena de Indias", "CARTAGENA DE INDIAS", "Bolívar"),
        municipio("54001", "San José de Cúcuta", "SAN JOSÉ DE CÚCUTA", "Norte de Santander"),
        municipio("19548", "Piendamó - Tunía", "PIENDAMÓ - TUNÍA", "Cauca"),
        municipio("25473", "Mosquera", "MOSQUERA", "Cundinamarca"),
        municipio("52473", "Mosquera", "MOSQUERA", "Nariño"),
        municipio("05045", "Apartadó", "APARTADÓ", "Antioquia"),
        municipio("05051", "Arboletes", "ARBOLETES", "Antioquia"),
        municipio("88001", "San Andrés", "SAN ANDRÉS", "San Andrés y Providencia"),
    ]
)


def test_clave_normaliza():
    assert clave("Bogotá, D.C.") == "BOGOTA D C"
    assert clave("  san  josé de Cúcuta ") == "SAN JOSE DE CUCUTA"
    assert clave("NARI¥O") == "NARINO"  # Ñ mal codificada en ADRES


@pytest.mark.parametrize(
    ("departamento", "nombre", "esperado"),
    [
        ("BOGOTA D.C.", "BOGOTA D.C.", "11001"),
        ("Bogotá", "Bogotá, D.C.", "11001"),
        ("BOLIVAR", "CARTAGENA", "13001"),
        ("NORTE SANTANDER", "CUCUTA", "54001"),
        ("CAUCA", "PIENDAMO", "19548"),
        ("Cundinamarca", "MOSQUERA", "25473"),
        ("NARIÑO", "MOSQUERA", "52473"),
        ("ANTIOQUIA", "APARTADO", "05045"),
        ("ANTIOQUIA", "ARBOLETTES", "05051"),  # error de tipeo: parecido muy alto
        ("SAN ANDRES", "SAN ANDRES", "88001"),
    ],
)
def test_cruza_variantes_comunes(departamento, nombre, esperado):
    assert CRUCE.municipio(departamento, nombre) == esperado


def test_no_inventa_coincidencias():
    assert CRUCE.municipio("ANTIOQUIA", "MEDELLIN") is None
    assert CRUCE.municipio("DEPARTAMENTO INEXISTENTE", "MOSQUERA") is None
