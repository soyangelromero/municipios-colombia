"""Cálculo del índice a partir de los datos y de pipeline/config/indice.toml.

1. Puntaje de cada componente (0-100): absoluto, o percentil entre pares del mismo grupo DNP.
2. Puntaje de cada pilar: promedio ponderado de sus componentes con dato. El pilar vale si cubre
   al menos `cobertura_minima_pilar` de su peso.
3. Índice: promedio ponderado de los pilares válidos (con sus pesos re-normalizados). Exige el
   pilar de transparencia y al menos `pilares_minimos` pilares. Se topa si no hay cuentas.
4. Puestos (nacional, departamental, entre pares) y rango de puestos con pesos ±N puntos.
"""

import tomllib
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from municipios.comun.modelos import Municipio
from municipios.config import DIR_CONFIG
from municipios.indice.derivados import Dato


@dataclass(frozen=True, slots=True)
class Componente:
    id: str
    nombre: str
    peso: float
    puntaje: str  # absoluto | pares
    sentido: str  # mayor_mejor | menor_mejor
    si_falta: float | None = None  # puntaje sin dato (obligaciones); None = repartir el peso


@dataclass(frozen=True, slots=True)
class Pilar:
    id: str
    nombre: str
    peso: float
    descripcion: str
    componentes: tuple[Componente, ...]


@dataclass(frozen=True)
class Config:
    version: str
    pilares: tuple[Pilar, ...]
    semaforo: dict[str, float]
    reglas: dict[str, float]
    contexto: tuple[str, ...]
    crudo: dict[str, Any] = field(repr=False, default_factory=dict)

    def pilar(self, id_: str) -> Pilar:
        return next(p for p in self.pilares if p.id == id_)


def cargar_config(ruta: Path = DIR_CONFIG / "indice.toml") -> Config:
    with ruta.open("rb") as f:
        crudo = tomllib.load(f)
    pilares = tuple(
        Pilar(
            id=id_,
            nombre=p["nombre"],
            peso=float(p["peso"]),
            descripcion=p.get("descripcion", ""),
            componentes=tuple(
                Componente(
                    id=c["id"],
                    nombre=c["nombre"],
                    peso=float(c["peso"]),
                    puntaje=c["puntaje"],
                    sentido=c["sentido"],
                    si_falta=None if "si_falta" not in c else float(c["si_falta"]),
                )
                for c in p["componentes"]
            ),
        )
        for id_, p in crudo["pilares"].items()
    )
    if abs(sum(p.peso for p in pilares) - 100) > 1e-9:
        raise ValueError("Los pesos de los pilares deben sumar 100")
    return Config(
        version=crudo["version"],
        pilares=pilares,
        semaforo=crudo["semaforo"],
        reglas=crudo["reglas"],
        contexto=tuple(crudo.get("contexto", {}).get("indicadores", [])),
        crudo=crudo,
    )


def semaforo(valor: float | None, config: Config) -> str | None:
    if valor is None:
        return None
    if valor < config.semaforo["rojo_menor_a"]:
        return "rojo"
    return "verde" if valor >= config.semaforo["verde_desde"] else "amarillo"


def percentiles(valores: dict[str, float], sentido: str) -> dict[str, float]:
    """Percentil 0-100 de cada valor dentro del conjunto (empates reciben el promedio)."""
    if len(valores) == 1:
        return dict.fromkeys(valores, 50.0)
    signo = 1 if sentido == "mayor_mejor" else -1
    ordenados = sorted(valores.items(), key=lambda kv: signo * kv[1])
    resultado: dict[str, float] = {}
    i = 0
    while i < len(ordenados):
        j = i
        while j + 1 < len(ordenados) and ordenados[j + 1][1] == ordenados[i][1]:
            j += 1
        rango_medio = (i + j) / 2
        for k in range(i, j + 1):
            resultado[ordenados[k][0]] = round(100 * rango_medio / (len(ordenados) - 1), 2)
        i = j + 1
    return resultado


def puntajes_de_componentes(
    datos: dict[str, dict[str, Dato]],
    elegibles: set[str],
    grupos: dict[str, str],
    config: Config,
) -> dict[str, dict[str, float]]:
    """Puntaje 0-100 de cada componente para cada municipio elegible."""
    puntajes: dict[str, dict[str, float]] = defaultdict(dict)
    minimo = int(config.reglas["pares_minimos"])
    for pilar in config.pilares:
        for comp in pilar.componentes:
            con_dato = {c: datos[c][comp.id].puntuable for c in elegibles if comp.id in datos[c]}
            if comp.puntaje == "absoluto":
                for codigo, valor in con_dato.items():
                    v = max(0.0, min(100.0, valor))
                    puntajes[codigo][comp.id] = v if comp.sentido == "mayor_mejor" else 100 - v
            else:
                _percentiles_por_grupo(puntajes, comp, con_dato, grupos, minimo)
            if comp.si_falta is not None:
                for codigo in elegibles - set(con_dato):
                    puntajes[codigo][comp.id] = comp.si_falta
    return puntajes


def _percentiles_por_grupo(
    puntajes: dict[str, dict[str, float]],
    comp: Componente,
    con_dato: dict[str, float],
    grupos: dict[str, str],
    minimo: int,
) -> None:
    """Percentil dentro del grupo; los grupos con menos de `minimo` se comparan con el país."""
    por_grupo: dict[str, dict[str, float]] = defaultdict(dict)
    for codigo, valor in con_dato.items():
        por_grupo[grupos.get(codigo, "")][codigo] = valor
    for grupo, valores in por_grupo.items():
        referencia = valores if grupo and len(valores) >= minimo else con_dato
        pct = percentiles(referencia, comp.sentido)
        for codigo in valores:
            puntajes[codigo][comp.id] = pct[codigo]


def _pilares(puntajes: dict[str, float], config: Config) -> dict[str, dict[str, float]]:
    resultado = {}
    for pilar in config.pilares:
        total = sum(c.peso for c in pilar.componentes)
        con_dato = [c for c in pilar.componentes if c.id in puntajes]
        peso_con_dato = sum(c.peso for c in con_dato)
        cobertura = peso_con_dato / total
        puntaje = (
            sum(c.peso * puntajes[c.id] for c in con_dato) / peso_con_dato if con_dato else None
        )
        resultado[pilar.id] = {
            "puntaje": None if puntaje is None else round(puntaje, 1),
            "cobertura": round(cobertura, 2),
            "valido": puntaje is not None and cobertura >= config.reglas["cobertura_minima_pilar"],
        }
    return resultado


def _combinar(pilares: dict[str, dict[str, Any]], pesos: dict[str, float]) -> float | None:
    validos = {p: v for p, v in pilares.items() if v["valido"]}
    total = sum(pesos[p] for p in validos)
    if not total:
        return None
    return sum(pesos[p] * v["puntaje"] for p, v in validos.items()) / total


def _valor_indice(
    pilares: dict[str, dict[str, Any]], pesos: dict[str, float], sin_cuentas: bool, config: Config
) -> float | None:
    validos = [p for p, v in pilares.items() if v["valido"]]
    if "T" not in validos or len(validos) < config.reglas["pilares_minimos"]:
        return None
    valor = _combinar(pilares, pesos)
    if valor is not None and sin_cuentas:
        valor = min(valor, config.reglas["tope_sin_cuentas"])
    return None if valor is None else round(valor, 1)


def _puestos(valores: dict[str, float]) -> dict[str, int]:
    """Puesto 1 = mejor. Empates comparten puesto (1, 2, 2, 4…)."""
    ordenados = sorted(valores.items(), key=lambda kv: -kv[1])
    puestos: dict[str, int] = {}
    for i, (codigo, valor) in enumerate(ordenados):
        anterior = ordenados[i - 1] if i else None
        puestos[codigo] = puestos[anterior[0]] if anterior and anterior[1] == valor else i + 1
    return puestos


def pesos_alternativos(config: Config) -> list[tuple[str, dict[str, float]]]:
    """Escenarios con el peso de cada pilar ± N puntos y el resto re-escalado a 100."""
    base = {p.id: p.peso for p in config.pilares}
    delta = config.reglas["sensibilidad_puntos"]
    escenarios = []
    for pilar in base:
        for signo in (1, -1):
            nuevo = base[pilar] + signo * delta
            if not 0 < nuevo < 100:
                continue
            resto = 100 - base[pilar]
            pesos = {
                p: (nuevo if p == pilar else w * (100 - nuevo) / resto) for p, w in base.items()
            }
            escenarios.append((f"{pilar} {'+' if signo > 0 else '-'}{delta:g}", pesos))
    return escenarios


def calcular(
    datos: dict[str, dict[str, Dato]],
    municipios: dict[str, Municipio],
    grupos: dict[str, str],
    config: Config,
) -> dict[str, dict[str, Any]]:
    """Resultado por municipio: índice, semáforo, pilares, componentes, puestos y rango."""
    elegibles = {c for c, m in municipios.items() if m.tipo == "municipio" and c in grupos}
    puntajes = puntajes_de_componentes(datos, elegibles, grupos, config)
    pesos = {p.id: p.peso for p in config.pilares}

    resultado: dict[str, dict[str, Any]] = {}
    for codigo, municipio in municipios.items():
        fila: dict[str, Any] = {
            "indice": None,
            "semaforo": None,
            "grupo": grupos.get(codigo),
            "pilares": {},
            "componentes": {},
            "tope": False,
        }
        if codigo not in elegibles:
            fila["motivo_sin_indice"] = (
                "Área no municipalizada: no tiene alcaldía."
                if municipio.tipo == "area_no_municipalizada"
                else "Lo administra el departamento de San Andrés y Providencia."
                if municipio.tipo == "isla"
                else "Sin grupo de capacidades del DNP."
            )
            resultado[codigo] = fila
            continue
        pilares = _pilares(puntajes[codigo], config)
        sin_cuentas = datos[codigo].get("reporta_cuipo", Dato(0, "", ())).valor == 0
        valor = _valor_indice(pilares, pesos, sin_cuentas, config)
        fila.update(
            indice=valor,
            semaforo=semaforo(valor, config),
            pilares=pilares,
            tope=bool(valor is not None and sin_cuentas),
            componentes={
                c.id: {
                    "puntaje": round(puntajes[codigo][c.id], 1)
                    if c.id in puntajes[codigo]
                    else None
                }
                for p in config.pilares
                for c in p.componentes
            },
        )
        if valor is None:
            validos = [p for p, v in pilares.items() if v["valido"]]
            fila["motivo_sin_indice"] = (
                "Faltan datos de transparencia."
                if "T" not in validos
                else f"Solo {len(validos)} de {len(pilares)} pilares tienen datos suficientes."
            )
        resultado[codigo] = fila

    _asignar_puestos(resultado, municipios, config, puntajes, datos)
    return resultado


def _asignar_puestos(
    resultado: dict[str, dict[str, Any]],
    municipios: dict[str, Municipio],
    config: Config,
    puntajes: dict[str, dict[str, float]],
    datos: dict[str, dict[str, Dato]],
) -> None:
    con_indice = {c: f["indice"] for c, f in resultado.items() if f["indice"] is not None}
    nacional = _puestos(con_indice)
    por_dep: dict[str, dict[str, float]] = defaultdict(dict)
    por_grupo: dict[str, dict[str, float]] = defaultdict(dict)
    for codigo, valor in con_indice.items():
        por_dep[municipios[codigo].departamento_codigo][codigo] = valor
        por_grupo[resultado[codigo]["grupo"]][codigo] = valor
    puestos_dep = {c: p for g in por_dep.values() for c, p in _puestos(g).items()}
    puestos_grupo = {c: p for g in por_grupo.values() for c, p in _puestos(g).items()}

    # Sensibilidad: puesto nacional en cada escenario de pesos.
    rangos: dict[str, list[int]] = {c: [nacional[c], nacional[c]] for c in con_indice}
    for _, pesos in pesos_alternativos(config):
        valores = {}
        for codigo in con_indice:
            sin_cuentas = datos[codigo].get("reporta_cuipo", Dato(0, "", ())).valor == 0
            v = _valor_indice(_pilares(puntajes[codigo], config), pesos, sin_cuentas, config)
            if v is not None:
                valores[codigo] = v
        for codigo, puesto in _puestos(valores).items():
            rangos[codigo][0] = min(rangos[codigo][0], puesto)
            rangos[codigo][1] = max(rangos[codigo][1], puesto)

    for codigo in con_indice:
        dep = municipios[codigo].departamento_codigo
        grupo = resultado[codigo]["grupo"]
        resultado[codigo]["puesto"] = {
            "nacional": nacional[codigo],
            "nacional_de": len(con_indice),
            "departamento": puestos_dep[codigo],
            "departamento_de": len(por_dep[dep]),
            "grupo": puestos_grupo[codigo],
            "grupo_de": len(por_grupo[grupo]),
        }
        resultado[codigo]["rango_puestos"] = rangos[codigo]
