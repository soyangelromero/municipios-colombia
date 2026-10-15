# Fuentes de datos

El registro que usa el código es [`pipeline/config/fuentes.toml`](../pipeline/config/fuentes.toml). Esta página explica cada fuente para quien lee.

## Integradas

| Clave | Organismo | Conjunto | Qué aporta | Actualización |
|---|---|---|---|---|
| `dane_divipola` | DANE | [DIVIPOLA – Códigos municipios](https://www.datos.gov.co/d/gdxc-w37w) (`gdxc-w37w`) | Lista oficial de municipios y áreas no municipalizadas, con códigos y coordenadas | Cuando cambia la división político-administrativa |
| `dane_proyecciones_poblacion` | DANE | [Proyecciones municipales por área 2018-2042](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion) (Excel, versión del 30-jul-2025) | Población total, en cabecera y rural por municipio y año | Cuando el DANE actualiza las proyecciones |
| `dane_mgn` | DANE | [Marco Geoestadístico Nacional 2025](https://portalgis.dane.gov.co/mparcgis/services/MGN2025/Serv_CapasMGN_2025/MapServer/WFSServer?service=WFS&request=GetCapabilities) (WFS) | Contornos de municipios y departamentos (mapas) y superficie oficial en km² | Anual |
| `mindefensa_homicidios` | Ministerio de Defensa / Policía Nacional | [Homicidio](https://www.datos.gov.co/d/m8fd-ahd9) (`m8fd-ahd9`) | Homicidios por municipio y año (desde 2003) | Mensual |
| `mindefensa_hurto_personas` | Ministerio de Defensa / Policía Nacional | [Hurto personas](https://www.datos.gov.co/d/4rxi-8m8d) (`4rxi-8m8d`) | Hurtos a personas por municipio y año | Mensual |

## Próximas (ver PLAN.md, §2)

- Transparencia: ITA de la Procuraduría (`im79-n45d`) y relevamiento propio.
- Finanzas: CUIPO de la Contraloría (`4f7r-epif`, `9axr-9gnb`) e Índice de Desempeño Fiscal del DNP.
- Contratación: SECOP II (`jbjy-vk9h`).
- Servicios: MEN (`nudc-7mev`), ADRES (`d7a5-cnra`), SUI y SIVICAP.
- Control: FURAG (`daed-z4fw`).

## Notas de calidad

- **Seguridad**: el año en curso es parcial; su período se marca como rango (`2026-01/2026-08`). Las cifras de la Policía se actualizan y pueden cambiar en meses posteriores. Medicina Legal (`vtub-3de2`) sirve de contraste.
- **DIVIPOLA**: incluye 1.103 registros de tipo «Municipio» (entre ellos Bogotá D.C.), 1 «Isla» (San Andrés) y 18 «Áreas no municipalizadas».
- **Población**:
  - Son proyecciones: el período indica el año proyectado, no un conteo.
  - En el Excel, la columna «MPIO» trae el código y «DPMP» el nombre (los rótulos están cruzados).
  - El código `94663` (Mapiripana) ya no existe en DIVIPOLA: se fusionó en Barrancominas (2019) y figura con población 0. Se reporta como «sin cruce».
- **MGN**:
  - Los 1.122 contornos cruzan uno a uno con DIVIPOLA, incluido Nuevo Belén de Bajirá (creado en 2023).
  - El servicio ArcGIS REST del mismo MGN no devuelve geometrías, por eso se usa el WFS.
  - El firewall del DANE rechaza filtros genéricos (`1=1`) y filtros XML en la URL, así que se pagina la capa completa (unos 180 MB, en caché tras la primera descarga).
  - El servicio rotula el campo de área del municipio como «Área_departamento…».

