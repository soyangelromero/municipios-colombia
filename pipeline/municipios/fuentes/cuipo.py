"""CUIPO (Contraloría General, vía CHIP): ejecución presupuestal de cada municipio.

- Los reportes son trimestrales y acumulados (períodos 'AAAAMM01' con MM = 03, 06, 09, 12): se
  usa diciembre de cada año y, para el año en curso, el último trimestre disponible.
- Las cuentas son jerárquicas (2 → 2.1 → 2.1.1 …) y cada nivel trae su total, así que se piden
  solo las cuentas agregadas que interesan; sumar todo contaría lo mismo varias veces.
- En gastos se toma solo la «vigencia actual» (sin reservas ni cuentas por pagar de años previos).
- El código de entidad del CHIP termina en el código DIVIPOLA: '210005400' → '05400'.
"""

from collections import defaultdict
from typing import Any

from municipios.comun import periodos
from municipios.comun.contexto import Contexto, Resultado
from municipios.comun.modelos import Observacion

GASTOS = "4f7r-epif"
PROGRAMACION = "d9mu-h6ar"
INGRESOS = "9axr-9gnb"
DESDE = "20230101"  # CUIPO reemplazó al FUT en 2023
FILTRO = f"ambito_nombre IN ('Municipios', 'Bogotá') AND periodo >= '{DESDE}'"

# (cuenta, campo) -> indicador
CUENTAS_GASTOS = {
    ("2", "compromisos"): "gasto_compromisos",
    ("2", "obligaciones"): "gasto_obligaciones",
    ("2", "pagos"): "gasto_pagos",
    ("2.1", "compromisos"): "gasto_funcionamiento",
    ("2.2", "compromisos"): "gasto_servicio_deuda",
    ("2.3", "compromisos"): "gasto_inversion",
}
CUENTAS_INGRESOS = {
    "1": "ingresos_total",
    "1.1": "ingresos_corrientes",
    "1.1.01": "ingresos_tributarios",
    "1.1.02": "ingresos_no_tributarios",
    "1.1.02.06": "transferencias_corrientes",
    "1.2": "recursos_capital",
}
FUENTES = {
    GASTOS: "cgr_cuipo_gastos",
    PROGRAMACION: "cgr_cuipo_programacion",
    INGRESOS: "cgr_cuipo_ingresos",
}
INDICADORES = (
    *CUENTAS_GASTOS.values(),
    "presupuesto_gastos_definitivo",
    *CUENTAS_INGRESOS.values(),
)


def _lista(cuentas: Any) -> str:
    return ", ".join(f"'{c}'" for c in sorted(set(cuentas)))


def descargar(contexto: Contexto) -> dict[str, list[dict[str, Any]]]:
    """Tres consultas agregadas en la API: una por conjunto."""
    consultar = contexto.cliente.consultar
    refrescar = contexto.refrescar
    cuentas_gasto = _lista(c for c, _ in CUENTAS_GASTOS)
    return {
        GASTOS: consultar(
            GASTOS,
            select="periodo, codigo_entidad, cuenta, sum(compromisos) AS compromisos,"
            " sum(obligaciones) AS obligaciones, sum(pagos) AS pagos",
            where=f"{FILTRO} AND cod_vigencia_del_gasto = '1' AND cuenta IN ({cuentas_gasto})",
            group="periodo, codigo_entidad, cuenta",
            refrescar=refrescar,
        ),
        PROGRAMACION: consultar(
            PROGRAMACION,
            select="periodo, codigo_entidad, cuenta, sum(apropiacion_definitiva) AS definitiva",
            where=f"{FILTRO} AND cod_vigencia_del_gasto = '1' AND cuenta = '2'",
            group="periodo, codigo_entidad, cuenta",
            refrescar=refrescar,
        ),
        INGRESOS: consultar(
            INGRESOS,
            select="periodo, codigo_entidad, cuenta, sum(total_recaudo) AS recaudo",
            where=f"{FILTRO} AND cuenta IN ({_lista(CUENTAS_INGRESOS)})",
            group="periodo, codigo_entidad, cuenta",
            refrescar=refrescar,
        ),
    }


# Municipios creados después del esquema de códigos del CHIP: su código no termina en el DIVIPOLA.
CODIGOS_CHIP_ESPECIALES = {
    "923270346": "19300",  # Guachené
    "923271475": "23682",  # San José de Uré
    "923271489": "13490",  # Norosí
    "923271490": "23815",  # Tuchín
    "923272927": "94343",  # Barrancominas
    "923273478": "27493",  # Nuevo Belén de Bajirá
}


def divipola(codigo_entidad: str) -> str:
    """'210005400' -> '05400' (salvo los códigos especiales de municipios nuevos)."""
    codigo = codigo_entidad.strip()
    return CODIGOS_CHIP_ESPECIALES.get(codigo, codigo[-5:])


def _ultimo_corte_por_anio(filas: list[dict[str, Any]]) -> dict[tuple[str, int], str]:
    """(entidad, año) -> período más reciente reportado ese año."""
    cortes: dict[tuple[str, int], str] = {}
    for fila in filas:
        clave = (fila["codigo_entidad"], int(fila["periodo"][:4]))
        cortes[clave] = max(cortes.get(clave, ""), fila["periodo"])
    return cortes


def _observaciones(
    filas: list[dict[str, Any]],
    conjunto: str,
    indicador_de: dict[tuple[str, str], str],
    codigos: set[str],
    sin_cruce: dict[str, str],
) -> list[Observacion]:
    """Convierte filas agregadas en observaciones, usando solo el último corte de cada año.

    `indicador_de` mapea (cuenta, campo) -> indicador.
    """
    cortes = _ultimo_corte_por_anio(filas)
    valores: dict[tuple[str, str, str], float] = defaultdict(float)
    for fila in filas:
        entidad, corte = fila["codigo_entidad"], fila["periodo"]
        if cortes[(entidad, int(corte[:4]))] != corte:
            continue
        codigo = divipola(entidad)
        if codigo not in codigos:
            sin_cruce[entidad] = codigo
            continue
        per = periodos.anual(int(corte[:4]), int(corte[4:6]))
        for (cuenta, campo), indicador in indicador_de.items():
            if fila["cuenta"] == cuenta and fila.get(campo) not in (None, ""):
                valores[(codigo, indicador, per)] += float(fila[campo])
    return [
        Observacion(codigo, indicador, round(valor), per, FUENTES[conjunto])
        for (codigo, indicador, per), valor in sorted(valores.items())
    ]


def normalizar(datos: dict[str, list[dict[str, Any]]], codigos: set[str]) -> Resultado:
    sin_cruce: dict[str, str] = {}
    observaciones = [
        *_observaciones(datos[GASTOS], GASTOS, CUENTAS_GASTOS, codigos, sin_cruce),
        *_observaciones(
            datos[PROGRAMACION],
            PROGRAMACION,
            {("2", "definitiva"): "presupuesto_gastos_definitivo"},
            codigos,
            sin_cruce,
        ),
        *_observaciones(
            datos[INGRESOS],
            INGRESOS,
            {(cuenta, "recaudo"): ind for cuenta, ind in CUENTAS_INGRESOS.items()},
            codigos,
            sin_cruce,
        ),
    ]
    return Resultado(observaciones, sin_cruce=sin_cruce)


def ejecutar(contexto: Contexto) -> Resultado:
    return normalizar(descargar(contexto), contexto.codigos)
