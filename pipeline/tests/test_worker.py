"""Pruebas del Worker de Cloudflare (node:test con SQLite en memoria); se omiten sin Node 22.13+."""

import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
NODE = shutil.which("node")


def _node_con_sqlite() -> bool:
    if NODE is None:
        return False
    sonda = subprocess.run(
        [NODE, "--no-warnings", "-e", "require('node:sqlite')"], capture_output=True, check=False
    )
    return sonda.returncode == 0


@pytest.mark.skipif(not _node_con_sqlite(), reason="hace falta Node con node:sqlite (22.13+)")
def test_worker_de_pedidos():
    resultado = subprocess.run(
        [NODE, "--no-warnings", "--test"],
        cwd=RAIZ / "worker",
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
