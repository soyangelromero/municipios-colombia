import pytest

from municipios.comun import periodos
from municipios.fuentes import furag, gobierno_digital, ita


def test_periodo_anual():
    assert periodos.anual(2025) == "2025"
    assert periodos.anual(2026, 6) == "2026-01/2026-06"
    with pytest.raises(ValueError):
        periodos.anual(2026, 13)


def test_ita_periodo_y_nit():
    assert ita.periodo("2019 SEMESTRE 2") == "2019-S2"
    assert ita.periodo("2026") == "2026"
    assert ita.nit("8180013419") == "818001341"
    assert ita.nit("890.982.141") == "890982141"


def fila_ita(sujeto, nit, auto, audit, municipio="MEDELLIN", periodo="2025"):
    return {
        "periodo_medicion": periodo,
        "departamento": "ANTIOQUIA",
        "municipio": municipio,
        "sujeto_obligado": sujeto,
        "numero_documento": nit,
        "autodiagnostico": auto,
        "auditoria": audit,
    }


def test_ita_es_alcaldia():
    assert ita.es_alcaldia("ALCALDÍA DISTRITAL DE SANTA MARTA, DISTRITO TURÍSTICO")
    assert ita.es_alcaldia("SECRETARIA GENERAL ALCALDIA MAYOR DE BOGOTA D.C.")
    assert ita.es_alcaldia("MUNICIPIO DE ENVIGADO")
    assert not ita.es_alcaldia("ALCALDIA LOCAL DE BOSA")
    assert not ita.es_alcaldia("CONCEJO MUNICIPAL DE SAN PEDRO DE LOS MILAGROS")
    assert not ita.es_alcaldia("EMPRESAS PUBLICAS DEL MUNICIPIO DE X")


def test_ita_toma_solo_la_alcaldia_y_arma_mapa_de_nits(cruce):
    filas = [
        fila_ita("CONCEJO MUNICIPAL", "800000001", "50", None),
        fila_ita("ALCALDIA DE MEDELLIN", "8909052111", "98", "71.5"),
        fila_ita("ALCALDIA DE GOTHAM", "900000000", "10", None, municipio="GOTHAM"),
    ]
    resultado, nits = ita.normalizar(filas, cruce)
    assert {(o.indicador, o.valor) for o in resultado.observaciones} == {
        ("ita_autodiagnostico", 98.0),
        ("ita_auditoria", 71.5),
    }
    assert nits == {"890905211": "05001"}
    assert list(resultado.sin_cruce) == ["ANTIOQUIA / GOTHAM"]


def test_codigo_sigep_comparable_entre_conjuntos():
    assert gobierno_digital.codigo_sigep("6,418") == "6418"
    assert gobierno_digital.codigo_sigep("0039") == "39"


def test_gobierno_digital_y_furag_cruzan_por_sigep():
    filas_gd = [
        {
            "c_digo_sigep": "1,067",
            "id_municipio": "5001",
            "vigencia": "2025",
            "id_ndice": "POL07",
            "puntaje_entidad": "81.3",
        },
        {"c_digo_sigep": "9", "id_municipio": "99999", "vigencia": "2025", "id_ndice": "POL07"},
    ]
    resultado_gd, sigep = gobierno_digital.normalizar(filas_gd, {"05001"})
    assert sigep == {"1067": "05001"}
    assert resultado_gd.observaciones[0].indicador == "indice_gobierno_digital"
    assert resultado_gd.sin_cruce == {"99999": "9"}

    filas_furag = [
        {
            "c_digo_sigep": "1067",
            "entidad": "ALCALDIA DE MEDELLIN",
            "vigencia": "2,024",
            "id_indice": "IDI",
            "puntaje_entidad": "90.1",
        },
        {"c_digo_sigep": "5", "entidad": "ALCALDIA X", "vigencia": "2024", "id_indice": "IDI"},
    ]
    resultado = furag.normalizar(filas_furag, sigep)
    (obs,) = resultado.observaciones
    assert (obs.divipola, obs.indicador, obs.valor, obs.periodo) == (
        "05001",
        "furag_desempeno_institucional",
        90.1,
        "2024",
    )
    assert resultado.sin_cruce == {"5": "ALCALDIA X"}
