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
| `cli.py` | Punto de entrada: `python -m municipios …`. |

Fases siguientes: `indice/` (pares, puntajes, sensibilidad), `exportar/` (JSON, HTML, SVG, sitemap) y `relevamiento/` (transparencia con Scrapling).

## Web (`web/`)

- `assets/css/tokens.css`: colores, tipografía y espacios. Modo claro y oscuro.
- `assets/js/config.js`: configuración (por ejemplo `endpoint` del PHP; `null` = sin formularios).
- `api/`: PHP 8.1+ con PDO SQLite. La configuración y la base viven en `privado/`, fuera de la carpeta pública.

## Despliegue

Se sube la carpeta `web/` al hosting, por FTP/SFTP o con el workflow de despliegue. Las credenciales viven en los *secrets* de GitHub, nunca en el repositorio. Detalle en `docs/despliegue.md` (fase 7).
