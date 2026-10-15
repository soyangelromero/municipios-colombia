# 0002. Código DIVIPOLA como clave y slugs `departamento--municipio`

- Estado: aceptada
- Fecha: 2026-10-14

## Contexto

Los nombres de municipios se repiten entre departamentos (hay varios «San Andrés», «Mosquera», «Buenavista»), cambian de escritura según la fuente («Bogotá, D.C.» o «Bogotá D.C.») y algunos cambian de nombre oficial.

## Decisión

- La clave interna es el **código DIVIPOLA de 5 dígitos** del DANE, siempre como texto.
- La URL pública usa un **slug legible y estable**: `departamento--municipio`, en minúsculas, sin tildes y con guiones (`antioquia--el-carmen-de-viboral`). Las excepciones se declaran explícitamente en `fuentes/divipola.py` (`SLUGS_ESPECIALES`). Hoy solo hay una: Bogotá D.C. (`11001`) usa `bogota`.
- Los departamentos tienen un nombre y un slug cortos definidos en el código (por ejemplo, el 88 se muestra como «San Andrés y Providencia», con slug `san-andres`).

## Consecuencias

- Si el DANE cambia el nombre de un municipio, el slug cambiaría. En ese caso se agrega una redirección y se registra en el `CHANGELOG.md`.
- Cada fuente nueva debe resolver su código al DIVIPOLA. Las filas que no cruzan se reportan, no se descartan en silencio.
