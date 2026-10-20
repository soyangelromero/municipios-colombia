from municipios import cli


def test_todo_corre_los_mapas_antes_del_indice(monkeypatch):
    """La superficie sale de los mapas y el índice la necesita para la densidad."""
    orden: list[str] = []
    for nombre in ("divipola", "alcaldes", "mapas", "indice", "sitio"):
        monkeypatch.setattr(cli, f"comando_{nombre}", lambda _, n=nombre: orden.append(n))
    monkeypatch.setattr(cli, "FUENTES", {})
    monkeypatch.setattr(cli, "escribir_json", lambda *a, **k: None)
    cli.comando_todo(object())
    assert orden == ["divipola", "alcaldes", "mapas", "indice", "sitio"]
