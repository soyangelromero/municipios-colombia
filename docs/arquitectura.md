# Arquitectura

```
          (tu PC o GitHub Actions)                                 (hosting)
 datos.gov.co ─┐
 DANE / DNP  ──┤   pipeline/ (Python + Scrapling)                web/  (estático)
 SUI / INS   ──┼─► descargar → normalizar → indicadores ──►  ├─ index.html, m/<slug>/…  (HTML generado)
 webs alcaldías┤   → índice → exportar JSON/HTML/SVG            ├─ data/*.json             (datos generados)
 CSV manuales ─┘                                                ├─ assets/ css, js, img    (escritos a mano)
                                                                └─ api/*.php ─► SQLite (fuera de web/)
```

## Principios

1. **El hosting solo sirve archivos.** Todo el cálculo pesado ocurre antes, en el pipeline. El sitio funciona en cualquier hosting compartido o en un servicio de páginas estáticas.
2. **Sin frameworks ni compilación en la web.** HTML semántico, CSS con tokens y módulos ES nativos. PHP solo para recibir formularios.
3. **Las cifras se escriben en el HTML.** Las páginas por municipio son legibles sin JavaScript. El JS solo agrega interactividad: buscador, mapa, comparador y modo historia.
4. **Cada cifra tiene fuente.** El pipeline nunca produce un número sin `periodo` ni `fuente` (ver [modelo-de-datos.md](modelo-de-datos.md)).
5. **Reproducible.** Con el mismo código y las mismas descargas en caché, el resultado es idéntico.

## Pipeline (`pipeline/municipios/`)

| Módulo | Responsabilidad |
|---|---|
| `comun/socrata.py` | Cliente de datos.gov.co: paginación, caché en disco, token opcional, transporte inyectable para pruebas. |
| `comun/modelos.py` | Tipos de datos compartidos: `Fuente`, `Municipio`, `Observacion`. |
| `comun/textos.py` | Slugs y nombres legibles (de `SAN ANDRÉS DE TUMACO` a `San Andrés de Tumaco`). |
| `comun/registro.py` | Lee `config/fuentes.toml`. |
| `fuentes/<nombre>.py` | Una fuente por módulo: `descargar()` (con red) + `normalizar()` (función pura, probada). |
| `comun/geometria.py` | Geometría plana mínima: Douglas-Peucker, áreas, cajas. Sin dependencias. |
| `exportar/mapa_svg.py` | Convierte contornos en SVG: un `<path>` por entidad, coordenadas relativas, recuadros y paneles. |
| `exportar/mapas.py` | Arma el mapa nacional (departamentos) y uno por departamento (municipios). |
| `cli.py` | Punto de entrada: `python -m municipios …`. |

Fases siguientes: `indice/` (pares, puntajes, sensibilidad), más exportaciones (JSON, HTML, sitemap) y `relevamiento/` (transparencia con Scrapling).

## Mapas

- Fuente: MGN 2025 del DANE, en Web Mercator (la misma proyección de casi todos los mapas web).
- Al leer cada entidad se pre-simplifica a 10 m para no tener millones de puntos en memoria. Luego cada mapa se simplifica a su escala: 0,6 unidades del viewBox de 1.000 de ancho. Se descartan islotes de menos de 2 unidades², pero ninguna entidad queda sin dibujo.
- Salida en `web/data/mapas/`:
  - `colombia.svg` (departamentos) y `<departamento>.svg` (municipios), de entre 4 y 110 KB cada uno;
  - `index.html`, una vista previa para revisar.
- Cada `<path>` lleva `data-codigo` (DIVIPOLA) y `data-slug`. Los colores los pone la web con CSS. El SVG trae un estilo base con `:where()` (especificidad cero), fácil de reemplazar.
- San Andrés y Providencia va en un recuadro en el mapa nacional, con una celda por isla principal y sin cayos lejanos. En su mapa departamental, cada municipio va en su propio panel.

## Web (`web/`)

- `assets/css/tokens.css`: colores, tipografía y espacios. Modo claro y oscuro.
- `assets/js/config.js`: configuración (por ejemplo `endpoint` del PHP; `null` = sin formularios).
- `api/`: PHP 8.1+ con PDO SQLite. La configuración y la base viven en `privado/`, fuera de la carpeta pública.

## Despliegue

Se sube la carpeta `web/` al hosting, por FTP/SFTP o con el workflow de despliegue. Las credenciales viven en los *secrets* de GitHub, nunca en el repositorio. Detalle en `docs/despliegue.md` (fase 7).
