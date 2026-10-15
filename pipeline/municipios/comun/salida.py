"""Escritura de resultados del pipeline."""

import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def ahora_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _serializable(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    raise TypeError(f"No se puede serializar {type(obj).__name__}")


def escribir_json(ruta: Path, datos: Any, compacto: bool = False) -> None:
    """Escribe JSON en UTF-8, creando la carpeta si hace falta.

    Por defecto, legible (para revisar los intermedios); `compacto` para lo que se publica.
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if compacto:
        texto = json.dumps(datos, ensure_ascii=False, separators=(",", ":"), default=_serializable)
    else:
        texto = json.dumps(datos, ensure_ascii=False, indent=1, default=_serializable)
    ruta.write_text(texto + "\n", encoding="utf-8")


def leer_json(ruta: Path) -> Any:
    return json.loads(ruta.read_text(encoding="utf-8"))
