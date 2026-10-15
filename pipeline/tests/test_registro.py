from municipios.cli import FUENTES
from municipios.comun.registro import cargar_fuentes, cargar_indicadores
from municipios.fuentes import divipola, mgn


def test_registro_de_fuentes_tiene_campos_completos():
    fuentes = cargar_fuentes()
    assert fuentes
    for fuente in fuentes.values():
        assert fuente.organismo and fuente.titulo and fuente.licencia
        assert fuente.url.startswith("https://")


def test_todo_indicador_de_las_fuentes_tiene_ficha():
    declarados = {i for modulo, _ in FUENTES.values() for i in modulo.INDICADORES}
    assert declarados | {"superficie_km2"} <= set(cargar_indicadores())


def test_toda_ficha_apunta_a_una_fuente_registrada():
    fuentes = set(cargar_fuentes())
    assert {i.fuente for i in cargar_indicadores().values()} <= fuentes
    assert {divipola.FUENTE, mgn.FUENTE} <= fuentes
