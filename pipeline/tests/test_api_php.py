"""Pruebas de la API PHP de formularios con el servidor integrado de PHP (se omiten sin `php`)."""

import json
import os
import shutil
import socket
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
PHP = shutil.which("php")
pytestmark = pytest.mark.skipif(PHP is None, reason="php no está instalado")

ORIGEN = "http://sitio.test"


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def api(tmp_path):
    base = tmp_path / "datos.sqlite"
    config = tmp_path / "config.php"
    config.write_text(
        f"<?php return ['ruta_base' => '{base.as_posix()}', 'sal' => 'sal-de-prueba',"
        f" 'correo' => 'a@b.c', 'origen' => '{ORIGEN}', 'dias_retencion' => 30,"
        " 'max_por_hora' => 3];",
        encoding="utf-8",
    )
    puerto = _puerto_libre()
    proceso = subprocess.Popen(
        [PHP, "-S", f"127.0.0.1:{puerto}", "-t", str(RAIZ / "web")],
        env={**os.environ, "MUNICIPIOS_CONFIG": str(config)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{puerto}"
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", puerto), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    else:
        proceso.kill()
        pytest.fail("el servidor de PHP no arrancó")
    yield url, base
    proceso.terminate()
    proceso.wait(timeout=5)


def _enviar(url, archivo, cuerpo, *, origen=ORIGEN, metodo="POST"):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    peticion = urllib.request.Request(f"{url}/api/{archivo}.php", data=datos, method=metodo)
    peticion.add_header("Content-Type", "application/json")
    if origen:
        peticion.add_header("Origin", origen)
    try:
        with urllib.request.urlopen(peticion, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _valido(**extra):
    return {
        "t": int(time.time() * 1000) - 5000,
        "mensaje": "El dato de población está mal.",
        **extra,
    }


def test_envio_valido_se_guarda_sin_la_ip(api):
    url, base = api
    estado, cuerpo = _enviar(url, "reportes", _valido(municipio="Sopó", contacto="a@b.co"))
    assert estado == 200 and cuerpo["ok"] is True
    fila = sqlite3.connect(base).execute("SELECT tipo, municipio, ip_hash FROM envios").fetchone()
    assert fila[0] == "reporte" and fila[1] == "Sopó"
    assert len(fila[2]) == 64 and "127.0.0.1" not in fila[2]


@pytest.mark.parametrize("archivo", ["reportes", "pedidos", "contacto"])
def test_los_tres_formularios_responden(api, archivo):
    estado, _ = _enviar(api[0], archivo, _valido(asunto="Hola"))
    assert estado == 200


def test_rechaza_metodo_y_origen_ajenos(api):
    url, _ = api
    assert _enviar(url, "contacto", None, metodo="GET")[0] == 405
    assert _enviar(url, "contacto", _valido(), origen="http://otro.test")[0] == 403
    assert _enviar(url, "contacto", _valido(), origen=None)[0] == 403


def test_campo_trampa_y_tiempo_minimo(api):
    url, _ = api
    assert _enviar(url, "contacto", _valido(web="soy un robot"))[0] == 400
    demasiado_rapido = {"t": int(time.time() * 1000), "mensaje": "Hola, mensaje válido."}
    assert _enviar(url, "contacto", demasiado_rapido)[0] == 400
    assert _enviar(url, "contacto", {"mensaje": "Hola, mensaje válido."})[0] == 400


def test_mensaje_corto_se_rechaza(api):
    assert _enviar(api[0], "contacto", _valido(mensaje="hi"))[0] == 422


def test_limite_por_ip_y_hora(api):
    url, _ = api
    estados = [_enviar(url, "contacto", _valido())[0] for _ in range(5)]
    assert estados == [200, 200, 200, 429, 429]


def test_borra_lo_viejo(api):
    url, base = api
    assert _enviar(url, "contacto", _valido())[0] == 200
    viejo = (datetime.now(UTC) - timedelta(days=45)).isoformat()
    con = sqlite3.connect(base)
    con.execute(
        "INSERT INTO envios (tipo, mensaje, ip_hash, creado) VALUES ('contacto', 'viejo', 'x', ?)",
        (viejo,),
    )
    con.commit()
    con.close()
    assert _enviar(url, "contacto", _valido())[0] == 200
    mensajes = [r[0] for r in sqlite3.connect(base).execute("SELECT mensaje FROM envios")]
    assert "viejo" not in mensajes


def _apoyo(url, municipio="05001", dato="ejecucion_presupuestal", **extra):
    cuerpo = {"t": int(time.time() * 1000) - 5000, "municipio": municipio, "dato": dato, **extra}
    return _enviar(url, "apoyos", cuerpo)


def _ranking(url, consulta=""):
    with urllib.request.urlopen(f"{url}/api/pedidos-ranking.php{consulta}", timeout=10) as r:
        return json.loads(r.read())


def test_apoyo_cuenta_una_sola_vez_por_persona(api):
    url, base = api
    assert _apoyo(url) == (200, {"ok": True, "yaPedido": False, "total": 1})
    assert _apoyo(url) == (200, {"ok": True, "yaPedido": True, "total": 1})
    fila = sqlite3.connect(base).execute("SELECT ip_hash FROM apoyos").fetchone()
    assert len(fila[0]) == 64 and "127.0.0.1" not in fila[0]


def test_apoyo_valida_municipio_dato_y_robots(api):
    url, _ = api
    assert _apoyo(url, municipio="abc")[0] == 422
    assert _apoyo(url, dato="Dato Raro!")[0] == 422
    assert _apoyo(url, web="robot")[0] == 400
    assert _enviar(url, "apoyos", {"municipio": "05001", "dato": "x"})[0] == 400


def test_ranking_ordena_y_detalla_por_municipio(api):
    url, base = api
    _apoyo(url, "05001", "sueldos")
    _apoyo(url, "05001", "compras")
    _apoyo(url, "15759", "sueldos")
    con = sqlite3.connect(base)
    con.execute(
        "INSERT INTO apoyos VALUES ('05001', 'sueldos', 'otra-persona', ?)",
        (datetime.now(UTC).isoformat(),),
    )
    con.commit()
    con.close()
    ranking = _ranking(url)
    assert [m["codigo"] for m in ranking["municipios"]] == ["05001", "15759"]
    primero = ranking["municipios"][0]
    assert primero["total"] == 3 and primero["porDato"]["sueldos"] == 2
    detalle = _ranking(url, "?municipio=05001")
    assert detalle["porDato"] == {"sueldos": 2, "compras": 1}
    assert sorted(detalle["mios"]) == ["compras", "sueldos"]


def test_apoyos_viejos_se_borran_y_hay_limite_por_hora(api):
    url, base = api
    _apoyo(url, "05001", "a")
    viejo = (datetime.now(UTC) - timedelta(days=400)).isoformat()
    con = sqlite3.connect(base)
    con.execute("INSERT INTO apoyos VALUES ('05001', 'viejo', 'x', ?)", (viejo,))
    con.commit()
    _apoyo(url, "05001", "b")
    assert con.execute("SELECT COUNT(*) FROM apoyos WHERE dato = 'viejo'").fetchone()[0] == 0
    estados = [_apoyo(url, "05001", f"d{i}")[0] for i in range(40)]
    assert 429 in estados
