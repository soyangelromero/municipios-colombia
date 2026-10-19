from municipios.exportar.aligerar import aligerar_svg

# Un cuadrado de 100 con vértices intermedios casi alineados que deben desaparecer.
SVG = (
    '<svg><path id="e-1" data-codigo="1" d="M0 0l25 0.1 25 -0.1 25 0.1 25 -0.1 0 100 -100 0z"/>'
    '<path id="e-2" d="M200 200l10 0 0 10z"/></svg>'
)


def test_quita_vertices_redundantes_y_conserva_las_esquinas():
    salida = aligerar_svg(SVG, tolerancia=0.5)
    assert salida.startswith("<svg>") and salida.count("<path") == 2
    # De 7 desplazamientos del primer trazado quedan los 3 de las esquinas.
    assert 'd="M0 0l100 0 0 100 -100 0z"' in salida


def test_conserva_atributos_y_triangulos_pequenos():
    salida = aligerar_svg(SVG, tolerancia=0.5)
    assert 'id="e-1" data-codigo="1"' in salida
    assert 'd="M200 200l10 0 0 10z"' in salida


def test_sin_trazados_no_cambia_nada():
    assert aligerar_svg("<svg></svg>") == "<svg></svg>"
