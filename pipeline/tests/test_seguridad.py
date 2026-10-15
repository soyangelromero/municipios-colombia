from datetime import date

from municipios.fuentes.seguridad import ANIO_INICIAL, DELITOS, normalizar, periodo

HOMICIDIOS = DELITOS[0]


def test_periodo_anio_completo_y_parcial():
    assert periodo(2025, date(2026, 8, 31)) == "2025"
    assert periodo(2026, date(2026, 8, 31)) == "2026-01/2026-08"
    assert periodo(2026, date(2026, 12, 31)) == "2026"


def test_suma_completa_con_ceros_y_reporta_sin_cruce():
    filas = [
        {"cod_muni": "05001", "anio": str(ANIO_INICIAL), "total": "10"},
        {"cod_muni": "05001", "anio": str(ANIO_INICIAL), "total": "2"},
        {"cod_muni": "99999", "anio": str(ANIO_INICIAL), "total": "3"},
    ]
    obs, sin_cruce = normalizar(
        filas, HOMICIDIOS, date(ANIO_INICIAL + 1, 3, 31), {"05001", "05002"}
    )

    valores = {(o.divipola, o.periodo): o.valor for o in obs}
    assert valores == {
        ("05001", str(ANIO_INICIAL)): 12,
        ("05001", f"{ANIO_INICIAL + 1}-01/{ANIO_INICIAL + 1}-03"): 0,
        ("05002", str(ANIO_INICIAL)): 0,
        ("05002", f"{ANIO_INICIAL + 1}-01/{ANIO_INICIAL + 1}-03"): 0,
    }
    assert sin_cruce == {"99999": 3}
    assert {o.fuente for o in obs} == {"mindefensa_homicidios"}
    assert {o.indicador for o in obs} == {"homicidios"}


def test_completa_ceros_a_la_izquierda_del_codigo():
    filas = [{"cod_muni": "5001", "anio": str(ANIO_INICIAL), "total": "1.0"}]
    obs, sin_cruce = normalizar(filas, HOMICIDIOS, date(ANIO_INICIAL, 12, 31), {"05001"})
    assert obs[0].valor == 1
    assert sin_cruce == {}
