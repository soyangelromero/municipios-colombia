# Metodología del índice municipal (v0.1)

La configuración exacta (pesos, componentes y reglas) está en [`pipeline/config/indice.toml`](../pipeline/config/indice.toml). La página de metodología del sitio se genera desde ese mismo archivo, así que nunca se contradicen. El código está en [`pipeline/municipios/indice/`](../pipeline/municipios/indice/).

## Qué mide

Un número de 0 a 100 que resume cuatro preguntas sobre cada municipio:

| Pilar | Peso | Pregunta | Cómo se puntúa |
|---|---|---|---|
| **Transparencia** | 40 % | ¿La alcaldía muestra sus cuentas y cumple sus obligaciones de información? | Escala absoluta: la obligación es la misma para todos |
| **Servicios y seguridad** | 30 % | ¿Qué recibe su población? | Entre pares (grupo DNP) |
| **Gestión fiscal y contratación** | 15 % | ¿Cómo ejecuta su presupuesto y cómo contrata? | Entre pares |
| **Control e institucionalidad** | 15 % | ¿Qué capacidad institucional y control interno tiene? | Escala absoluta (FURAG) |

## Con quién se compara cada municipio

Con su **grupo de capacidades iniciales** del DNP (Medición de Desempeño Municipal): Ciudades, G1 (alto) a G5 (bajo). Es la agrupación oficial para comparar municipios con condiciones de partida parecidas. Un municipio pequeño del grupo G5 no se mide contra Medellín.

En los componentes «entre pares», el puntaje es el **percentil dentro del grupo**: 0 es el peor del grupo y 100 el mejor; los empates comparten percentil.

## Reglas

1. **Obligaciones no reportadas cuentan como 0.** Si una alcaldía no diligencia el ITA o el FURAG, ese componente vale 0 y su peso no se reparte entre los demás.
2. **Datos que no dependen del municipio sí se reparten.** La auditoría del ITA depende del muestreo de la Procuraduría: si no hay auditoría, su peso se reparte dentro del pilar.
3. **Un pilar vale** si tiene datos para al menos el 60 % de su peso.
4. **El índice exige** el pilar de transparencia y al menos 3 de los 4 pilares.
5. **Tope sin cuentas:** si la alcaldía no reportó su ejecución presupuestal (CUIPO) del último año completo, su índice no pasa de 39,9 (rojo).
6. **Antigüedad:** no entran datos de más de 3 años atrás.
7. **Un mismo año para todos:** cada indicador anual se compara en su año de referencia (el último año completo con datos de al menos la mitad de los municipios).
8. **Tasas de delitos suavizadas:** promedio de 3 años y suavizado hacia la tasa del grupo, para que en un municipio de 2.000 habitantes un hecho aislado no lo convierta en el peor del país:

   tasa suavizada = (hechos + tasa del grupo × P0 × 3 / 100.000) / ((población de los 3 años + P0 × 3) / 100.000)

   con P0 = 20.000. La ficha muestra la tasa sin suavizar.

## Semáforo

- **Rojo:** menos de 40.
- **Amarillo:** de 40 a 69,9.
- **Verde:** 70 o más.

## Qué tan estable es el puesto

Se recalcula el índice moviendo ±10 puntos el peso de cada pilar (y re-escalando los demás). Cada ficha muestra el **rango de puestos** resultante. Un rango amplio significa que el puesto depende mucho de cómo se ponderen los pilares.

## Qué no puntúa

Se muestran como contexto, pero no definen el índice:
- población, superficie y densidad;
- gasto e ingresos tributarios por habitante;
- dependencia de transferencias;
- número y valor de contratos;
- el puntaje MDM del DNP.

## Limitaciones conocidas (v0.1)

- **ITA:** el autodiagnóstico lo reporta la propia alcaldía y la mayoría declara 99-100. Por eso pesa poco (0,5) frente a la auditoría de la Procuraduría (2).
- **Servicios faltantes:** todavía no hay datos de acueducto, alcantarillado ni calidad del agua (CNPV 2018, SUI, IRCA).
- **SECOP:** solo SECOP II. Las alcaldías que publican solo en SECOP I aparecen como «no publica».
- **Relevamiento propio:** el relevamiento propio de los sitios web (fase 5) todavía no puntúa: sale de una revisión automática y le falta la verificación humana.
- **Grupos DNP:** son de la medición 2020, la última en datos abiertos. Dos municipios creados después tienen grupo asignado por el proyecto: Nuevo Belén de Bajirá toma el de Riosucio, del que se segregó, y Barrancominas el G5.
