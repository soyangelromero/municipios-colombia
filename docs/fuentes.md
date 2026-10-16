# Fuentes de datos

El registro que usa el código es [`pipeline/config/fuentes.toml`](../pipeline/config/fuentes.toml). La ficha de cada indicador (etiqueta, unidad, sentido) está en [`pipeline/config/indicadores.toml`](../pipeline/config/indicadores.toml). Esta página explica cada fuente para quien lee.

## Integradas

| Comando | Organismo | Conjunto | Qué aporta | Cruce con DIVIPOLA | Cobertura (oct. 2026) |
|---|---|---|---|---|---|
| `divipola` | DANE | [DIVIPOLA](https://www.datos.gov.co/d/gdxc-w37w) (`gdxc-w37w`) | Lista oficial de municipios, islas y áreas no municipalizadas | Es la base | 1.122 |
| `poblacion` | DANE | [Proyecciones municipales 2018-2042](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion) (Excel, 30-jul-2025) | Población total, en cabecera y rural | Código | 1.122 |
| `mapas` | DANE | [MGN 2025](https://portalgis.dane.gov.co/mparcgis/services/MGN2025/Serv_CapasMGN_2025/MapServer/WFSServer?service=WFS&request=GetCapabilities) (WFS) | Contornos y superficie en km² | Código | 1.122 |
| `seguridad` | MinDefensa / Policía | [Homicidio](https://www.datos.gov.co/d/m8fd-ahd9), [Hurto personas](https://www.datos.gov.co/d/4rxi-8m8d) | Hechos por municipio y año, desde 2018 | Código | 1.122 |
| `transparencia` | Procuraduría | [ITA](https://www.datos.gov.co/d/im79-n45d) (`im79-n45d`) | Índice de Transparencia y Acceso a la Información: autodiagnóstico y auditoría | Nombre | 1.007 alcaldías |
| `gobierno_digital` | MinTIC | [Índice de Gobierno Digital](https://www.datos.gov.co/d/rtai-k9uh) (`rtai-k9uh`) | Puntaje por alcaldía y vigencia | Código | 1.102 |
| `desempeno_institucional` | Función Pública | [FURAG](https://www.datos.gov.co/d/daed-z4fw) (`daed-z4fw`) | Desempeño institucional, control interno, publicación contractual y estado abierto (2022-2024) | Código SIGEP (vía Gobierno Digital) | 1.102 |
| `finanzas` | Contraloría (CHIP) | CUIPO: [gastos](https://www.datos.gov.co/d/4f7r-epif), [programación](https://www.datos.gov.co/d/d9mu-h6ar), [ingresos](https://www.datos.gov.co/d/9axr-9gnb) | Gasto comprometido, obligado y pagado; funcionamiento, deuda e inversión; presupuesto; ingresos por tipo (2023 en adelante) | Código CHIP (últimos 5 dígitos; tabla para 6 municipios nuevos) | 1.103 |
| `contratacion` | Colombia Compra Eficiente | [SECOP II contratos](https://www.datos.gov.co/d/jbjy-vk9h) (`jbjy-vk9h`) | Contratos firmados por la alcaldía y su valor, total y por contratación directa (2020 en adelante) | NIT (desde SECOP y el ITA) | 870 alcaldías |
| `educacion` | MinEducación | [Estadísticas por municipio](https://www.datos.gov.co/d/nudc-7mev) (`nudc-7mev`) | Cobertura neta y bruta, deserción, reprobación (2018 en adelante) | Código | 1.122 |
| `salud` | ADRES | BDUA [subsidiado](https://www.datos.gov.co/d/d7a5-cnra) y [contributivo](https://www.datos.gov.co/d/tq4m-hmg2) | Afiliados activos (foto del mes de actualización) | Nombre | 1.121 |

## Pendientes

- **Índice de Desempeño Fiscal (DNP):** se publica como Excel anual, sin conjunto de datos abierto. Pendiente de automatizar.
- **Servicios públicos:** acueducto y alcantarillado (CNPV 2018 y SUI-REC de Superservicios) y calidad del agua (IRCA, SIVICAP del INS). No tienen API; se publican como reportes.
- **Alcaldes y partidos (Registraduría):** sin conjunto descargable; irá como CSV curado a mano en `datos/manual/alcaldes.csv`.
- **Relevamiento propio de transparencia:** revisión automática del menú de transparencia de las alcaldías (`datos/relevamiento/transparencia_automatica.csv`). No puntúa; ver `docs/metodologia.md`.

## Cómo se cruza cada fuente

- **Por código:** la fuente trae el código DIVIPOLA. Se completan ceros a la izquierda (`5001` → `05001`).
- **Por nombre:** [`comun/cruce.py`](../pipeline/municipios/comun/cruce.py). Prueba, en orden:
  1. coincidencia exacta normalizada (sin tildes ni signos);
  2. alias verificados (`ALIAS_MUNICIPIOS`, `ALIAS_DEPARTAMENTOS`);
  3. coincidencia de palabras sin ambigüedad («CUCUTA» ⊂ «SAN JOSE DE CUCUTA»);
  4. un parecido muy alto (≥ 0,88).

  Lo que no cruza se guarda en `sin_cruce` y se avisa en la consola.
- **Por NIT (SECOP):** las alcaldías se identifican en el propio SECOP por el nombre de la entidad (excluyendo concejos, personerías, hospitales, empresas…) y por su departamento y ciudad. Se complementa con el NIT que reporta el ITA. Si las dos fuentes difieren, manda SECOP, porque el ITA trae algunos NIT mal digitados.
- **Por código SIGEP (FURAG):** el Índice de Gobierno Digital trae el código SIGEP y el DIVIPOLA de cada alcaldía, y así se cruza FURAG. Los códigos se comparan sin ceros a la izquierda.

## Notas de calidad

- **Seguridad**:
  - El año en curso es parcial; su período se marca como rango (`2026-01/2026-08`).
  - Las cifras de la Policía se actualizan y pueden cambiar en meses posteriores. Medicina Legal (`vtub-3de2`) sirve de contraste.
  - Que un municipio no aparezca en un año significa cero hechos reportados.
- **DIVIPOLA**: incluye 1.103 registros de tipo «Municipio» (entre ellos Bogotá D.C.), 1 «Isla» (San Andrés) y 18 «Áreas no municipalizadas».
- **Población**:
  - Son proyecciones: el período indica el año proyectado, no un conteo.
  - En el Excel, la columna «MPIO» trae el código y «DPMP» el nombre (los rótulos están cruzados).
  - El código `94663` (Mapiripana) ya no existe en DIVIPOLA: se fusionó en Barrancominas (2019). Se reporta como «sin cruce».
- **MGN**:
  - Los 1.122 contornos cruzan uno a uno con DIVIPOLA, incluido Nuevo Belén de Bajirá (creado en 2023).
  - El servicio ArcGIS REST del mismo MGN no devuelve geometrías, por eso se usa el WFS.
  - El firewall del DANE rechaza filtros genéricos (`1=1`) y filtros XML en la URL, así que se pagina la capa completa (unos 180 MB, en caché tras la primera descarga).
  - El servicio rotula el campo de área del municipio como «Área_departamento…».
- **ITA**:
  - El autodiagnóstico lo diligencia la propia alcaldía: muchas reportan 100. La auditoría de la Procuraduría cubre solo una parte de las entidades y años.
  - 2023 casi no tiene auditorías.
- **CUIPO**:
  - Reemplazó al FUT en 2023: no hay serie anterior comparable en este conjunto.
  - Las cuentas son jerárquicas: se usan solo los totales de las cuentas 2, 2.1, 2.2 y 2.3 (gastos) y 1, 1.1, 1.1.01, 1.1.02, 1.1.02.06 y 1.2 (ingresos), en la «vigencia actual».
  - Se toma el corte de diciembre de cada año y el último trimestre del año en curso.
- **SECOP II**:
  - No incluye lo publicado solo en SECOP I.
  - SECOP clasifica algunas alcaldías con orden «Nacional», por eso no se filtra por orden.
  - Unas 230 alcaldías no muestran contratos en SECOP II desde 2020 con ningún NIT conocido. Eso mismo es un dato de transparencia.
- **ADRES**:
  - Publica la «Ñ» mal codificada («NARI¥O»); el cruce lo corrige.
  - Tres registros quedan sin cruce: dos asignados al departamento («DPTO. GUAINIA», «DPTO. VAUPES») y uno a un municipio que no existe («EL PEÑOL», Cundinamarca).
