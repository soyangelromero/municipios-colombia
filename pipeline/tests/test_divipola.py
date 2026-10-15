import pytest

from municipios.fuentes.divipola import normalizar


def fila(cod, nombre, tipo="Municipio", lat="6,246631", lon="-75,581775"):
    return {
        "cod_dpto": cod[:2],
        "dpto": "X",
        "cod_mpio": cod,
        "nom_mpio": nombre,
        "tipo_municipio": tipo,
        "latitud": lat,
        "longitud": lon,
    }


def test_normaliza_municipio_comun():
    (m,) = normalizar([fila("05001", "MEDELLÍN")])
    assert m.divipola == "05001"
    assert m.nombre == "Medellín"
    assert m.nombre_oficial == "MEDELLÍN"
    assert m.departamento == "Antioquia"
    assert m.slug == "antioquia--medellin"
    assert m.tipo == "municipio"
    assert (m.lat, m.lon) == (6.246631, -75.581775)


def test_bogota_tiene_nombre_y_slug_especiales():
    (m,) = normalizar([fila("11001", "BOGOTÁ, D.C.")])
    assert m.nombre == "Bogotá D.C."
    assert m.slug == "bogota"


def test_tipos_isla_y_area_no_municipalizada():
    municipios = normalizar(
        [
            fila("88001", "SAN ANDRÉS", tipo="Isla"),
            fila("91263", "EL ENCANTO", tipo="Área no municipalizada"),
        ]
    )
    assert [m.tipo for m in municipios] == ["isla", "area_no_municipalizada"]
    assert municipios[0].slug == "san-andres--san-andres"


def test_mismo_nombre_en_departamentos_distintos_no_choca():
    municipios = normalizar([fila("25473", "MOSQUERA"), fila("52473", "MOSQUERA")])
    assert {m.slug for m in municipios} == {"cundinamarca--mosquera", "narino--mosquera"}


def test_ordena_por_codigo():
    municipios = normalizar([fila("08001", "BARRANQUILLA"), fila("05001", "MEDELLÍN")])
    assert [m.divipola for m in municipios] == ["05001", "08001"]


def test_coordenadas_vacias_quedan_en_none():
    (m,) = normalizar([fila("05001", "MEDELLÍN", lat="", lon=None)])
    assert m.lat is None and m.lon is None


@pytest.mark.parametrize(
    ("filas", "mensaje"),
    [
        ([fila("5001", "MEDELLÍN")], "inválido"),
        ([fila("00001", "NINGUNO")], "Departamento desconocido"),
        ([fila("05001", "MEDELLÍN", tipo="Corregimiento")], "Tipo desconocido"),
        ([fila("05001", "MEDELLÍN"), fila("05001", "MEDELLÍN")], "repetidos"),
    ],
)
def test_errores_de_fuente(filas, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        normalizar(filas)
