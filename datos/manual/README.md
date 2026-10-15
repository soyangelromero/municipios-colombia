# Datos curados a mano

Aquí viven los archivos que **no salen de una API** y que revisa una persona. Se versionan con git y se publican bajo CC BY 4.0.

| Archivo (fase) | Contenido |
|---|---|
| `alcaldes.csv` (fase 2) | Alcalde/sa en ejercicio, partido o coalición, fecha de inicio y fuente oficial por fila. |
| `sitios.csv` (fase 5) | Sitio web oficial de cada alcaldía, cuando no sigue el patrón `municipio-departamento.gov.co`. |
| `transparencia.csv` (fase 5) | Relevamiento de los 10 criterios: valor (`si`/`parcial`/`no`), URL de evidencia, fecha y revisor. |
| `correcciones.csv` (fase 6) | Registro público de correcciones: qué cambió, cuándo, por qué y quién lo reportó (sin datos personales). |

Reglas:
- Una fila por municipio y dato, con el **código DIVIPOLA** como primera columna.
- Toda fila lleva una fuente (URL) y una fecha (`AAAA-MM-DD`).
- Codificación UTF-8, separador coma y encabezados en minúscula sin tildes.
