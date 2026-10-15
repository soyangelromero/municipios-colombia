# 0001. Sitio en HTML, CSS y JavaScript puro, con PHP opcional

- Estado: aceptada
- Fecha: 2026-10-14

## Contexto

El proyecto debe poder publicarlo cualquier persona u organización, incluso en un hosting compartido barato, y debe ser fácil de entender para quien quiera contribuir. Los frameworks (React, Vue, Next, etc.) agregan herramientas de compilación, dependencias que envejecen y una barrera de entrada.

## Decisión

- La web publicada usa solo **HTML, CSS y JavaScript nativo** (módulos ES), sin npm, sin compilación y sin librerías de terceros en el navegador.
- **PHP 8.1+** se usa solo para recibir formularios y guarda en SQLite mediante PDO, sin Composer.
- El procesamiento de datos usa **Python** (con Scrapling), pero corre fuera del hosting: en la PC de quien mantiene o en GitHub Actions.

## Consecuencias

- Desplegar es subir una carpeta.
- No hay animaciones con librerías (se usa CSS) ni mapas con WebGL: el mapa se genera como SVG en el pipeline.
- Hay que cuidar a mano la organización del JS (módulos pequeños, sin variables globales).
