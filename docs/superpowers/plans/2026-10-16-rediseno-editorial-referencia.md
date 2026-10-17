# Rediseño editorial (referencia municipiosargentinos.net) — Plan de implementación

> **Para quien ejecuta:** sub-skill requerido: `superpowers:subagent-driven-development` (recomendado) o
> `superpowers:executing-plans`. Los pasos van con casillas (`- [ ]`).

**Goal:** Reconstruir la estética y el comportamiento del sitio para que sea equivalente al de
referencia (`https://municipiosargentinos.net/`), adaptado a Colombia, manteniendo el stack sin
frameworks y el funcionamiento sin JavaScript.

**Architecture:** Sitio estático generado por el pipeline Python. El rediseño vive en
`web/assets/css/*` (tokens + componentes), `web/assets/js/*` (módulos ES propios) y el marcado que
emiten `pipeline/municipios/exportar/paginas.py` y `plantillas.py`. Las fotos y el mapa SVG ya
existen. No se añaden dependencias.

**Tech Stack:** HTML semántico, CSS (custom properties, `clamp`, `color-mix`, `scroll-snap`,
`@supports`, View Transitions nativa), módulos ES, Web Animations API, SVG propio. Pipeline Python
existente.

**Spec (viaja con el plan):** `e2e/00-LEEME.md` … `e2e/12-plan-de-implementacion.md` y las
capturas `e2e/capturas/01-19`. Todos los valores exactos (colores, tamaños, tiempos, curvas,
estructura de cada capa) viven ahí; este plan solo los mapea a archivos del repositorio.

## Global Constraints (de `e2e/11`)

- Sitio publicado: HTML + CSS + JS puro (módulos ES). **Sin npm, sin compilación, sin librerías de
  terceros en el navegador.** PHP 8.1+ solo para formularios (ya hecho). Python solo en el pipeline.
- Nombres y comentarios en español; identificadores sin tildes. `ruff check`, `ruff format --check`,
  `pytest` en verde. Pruebas del pipeline para toda lógica nueva.
- Sin Google Fonts ni CDNs (fuentes autoalojadas, ya en `web/assets/fonts/`). Sin secretos.
- Cada cifra con fuente; nada «verificado» sin revisión humana. Funciona **sin JavaScript**.
- WCAG 2.1 AA; `prefers-reduced-motion` respetado en toda pieza animada.
- Commits a nombre de Angel Romero, **sin** `Co-Authored-By` ni «Generated with Claude Code».
- Acento único: `#3D7CFF` (el resto de tokens, ver `02`). Acento `--q-info` violeta para lo que no
  puntúa (subir a `#B58CF0`).
- Presupuesto: HTML de la ficha < 40 KB; JS total < 80 KB; fotos WebP con `srcset` y `loading="lazy"`
  (salvo 3 primeras tarjetas y la foto de la ficha).

## Asignación de archivos

| Archivo | Responsabilidad nueva |
|---|---|
| `web/assets/css/tokens.css` | Reescrito: tokens de `02` (colores, escala tipográfica, radios, sombras, curvas, `--gut`). Claro opcional. |
| `web/assets/css/base.css` | Tipografía base del sistema (`.lt`/`.o`, `.mono`, `.lede`, `.big`, `.h`), foco, utilidades. |
| `web/assets/css/componentes.css` | Componentes de `02`: pill, chip, segmentado `mseg`, gauge, anillo, `.bar2`, KPI, hoja `sheet`, modal, buscador, tarjetas del ranking. |
| `web/assets/css/editorial.css` | Piezas compuestas: top bar `.top`, hero+mapa, carrusel (`05`), historia (`06`), comparador (`07`), intro (`03`). |
| `web/assets/js/{inicio,carrusel,historia,mapa,comparar,compartir,tema,busqueda,comun,config}.js` | Reescritos/ampliados según `03`–`10`. |
| `pipeline/municipios/exportar/plantillas.py` | `documento()`: barra superior `.top` + iconos `<symbol>`, chip fijo, pie nuevo. |
| `pipeline/municipios/exportar/paginas.py` | `inicio()`, `ficha()` (historias + estática), `departamento()`, `ranking()` con el lenguaje nuevo. |
| `pipeline/tests/` | Pruebas para cada cambio de lógica del pipeline. |

---

## Fase A — Sistema de diseño y esqueleto (pasos 1–2 de `12`)

### Task 1: Tokens y tipografía (`02`)

**Files:** Modify `web/assets/css/tokens.css`, `web/assets/css/base.css`; Test `pipeline/tests/test_sitio.py` (assert de tokens presentes en el CSS emitido).

- [ ] Reescribir `tokens.css` con los tokens de `02`: `--ink:#0B0D10`, `--ink-2:#14171C`,
  `--fg:#F4F5F7`, `--mute:rgba(244,245,247,.62)`, `--line:rgba(255,255,255,.14)`,
  `--acc:#3D7CFF`, `--acc-fg:#06101F`, `--ok:#22C55E`, `--warn:#EAB308`, `--bad:#EF4444`,
  `--q-grad`, `--q-info:#B58CF0`, `--q-info-grad`, `--gut:clamp(16px,4vw,48px)`,
  `--ease:cubic-bezier(.2,.8,.2,1)`, `--expo:cubic-bezier(.16,1,.3,1)`, radios y sombras de `02`.
  Mantener el bloque `:root[data-tema="claro"]` con los valores de `11`.
- [ ] En `base.css`: clases `--` de escala — `.lt{font-weight:250;color:var(--mute)}`,
  `.o{font-weight:800;color:var(--fg)}`, `.acc{color:var(--acc)}`, `.mono{font-family:var(--fuente-mono);
  font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--mute)}`,
  `.lede`, `.lede.sm`, `.big`, `.h` con los `clamp()` de `02`.
- [ ] `body{-webkit-font-smoothing:antialiased;background:var(--ink);color:var(--fg)}`.
- [ ] Verificar: `python -m municipios sitio` y abrir `dist/` (fondo negro, titulares gigantes).
- [ ] `ruff`, `pytest`, commit.

### Task 2: Barra superior, chip fijo y pie (`04`, `09`)

**Files:** Modify `plantillas.py` (`documento()`), `componentes.css`, `editorial.css`.

- [ ] Sustituir `.cabecera` por `.top`: `position:fixed`, z 30, logo 28 px + «Municipios» 650 +
  «Colombia» 300; píldoras **Mapa**, **Comparar**, **Contacto** a la derecha; clase `solid` al
  bajar > 40 px (JS mínimo en `inicio.js`), con velo y blur de `04`.
- [ ] Definir el conjunto de iconos SVG como `<symbol>` (lupa, cerrar, VS, pausa, play, chevron,
  flecha, mapa, pin, expandir, más, menos, brújula, compartir, bandera, info) y usarlos con `<use>`.
- [ ] Chip fijo «Datos oficiales · última actualización dd/mm/aaaa» (píldora blanca, abajo a la
  derecha, z 40, enlace a fuentes).
- [ ] Pie nuevo (`plantillas.py`) con el pie de `09` (contacto, fuentes, metodología, legales),
  conservando el crédito «Creado y mantenido por Angel Romero».
- [ ] Commit.

### Task 3: Logo propio (`02`, `11`)

**Files:** `web/assets/img/icono.svg` (reescrito), `dist` favicon.

- [ ] Rediseñar la marca: mini gráfico de barras con **una** pieza en `--acc` (no las tres barras de
  la referencia). Animar su «armado» en la intro (Fase C). Commit.

---

## Fase B — Portada (pasos 3–5, 7 de `12`)

### Task 4: Carrusel de tarjetas (`05`)

**Files:** `paginas.py` (`inicio()`/`tarjeta_carrusel()`), `editorial.css`, `web/assets/js/carrusel.js` (nuevo), `pipeline/tests/test_paginas.py`.

- [ ] Tarjeta 9:15 `min(72vw,300px)`, radio 22, foto a sangre, degradado de `05`, chip «● Índice NN»
  arriba-izq., puesto mono arriba-der., bloque inferior (nombre 30 px/750, línea gris, recuadro
  informativo con FUENTE). Sin foto → silueta.
- [ ] Encabezado `.rail-h` («Elige un municipio» + conteo mono) y filtros (select de departamento +
  píldoras de grupo DNP). Orden por índice desc.; 40 primeros.
- [ ] `carrusel.js`: tilt 3D por `scroll` + `requestAnimationFrame` (`rotateY`, `translateZ`),
  entrada escalonada de las 8 primeras, `scroll-snap`, arrastre con mouse, ondulación al clic y
  View Transition de la foto hacia la historia. Con `prefers-reduced-motion`: sin tilt/entrada.
- [ ] Pruebas: el HTML contiene chip, puesto y nombre; orden correcto. Commit.

### Task 5: Hero + mapa SVG con CSS 3D (`04`)

**Files:** `paginas.py` (`inicio()`), `editorial.css`, `web/assets/js/mapa.js`, `web/assets/js/inicio.js`.

- [ ] Hero: titular mezclado («¿Tu municipio **muestra** sus **cuentas**?»), párrafo, buscador 54 px
  con panel de sugerencias. En ≥1024 px se superpone al mapa (`min(50vw,780px)`, `padding-top` 112).
- [ ] Mapa SVG (ya existe en `dist/data/mapas/colombia.svg`) con `perspective:1200px;
  rotateX(38deg)` y capas `translateZ` para simular extrusión; fallback plano sin 3D.
- [ ] Pestañas de capa (segmentado `mseg`): Índice, Transparencia, Servicios, Seguridad, Gestión,
  Control, Gasto (violeta). Recolorean y re-extruyen con transición.
- [ ] Hover → tooltip rico; clic → panel de detalle (hoja móvil / panel lateral escritorio) con foto,
  nombre, autoridad, cifra, KPIs, pares y botones. Leyenda con histograma (oculta < 768 px).
- [ ] Commit.

### Task 6: `inicio()` recompuesto (`01`)

- [ ] Orden de la portada de `01`: intro, `.top`, hero+mapa, carrusel, (sin secciones de comunidad
  del sitio argentino), ranking, pie, chip fijo. Commit.

---

## Fase C — Interactivo (pasos 5–6, 8–9)

### Task 7: Historias (`06`) — la pieza central
**Files:** `paginas.py` (`ficha()` + capítulos), `editorial.css`, `web/assets/js/historia.js`.

- [ ] Capa `#story` con `.st-bg` (Ken Burns), `.st-shade` (dim ≥ cap.1), `.st-ui` (`.prog`,
  `.st-head`, `.st-body`). Hash `#<slug>` con `replaceState`; abrir por URL con hash.
- [ ] 9 s por capítulo, pausa (botón/mantener/hojas), toque izq./der., flechas, Espacio, rueda,
  deslizar para cerrar, siguiente/anterior municipio. 7 capítulos de `11` (00 Portada, 01
  Transparencia, 02 Servicios y seguridad, 03 Gestión, 04 Control, 05 Contexto, 06 Resumen).
- [ ] Animación de entrada por capítulo (split palabra a palabra, conteo, barras, anillos, Ken Burns).
- [ ] Ojo con **Reportar** y **Compartir esta parte** (excepto portada y resumen). Hojas FUENTE/MÉTODO.
- [ ] Cada cifra con botón FUENTE a la URL exacta. Aviso rojo «Sin dato» cuando falte.
- [ ] Pruebas del generador de capítulos (con y sin datos). Commit.

### Task 8: Compartir en canvas (`08`)
**Files:** `web/assets/js/compartir.js`, `editorial.css`.

- [ ] Hoja de compartir (feed 1080×1350 / stories 1080×1920), pestañas, tres acciones, rejilla de
  redes. Tarjeta por municipio y por capítulo con capas de `08`. Pausa la historia. Commit.

### Task 9: Comparador (`07`)
**Files:** `paginas.py` (`comparar()`), `web/assets/js/comparar.js`, `editorial.css`.

- [ ] `#cmp` a pantalla completa, dos mitades con foto+select, «VS», titular-resumen y una «duel» por
  rubro (barras opuestas). URL `comparar/?a=…&b=…`. Commit.

---

## Fase D — Intro, ranking, estáticas y pulido (pasos 8–12)

### Task 10: Intro (`03`)
- [ ] `#intro` en `<head>` antes del primer render (marca en `localStorage`), 4,5 s, «Saltar» visible,
  aterrizaje sobre el mapa, `aria-modal`, sin JS no existe. Cifras reales del `<script>` de datos.

### Task 11: Ranking y páginas estáticas (`09`)
- [ ] Ranking en la portada (lista `.rk`, barras, «Ver más» 20 en 20). Rediseñar `m/<slug>/`,
  `ranking/`, `metodologia/` (héroe con foto, puntaje 56 px con barra degradada, rejilla `dl`).

### Task 12: Movimiento y accesibilidad (`10`)
- [ ] Curvas/duraciones de `10`, `prefers-reduced-motion` en toda pieza, foco, `aria-*`, áreas ≥44 px,
  funciona sin JS, consola sin errores. Revisión final con capturas (escritorio 1440×900 y móvil
  390×844, oscuro y claro).

---

## Autorevisión

- **Cobertura:** cada paso 1–12 de `e2e/12` tiene tarea (1→Task 1, 2→2/3/6, 3→ya previsto, 4→4,
  5→7, 6→8, 7→5, 8→10, 9→9, 10→11, 11→12, 12→12).
- **Consistencia:** nombres de clases tomados de `02` (`mseg`, `bar2`, `.rk`, `.sheet`, `.big`, `.h`,
  `.lede`, `.st-*`, `#cmp`, `#story`, `#intro`) usados igual en todo el plan.
- **Riesgo mayor:** el mapa 3D sin librería (Task 5) — se acepta la versión SVG + CSS 3D.
