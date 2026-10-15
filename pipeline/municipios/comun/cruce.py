"""Cruce de nombres de departamento y municipio con códigos DIVIPOLA.

Algunas fuentes (ITA, ADRES) no traen el código del municipio, solo su nombre, y cada una lo
escribe distinto: «BOGOTA D.C.», «CARTAGENA» o «CARTAGENA DE INDIAS», «SAN JOSE DE CUCUTA»…
El cruce prueba, en orden: coincidencia exacta normalizada, alias conocidos, coincidencia de
palabras sin ambigüedad y, por último, un parecido muy alto. Lo que no cruza se reporta.
"""

import re
from collections.abc import Iterable
from difflib import get_close_matches

from municipios.comun.modelos import Municipio
from municipios.comun.textos import sin_tildes

PARECIDO_MINIMO = 0.88

# Nombres de departamento que usan las fuentes y no salen de normalizar el oficial.
ALIAS_DEPARTAMENTOS = {
    "BOGOTA": "11",
    "BOGOTA D C": "11",
    "DISTRITO CAPITAL": "11",
    "DISTRITO CAPITAL DE BOGOTA": "11",
    "BOGOTA DISTRITO CAPITAL": "11",
    "SAN ANDRES": "88",
    "SAN ANDRES PROV": "88",  # ITA: «SAN ANDRES,  PROV.»
    "SAN ANDRES PROVIDENCIA Y SANTA CATALINA": "88",
    "ARCHIPIELAGO DE SAN ANDRES": "88",
    "VALLE": "76",
    "NORTE SANTANDER": "54",
    "GUAJIRA": "44",
}

# Variantes de nombres de municipio (clave normalizada -> DIVIPOLA) que el cruce automático no
# resuelve solo. Cada alias vale solo dentro del departamento de su código. Agregar aquí, con un
# comentario, cada caso que aparezca como «sin cruce» y se pueda verificar.
ALIAS_MUNICIPIOS: dict[str, str] = {
    "BOGOTA DISTRITO CAPITAL": "11001",  # ITA: «BOGOTÁ, DISTRITO CAPITAL»
    "SAN PEDRO": "05664",  # Antioquia: San Pedro de los Milagros (ITA y ADRES)
    "MOMPOS": "13468",  # Santa Cruz de Mompox
    "TUTASA": "15839",  # Tutazá
    "ITSMINA": "27361",  # Istmina
    "S ANTONIO TEQUENDAMA": "25645",  # San Antonio del Tequendama
    "LEYVA": "52405",  # Leiva
    "PALMAS SOCORRO": "68524",  # Palmas del Socorro
    "GUAYABAL": "73055",  # Armero (su cabecera es Guayabal)
}


def clave(texto: str) -> str:
    """'Bogotá, D.C.' -> 'BOGOTA D C'. Sin tildes, mayúsculas y solo letras y números.

    Corrige además la «Ñ» mal codificada como «¥» (ADRES publica «NARI¥O»).
    """
    texto = texto.replace("¥", "Ñ")
    return " ".join(re.sub(r"[^A-Z0-9]+", " ", sin_tildes(texto).upper()).split())


def _sin_parentesis(texto: str) -> str:
    """'PIENDAMO (TUNIA)' -> 'PIENDAMO'."""
    return re.sub(r"\(.*?\)", " ", texto)


class Cruce:
    def __init__(self, municipios: Iterable[Municipio]) -> None:
        self.departamentos: dict[str, str] = dict(ALIAS_DEPARTAMENTOS)
        self.por_departamento: dict[str, dict[str, str]] = {}
        for m in municipios:
            self.departamentos.setdefault(clave(m.departamento), m.departamento_codigo)
            nombres = self.por_departamento.setdefault(m.departamento_codigo, {})
            for nombre in (m.nombre, m.nombre_oficial):
                nombres.setdefault(clave(nombre), m.divipola)
        for alias, codigo in ALIAS_MUNICIPIOS.items():
            self.por_departamento.setdefault(codigo[:2], {})[alias] = codigo

    def departamento(self, texto: str) -> str | None:
        k = clave(texto)
        if k in self.departamentos:
            return self.departamentos[k]
        parecidos = get_close_matches(k, self.departamentos, n=1, cutoff=PARECIDO_MINIMO)
        return self.departamentos[parecidos[0]] if parecidos else None

    def municipio(self, departamento: str, municipio: str) -> str | None:
        """Código DIVIPOLA del municipio, o None si no hay una coincidencia segura."""
        cod_dep = self.departamento(departamento)
        if cod_dep is None:
            return None
        nombres = self.por_departamento.get(cod_dep, {})
        k = clave(_sin_parentesis(municipio)) or clave(municipio)
        if k in nombres:
            return nombres[k]

        # Coincidencia de palabras: «CARTAGENA» ⊂ «CARTAGENA DE INDIAS», «CUCUTA» ⊂ «SAN JOSE DE
        # CUCUTA». Solo vale si hay un único candidato.
        palabras = set(k.split())
        candidatos = {
            codigo
            for nombre, codigo in nombres.items()
            if palabras <= set(nombre.split()) or set(nombre.split()) <= palabras
        }
        if len(candidatos) == 1:
            return candidatos.pop()

        parecidos = get_close_matches(k, nombres, n=2, cutoff=PARECIDO_MINIMO)
        if len(parecidos) == 1 or (
            len(parecidos) == 2 and nombres[parecidos[0]] == nombres[parecidos[1]]
        ):
            return nombres[parecidos[0]]
        return None
