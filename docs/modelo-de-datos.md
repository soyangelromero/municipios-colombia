# Modelo de datos

## Identificador: código DIVIPOLA

Todo municipio se identifica por su **código DIVIPOLA de 5 dígitos** (DANE), siempre como texto con ceros a la izquierda: `"05001"` es Medellín, `"11001"` es Bogotá D.C.

Los dos primeros dígitos son el departamento. Toda fuente nueva debe poder cruzarse por este código. Ejemplo: los códigos CHIP de la Contaduría terminan en el DIVIPOLA (`217870678` → `70678`).

## Municipio

| Campo | Ejemplo | Notas |
|---|---|---|
| `divipola` | `"05001"` | Clave. |
| `nombre` | `"Medellín"` | Legible, con tildes. |
| `nombre_oficial` | `"MEDELLÍN"` | Tal como lo publica el DANE. |
| `departamento_codigo` | `"05"` | |
| `departamento` | `"Antioquia"` | Nombre corto para mostrar. |
| `tipo` | `"municipio"` · `"isla"` · `"area_no_municipalizada"` | Las áreas no municipalizadas se muestran, pero no reciben índice. |
| `slug` | `"antioquia--medellin"` | URL estable: `departamento--municipio`. Excepción: Bogotá D.C. usa `"bogota"` (ADR 0002). |
| `lat`, `lon` | `6.246631`, `-75.581775` | Punto de referencia del DANE. |

## Observación: `[valor, periodo, fuente]`

Cada dato es una observación:

```json
{"divipola": "05001", "indicador": "homicidios", "valor": 333, "periodo": "2025", "fuente": "mindefensa_homicidios"}
```

- `valor`: número (o texto, para categorías). Nunca `null`: si no hay dato, no hay observación.
- `periodo`: año (`"2025"`), mes (`"2026-08"`), rango parcial (`"2026-01/2026-08"`) o ventana (`"2023-2025"`), con notación ISO 8601.
- `fuente`: clave en el registro de fuentes (`pipeline/config/fuentes.toml`). El registro guarda el organismo, el título, la URL, el conjunto de datos, la licencia y si es oficial. La fecha de consulta se agrega al exportar.

Al publicarse para la web, las observaciones se compactan en tuplas `[valor, periodo, fuente]` para ahorrar espacio. Los nombres largos viven una sola vez en la tabla de fuentes.

## Indicador

Cada indicador tiene una ficha (en `pipeline/config/indicadores.toml`, desde la fase 2):
- etiqueta,
- unidad,
- fórmula,
- sentido («más alto es mejor» o «más bajo es mejor»),
- si puntúa o es solo contexto.
