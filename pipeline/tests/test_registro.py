from municipios.comun.registro import cargar_fuentes
from municipios.fuentes import divipola, mgn, poblacion, seguridad


def test_registro_tiene_campos_completos():
    fuentes = cargar_fuentes()
    assert fuentes
    for fuente in fuentes.values():
        assert fuente.organismo and fuente.titulo and fuente.licencia
        assert fuente.url.startswith("https://")


def test_toda_fuente_usada_en_el_codigo_esta_registrada():
    usadas = {divipola.FUENTE, poblacion.FUENTE, mgn.FUENTE} | {d.fuente for d in seguridad.DELITOS}
    assert usadas <= set(cargar_fuentes())
