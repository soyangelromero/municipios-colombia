from municipios.exportar.silueta import PUNTOS_MAXIMOS, silueta

SVG = (
    '<svg><g><path id="e-05001" data-codigo="05001" data-slug="a--b" '
    'd="M10 10l20 0 0 10 -20 0z"/>'
    '<path id="e-05002" data-codigo="05002" d="M0 0l1 1 1 0z"/></g></svg>'
)


def test_silueta_reescala_al_lado_mayor():
    s = silueta(SVG, "05001")
    assert s is not None
    assert 'viewBox="0 0 200 100"' in s  # 20 x 10 -> 200 x 100
    assert s.count("M") == 1 and "aria-hidden" in s


def test_silueta_de_municipio_ausente():
    assert silueta(SVG, "99999") is None


def test_silueta_adelgaza_trazados_enormes():
    deltas = " ".join("1 1 1 -1" for _ in range(3000))
    svg = f'<path id="e-1" d="M0 0l{deltas}z"/>'
    s = silueta(svg, "1")
    assert s is not None
    assert s.count("L") <= PUNTOS_MAXIMOS + 20
