"""Coherencia entre los datos pedibles de la web y los criterios del relevamiento."""

import re
from pathlib import Path

from municipios.relevamiento.criterios import CRITERIOS

RAIZ = Path(__file__).resolve().parents[2]


def test_los_datos_pedibles_son_los_criterios_del_relevamiento():
    js = (RAIZ / "web" / "assets" / "js" / "pedidos.js").read_text(encoding="utf-8")
    bloque = re.search(r"export const CRITERIOS = \{(.*?)\n\};", js, re.S)
    assert bloque, "pedidos.js ya no exporta CRITERIOS"
    claves = set(re.findall(r"^\s+(\w+):", bloque.group(1), re.M))
    assert claves == {c.id for c in CRITERIOS}
    # El servidor solo acepta claves en minúscula, dígitos y guion bajo.
    assert all(re.fullmatch(r"[a-z0-9_]{1,60}", c) for c in claves)
