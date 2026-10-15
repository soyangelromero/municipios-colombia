# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Se registran cambios de **código**, de **metodología del índice** y de **datos**.

## [Sin publicar]

### Agregado
- Estructura del repositorio, licencias (MIT para el código, CC BY 4.0 para los datos), guía de contribución, código de conducta y política de seguridad.
- Pipeline en Python con:
  - cliente de datos.gov.co (Socrata) con paginación, caché y token opcional;
  - registro de fuentes en `pipeline/config/fuentes.toml`;
  - fuente **DIVIPOLA** (DANE): lista oficial de municipios, nombres legibles y slugs únicos;
  - fuente **seguridad** (Ministerio de Defensa): homicidios y hurtos a personas por municipio y año.
- Pruebas unitarias sin red y CI en GitHub Actions (ruff, pytest, gitleaks).
- Decisiones de diseño 0001 a 0003.
