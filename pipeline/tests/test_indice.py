import pytest

from municipios.comun.modelos import Municipio, Observacion
from municipios.indice.almacen import Almacen, clave_periodo
from municipios.indice.calculo import (
    Componente,
    Config,
    Pilar,
    calcular,
    cargar_config,
    percentiles,
    pesos_alternativos,
    semaforo,
)
from municipios.indice.derivados import Calculadora, Dato


def test_clave_periodo_ordena_todos_los_formatos():
    assert clave_periodo("2025") == (2025, 12)
    assert clave_periodo("2026-01/2026-08") == (2026, 8)
    assert clave_periodo("2019-S2") == (2019, 12)
    assert clave_periodo("2026-10") == (2026, 10)
    with pytest.raises(ValueError):
        clave_periodo("hace poco")


def test_anio_referencia_exige_cobertura():
    obs = [Observacion(f"0500{i}", "x", 1, "2024", "f") for i in range(4)]
    obs += [Observacion("05000", "x", 1, "2025", "f")]  # 2025: solo 1 de 4
    assert Almacen(obs).anio_referencia("x") == 2024


def test_percentiles_con_empates_y_sentido():
    assert percentiles({"a": 1, "b": 2, "c": 2, "d": 3}, "mayor_mejor") == {
        "a": 0.0,
        "b": 50.0,
        "c": 50.0,
        "d": 100.0,
    }
    assert percentiles({"a": 1, "b": 3}, "menor_mejor") == {"a": 100.0, "b": 0.0}


def test_configuracion_real_es_valida():
    config = cargar_config()
    assert sum(p.peso for p in config.pilares) == 100
    assert {p.id for p in config.pilares} == {"T", "S", "G", "C"}
    for _, pesos in pesos_alternativos(config):
        assert sum(pesos.values()) == pytest.approx(100)
    assert semaforo(39.9, config) == "rojo"
    assert semaforo(70, config) == "verde"


def municipio(codigo, tipo="municipio"):
    return Municipio(codigo, codigo, codigo, codigo[:2], "Dep", "dep", tipo, codigo, None, None)


CONFIG = Config(
    version="prueba",
    pilares=(
        Pilar(
            "T",
            "Transparencia",
            50,
            "",
            (
                Componente("obligacion", "Obligación", 1, "absoluto", "mayor_mejor", si_falta=0),
                Componente("reporta_cuipo", "Cuentas", 1, "absoluto", "mayor_mejor"),
            ),
        ),
        Pilar(
            "S",
            "Servicios",
            30,
            "",
            (Componente("servicio", "Servicio", 1, "pares", "mayor_mejor"),),
        ),
        Pilar(
            "G", "Gestión", 20, "", (Componente("gestion", "Gestión", 1, "pares", "menor_mejor"),)
        ),
    ),
    semaforo={"rojo_menor_a": 40, "verde_desde": 70},
    reglas={
        "tope_sin_cuentas": 39.9,
        "cobertura_minima_pilar": 0.6,
        "pilares_minimos": 3,
        "pares_minimos": 2,
        "sensibilidad_puntos": 10,
    },
    contexto=(),
)


def d(valor):
    return Dato(valor, "2025", ("f",))


def test_calcular_aplica_reglas():
    municipios = {c: municipio(c) for c in ("05001", "05002", "05003")}
    municipios["91263"] = municipio("91263", "area_no_municipalizada")
    grupos = dict.fromkeys(municipios, "G1")
    datos = {
        "05001": {"obligacion": d(90), "reporta_cuipo": d(100), "servicio": d(10), "gestion": d(1)},
        "05002": {"reporta_cuipo": d(100), "servicio": d(5), "gestion": d(2)},  # no reportó
        "05003": {"obligacion": d(100), "reporta_cuipo": d(0), "servicio": d(20), "gestion": d(3)},
        "91263": {},
    }
    r = calcular(datos, municipios, grupos, CONFIG)

    # No reportar una obligación con si_falta cuenta como 0, no se reparte el peso.
    assert r["05002"]["componentes"]["obligacion"]["puntaje"] == 0
    # Sin cuentas: tope.
    assert r["05003"]["tope"] is True and r["05003"]["indice"] <= 39.9
    assert r["05003"]["semaforo"] == "rojo"
    # Pares: percentil dentro del grupo; «menor_mejor» invierte.
    assert r["05003"]["componentes"]["servicio"]["puntaje"] == 100
    assert r["05003"]["componentes"]["gestion"]["puntaje"] == 0
    # Puestos y rango de sensibilidad.
    assert r["05001"]["puesto"]["nacional"] == 1
    assert r["05001"]["puesto"]["nacional_de"] == 3
    lo, hi = r["05001"]["rango_puestos"]
    assert lo <= 1 <= hi
    # Sin alcaldía: sin índice, con motivo.
    assert r["91263"]["indice"] is None
    assert "no municipalizada" in r["91263"]["motivo_sin_indice"]


def test_tasas_de_delito_suavizadas_hacia_el_grupo():
    obs = []
    for anio in (2023, 2024, 2025):
        obs += [
            Observacion("05001", "poblacion", 1_000_000, str(anio), "p"),
            Observacion("05001", "homicidios", 100, str(anio), "h"),
            Observacion("05002", "poblacion", 1_000, str(anio), "p"),
            Observacion("05002", "homicidios", 1 if anio == 2025 else 0, str(anio), "h"),
        ]
    municipios = {c: municipio(c) for c in ("05001", "05002")}
    calc = Calculadora(Almacen(obs), municipios, dict.fromkeys(municipios, "G1"), 2026, 3, 20000)
    datos = calc.calcular()
    grande, chico = datos["05001"]["tasa_homicidios"], datos["05002"]["tasa_homicidios"]
    assert grande.valor == pytest.approx(10.0)
    assert grande.puntuable == pytest.approx(10.0, abs=0.1)  # casi no cambia
    assert chico.valor == pytest.approx(33.33, abs=0.01)  # 1 hecho en 3.000 hab-año
    assert chico.puntuable < 15  # el suavizado lo acerca a la tasa del grupo (~10)
    assert chico.periodo == "2023-2025"
