import pytest
from openpyxl import Workbook

from municipios.fuentes.poblacion import HOJA, leer_filas, normalizar


def fila(codigo, anio, area, total):
    return {"codigo": codigo, "anio": anio, "area": area, "total": total}


def test_normaliza_las_tres_areas():
    obs, sin_cruce = normalizar(
        [
            fila("05001", 2026, "Total", 100),
            fila("05001", 2026, "Cabecera Municipal", 90),
            fila("05001", 2026, "Centros Poblados y Rural Disperso", 10),
        ],
        {"05001"},
    )
    assert {(o.indicador, o.valor, o.periodo) for o in obs} == {
        ("poblacion", 100, "2026"),
        ("poblacion_cabecera", 90, "2026"),
        ("poblacion_rural", 10, "2026"),
    }
    assert sin_cruce == {}
    assert {o.fuente for o in obs} == {"dane_proyecciones_poblacion"}


def test_reporta_codigos_sin_cruce():
    obs, sin_cruce = normalizar(
        [fila("27150", 2026, "Total", 5), fila("27150", 2026, "Cabecera Municipal", 3)],
        {"05001"},
    )
    assert obs == []
    assert sin_cruce == {"27150": 5}


def test_area_desconocida_falla():
    with pytest.raises(ValueError, match="Área geográfica"):
        normalizar([fila("05001", 2026, "Urbana", 1)], {"05001"})


def test_leer_filas_usa_el_encabezado_y_salta_notas(tmp_path):
    libro = Workbook()
    hoja = libro.active
    hoja.title = HOJA
    hoja.append(["PROYECCIONES DE POBLACIÓN"])
    hoja.append(["DP", "DPNOM", "MPIO", "DPMP", "AÑO", "ÁREA GEOGRÁFICA", "TOTAL"])
    hoja.append([None])
    hoja.append(["05", "Antioquia", "05001", "Medellín", 2026, "Total", 2700000])
    hoja.append(["Nota: texto al pie"])
    ruta = tmp_path / "poblacion.xlsx"
    libro.save(ruta)

    assert list(leer_filas(ruta)) == [
        {"codigo": "05001", "anio": 2026, "area": "Total", "total": 2700000}
    ]
