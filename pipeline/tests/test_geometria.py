from municipios.comun.geometria import area, caja, douglas_peucker, simplificar, simplificar_anillo

CUADRADO = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]


def test_area_y_caja():
    assert area(CUADRADO) == 100
    assert caja([[CUADRADO]]) == (0, 0, 10, 10)


def test_douglas_peucker_quita_puntos_casi_alineados():
    linea = [(0.0, 0.0), (1.0, 0.1), (2.0, -0.1), (3.0, 5.0), (4.0, 6.0)]
    assert douglas_peucker(linea, 0.5) == [(0.0, 0.0), (2.0, -0.1), (3.0, 5.0), (4.0, 6.0)]
    assert douglas_peucker(linea, 100) == [(0.0, 0.0), (4.0, 6.0)]


def test_simplificar_anillo_conserva_esquinas_y_quita_ruido():
    con_ruido = [(0.0, 0.0), (5.0, 0.01), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
    resultado = simplificar_anillo(con_ruido, 0.1)
    assert set(resultado) == {(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)}


def test_simplificar_anillo_degenerado_devuelve_none():
    assert simplificar_anillo([(0.0, 0.0), (1.0, 1.0), (0.0, 0.0)], 0.1) is None


def test_simplificar_descarta_islotes_y_huecos_chicos():
    islote = [(20.0, 20.0), (20.5, 20.0), (20.5, 20.5), (20.0, 20.5), (20.0, 20.0)]
    hueco = [(4.0, 4.0), (4.2, 4.0), (4.2, 4.2), (4.0, 4.2), (4.0, 4.0)]
    resultado = simplificar([[CUADRADO, hueco], [islote]], tolerancia=0.01, area_minima=1)
    assert len(resultado) == 1
    assert len(resultado[0]) == 1  # sin el hueco


def test_simplificar_nunca_deja_una_entidad_vacia():
    diminuto = [(0.0, 0.0), (0.1, 0.0), (0.1, 0.1), (0.0, 0.1), (0.0, 0.0)]
    resultado = simplificar([[diminuto]], tolerancia=0.001, area_minima=100)
    assert len(resultado) == 1
