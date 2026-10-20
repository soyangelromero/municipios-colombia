# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Se registran cambios de **código**, de **metodología del índice** y de **datos**.

## [Sin publicar]

### Agregado: alcalde de cada municipio
- `python -m municipios alcaldes` descarga las «Personas Expuestas Políticamente» de SIGEP II (Función Pública) y deja en `datos/intermedios/alcaldes.json` el alcalde vigente de cada municipio, unido por nombre de entidad, NIT y el mapa del ITA. Va dentro de `todo`; si falla, el sitio sale sin el nombre.
- Solo se publica un nombre cuando hay una única persona vigente (sin fecha de desvinculación) posesionada desde el 1 de enero de 2024. Con dos o más, o ninguna, el municipio no muestra alcalde: 637 de 1.104 al día de hoy (61 dudosos).
- La ficha («Alcaldía 2024-2027: nombre», con enlace a SIGEP II y la fecha de posesión registrada), la historia y la tarjeta para compartir muestran el nombre. No se muestra el género del cargo ni foto: SIGEP no trae género y no hay fuente abierta de fotos.
- Pruebas del cruce, los casos dudosos y la línea de la ficha.

### Mejorado: tarjeta para compartir
- Nuevo diseño (feed 1080×1350 e historias 1080×1920): foto del municipio a toda la tarjeta, nombre grande, habitantes y grupo, medidor en arco de rojo a verde con el índice al centro, puesto en el departamento y en el país, y los cuatro pilares con su puntaje y color. Pie con «Datos públicos y fuentes oficiales. Lectura de datos, no una acusación.» y la dirección de la ficha.
- Los datos de la tarjeta salen ahora de los JSON del sitio (`infoTarjeta` en `compartir.js`), igual desde la ficha que desde la historia. Al compartir un pilar desde la historia, el medidor muestra el puntaje de ese pilar.

### Mejorado: el relevamiento de transparencia halla más (menos falsos «no hallado»)
- **Rastreo más profundo** (`relevamiento/rastreo.py`): si tras leer el menú de transparencia faltan criterios, abre hasta 2 niveles de las secciones que podrían tenerlos (según la estructura de la Resolución MinTIC 1519: información de la entidad, planeación, presupuesto, contratación, control, participación, datos abiertos), solo del mismo sitio, sin archivos y con tope de 6 páginas por municipio. Respeta `robots.txt` (y su `Crawl-delay`, con tope de 10 s), espera 2 s entre páginas del mismo sitio y se identifica con el agente propio. Los enlaces sin texto (iconos) se leen ahora por su texto interno, `title`, `aria-label` o dirección.
- **Cruce con fuentes oficiales** (`relevamiento/cruces.py`): un criterio que el sitio no muestra pero que SECOP II (contratación), SIGEP II (directorio y salarios, por NIT) o el catálogo de datos.gov.co (conjuntos de la propia alcaldía) sí muestran pasa a `fuente_oficial`, con la URL y un detalle. No se usan buscadores. El Kit de Planeación Territorial del DNP no se cruza: no tiene datos abiertos por municipio legibles sin raspar su portal (ver `docs/metodologia.md`).
- `transparencia_automatica.csv` gana la columna `detalle` (dónde se halló el enlace o cuántas páginas se leyeron sin éxito) y el resultado `fuente_oficial`. «No hallado» sigue sin significar «no publica» y todo sigue marcado «sin verificación humana, no puntúa».
- Corrida larga: `--particion K/N` reparte la revisión en varios procesos, `--unir` junta las partes, `--reanudar` salta lo ya revisado hoy, `--solo-cruces` reaplica los cruces sin rastrear; el CSV se guarda cada 25 municipios.
- La ficha y la historia muestran «Fuente oficial» (con enlace y detalle) y «Sin leer» donde corresponde; la hoja «Súmate al pedido» sigue proponiendo solo lo «no hallado».
- Pruebas sin red del rastreo (sitio ficticio), los cruces, la unión de partes y la ficha.
- Resultado en las 31 capitales (310 criterios; Quibdó conserva la revisión del 16/10 porque su sitio no respondió): «no hallado» bajó de 78 a 45, «enlace encontrado» subió de 212 a 248, «menú no legible» bajó de 20 a 7 y 10 criterios pasaron a «fuente oficial». El resto de los municipios (1.104) no se reejecutó: tarda unas 13 h en un equipo de 8 núcleos; queda para correr con `--alcance todos --particion K/N`.

### Agregado: «Lo que más le piden los vecinos»
- **Portada**: bloque con podio de 3 municipios (foto, total de pedidos, datos más pedidos, «Súmate al reclamo» y fila para compartir), lista del 4.º en adelante con «Cargar más», filtro por departamento y aviso «en vivo» con el último pedido. Se descarga solo al acercarse (`vecinos.js`, `pedidos.css`).
- **Historia de transparencia**: botón «Súmate al pedido · N pedidos» que abre la hoja «Lo que no encontramos» (con la fecha de la revisión automática, «sin verificación humana» y un enlace para avisar si ya lo publica): cada dato pendiente con su contador y «Quiero que lo publiquen»; al pedir, confirmación y compartir en WhatsApp, Instagram, Facebook, X, Threads, Telegram, copiar enlace o el menú del sistema.
- **Sin hosting propio**: `worker/` es el mismo servicio para Cloudflare Workers (plan gratuito + D1), con la misma API y pruebas; guía paso a paso en `docs/cloudflare.md`. La página de privacidad declara que, con el servicio activo, el navegador consulta a Cloudflare.
- **API PHP**: `apoyos.php` (una persona cuenta una vez por municipio y dato, por hash de IP) y `pedidos-ranking.php` (ranking y detalle por municipio); retención `dias_apoyos` (365) y límite `max_apoyos_hora`. Pruebas con `php -S`. Sin servidor, el bloque muestra el buscador y la hoja remite al formulario de la ficha.

### Cambiado
- Portada: la tarjeta «Índice municipal · promedio por departamento» crece en escritorio (400–660 px según la pantalla, barras más altas y textos algo mayores) para aprovechar el espacio libre a su izquierda del mapa; en móvil no cambia.

### Corregido: modo claro y modo oscuro (auditoría de contraste)
- Auditoría automática de **todo el texto visible** (WCAG AA, 4,5:1) en claro y oscuro, escritorio y móvil, páginas y estados (buscador, historia, hojas, comparador, filtros): de 96 fallos a 0.
- **Etiquetas de semáforo** (verde/amarillo/rojo) en claro: tenían fondo casi negro con letra oscura; ahora fondos claros propios y colores de texto más oscuros (`--ok`, `--warn`).
- **Ficha con foto** en claro: cabecera, habitantes, alcalde, anillos y miga de pan se leían oscuros sobre la foto; el héroe y la barra superior sobre la foto llevan tokens oscuros propios. Sin foto, el héroe ya no lleva el velo oscuro (quedaba gris) y la miga usa el color del tema.
- **Comparador** en claro: los alias de color (`--acento`, `--verde`…) se resolvían con los valores del tema claro; ahora se redefinen en el bloque oscuro.
- **Portada**: el podio de «Lo que más le piden los vecinos» y la intro llevan tokens oscuros propios (van sobre fotos/fondo oscuro); el selector de departamento usa el mismo estilo que los demás.
- Bordes y rellenos escritos en blanco fijo (selectores, buscador del ranking, barras vacías, filas de tablas y de hojas) ahora usan el color del tema; el azul de acento en oscuro sube a `#4a85ff` (4,7:1 sobre las superficies).
- **Móvil a 360 px**: la barra superior ocultaba parcialmente el botón de tema; sin la palabra «Colombia» caben los cuatro botones.

### Corregido
- Portada: el carrusel de municipios tiene botones de flecha (anterior/siguiente, que se apagan en los extremos); antes solo se podía avanzar con el teclado. Las listas desplegables de los filtros ya no salen en blanco sobre blanco en modo oscuro.
- Cifras en pesos: singular correcto («$ 1 millón», «$ 1 billón») y un decimal por debajo de 10 («$ 1,4 millones»); antes salía «$ 1 millones» y se perdía precisión. La cifra grande de «Gastó por vecino» en la ficha muestra el valor completo (como la historia) y se quitó el «(contexto)» del título, que ya dice «Contexto · no puntúa» encima.
- «Lo que más le piden los vecinos»: usa el mismo contenedor centrado y el mismo título grande que el resto de la portada; el armazón de la sección pasa a `editorial.css` (antes se veía sin estilo hasta que cargaba `pedidos.css`) y el estado vacío es una tarjeta contenida.
- La portada de la ficha (y la de la historia) omite la población, la superficie o la densidad cuando no hay dato, en lugar de mostrar «—».
- La portada de la ficha mostraba «habitantes · — · —» en el sitio publicado: `todo` calculaba el índice antes de los mapas, y la superficie (de donde sale la densidad) viene de los mapas. En una máquina limpia, como la de la publicación, esos datos no existían al calcular el índice. Ahora `todo` corre `mapas` antes que `indice` (con prueba del orden).
- Accesibilidad: los enlaces «Mapa», «Comparar» y «Contacto» del encabezado tenían nombre accesible vacío en pantallas angostas (solo se veía el icono); ahora llevan `aria-label` (aviso de PageSpeed Insights).

### Agregado
- Etiqueta de verificación de Google Search Console en todas las páginas (`google_verificacion` en `pipeline/config/sitio.toml`; quien haga un fork pone la suya).

### Agregado: SEO
- **Datos estructurados** (JSON-LD): `WebSite` y `Dataset` en la portada (para Google Dataset Search); `BreadcrumbList` en fichas y departamentos y `AdministrativeArea` en cada ficha.
- **Títulos** de ficha con índice y puesto («Sogamoso (Boyacá): índice 86,5/100, puesto 1 de 1.103 | …»), acortados cuando pasan de ~72 caracteres; título propio para la portada y los departamentos.
- **Imagen para redes** por defecto (`assets/img/og.jpg`, 1200 × 630) en todas las páginas sin foto, `og:locale`, `og:image:alt` y `twitter:image`.
- Un solo `h1` en la portada (la intro usa un párrafo), `alt` descriptivo en la foto de cada ficha y `noindex` en la 404.
- `docs/despliegue.md`: qué hace el sitio, dominio propio y Search Console.

### Corregido
- «Qué mide el índice» (portada): las tarjetas ya no quedan con sangría doble, los botones tienen aire arriba y entre sí, y ambos miden lo mismo.

### Corregido: «Compartir esta parte»
- La hoja de compartir quedaba **oculta** dentro de la historia (la regla que esconde la portada de fondo también la escondía a ella).
- Vista previa inmediata (la tarjeta se dibuja a escala pequeña) y la imagen completa se prepara de antemano: «Compartir» llama a la hoja del sistema sin esperas, como exigen los navegadores móviles. Antes la generaba tras el toque y podía caer a una descarga.
- La imagen se exporta en JPEG (≈ 180 KB en vez de 1,2 MB en PNG) y la foto ya no se sale de su franja en la tarjeta.
- «Compartir esta parte» comparte el capítulo en que estás (pilar y su puntaje); la historia se pausa mientras la hoja está abierta y `Esc` cierra solo la hoja.

### Fase 7: despliegue y revisión final
- `python -m municipios enlaces`: revisa que todos los enlaces y anclas internas de `dist/` existan (con prueba). Resultado actual: sin enlaces rotos.
- `docs/despliegue.md`: actualización mensual, revisión antes de publicar y aviso sobre `mirror --delete` en el workflow SFTP.
- Revisión de accesibilidad: el comparador tiene `h1`, el texto del hero va antes del mapa en el orden de tabulación (antes había que pasar por 33 departamentos para llegar al buscador) y «1 municipio» en singular.
- El conteo de la portada incluye la isla (1.104 municipios, igual que el resto del sitio).
- README con capturas (`docs/capturas/`, generadas con Chromium sin interfaz).

### Rendimiento de la portada
- La portada ya no descarga `pais.json` (118 KB) al abrir: el buscador lo pide la primera vez que se usa y el mapa lee un `departamentos.json` pequeño.
- `historia.js` (26 KB) y su CSS se cargan bajo demanda (al tocar, al apuntar o cuando el navegador está ocioso); `historia-enlaces.js` pesa 1 KB.
- Las fotos de las tarjetas piden la variante de 480 px (≈ 22 KB) en vez de la de 1080 px (≈ 95 KB) en pantallas habituales.
- Medido en local: DOMContentLoaded de ≈ 990 ms a ≈ 320 ms, sin tareas largas; HTML 125 KB (29 KB comprimido).

### Agregado y corregido (fase 6: formularios, rendimiento e íconos)
- **Formularios PHP**: el frontend pedía `reporte.php` y `pedido.php`, pero los archivos son `reportes.php` y `pedidos.php`; corregido. Nuevas pruebas de la API con el servidor integrado de PHP (`test_api_php.py`): origen, método, campo trampa, tiempo mínimo, límite por IP y hora, hash en lugar de la IP y borrado de lo viejo.
- **Portada más liviana**: el mapa ya no es 3D (sin `perspective`, sin cadena de `drop-shadow`); es un SVG plano con resalte al apuntar. Los trazados se re-simplifican al incrustarlos (`aligerar.py`) y la intro copia el mapa en vez de traerlo dos veces: el HTML de la portada baja de 246 KB a 125 KB. Las tarjetas ya no crean una capa 3D cada una.
- **Medidor**: el arco se dibuja exactamente hasta la aguja; antes el color podía pasarse del punto (con «reducir movimiento»).
- **Íconos pálidos**: el `<style>` de los mapas SVG en línea era global y pintaba también los íconos de la interfaz; ahora está acotado a cada mapa.

### Corregido (móvil y modo claro)
- Portada en móvil: el mapa va en su propia franja y la leyenda debajo; antes la leyenda tapaba el sur del país.
- Ranking en móvil: pestañas y semáforo en una fila desplazable y filtros compactos.
- Modo claro: el histograma usa la escala viva del mapa en lugar de los tonos de texto.

### Rediseño: comparador y ranking (e2e/07 y e2e/09)
- **Ranking**: titular gigante con pesos mezclados, pestañas por indicador (índice y los cuatro pilares), búsqueda, departamento, grupo y semáforo, histograma del índice con leyenda, barras por fila, «Ver más» (100 y luego de 50 en 50) y apertura de la historia en su sitio. Todo el listado sigue en el HTML para quien no use JavaScript. Nuevo `ranking.js`.
- **Comparador**: siempre oscuro, silueta del municipio cuando no hay foto, barras que crecen y datos de contexto en violeta. La silueta se comparte con las historias (`comun.js`).
- Modo claro: tarjetas, velo y mapa legibles; la historia y el comparador se mantienen oscuros.

### Corregido (rediseño según municipiosargentinos.net)
- **Historias reescritas**: ya no clonan la ficha estática. `historia.js` arma cada capítulo con los JSON del sitio (portada, transparencia, servicios y seguridad, gestión, control, contexto y resumen), con barras de progreso (9 s por capítulo), pausa, toque, teclas, rueda, deslizar para cerrar, siguiente municipio, hoja de método, «Compartir esta parte» y «Reportar». Nuevo `historia.css`.
- Las tarjetas del carrusel y las filas del ranking abren la historia en su sitio (`#departamento--municipio`), sin recargar.
- Hero de escritorio: titular a la izquierda y mapa a la derecha con grosor simulado; antes el titular desbordaba y tapaba el mapa.
- Tarjetas: se quitó un enlace dentro de otro enlace que sacaba la fuente fuera de la tarjeta; el gasto por habitante se muestra completo.
- Intro a dos columnas con barras de progreso; el mapa ya no desaparece con «reducir movimiento».
- Barra superior en móvil (nombre en una línea, botón de tema visible), chip de fecha y migas de la ficha sobre el héroe; unidades duplicadas («km² km²») en la ficha.
- El conteo de la portada usa solo municipios (1.103); el JSON de cada ficha incluye foto con crédito, revisión automática y enlace de reporte.

### Corregido (legibilidad, formularios y créditos)
- **Datos sobre las fotos.** El velo del héroe y de las tarjetas de la portada es más denso
  (arriba incluido) y todo el texto que va encima de una foto lleva sombra, así que se lee
  aunque la imagen sea clara o tenga mucho detalle. El porcentaje del índice, los puestos
  y el resumen suben de contraste sobre la foto.
- **Sin foto.** El héroe marca `sin-foto` cuando no hay imagen libre, de modo que en tema claro
  el texto vuelve a su color normal en lugar de quedar blanco sobre el fondo claro.
- **Formulario en móvil.** Los campos usan 16 px, lo que evita que iOS amplíe la página al
  enfocar; en pantallas angostas el botón ocupa todo el ancho. El campo trampa (honeypot) pasó
  a la utilidad `.visualmente-oculto`, así ya no se cuela ni genera desbordamiento en móvil.
- **Créditos.** El pie de página ahora acredita «Creado y mantenido por Angel Romero».

### Agregado (fase 7: despliegue)
- `docs/despliegue.md`: cómo publicar en GitHub Pages (sin formularios) o en un hosting
  propio con PHP (formularios activos), con la estructura de `privado/` y la tabla de
  configuración.
- `.github/workflows/deploy.yml`: despliegue manual por SFTP (opcional).

### Agregado (fase 6: formularios en PHP, opcionales)
- `web/api/`: `reportes.php`, `contacto.php` y `pedidos.php` con una librería compartida
  (`web/api/lib/comun.php`). Sin Composer, con PDO SQLite.
  - La base y la sal viven en `privado/`, **fuera** de la carpeta pública; nunca se versiona.
  - Límite de envíos por IP guardando solo `hash_hmac('sha256', ip, sal)` (nunca la IP),
    borrado de envíos a los 30 días, campo trampa (honeypot), control de tiempo mínimo y
    comprobación de origen; salida siempre en JSON y escapada.
- `privado/config.example.php` (versionado, sin valores) documenta qué hace falta.
- Formulario en cada ficha («Reportar un error» y «Pedir un dato») y en «Acerca» (contacto).
  Sin endpoint —como en GitHub Pages— caen al issue de GitHub prellenado o al correo; con PHP,
  envían a la API. `web/assets/js/formularios.js` decide según `config.js`.
- `.gitignore`: se versiona solo `privado/config.example.php`, nunca el resto de `privado/`.

### Cambiado (rediseño editorial)
- Lenguaje visual propio, inspirado en el tono editorial de municipiosargentinos.net pero
  reimplementado desde cero y con identidad colombiana:
  - tipografía libre Geist y Geist Mono (OFL), autoalojadas, para titular, texto y etiquetas
    monoespaciadas en mayúsculas;
  - **modo oscuro por defecto**, claro opcional con un botón que guarda la preferencia;
  - un acento fuerte único (azul cobalto), distinto del semáforo.
- **Ficha con foto**: cada municipio busca una imagen con licencia libre en Wikimedia Commons
  (`python -m municipios fotos`); se guarda en WebP (480 y 1080 px) con su crédito y licencia,
  siempre visibles. Sin foto, se dibuja la **silueta del municipio** a partir de su trazado en
  el mapa del departamento (`exportar/silueta.py`).
- **Portada**: intro animada de unos 4 segundos la primera vez, con «Saltar» siempre visible;
  carrusel de tarjetas con foto o silueta; chip «Datos oficiales · actualizado el …»;
  apariciones suaves con IntersectionObserver.
- **Modo historia a pantalla completa**: capítulos con la foto de fondo, avance por toque,
  teclas y barra de progreso, y botón para compartir.
- **Tarjeta para compartir** en `<canvas>` (feed 1080×1350): nombre, índice, semáforo, puesto y
  URL; se comparte como archivo o se descarga.
- `og:image` por ficha con su foto; el movimiento se desactiva con `prefers-reduced-motion`.

### Agregado (fase 5: relevamiento de transparencia)
- `python -m municipios relevamiento`: un navegador automático (Scrapling `DynamicFetcher`) abre el menú de transparencia de cada alcaldía y busca 10 criterios de la Ley 1712 por el texto y la dirección de cada enlace. Por defecto revisa las 31 capitales; `--alcance todos`, los 1.104 municipios.
  - Respeta `robots.txt`, pausa 3 s entre sitios y se identifica con un agente propio.
  - `datos/manual/sitios.csv`: 18 dominios propios verificados; el resto sigue el patrón `www.<municipio>-<departamento>.gov.co`.
  - Resultado en `datos/relevamiento/transparencia_automatica.csv`. Si el menú no se puede leer, se registra «menú no legible», nunca «no publica».
- Cada ficha con relevamiento muestra, en el pilar de transparencia, «Revisión automática del sitio web — sin verificación humana, no puntúa», con el estado de cada criterio, el enlace de evidencia y la fecha.
- `datos/manual/transparencia.csv` (solo encabezado) para la revisión humana, y el flujo documentado en `datos/manual/README.md` y `docs/metodologia.md`.
- Pruebas de `clasificar()`, `dominio()`, `candidatos()` y de la lectura del relevamiento, sin red.

### Agregado (fase 4: sitio web)
- Generación del sitio completo en `dist/` (`python -m municipios sitio`):
  - portada con buscador, cifras, mapa de departamentos con capas y listas de mejores y peores;
  - una ficha por municipio: índice, puestos, rango, pilares, cada indicador con valor, período, puntaje y fuente, contexto y mapa del departamento;
  - una página por departamento, con mapa coloreado y ranking;
  - ranking nacional con filtros y orden;
  - comparador con URL compartible;
  - metodología (generada desde `indice.toml`), fuentes y acerca/privacidad;
  - `sitemap.xml`, `robots.txt` y página 404.
- Diseño propio (modo claro y oscuro, escala de color accesible) y JavaScript sin dependencias.
- Fichas legibles en el celular: los indicadores se apilan como tarjetas.
- Modo historia en cada ficha y botón para reportar un error, que abre un issue con el municipio ya cargado.
- Configuración del sitio en `pipeline/config/sitio.toml`.

### Corregido
- ITA: Bogotá y los distritos (Barranquilla, Cartagena, Santa Marta, Tumaco, Buenaventura) figuran como «DISTRITAL» y quedaban sin dato. Ahora se identifica a la alcaldía por el nombre del sujeto obligado, sin alcaldías locales ni concejos. La cobertura pasa de 1.007 a 1.091 alcaldías.

### Agregado (fase 3: índice municipal v0.1)
- Fuente `grupos`: grupos de capacidades iniciales del DNP (MDM 2020) como pares del índice, con asignación documentada para dos municipios nuevos.
- Índice municipal v0.1 (`python -m municipios indice`), configurado en `pipeline/config/indice.toml`:
  - 4 pilares: transparencia 40, servicios y seguridad 30, gestión 15, control 15;
  - puntajes absolutos o percentil entre pares;
  - obligaciones no reportadas cuentan como 0;
  - tope de 39,9 sin cuentas;
  - tasas de delitos suavizadas;
  - puestos nacional, departamental y en el grupo;
  - rango de puestos con pesos ±10 puntos.
- `docs/metodologia.md`.

### Agregado (fase 2: indicadores automáticos)
- Fuentes:
  - transparencia (ITA de la Procuraduría);
  - Gobierno Digital (MinTIC);
  - desempeño institucional (FURAG);
  - finanzas (CUIPO: gastos, presupuesto e ingresos);
  - contratación (SECOP II);
  - educación (MEN);
  - salud (ADRES).
- Cruce por nombre de departamento y municipio, con alias verificados y corrección de la «Ñ» mal codificada.
- Registro de indicadores (`pipeline/config/indicadores.toml`): cada indicador tiene ficha y una prueba lo verifica.
- Patrón común de fuentes (`ejecutar(contexto) -> Resultado`) y CLI genérica.
- Modo `--tolerante` para `todo`: una fuente que falla no detiene el despliegue.
- GitHub Pages: el sitio se publica en cada push a `main`.

### Agregado (fase 1: base territorial)
- Fuente **población** (DANE): proyecciones municipales 2018-2042 por área (total, cabecera y rural), versión del 30 de julio de 2025.
- Fuente **MGN 2025** (DANE): contornos de los 1.122 municipios y 33 departamentos desde el WFS oficial, y superficie oficial en km².
- Mapas SVG en `web/data/mapas/`:
  - el nacional por departamentos, con San Andrés en recuadro;
  - uno por departamento, con sus municipios;
  - una página de vista previa.
- Geometría sin dependencias (Douglas-Peucker y áreas) y comandos `poblacion` y `mapas`.
- Dependencia `openpyxl` para leer el Excel del DANE.

### Agregado (fase 0: fundaciones)
- Estructura del repositorio, licencias (MIT para el código, CC BY 4.0 para los datos), guía de contribución, código de conducta y política de seguridad.
- Pipeline en Python con:
  - cliente de datos.gov.co (Socrata) con paginación, caché y token opcional;
  - registro de fuentes en `pipeline/config/fuentes.toml`;
  - fuente **DIVIPOLA** (DANE): lista oficial de municipios, nombres legibles y slugs únicos;
  - fuente **seguridad** (Ministerio de Defensa): homicidios y hurtos a personas por municipio y año.
- Pruebas unitarias sin red y CI en GitHub Actions (ruff, pytest, gitleaks).
- Decisiones de diseño 0001 a 0003.
