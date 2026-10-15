# 0003. Cada dato es una observación `[valor, periodo, fuente]`

- Estado: aceptada
- Fecha: 2026-10-14

## Contexto

La credibilidad del proyecto depende de que cada cifra se pueda verificar. Un número sin período ni fuente no se puede auditar, y además invita a comparar años distintos sin advertirlo.

## Decisión

- El pipeline produce **observaciones** en formato largo: `divipola`, `indicador`, `valor`, `periodo`, `fuente`.
- `fuente` apunta a una entrada del registro `pipeline/config/fuentes.toml`, que guarda organismo, título, URL, conjunto de datos, licencia y si es oficial.
- Si no hay dato, no se crea observación: nunca se rellena con cero ni con `null`.
- Para la web, se compacta como `[valor, periodo, fuente]`.

## Consecuencias

- La interfaz siempre puede mostrar «Fuente» y el período junto a cada cifra.
- Los indicadores derivados (tasas, puntajes) citan una lista de fuentes: `[principal, insumos…]`.
