import pytest

from municipios.comun.socrata import ClienteSocrata, ErrorSocrata


class TransporteFalso:
    """Simula la API: devuelve `total` filas numeradas, respetando $limit y $offset."""

    def __init__(self, total):
        self.total = total
        self.llamadas = []

    def __call__(self, url, params, headers):
        self.llamadas.append((url, params, headers))
        inicio, limite = int(params["$offset"]), int(params["$limit"])
        return [{"n": i} for i in range(inicio, min(inicio + limite, self.total))]


def test_pagina_hasta_el_final():
    transporte = TransporteFalso(total=25)
    cliente = ClienteSocrata(transporte=transporte, tam_pagina=10)
    filas = cliente.consultar("abcd-1234")
    assert [f["n"] for f in filas] == list(range(25))
    assert len(transporte.llamadas) == 3
    url, params, headers = transporte.llamadas[0]
    assert url == "https://www.datos.gov.co/resource/abcd-1234.json"
    assert params["$order"] == ":id"
    assert headers == {}


def test_usa_group_como_orden_y_envia_token():
    transporte = TransporteFalso(total=1)
    cliente = ClienteSocrata(token="secreto", transporte=transporte)
    cliente.consultar("abcd-1234", select="a, count(*)", group="a")
    _, params, headers = transporte.llamadas[0]
    assert params["$order"] == "a"
    assert params["$group"] == "a"
    assert headers == {"X-App-Token": "secreto"}


def test_agregado_sin_group_no_ordena():
    transporte = TransporteFalso(total=1)
    ClienteSocrata(transporte=transporte).consultar("abcd-1234", select="max(fecha) AS ultima")
    _, params, _ = transporte.llamadas[0]
    assert "$order" not in params


def test_cache_evita_segunda_descarga(tmp_path):
    transporte = TransporteFalso(total=3)
    cliente = ClienteSocrata(transporte=transporte, dir_cache=tmp_path)
    primera = cliente.consultar("abcd-1234", where="x > 1")
    segunda = cliente.consultar("abcd-1234", where="x > 1")
    assert primera == segunda
    assert len(transporte.llamadas) == 1

    cliente.consultar("abcd-1234", where="x > 1", refrescar=True)
    assert len(transporte.llamadas) == 2


def test_respuesta_inesperada_falla():
    cliente = ClienteSocrata(transporte=lambda *_: {"error": True, "message": "mal"})
    with pytest.raises(ErrorSocrata):
        cliente.consultar("abcd-1234")
