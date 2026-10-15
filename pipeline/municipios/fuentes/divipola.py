"""DIVIPOLA (DANE): lista oficial de municipios, islas y áreas no municipalizadas."""

from collections import Counter
from typing import Any

from municipios.comun.modelos import Municipio
from municipios.comun.socrata import ClienteSocrata
from municipios.comun.textos import nombre_legible, slug

FUENTE = "dane_divipola"
CONJUNTO = "gdxc-w37w"

# Nombre corto para mostrar y slug estable de cada departamento (ver ADR 0002).
DEPARTAMENTOS: dict[str, tuple[str, str]] = {
    "05": ("Antioquia", "antioquia"),
    "08": ("Atlántico", "atlantico"),
    "11": ("Bogotá D.C.", "bogota"),
    "13": ("Bolívar", "bolivar"),
    "15": ("Boyacá", "boyaca"),
    "17": ("Caldas", "caldas"),
    "18": ("Caquetá", "caqueta"),
    "19": ("Cauca", "cauca"),
    "20": ("Cesar", "cesar"),
    "23": ("Córdoba", "cordoba"),
    "25": ("Cundinamarca", "cundinamarca"),
    "27": ("Chocó", "choco"),
    "41": ("Huila", "huila"),
    "44": ("La Guajira", "la-guajira"),
    "47": ("Magdalena", "magdalena"),
    "50": ("Meta", "meta"),
    "52": ("Nariño", "narino"),
    "54": ("Norte de Santander", "norte-de-santander"),
    "63": ("Quindío", "quindio"),
    "66": ("Risaralda", "risaralda"),
    "68": ("Santander", "santander"),
    "70": ("Sucre", "sucre"),
    "73": ("Tolima", "tolima"),
    "76": ("Valle del Cauca", "valle-del-cauca"),
    "81": ("Arauca", "arauca"),
    "85": ("Casanare", "casanare"),
    "86": ("Putumayo", "putumayo"),
    "88": ("San Andrés y Providencia", "san-andres"),
    "91": ("Amazonas", "amazonas"),
    "94": ("Guainía", "guainia"),
    "95": ("Guaviare", "guaviare"),
    "97": ("Vaupés", "vaupes"),
    "99": ("Vichada", "vichada"),
}

# Excepciones de nombre y slug para municipios puntuales.
NOMBRES_ESPECIALES = {"11001": "Bogotá D.C."}
SLUGS_ESPECIALES = {"11001": "bogota"}

TIPOS = {
    "Municipio": "municipio",
    "Isla": "isla",
    "Área no municipalizada": "area_no_municipalizada",
}


def descargar(cliente: ClienteSocrata, refrescar: bool = False) -> list[dict[str, Any]]:
    return cliente.consultar(CONJUNTO, order="cod_mpio", refrescar=refrescar)


def normalizar(filas: list[dict[str, Any]]) -> list[Municipio]:
    """Convierte las filas del DANE en municipios con nombre legible y slug único.

    Falla con ValueError si aparece un código mal formado, un tipo o departamento desconocido,
    o un slug repetido: son señales de que la fuente cambió y hay que revisarla.
    """
    municipios = [_municipio(fila) for fila in filas]
    _verificar_unicos(municipios)
    return sorted(municipios, key=lambda m: m.divipola)


def _municipio(fila: dict[str, Any]) -> Municipio:
    codigo = str(fila["cod_mpio"]).strip()
    if len(codigo) != 5 or not codigo.isdigit():
        raise ValueError(f"Código DIVIPOLA inválido: {codigo!r}")
    cod_dep = codigo[:2]
    if cod_dep not in DEPARTAMENTOS:
        raise ValueError(f"Departamento desconocido {cod_dep!r} en {codigo}")
    tipo = TIPOS.get(fila.get("tipo_municipio", ""))
    if tipo is None:
        raise ValueError(f"Tipo desconocido {fila.get('tipo_municipio')!r} en {codigo}")

    departamento, dep_slug = DEPARTAMENTOS[cod_dep]
    oficial = " ".join(str(fila["nom_mpio"]).split())
    nombre = NOMBRES_ESPECIALES.get(codigo, nombre_legible(oficial))
    return Municipio(
        divipola=codigo,
        nombre=nombre,
        nombre_oficial=oficial,
        departamento_codigo=cod_dep,
        departamento=departamento,
        departamento_slug=dep_slug,
        tipo=tipo,
        slug=SLUGS_ESPECIALES.get(codigo, f"{dep_slug}--{slug(nombre)}"),
        lat=_coordenada(fila.get("latitud")),
        lon=_coordenada(fila.get("longitud")),
    )


def _coordenada(texto: Any) -> float | None:
    """El DANE publica coordenadas con coma decimal: '-75,581775'."""
    if texto in (None, ""):
        return None
    return float(str(texto).replace(",", "."))


def _verificar_unicos(municipios: list[Municipio]) -> None:
    for campo in ("divipola", "slug"):
        conteo = Counter(getattr(m, campo) for m in municipios)
        repetidos = sorted(valor for valor, veces in conteo.items() if veces > 1)
        if repetidos:
            raise ValueError(f"Valores de {campo} repetidos: {repetidos}")
