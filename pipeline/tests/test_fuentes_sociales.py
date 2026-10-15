from municipios.fuentes import educacion, salud


def test_educacion_convierte_campos_y_reporta_codigos_sin_cruce():
    filas = [
        {"a_o": "2024", "c_digo_municipio": "5001", "cobertura_neta": "93.58", "deserci_n": "3.18"},
        {"a_o": "2024", "c_digo_municipio": "99999", "cobertura_neta": "50"},
    ]
    resultado = educacion.normalizar(filas, {"05001"})
    assert {(o.indicador, o.valor, o.periodo) for o in resultado.observaciones} == {
        ("educacion_cobertura_neta", 93.58, "2024"),
        ("educacion_desercion", 3.18, "2024"),
    }
    assert resultado.sin_cruce == {"99999": "2024"}


def test_salud_cruza_por_nombre_y_usa_la_fecha_de_actualizacion(cruce):
    filas = [
        {"dpr_nombre": "ANTIOQUIA", "mnc_nombre": "MEDELLIN", "afiliados": "100"},
        {"dpr_nombre": "BOLIVAR", "mnc_nombre": "CARTAGENA", "afiliados": "50"},
        {"dpr_nombre": "ANTIOQUIA", "mnc_nombre": "GOTHAM", "afiliados": "7"},
    ]
    resultado = salud.normalizar(filas, "d7a5-cnra", "2026-10-03", cruce)
    assert {(o.divipola, o.valor, o.periodo) for o in resultado.observaciones} == {
        ("05001", 100, "2026-10"),
        ("13001", 50, "2026-10"),
    }
    assert resultado.sin_cruce == {"ANTIOQUIA / GOTHAM": 7}
    assert {o.indicador for o in resultado.observaciones} == {"afiliados_subsidiado"}
