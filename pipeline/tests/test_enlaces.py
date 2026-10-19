from municipios.exportar.enlaces import revisar


def _sitio(tmp_path):
    (tmp_path / "m" / "a").mkdir(parents=True)
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "x.css").write_text("", encoding="utf-8")
    (tmp_path / "index.html").write_text(
        '<a href="m/a/">ok</a><a href="m/b/">roto</a><link href="assets/x.css">'
        '<img src="assets/falta.webp"><a href="https://x.org/n">ext</a><a href="#arriba">a</a>'
        '<a href="#nada-aqui">b</a><h1 id="arriba">t</h1>',
        encoding="utf-8",
    )
    (tmp_path / "m" / "a" / "index.html").write_text(
        '<a href="../../">inicio</a><a href="../../#arriba">ancla</a><a href="../../#Falta">x</a>',
        encoding="utf-8",
    )


def test_detecta_rotos_y_respeta_lo_valido(tmp_path):
    _sitio(tmp_path)
    rotos = {(p, e) for p, e, _ in revisar(tmp_path)}
    assert ("index.html", "m/b/") in rotos
    assert ("index.html", "assets/falta.webp") in rotos
    assert ("m/a/index.html", "../../#Falta") in rotos
    assert ("index.html", "#nada-aqui") in rotos
    assert ("index.html", "m/a/") not in rotos
    assert ("index.html", "assets/x.css") not in rotos
    assert ("m/a/index.html", "../../#arriba") not in rotos
    assert not any(e.startswith("https:") for _, e in rotos)
