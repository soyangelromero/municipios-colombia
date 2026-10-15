"""Datos que entran al índice: los publicados por las fuentes y los calculados (tasas, %).

Cada dato lleva su valor para mostrar, el valor que se usa para puntuar (por ejemplo, la tasa
suavizada o el porcentaje topado en 100), su período y las fuentes que lo respaldan.
"""

from collections import defaultdict
from dataclasses import dataclass

from municipios.comun.modelos import Municipio
from municipios.indice.almacen import Almacen, clave_periodo

DELITOS = {"tasa_homicidios": "homicidios", "tasa_hurto_personas": "hurto_personas"}
DIRECTOS = (
    "ita_autodiagnostico",
    "ita_auditoria",
    "furag_publicacion_contractual",
    "furag_estado_abierto",
    "furag_desempeno_institucional",
    "furag_control_interno",
    "indice_gobierno_digital",
    "educacion_cobertura_neta",
    "educacion_desercion",
    "mdm_puntaje",
    "superficie_km2",
)


@dataclass(frozen=True, slots=True)
class Dato:
    valor: float
    periodo: str
    fuentes: tuple[str, ...]
    para_puntaje: float | None = None  # si es None, se puntúa con `valor`

    @property
    def puntuable(self) -> float:
        return self.valor if self.para_puntaje is None else self.para_puntaje


def _anio(periodo: str) -> int:
    return clave_periodo(periodo)[0]


class Calculadora:
    def __init__(
        self,
        almacen: Almacen,
        municipios: dict[str, Municipio],
        grupos: dict[str, str],
        anio_actual: int,
        antiguedad_maxima: int,
        suavizado_poblacion: float,
    ) -> None:
        self.a = almacen
        self.municipios = municipios
        self.grupos = grupos
        self.anio_actual = anio_actual
        self.antiguedad_maxima = antiguedad_maxima
        self.suavizado = suavizado_poblacion
        self.ref = {
            ind: almacen.anio_referencia(ind)
            for ind in ("gasto_compromisos", "contratos_numero", "homicidios", "hurto_personas")
        }

    # --- utilidades ------------------------------------------------------------------------
    def _vigente(self, periodo: str) -> bool:
        return _anio(periodo) >= self.anio_actual - self.antiguedad_maxima

    def _poblacion(self, codigo: str, anio: int) -> float | None:
        o = self.a.anual(codigo, "poblacion", anio)
        return float(o.valor) if o and float(o.valor) > 0 else None

    def _anual(self, codigo: str, indicador: str, anio: int | None) -> float | None:
        if anio is None:
            return None
        o = self.a.anual(codigo, indicador, anio)
        return float(o.valor) if o is not None else None

    # --- cálculo ---------------------------------------------------------------------------
    def calcular(self) -> dict[str, dict[str, Dato]]:
        datos: dict[str, dict[str, Dato]] = {codigo: {} for codigo in self.municipios}
        for codigo in self.municipios:
            d = datos[codigo]
            self._directos(codigo, d)
            self._territorio(codigo, d)
            self._finanzas(codigo, d)
            self._contratacion(codigo, d)
            self._salud(codigo, d)
        self._delitos(datos)
        return datos

    def _directos(self, codigo: str, d: dict[str, Dato]) -> None:
        for indicador in DIRECTOS:
            o = self.a.ultimo(codigo, indicador)
            if o is not None and self._vigente(o.periodo):
                d[indicador] = Dato(float(o.valor), o.periodo, (o.fuente,))

    def _territorio(self, codigo: str, d: dict[str, Dato]) -> None:
        poblacion = self._poblacion(codigo, self.anio_actual)
        if poblacion is None:
            return
        d["poblacion"] = Dato(poblacion, str(self.anio_actual), ("dane_proyecciones_poblacion",))
        if "superficie_km2" in d and d["superficie_km2"].valor > 0:
            d["densidad"] = Dato(
                round(poblacion / d["superficie_km2"].valor, 1),
                str(self.anio_actual),
                ("dane_proyecciones_poblacion", "dane_mgn"),
            )

    def _finanzas(self, codigo: str, d: dict[str, Dato]) -> None:
        anio = self.ref["gasto_compromisos"]
        if anio is None:
            return
        per = str(anio)
        compromisos = self._anual(codigo, "gasto_compromisos", anio)
        d["reporta_cuipo"] = Dato(100.0 if compromisos else 0.0, per, ("cgr_cuipo_gastos",))
        if not compromisos:
            return
        inversion = self._anual(codigo, "gasto_inversion", anio)
        if inversion is not None:
            d["pct_inversion"] = Dato(
                round(100 * inversion / compromisos, 2), per, ("cgr_cuipo_gastos",)
            )
        definitivo = self._anual(codigo, "presupuesto_gastos_definitivo", anio)
        if definitivo:
            ejecucion = round(100 * compromisos / definitivo, 2)
            d["ejecucion_presupuestal"] = Dato(
                ejecucion, per, ("cgr_cuipo_gastos", "cgr_cuipo_programacion"), min(ejecucion, 100)
            )
        poblacion = self._poblacion(codigo, anio)
        if poblacion:
            d["gasto_por_habitante"] = Dato(
                round(compromisos / poblacion),
                per,
                ("cgr_cuipo_gastos", "dane_proyecciones_poblacion"),
            )
            tributarios = self._anual(codigo, "ingresos_tributarios", anio)
            if tributarios is not None:
                d["ingresos_tributarios_por_habitante"] = Dato(
                    round(tributarios / poblacion),
                    per,
                    ("cgr_cuipo_ingresos", "dane_proyecciones_poblacion"),
                )
        ingresos = self._anual(codigo, "ingresos_total", anio)
        transferencias = self._anual(codigo, "transferencias_corrientes", anio)
        if ingresos and transferencias is not None:
            d["dependencia_transferencias"] = Dato(
                round(100 * transferencias / ingresos, 2), per, ("cgr_cuipo_ingresos",)
            )

    def _contratacion(self, codigo: str, d: dict[str, Dato]) -> None:
        anio = self.ref["contratos_numero"]
        if anio is None:
            return
        per = str(anio)
        numero = self._anual(codigo, "contratos_numero", anio) or 0
        d["publica_secop"] = Dato(100.0 if numero > 0 else 0.0, per, ("cce_secop2_contratos",))
        if numero <= 0:
            return
        valor = self._anual(codigo, "contratos_valor", anio) or 0
        d["contratos_numero"] = Dato(numero, per, ("cce_secop2_contratos",))
        d["contratos_valor"] = Dato(valor, per, ("cce_secop2_contratos",))
        directa = self._anual(codigo, "contratos_directa_valor", anio) or 0
        if valor > 0:
            d["pct_contratacion_directa"] = Dato(
                round(100 * directa / valor, 2), per, ("cce_secop2_contratos",)
            )

    def _salud(self, codigo: str, d: dict[str, Dato]) -> None:
        sub = self.a.ultimo(codigo, "afiliados_subsidiado")
        con = self.a.ultimo(codigo, "afiliados_contributivo")
        if sub is None and con is None:
            return
        periodo = (sub or con).periodo
        poblacion = self._poblacion(codigo, _anio(periodo))
        if not poblacion:
            return
        total = (float(sub.valor) if sub else 0) + (float(con.valor) if con else 0)
        cobertura = round(100 * total / poblacion, 2)
        d["cobertura_salud"] = Dato(
            cobertura,
            periodo,
            ("adres_bdua_subsidiado", "adres_bdua_contributivo", "dane_proyecciones_poblacion"),
            min(cobertura, 100),
        )

    def _delitos(self, datos: dict[str, dict[str, Dato]]) -> None:
        """Tasas por 100.000 habitantes, promedio de 3 años, suavizadas hacia la de su grupo.

        tasa suavizada = (hechos + tasa_grupo * P0 * 3 / 100.000) / ((población + P0 * 3) / 100.000)
        donde P0 es `suavizado_poblacion`: un municipio grande casi no cambia; uno de 2.000
        habitantes con un hecho aislado no queda como el peor del país.
        """
        for tasa, indicador in DELITOS.items():
            fin = self.ref[indicador]
            if fin is None:
                continue
            anios = range(fin - 2, fin + 1)
            per = f"{anios[0]}-{anios[-1]}"
            crudos: dict[str, tuple[float, float]] = {}
            por_grupo: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
            for codigo in self.municipios:
                hechos = [self._anual(codigo, indicador, a) for a in anios]
                poblaciones = [self._poblacion(codigo, a) for a in anios]
                if None in hechos or None in poblaciones:
                    continue
                total_hechos, total_pob = sum(hechos), sum(poblaciones)
                crudos[codigo] = (total_hechos, total_pob)
                grupo = self.grupos.get(codigo)
                if grupo:
                    por_grupo[grupo][0] += total_hechos
                    por_grupo[grupo][1] += total_pob
            for codigo, (hechos, poblacion) in crudos.items():
                tasa_cruda = 1e5 * hechos / poblacion
                g = por_grupo.get(self.grupos.get(codigo, ""))
                tasa_grupo = 1e5 * g[0] / g[1] if g and g[1] else tasa_cruda
                extra = self.suavizado * len(anios)
                suavizada = (hechos + tasa_grupo * extra / 1e5) / ((poblacion + extra) / 1e5)
                datos[codigo][tasa] = Dato(
                    round(tasa_cruda, 2),
                    per,
                    (f"mindefensa_{indicador}", "dane_proyecciones_poblacion"),
                    round(suavizada, 4),
                )
