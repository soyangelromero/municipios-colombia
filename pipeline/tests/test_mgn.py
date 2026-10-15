from municipios.fuentes.mgn import MUNICIPIOS, _total_de_entidades, leer

GML = """<?xml version="1.0" encoding="utf-8" ?>
<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"
  xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:S="https://ejemplo/S"
  numberMatched="1122" numberReturned="1">
 <wfs:member><S:Municipio gml:id="Municipio.1">
  <S:Código_DANE_concatenado_departamento_y_municipio>05001</S:Código_DANE_concatenado_departamento_y_municipio>
  <S:Nombre_municipio>MEDELLÍN</S:Nombre_municipio>
  <S:Área_departamento_en_kilómetros_cuadrados>374.74</S:Área_departamento_en_kilómetros_cuadrados>
  <S:Año_versión_DANE>2025</S:Año_versión_DANE>
  <S:SHAPE><gml:MultiSurface><gml:surfaceMember><gml:Polygon>
   <gml:exterior><gml:LinearRing><gml:posList>0 0 10 0 10 10 0 10 0 0</gml:posList></gml:LinearRing></gml:exterior>
   <gml:interior><gml:LinearRing><gml:posList>2 2 3 2 3 3 2 2</gml:posList></gml:LinearRing></gml:interior>
  </gml:Polygon></gml:surfaceMember>
  <gml:surfaceMember><gml:Polygon>
   <gml:exterior><gml:LinearRing><gml:posList>20 20 21 20 21 21 20 20</gml:posList></gml:LinearRing></gml:exterior>
  </gml:Polygon></gml:surfaceMember></gml:MultiSurface></S:SHAPE>
 </S:Municipio></wfs:member>
</wfs:FeatureCollection>
"""


def test_lee_atributos_y_poligonos_con_huecos(tmp_path):
    ruta = tmp_path / "pagina.gml"
    ruta.write_text(GML, encoding="utf-8")

    (entidad,) = list(leer([ruta], MUNICIPIOS))

    assert entidad.codigo == "05001"
    assert entidad.nombre == "MEDELLÍN"
    assert entidad.area_km2 == 374.74
    assert entidad.anio_version == "2025"
    assert len(entidad.poligonos) == 2
    exterior, hueco = entidad.poligonos[0]
    assert exterior[1] == (10.0, 0.0)
    assert hueco[0] == (2.0, 2.0)
    assert _total_de_entidades(ruta) == 1122
