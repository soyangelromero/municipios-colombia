"""Cliente mínimo para la API SODA de datos.gov.co (Socrata).

Pagina automáticamente, guarda cada consulta en caché en disco y acepta un token de aplicación
opcional. El transporte HTTP es inyectable para poder probar sin red.
"""

import hashlib
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scrapling.fetchers import Fetcher

from municipios.comun.salida import ahora_iso, escribir_json, leer_json

log = logging.getLogger(__name__)

Transporte = Callable[[str, dict[str, str], dict[str, str]], Any]


class ErrorSocrata(RuntimeError):
    """La API respondió con un error o con un formato inesperado."""


def transporte_scrapling(url: str, params: dict[str, str], headers: dict[str, str]) -> Any:
    """GET con Scrapling (curl_cffi): reintentos y cabeceras de navegador real."""
    respuesta = Fetcher.get(url, params=params, headers=headers, timeout=120, retries=3)
    if respuesta.status != 200:
        raise ErrorSocrata(f"HTTP {respuesta.status} en {url}: {respuesta.body[:300]!r}")
    return respuesta.json()


class ClienteSocrata:
    def __init__(
        self,
        dominio: str = "www.datos.gov.co",
        token: str | None = None,
        dir_cache: Path | None = None,
        transporte: Transporte = transporte_scrapling,
        tam_pagina: int = 50_000,
    ) -> None:
        self.dominio = dominio
        self.token = token
        self.dir_cache = dir_cache
        self.transporte = transporte
        self.tam_pagina = tam_pagina

    def consultar(
        self,
        conjunto: str,
        *,
        select: str | None = None,
        where: str | None = None,
        group: str | None = None,
        order: str | None = None,
        refrescar: bool = False,
    ) -> list[dict[str, Any]]:
        """Devuelve todas las filas de una consulta SoQL, paginando hasta el final.

        Para paginar de forma estable hace falta un orden. Si no se indica, se usan las columnas
        agrupadas (con group) o el campo interno ':id' (sin select). Un select de agregados sin
        group devuelve una sola fila y no necesita orden.
        """
        orden_por_defecto = group or (None if select else ":id")
        params = {
            clave: valor
            for clave, valor in {
                "$select": select,
                "$where": where,
                "$group": group,
                "$order": order or orden_por_defecto,
            }.items()
            if valor
        }
        ruta_cache = self._ruta_cache(conjunto, params)
        if ruta_cache and ruta_cache.exists() and not refrescar:
            log.debug("Caché: %s", ruta_cache)
            return leer_json(ruta_cache)["filas"]

        filas = self._descargar_todo(conjunto, params)
        if ruta_cache:
            escribir_json(
                ruta_cache,
                {"conjunto": conjunto, "params": params, "consultado": ahora_iso(), "filas": filas},
            )
        return filas

    def fecha_actualizacion(self, conjunto: str) -> str:
        """Fecha (AAAA-MM-DD) de la última actualización de los datos del conjunto.

        Sirve como período de las fuentes que son una «foto» del momento (por ejemplo, afiliados
        activos). No se guarda en caché: cambia con cada actualización de la fuente.
        """
        url = f"https://{self.dominio}/api/views/{conjunto}.json"
        headers = {"X-App-Token": self.token} if self.token else {}
        meta = self.transporte(url, {}, headers)
        marca = meta.get("rowsUpdatedAt") or meta.get("viewLastModified")
        if not marca:
            raise ErrorSocrata(f"{conjunto} no informa su fecha de actualización")
        return datetime.fromtimestamp(int(marca), UTC).date().isoformat()

    def _descargar_todo(self, conjunto: str, params: dict[str, str]) -> list[dict[str, Any]]:
        url = f"https://{self.dominio}/resource/{conjunto}.json"
        headers = {"X-App-Token": self.token} if self.token else {}
        filas: list[dict[str, Any]] = []
        while True:
            pagina_params = {**params, "$limit": str(self.tam_pagina), "$offset": str(len(filas))}
            pagina = self.transporte(url, pagina_params, headers)
            if not isinstance(pagina, list):
                raise ErrorSocrata(f"Respuesta inesperada de {conjunto}: {str(pagina)[:300]}")
            filas.extend(pagina)
            log.info("%s: %d filas descargadas", conjunto, len(filas))
            if len(pagina) < self.tam_pagina:
                return filas

    def _ruta_cache(self, conjunto: str, params: dict[str, str]) -> Path | None:
        if self.dir_cache is None:
            return None
        huella = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16]
        return self.dir_cache / conjunto / f"{huella}.json"
