import os

from municipios.config import cargar_env


def test_cargar_env_no_pisa_variables_existentes(tmp_path, monkeypatch):
    archivo = tmp_path / ".env"
    archivo.write_text(
        "# comentario\nVAR_NUEVA_PRUEBA='valor'\nVAR_EXISTENTE_PRUEBA=del_archivo\nVACIA_PRUEBA=\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("VAR_EXISTENTE_PRUEBA", "del_entorno")
    monkeypatch.delenv("VAR_NUEVA_PRUEBA", raising=False)
    monkeypatch.delenv("VACIA_PRUEBA", raising=False)

    cargar_env(archivo)

    assert os.environ["VAR_NUEVA_PRUEBA"] == "valor"
    assert os.environ["VAR_EXISTENTE_PRUEBA"] == "del_entorno"
    assert "VACIA_PRUEBA" not in os.environ
    monkeypatch.delenv("VAR_NUEVA_PRUEBA")
