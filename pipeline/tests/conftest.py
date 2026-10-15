import pytest

from municipios.comun.cruce import Cruce
from municipios.comun.modelos import Municipio


def municipio(divipola, nombre, departamento):
    return Municipio(
        divipola=divipola,
        nombre=nombre,
        nombre_oficial=nombre.upper(),
        departamento_codigo=divipola[:2],
        departamento=departamento,
        departamento_slug="x",
        tipo="municipio",
        slug="x",
        lat=None,
        lon=None,
    )


@pytest.fixture
def cruce():
    return Cruce(
        [
            municipio("05001", "Medellín", "Antioquia"),
            municipio("05045", "Apartadó", "Antioquia"),
            municipio("13001", "Cartagena de Indias", "Bolívar"),
        ]
    )
