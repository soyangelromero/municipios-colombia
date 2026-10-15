# Cómo contribuir

¡Gracias por querer ayudar! Este proyecto vive de que más personas revisen sus datos y su código.

## Formas de ayudar

- **Reportar un dato equivocado**: abre un *issue* con la plantilla «Error en un dato». Indica el municipio, el dato, el valor correcto y la fuente oficial que lo respalda.
- **Proponer una fuente**: plantilla «Nueva fuente de datos».
- **Relevar la transparencia de un municipio**: ver `datos/manual/README.md` (disponible desde la fase 5).
- **Código y documentación**: abre un *issue* antes de cambios grandes, para acordar el enfoque.

## Flujo de trabajo

1. Haz un *fork* y crea una rama descriptiva: `fuente-secop`, `arreglo-slug-bogota`.
2. Instala el entorno (ver el README) y verifica que todo pasa:
   ```bash
   ruff check pipeline && ruff format --check pipeline && pytest pipeline
   ```
3. Haz *commits* pequeños, con mensajes en español y en imperativo: «Agrega fuente de hurtos», «Corrige el slug de Bogotá».
4. Abre el *pull request* con la plantilla. Explica qué cambia y cómo lo probaste.

## Estilo de código

- **Idioma**: nombres, comentarios y documentación en español. En los identificadores, sin tildes ni ñ (`anio`, `poblacion`).
- **Python**:
  - `ruff` define el formato y el lint, y tiene la última palabra.
  - Usa anotaciones de tipo y funciones pequeñas.
  - Separa la descarga (con red) de la normalización (pura, fácil de probar).
- **JavaScript**: módulos ES nativos, sin dependencias, sin variables globales y sin compilación.
- **CSS**: usa los tokens de `web/assets/css/tokens.css`; nada de colores sueltos.
- **PHP**: `declare(strict_types=1);`, PSR-12, consultas preparadas con PDO y salida siempre escapada.
- **Pruebas**: todo cálculo nuevo lleva una prueba. Las pruebas no usan la red: los datos de ejemplo van en la propia prueba.

## Agregar una fuente de datos

1. Regístrala en `pipeline/config/fuentes.toml`, con su organismo, URL, conjunto de datos y licencia.
2. Crea `pipeline/municipios/fuentes/<nombre>.py` con dos funciones:
   - `descargar(cliente) -> list[dict]`: trae las filas crudas.
   - `normalizar(filas, ...) -> list[Observacion]`: pura y probada.
3. Conéctala en `pipeline/municipios/cli.py` y documéntala en `docs/fuentes.md`.

## Datos y privacidad

- **Nunca** subas secretos (tokens, contraseñas, credenciales de FTP). Van en `.env` o en los *secrets* de GitHub. El CI corre gitleaks.
- No subas datos personales de ciudadanos. Los funcionarios públicos aparecen solo en su rol y con fuente oficial.
- Sanciones o procesos judiciales: solo decisiones oficiales y firmes, nunca notas de prensa sin respaldo.

## Neutralidad

El proyecto no toma partido político. Los cambios de metodología se discuten en un *issue* público y quedan registrados en `CHANGELOG.md`.
