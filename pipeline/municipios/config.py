"""Rutas del proyecto y lectura del archivo .env (sin dependencias externas)."""

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIR_CONFIG = RAIZ / "pipeline" / "config"
DIR_DATOS = RAIZ / "datos"
DIR_CRUDOS = DIR_DATOS / "crudos"
DIR_INTERMEDIOS = DIR_DATOS / "intermedios"


def cargar_env(ruta: Path = RAIZ / ".env") -> None:
    """Carga variables KEY=valor de .env sin pisar las que ya existen en el entorno."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valor = valor.strip().strip('"').strip("'")
        if valor:
            os.environ.setdefault(clave.strip(), valor)
