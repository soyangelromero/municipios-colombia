from datetime import date

from municipios.fuentes import cuipo, secop


def gasto(periodo, cuenta, compromisos, entidad="210005001"):
    return {
        "periodo": periodo,
        "codigo_entidad": entidad,
        "cuenta": cuenta,
        "compromisos": str(compromisos),
        "obligaciones": "0",
        "pagos": "0",
    }


def test_cuipo_toma_el_ultimo_corte_de_cada_anio():
    datos = {
        cuipo.GASTOS: [
            gasto("20250901", "2", 70),  # corte intermedio de 2025: se ignora
            gasto("20251201", "2", 100),
            gasto("20251201", "2.3", 60),
            gasto("20260601", "2", 40),
            gasto("20251201", "2", 5, entidad="219999999"),  # no cruza
        ],
        cuipo.PROGRAMACION: [
            {
                "periodo": "20251201",
                "codigo_entidad": "210005001",
                "cuenta": "2",
                "definitiva": "120",
            }
        ],
        cuipo.INGRESOS: [
            {
                "periodo": "20251201",
                "codigo_entidad": "210005001",
                "cuenta": "1.1.01",
                "recaudo": "30",
            }
        ],
    }
    resultado = cuipo.normalizar(datos, {"05001"})
    valores = {(o.indicador, o.periodo): o.valor for o in resultado.observaciones}
    assert valores[("gasto_compromisos", "2025")] == 100
    assert valores[("gasto_inversion", "2025")] == 60
    assert valores[("gasto_compromisos", "2026-01/2026-06")] == 40
    assert valores[("presupuesto_gastos_definitivo", "2025")] == 120
    assert valores[("ingresos_tributarios", "2025")] == 30
    assert resultado.sin_cruce == {"219999999": "99999"}
    assert {o.divipola for o in resultado.observaciones} == {"05001"}


def test_cuipo_divipola_sale_de_los_ultimos_cinco_digitos():
    assert cuipo.divipola("217870678") == "70678"
    assert cuipo.divipola("923273478") == "27493"  # municipio nuevo: código especial


def contrato(nit, anio, modalidad, contratos, valor):
    return {
        "nit_entidad": nit,
        "anio": str(anio),
        "modalidad": modalidad,
        "contratos": str(contratos),
        "valor": str(valor),
    }


def test_secop_identifica_alcaldias_por_nombre_y_ciudad(cruce):
    entidades = [
        {"nit_entidad": "890905211", "nombre_entidad": "ALCALDIA DE MEDELLIN",
         "departamento": "Antioquia", "ciudad": "Medellín"},
        {"nit_entidad": "890981150", "nombre_entidad": "Alcaldía Municipal de Apartadó",
         "departamento": "Antioquia", "ciudad": "No Definido"},
        {"nit_entidad": "800000001", "nombre_entidad": "CONCEJO MUNICIPAL DE MEDELLIN",
         "departamento": "Antioquia", "ciudad": "Medellín"},
        {"nit_entidad": "800000002", "nombre_entidad": "E.S.E. HOSPITAL MUNICIPAL",
         "departamento": "Antioquia", "ciudad": "Medellín"},
    ]  # fmt: skip
    assert secop.alcaldias_por_nombre(entidades, cruce) == {
        "890905211": "05001",
        "890981150": "05045",
    }


def test_secop_suma_por_alcaldia_y_separa_contratacion_directa():
    filas = [
        contrato("890905211", 2025, "Contratación directa", 10, 1000),
        contrato("890905211", 2025, "Licitación pública", 2, 5000),
        contrato("890905211", 2026, "Mínima cuantía", 1, 50),
        contrato("800000001", 2025, "Contratación directa", 99, 99),  # no es alcaldía
    ]
    resultado = secop.normalizar(filas, {"890905211": "05001"}, hoy=date(2026, 10, 14))
    valores = {(o.indicador, o.periodo): o.valor for o in resultado.observaciones}
    assert valores[("contratos_numero", "2025")] == 12
    assert valores[("contratos_valor", "2025")] == 6000
    assert valores[("contratos_directa_numero", "2025")] == 10
    assert valores[("contratos_directa_valor", "2025")] == 1000
    assert valores[("contratos_numero", "2026-01/2026-10")] == 1
    assert ("contratos_directa_numero", "2026-01/2026-10") not in valores
