# Municipios Colombia

Observatorio cívico, abierto y neutral sobre los **1.104 municipios de Colombia**. Para cada municipio muestra:
- si **publica sus cuentas**;
- **qué servicios y seguridad recibe su población**;
- **cómo gasta y contrata**;
- **qué dicen los órganos de control**.

Cada cifra lleva su fuente oficial.

> Estado: **fase 1, base territorial**. El pipeline ya descarga la lista oficial de municipios (DIVIPOLA), la población proyectada por el DANE, los contornos del Marco Geoestadístico Nacional (y con ellos genera los mapas SVG) y las cifras de homicidios y hurtos. El sitio web todavía no tiene contenido.

## Cómo está hecho

```
fuentes oficiales ──► pipeline/ (Python, corre en tu PC o en GitHub Actions)
                          │  descarga, normaliza y calcula
                          ▼
                      web/ (HTML + CSS + JS puro, más PHP opcional para formularios)
                          │  se sube tal cual a cualquier hosting
```

- **El sitio publicado no usa frameworks ni compilación.** Son HTML, CSS y JavaScript nativos. PHP solo hace falta para los formularios (reportar un error, contacto). Sin PHP, el sitio funciona igual, pero sin formularios.
- **Los datos se preparan antes**, con Python y [Scrapling](https://github.com/D4Vinci/Scrapling), y se publican como archivos estáticos.
- **Cada valor es una observación** `[valor, periodo, fuente]`. Ver [docs/modelo-de-datos.md](docs/modelo-de-datos.md).

Más detalle en [docs/arquitectura.md](docs/arquitectura.md) y en las [decisiones de diseño](docs/decisiones/).

## Empezar en 5 minutos

Requisitos: Python 3.12 o superior y git.

```bash
git clone https://github.com/soyangelromero/municipios-colombia.git
cd municipios-colombia
python -m venv .venv
# Windows: .venv\Scripts\activate    ·    macOS/Linux: source .venv/bin/activate
pip install -e "pipeline[dev]"
python -m municipios fuentes          # lista las fuentes registradas
python -m municipios todo             # corre todas las fuentes (la primera vez tarda unos minutos)
pytest pipeline                       # corre las pruebas
```

También se puede correr cada paso por separado: `divipola`, `poblacion`, `mapas` y `seguridad`.

- Los resultados quedan en `datos/intermedios/` y los mapas en `web/data/mapas/`. Ninguna de las dos carpetas se versiona.
- Las descargas se guardan en caché en `datos/crudos/`; la del MGN pesa unos 240 MB. Para forzar una descarga nueva, usa `--refrescar`.

Para ver los mapas generados, sirve la carpeta `web/` y abre http://localhost:8000/data/mapas/:

```bash
python -m http.server 8000 --directory web
```

### Token de datos.gov.co (opcional)

Sin token, la API de datos.gov.co funciona, pero con un límite de peticiones más bajo. Si tienes uno, copia `.env.example` a `.env` y completa `SOCRATA_APP_TOKEN`. **Nunca subas `.env` al repositorio.**

## Estructura

```
├── pipeline/          # Python: descarga, normalización, índice y exportación
│   ├── config/        # fuentes.toml (registro de fuentes)
│   ├── municipios/    # paquete: comun/, fuentes/, cli.py
│   └── tests/
├── datos/
│   ├── manual/        # CSV curados a mano (versionados)
│   ├── crudos/        # caché de descargas (ignorado por git)
│   └── intermedios/   # resultados del pipeline (ignorado por git)
├── web/               # lo que se sube al hosting
└── docs/              # arquitectura, modelo de datos, fuentes y decisiones
```

## Contribuir

¿Encontraste un dato equivocado, una fuente mejor o un error? Lee [CONTRIBUTING.md](CONTRIBUTING.md). Todas las personas que participan se comprometen con el [código de conducta](CODE_OF_CONDUCT.md).

## Contacto

- Errores en datos, propuestas y preguntas: abre un [*issue*](https://github.com/soyangelromero/municipios-colombia/issues).
- Asuntos privados o vulnerabilidades de seguridad: [iangelromero@outlook.com](mailto:iangelromero@outlook.com) (ver [SECURITY.md](SECURITY.md)).

## Licencias

- Código: [MIT](LICENSE).
- Datos propios (relevamientos, cálculos e índice): [CC BY 4.0](LICENSE-DATA.md).
- Los datos de terceros conservan la licencia de su fuente, citada en cada valor.
