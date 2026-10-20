# Datos curados a mano

Aquí viven los archivos que **no salen de una API** y que revisa una persona. Se versionan con git y se publican bajo CC BY 4.0.

| Archivo (fase) | Contenido |
|---|---|
| `alcaldes.csv` (fase 2) | Alcalde/sa en ejercicio, partido o coalición, fecha de inicio y fuente oficial por fila. |
| `sitios.csv` (fase 5) | Sitio web oficial de cada alcaldía, cuando no sigue el patrón `municipio-departamento.gov.co`. |
| `transparencia.csv` (fase 5) | Revisión **humana** de los 10 criterios: valor (`si`/`parcial`/`no`), URL de evidencia, fecha y revisor. Empieza vacío: solo esta revisión podrá puntuar. |
| `correcciones.csv` (fase 6) | Registro público de correcciones: qué cambió, cuándo, por qué y quién lo reportó (sin datos personales). |

Reglas:
- Una fila por municipio y dato, con el **código DIVIPOLA** como primera columna.
- Toda fila lleva una fuente (URL) y una fecha (`AAAA-MM-DD`).
- Codificación UTF-8, separador coma y encabezados en minúscula sin tildes.

## Flujo de la revisión de transparencia

1. `python -m municipios relevamiento` (necesita `scrapling install`) abre el menú de transparencia de cada alcaldía y escribe `datos/relevamiento/transparencia_automatica.csv`: por criterio, `enlace_encontrado` (en el sitio), `fuente_oficial` (SECOP, SIGEP o datos.gov.co), `no_encontrado` (que no es «no publica»), `menu_no_legible`, `sitio_no_encontrado`, `no_permitido` o `error`, con la URL de evidencia, la fecha, el método y un `detalle`. Revisa las 31 capitales; con `--alcance todos`, los 1.104 municipios (con `--particion K/N` se reparte en varios procesos y `--unir` junta las partes; `--reanudar` retoma una corrida; `--solo-cruces` reaplica los cruces oficiales sin rastrear).
2. Las fichas muestran ese resultado como «Revisión automática del sitio web — sin verificación humana, no puntúa».
3. Una persona abre la evidencia y comprueba que el documento exista, esté completo y esté al día. Añade una fila a `transparencia.csv` por municipio y criterio (`valor`: `si`, `parcial` o `no`; `evidencia`: URL; `fecha`; `revisor`: nombre público o seudónimo, nunca datos de contacto).
4. Solo las filas de `transparencia.csv` podrán entrar al índice, en una versión futura de la metodología.
