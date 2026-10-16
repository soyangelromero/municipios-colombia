# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Se registran cambios de **código**, de **metodología del índice** y de **datos**.

## [Sin publicar]

### Agregado (fase 5: relevamiento de transparencia)
- `python -m municipios relevamiento`: un navegador automático (Scrapling `DynamicFetcher`) abre el menú de transparencia de cada alcaldía y busca 10 criterios de la Ley 1712 por el texto y la dirección de cada enlace. Por defecto revisa las 31 capitales; `--alcance todos`, los 1.104 municipios.
  - Respeta `robots.txt`, pausa 3 s entre sitios y se identifica con un agente propio.
  - `datos/manual/sitios.csv`: 18 dominios propios verificados; el resto sigue el patrón `www.<municipio>-<departamento>.gov.co`.
  - Resultado en `datos/relevamiento/transparencia_automatica.csv`. Si el menú no se puede leer, se registra «menú no legible», nunca «no publica».
- Cada ficha con relevamiento muestra, en el pilar de transparencia, «Revisión automática del sitio web — sin verificación humana, no puntúa», con el estado de cada criterio, el enlace de evidencia y la fecha.
- `datos/manual/transparencia.csv` (solo encabezado) para la revisión humana, y el flujo documentado en `datos/manual/README.md` y `docs/metodologia.md`.
- Pruebas de `clasificar()`, `dominio()`, `candidatos()` y de la lectura del relevamiento, sin red.

### Agregado (fase 4: sitio web)
- Generación del sitio completo en `dist/` (`python -m municipios sitio`):
  - portada con buscador, cifras, mapa de departamentos con capas y listas de mejores y peores;
  - una ficha por municipio: índice, puestos, rango, pilares, cada indicador con valor, período, puntaje y fuente, contexto y mapa del departamento;
  - una página por departamento, con mapa coloreado y ranking;
  - ranking nacional con filtros y orden;
  - comparador con URL compartible;
  - metodología (generada desde `indice.toml`), fuentes y acerca/privacidad;
  - `sitemap.xml`, `robots.txt` y página 404.
- Diseño propio (modo claro y oscuro, escala de color accesible) y JavaScript sin dependencias.
- Fichas legibles en el celular: los indicadores se apilan como tarjetas.
- Modo historia en cada ficha y botón para reportar un error, que abre un issue con el municipio ya cargado.
- Configuración del sitio en `pipeline/config/sitio.toml`.

### Corregido
- ITA: Bogotá y los distritos (Barranquilla, Cartagena, Santa Marta, Tumaco, Buenaventura) figuran como «DISTRITAL» y quedaban sin dato. Ahora se identifica a la alcaldía por el nombre del sujeto obligado, sin alcaldías locales ni concejos. La cobertura pasa de 1.007 a 1.091 alcaldías.

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
