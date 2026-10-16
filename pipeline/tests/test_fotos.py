import pytest

from municipios.fotos.licencias import licencia_libre, limpiar_html, nombre_de_archivo


@pytest.mark.parametrize(
    ("nombre", "esperado"),
    [
        ("CC BY 4.0", True),
        ("CC BY-SA 3.0", True),
        ("CC BY-SA 2.5 es", True),
        ("CC0", True),
        ("Public domain", True),
        ("PD-old", True),
        ("CC BY-NC 4.0", False),
        ("CC BY-ND 2.0", False),
        ("CC BY-NC-SA 3.0", False),
        ("GFDL", False),
        ("Fair use", False),
        ("", False),
        (None, False),
    ],
)
def test_licencia_libre(nombre, esperado):
    assert licencia_libre(nombre) is esperado


def test_limpiar_html_quita_etiquetas_y_entidades():
    crudo = '<a href="//x">Juan P&eacute;rez</a>  <br> (CC)'
    assert limpiar_html(crudo) == "Juan Pérez (CC)"
    assert limpiar_html(None) == ""


def test_nombre_de_archivo_desde_url_de_commons():
    url = "http://commons.wikimedia.org/wiki/Special:FilePath/Casa%20hacienda%20Paispamba.JPG"
    assert nombre_de_archivo(url) == "Casa hacienda Paispamba.JPG"
