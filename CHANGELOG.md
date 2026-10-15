# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Se registran cambios de **código**, de **metodología del índice** y de **datos**.

## [Sin publicar]

### Agregado (fase 3: índice municipal v0.1)
- Fuente `grupos`: grupos de capacidades iniciales del DNP (MDM 2020) como pares del índice, con asignación documentada para dos municipios nuevos.
- Índice municipal v0.1 (`python -m municipios indice`), configurado en `pipeline/config/indice.toml`:
  - 4 pilares: transparencia 40, servicios y seguridad 30, gestión 15, control 15;
  - puntajes absolutos o percentil entre pares;
  - obligaciones no reportadas cuentan como 0;
  - tope de 39,9 sin cuentas;
  - tasas de delitos suavizadas;
  - puestos nacional, departamental y en el grupo;
  - rango de puestos con pesos ±10 puntos.
- `docs/metodologia.md`.

### Agregado (fase 2: indicadores automáticos)
- Fuentes:
  - transparencia (ITA de la Procuraduría);
  - Gobierno Digital (MinTIC);
  - desempeño institucional (FURAG);
  - finanzas (CUIPO: gastos, presupuesto e ingresos);
  - contratación (SECOP II);
  - educación (MEN);
  - salud (ADRES).
- Cruce por nombre de departamento y municipio, con alias verificados y corrección de la «Ñ» mal codificada.
- Registro de indicadores (`pipeline/config/indicadores.toml`): cada indicador tiene ficha y una prueba lo verifica.
- Patrón común de fuentes (`ejecutar(contexto) -> Resultado`) y CLI genérica.
- Modo `--tolerante` para `todo`: una fuente que falla no detiene el despliegue.
- GitHub Pages: el sitio se publica en cada push a `main`.

### Agregado (fase 1: base territorial)
- Fuente **población** (DANE): proyecciones municipales 2018-2042 por área (total, cabecera y rural), versión del 30 de julio de 2025.
- Fuente **MGN 2025** (DANE): contornos de los 1.122 municipios y 33 departamentos desde el WFS oficial, y superficie oficial en km².
- Mapas SVG en `web/data/mapas/`:
  - el nacional por departamentos, con San Andrés en recuadro;
  - uno por departamento, con sus municipios;
  - una página de vista previa.
- Geometría sin dependencias (Douglas-Peucker y áreas) y comandos `poblacion` y `mapas`.
- Dependencia `openpyxl` para leer el Excel del DANE.

### Agregado (fase 0: fundaciones)
- Estructura del repositorio, licencias (MIT para el código, CC BY 4.0 para los datos), guía de contribución, código de conducta y política de seguridad.
- Pipeline en Python con:
  - cliente de datos.gov.co (Socrata) con paginación, caché y token opcional;
  - registro de fuentes en `pipeline/config/fuentes.toml`;
  - fuente **DIVIPOLA** (DANE): lista oficial de municipios, nombres legibles y slugs únicos;
  - fuente **seguridad** (Ministerio de Defensa): homicidios y hurtos a personas por municipio y año.
- Pruebas unitarias sin red y CI en GitHub Actions (ruff, pytest, gitleaks).
- Decisiones de diseño 0001 a 0003.
