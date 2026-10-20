// Ficha en formato historias (e2e/06): capa a pantalla completa con un capítulo por pantalla.
// Cada capítulo se arma con los JSON del sitio (data/m/<código>.json, indice.json, pais.json).
import { cargarJSON, dibujarSilueta, escapar as esc, formatoNumero as num, formatoSegunUnidad as fmt, raiz } from './comun.js';
import { compartir } from './compartir.js';
import { CRITERIOS, ICONO_ALTAVOZ, abrirHojaPedido, cargarEstilos as estilosPedidos, detalle as detallePedidos } from './pedidos.js';

const DURACION = 9000; // ms por capítulo
const SIN_MOVIMIENTO = matchMedia('(prefers-reduced-motion: reduce)').matches;
const TEXTO = { verde: 'Verde', amarillo: 'Amarillo', rojo: 'Rojo' };
const CAPITULOS = ['portada', 'T', 'S', 'G', 'C', 'contexto', 'resumen'];
const TITULOS = {
  portada: 'Portada',
  T: '¿Muestra sus cuentas?',
  S: 'Servicios y seguridad',
  G: 'Gestión',
  C: 'Control',
  contexto: 'Contexto',
  resumen: 'En resumen',
};
const TITULARES = {
  T: '<span class="lt">¿Muestra</span> <span class="neg">sus cuentas?</span>',
  S: '<span class="lt">Servicios</span> <span class="neg">y seguridad</span>',
  G: '<span class="lt">Cómo gestiona</span> <span class="neg">sus recursos</span>',
  C: '<span class="lt">Qué dice</span> <span class="neg">el control</span>',
};
const CONTEXTO_KPI = [
  'poblacion',
  'superficie_km2',
  'densidad',
  'ingresos_tributarios_por_habitante',
  'dependencia_transferencias',
  'contratos_numero',
  'contratos_valor',
  'mdm_puntaje',
];

let estilos = null;

/** La hoja de estilos de las historias se descarga la primera vez que hace falta. */
export function cargarEstilos() {
  estilos ??= new Promise((resolver) => {
    const enlace = document.createElement('link');
    enlace.rel = 'stylesheet';
    enlace.href = new URL('../css/historia.css', import.meta.url).href;
    enlace.onload = enlace.onerror = () => resolver();
    document.head.append(enlace);
  });
  return estilos;
}

let datosGlobales = null; // { idx, pais, orden }
let abierta = null; // estado de la historia abierta

async function base() {
  if (!datosGlobales) {
    const [idx, pais] = await Promise.all([cargarJSON('data/indice.json'), cargarJSON('data/pais.json')]);
    const f = pais.campos.indexOf.bind(pais.campos);
    const orden = pais.municipios
      .filter((m) => m[f('indice')] !== null)
      .sort((a, b) => b[f('indice')] - a[f('indice')])
      .map((m) => ({ codigo: m[f('codigo')], slug: m[f('slug')] }));
    const porSlug = Object.fromEntries(pais.municipios.map((m) => [m[f('slug')], m[f('codigo')]]));
    datosGlobales = { idx, pais, orden, porSlug };
  }
  return datosGlobales;
}

// --- piezas pequeñas ------------------------------------------------------------------------
const estado = (v, idx) =>
  v === null || v === undefined ? 'sin' : v < idx.semaforo.rojo_menor_a ? 'rojo' : v >= idx.semaforo.verde_desde ? 'verde' : 'amarillo';

const SIGLAS = {
  dane_: 'DANE',
  mindefensa_: 'MinDefensa',
  pgn_: 'Procuraduría',
  mintic_: 'MinTIC',
  funcion_publica_: 'Función Pública',
  cgr_: 'Contraloría (CUIPO)',
  cce_: 'SECOP II',
  men_: 'MinEducación',
  adres_: 'ADRES',
  dnp_: 'DNP',
};
const sigla = (clave) => Object.entries(SIGLAS).find(([p]) => clave.startsWith(p))?.[1] ?? clave;

function fuentes(claves, idx) {
  const vistas = new Set();
  return (claves ?? [])
    .filter((k) => idx.fuentes[k] && !vistas.has(sigla(k)) && vistas.add(sigla(k)))
    .map((k) => {
      const f = idx.fuentes[k];
      return `<a href="${esc(f.url)}" target="_blank" rel="noopener" title="${esc(f.organismo)}: ${esc(f.titulo)}">${esc(sigla(k))}</a>`;
    })
    .join(' · ');
}

function medidor(valor, idx, etiqueta) {
  if (valor === null || valor === undefined) return '<div class="nd-red"><span class="nd-red__ico">!</span><span>Sin dato suficiente</span></div>';
  const t = Math.max(0, Math.min(1, valor / 100));
  const a = Math.PI * (1 - t);
  const x = (100 + 80 * Math.cos(a)).toFixed(2);
  const y = (100 - 80 * Math.sin(a)).toFixed(2);
  const e = estado(valor, idx);
  // El arco termina exactamente en la aguja (nunca más allá), con o sin animación.
  const arco = t > 0.002 ? `<path class="gauge__arco gauge__arco--${e}" d="M20 100 A80 80 0 0 1 ${x} ${y}" pathLength="1"/>` : '';
  return `<figure class="gauge" role="img" aria-label="${esc(etiqueta)}: ${num(valor)} de 100, estado ${TEXTO[e]}">
    <svg viewBox="0 0 200 108" aria-hidden="true"><path class="gauge__pista" d="M20 100 A80 80 0 0 1 180 100"/>${arco}
    <circle class="gauge__aguja" cx="${x}" cy="${y}" r="7"/></svg>
    <figcaption><span class="gauge__valor" data-cuenta="${valor}">${num(valor)}</span><span class="gauge__de">de 100</span>
    <span class="chip chip--sombra"><span class="chip__punto chip__punto--${e}"></span>${TEXTO[e]}</span></figcaption></figure>`;
}

const ojo = (n, texto, extra = '') =>
  `<div class="hi-ojo mono"><b>${String(n).padStart(2, '0')}</b><span>${esc(texto)}</span>${extra}</div>`;

function botonesCapitulo(cap) {
  const compartirBtn =
    cap === 'portada' || cap === 'resumen'
      ? ''
      : '<button type="button" class="hi-mini" data-compartir-cap aria-label="Compartir esta parte"><span aria-hidden="true">↗</span> Compartir esta parte</button>';
  return `${compartirBtn}<button type="button" class="hi-mini" data-reportar aria-label="Reportar un error en esta parte"><span aria-hidden="true">⚑</span> Reportar</button>`;
}

// --- capítulos -------------------------------------------------------------------------------
function portada(m, { idx, pais }) {
  const dato = (k) => (m.datos[k] ? fmt(m.datos[k].valor, idx.indicadores[k]?.unidad ?? '') : null);
  const lineas = [dato('poblacion') && `${dato('poblacion')} habitantes`, dato('superficie_km2'), dato('densidad')].filter(Boolean);
  const p = m.puesto;
  const tam = m.nombre.length > 18 ? 9 : m.nombre.length > 12 ? 13 : 18;
  const puestos = p
    ? `<dl class="hi-puestos"><div><dt>En el país</dt><dd>${num(p.nacional, 0)}<small> de ${num(p.nacional_de, 0)}</small></dd></div>
       <div><dt>En ${esc(m.departamento)}</dt><dd>${num(p.departamento, 0)}<small> de ${num(p.departamento_de, 0)}</small></dd></div>
       <div><dt>En su grupo</dt><dd>${num(p.grupo, 0)}<small> de ${num(p.grupo_de, 0)}</small></dd></div></dl>`
    : '';
  const cred = m.foto
    ? `<p class="hi-cred mono">Foto: ${esc(m.foto.autor.slice(0, 60))} · <a href="${esc(m.foto.url_licencia || m.foto.url_pagina)}" target="_blank" rel="noopener">${esc(m.foto.licencia)}</a> · <a href="${esc(m.foto.url_pagina)}" target="_blank" rel="noopener">Wikimedia Commons</a></p>`
    : '';
  return `${ojo(0, `Portada · ${m.departamento}`, botonesCapitulo('portada'))}
    ${cred}
    <h2 class="hi-nombre" style="font-size:clamp(48px,min(${tam}vw,15vh),180px)">${esc(m.nombre)}</h2>
    <p class="hi-lede">${lineas.map(esc).join(' · ')}${m.grupo ? ` · ${esc(pais.grupos[m.grupo] ?? m.grupo)}` : ''}</p>
    <div class="hi-indice">${medidor(m.indice, idx, 'Índice municipal')}${puestos}</div>
    ${m.indice === null ? `<div class="nd-red"><span class="nd-red__ico">!</span><span>${esc(m.motivo_sin_indice ?? 'Este municipio no tiene índice.')}</span></div>` : ''}
    <div class="hi-acciones">
      <button type="button" class="pill pill--claro hi-grande" data-ir="1">Empezar <span aria-hidden="true">→</span></button>
      <a class="pill" href="${raiz}comparar/?a=${m.codigo}">Comparar</a>
      <button type="button" class="pill" data-compartir-cap>Compartir</button>
      <a class="pill" href="${raiz}m/${m.slug}/">Ficha completa</a>
    </div>`;
}

function bloqueAuto(m) {
  const a = m.auto;
  if (!a) return '';
  const hay = a.criterios.some(([, r]) => r === 'enlace_encontrado' || r === 'no_encontrado');
  const lista = hay
    ? `<ul class="tchips">${a.criterios
        .map(([c, r, ev]) => {
          const ok = r === 'enlace_encontrado';
          const txt = ok ? `<a href="${esc(ev)}" target="_blank" rel="noopener">Enlace</a>` : 'No hallado';
          return `<li class="${ok ? 'c-ok' : 'c-na'}"><i></i><span>${esc(CRITERIOS[c] ?? c)}</span><b>${txt}</b></li>`;
        })
        .join('')}</ul>`
    : '<p class="hi-nota">El menú de transparencia de la alcaldía no se pudo leer de forma automática.</p>';
  return `<section class="hi-auto"><p class="mono hi-auto__t">Revisión automática del sitio web · sin verificación humana · no puntúa</p>${lista}
    <p class="hi-nota mono">Revisado el ${esc(a.fecha)}. Solo lee la página principal del menú.</p></section>`;
}

function botonPedir() {
  return `<div class="hi-pedir"><button type="button" class="pill pill--claro" data-pedir>${ICONO_ALTAVOZ}<b>Súmate al pedido</b><span class="mono" data-pedir-n hidden></span></button></div>`;
}

/** Datos de transparencia que no encontramos: criterios no hallados por el robot y cifras sin dato. */
function datosPendientes(m, idx) {
  const faltan = new Set((m.auto?.criterios ?? []).filter(([, r]) => r === 'no_encontrado').map(([c]) => c));
  const criterios = Object.keys(CRITERIOS).filter((c) => (m.auto ? faltan.has(c) : true)).map((c) => ({ id: c, nombre: CRITERIOS[c] }));
  const cifras = (idx.pilares.find((p) => p.id === 'T')?.componentes ?? []).filter((c) => !m.datos[c.id]).map((c) => ({ id: c.id, nombre: c.nombre }));
  return [...criterios, ...cifras];
}

async function mostrarPedidos() {
  const boton = abierta?.capa.querySelector('[data-pedir-n]');
  const d = await detallePedidos(abierta?.m.codigo);
  const destino = abierta?.capa.querySelector('[data-pedir-n]') ?? boton;
  if (!destino || !d) return;
  destino.textContent = `${num(d.total, 0)} ${d.total === 1 ? 'pedido' : 'pedidos'}`;
  destino.hidden = d.total === 0;
}

async function pedirActual(boton) {
  const { m, ctx } = abierta;
  const hayPausa = abierta.pausado;
  if (!hayPausa) pausa(true, true);
  boton.addEventListener('pedido', mostrarPedidos, { once: true });
  await abrirHojaPedido(
    { codigo: m.codigo, nombre: m.nombre, slug: m.slug, revision: m.auto?.fecha, reportar: m.reportar },
    datosPendientes(m, ctx.idx),
    boton,
  );
  if (abierta && !hayPausa) pausa(false, true);
}

function pilar(id, n, m, { idx }) {
  const p = idx.pilares.find((x) => x.id === id);
  const info = m.pilares[id] ?? {};
  const puntaje = info.valido ? info.puntaje : null;
  const filas = p.componentes
    .map((c) => {
      const d = m.datos[c.id];
      const pt = m.componentes[c.id]?.puntaje;
      const unidad = idx.indicadores[c.id]?.unidad ?? '';
      const e = estado(pt, idx);
      const valor = d ? esc(fmt(d.valor, unidad)) : `<span class="hi-sin">${c.si_falta !== null ? 'No reportó' : 'Sin dato'}</span>`;
      const barra =
        pt === null || pt === undefined
          ? '<span class="bar2 bar2--vacio" role="img" aria-label="Sin puntaje"></span>'
          : `<span class="bar2" role="img" aria-label="${esc(c.nombre)}: ${num(pt, 0)} de 100"><i class="bar2__f bar2__f--${e}" style="width:${Math.max(pt, 1)}%"></i></span>`;
      const fu = d ? fuentes(d.fuentes, idx) : fuentes([idx.indicadores[c.id]?.fuente], idx);
      return `<li class="hi-fila"><div class="hi-fila__t"><span>${esc(c.nombre)}</span><b>${valor}</b></div>${barra}
        <p class="hi-fila__pie mono">${d ? esc(d.periodo) + ' · ' : ''}${fu || '—'}${c.puntaje === 'pares' ? ' · entre pares' : ''}</p></li>`;
    })
    .join('');
  const tope =
    id === 'T' && m.tope
      ? '<div class="nd-red"><span class="nd-red__ico">!</span><span>Su índice está topado en 39,9 porque no reportó su ejecución presupuestal.</span></div>'
      : '';
  const aviso =
    puntaje === null
      ? '<div class="nd-red"><span class="nd-red__ico">!</span><span>No hay datos suficientes para puntuar este pilar.</span></div>'
      : '';
  return `${ojo(n, TITULOS[id], botonesCapitulo(id))}
    <h2 class="hi-h">${TITULARES[id]}</h2>
    <div class="hi-pilar">${medidor(puntaje, idx, p.nombre)}
      <div class="hi-pilar__txt"><p class="mono">${num(p.peso, 0)} % del índice</p><p>${esc(p.descripcion)}</p></div></div>
    ${aviso}${tope}
    <ul class="hi-filas">${filas}</ul>
    ${id === 'T' ? bloqueAuto(m) + botonPedir() : ''}`;
}

function contexto(m, { idx }) {
  const g = m.datos.gasto_por_habitante;
  const grande = g
    ? `<p class="hi-gigante"><span class="hi-gigante__n" data-cuenta="${g.valor}">${esc(fmt(g.valor, 'pesos por habitante'))}</span>
       <small class="mono">${esc(g.periodo)} · ${fuentes(g.fuentes, idx)}</small></p>`
    : '<div class="nd-red"><span class="nd-red__ico">!</span><span>Sin dato de gasto por habitante.</span></div>';
  const kpis = CONTEXTO_KPI.filter((k) => m.datos[k])
    .map((k) => {
      const d = m.datos[k];
      return `<div class="hi-kpi"><p>${esc(idx.indicadores[k]?.etiqueta ?? k)}</p><b>${esc(fmt(d.valor, idx.indicadores[k]?.unidad ?? ''))}</b>
        <small class="mono">${esc(d.periodo)} · ${fuentes(d.fuentes, idx)}</small></div>`;
    })
    .join('');
  return `${ojo(5, TITULOS.contexto, botonesCapitulo('contexto'))}
    <h2 class="hi-h"><span class="lt">Cuánto gasta</span> <span class="neg">por habitante</span></h2>
    ${grande}
    <div class="hi-kpis">${kpis}</div>
    <p class="hi-nota mono"><span class="info">●</span> Datos de contexto: no puntúan en el índice.</p>`;
}

function senales(m, { idx }) {
  const filas = idx.pilares.map((p) => {
    const i = m.pilares[p.id];
    const v = i?.valido ? i.puntaje : null;
    return { id: p.id, nombre: p.nombre, v, e: estado(v, idx), texto: v === null ? 'Sin dato' : `${num(v, 0)}/100` };
  });
  const pu = m.puesto;
  filas.push({
    id: 'indice',
    nombre: 'Índice municipal',
    v: m.indice,
    e: estado(m.indice, idx),
    texto: m.indice === null ? 'Sin índice' : `${num(m.indice)}/100${pu ? ` · puesto ${num(pu.nacional, 0)} de ${num(pu.nacional_de, 0)}` : ''}`,
  });
  return filas;
}

function resumen(m, ctx) {
  const s = senales(m, ctx);
  const rojos = s.filter((x) => x.e === 'rojo').length;
  const ambar = s.filter((x) => x.e === 'amarillo').length;
  const con = s.filter((x) => x.e !== 'sin').length;
  const pl = (n, a, b) => (n === 1 ? a : b);
  const titular =
    con < 2
      ? '<span class="lt">Con los datos publicados</span> <span class="neg">hay poco para evaluar</span>'
      : rojos
        ? `<span class="lt">Hay</span> <span class="neg">${rojos} ${pl(rojos, 'señal', 'señales')}</span> <span class="lt">para mirar de cerca</span>`
        : ambar
          ? `<span class="lt">Hay</span> <span class="neg">${ambar} ${pl(ambar, 'aspecto', 'aspectos')}</span> <span class="lt">para mejorar</span>`
          : '<span class="neg">Buenos resultados</span> <span class="lt">frente a sus pares</span>';
  const lista = s
    .map(
      (x) => `<li class="hi-senal hi-senal--${x.e}"><i></i><span>${esc(x.nombre)} · <b>${esc(x.texto)}</b></span>
      <button type="button" class="hi-metodo mono" data-metodo="${x.id}" aria-label="Cómo se calcula: ${esc(x.nombre)}">Método</button></li>`,
    )
    .join('');
  const rango = m.rango_puestos ? `Si se mueven ±10 puntos los pesos de los pilares, su puesto va del ${num(m.rango_puestos[0], 0)} al ${num(m.rango_puestos[1], 0)}.` : '';
  return `${ojo(6, TITULOS.resumen, botonesCapitulo('resumen'))}
    <h2 class="hi-h">${titular}</h2>
    <ul class="hi-veredicto">${lista}</ul>
    <p class="hi-nota">Lo que pesa es si muestra sus cuentas, qué servicios y seguridad tiene su gente frente a municipios parecidos, cómo gestiona y qué dice el control. ${esc(rango)} El gasto por habitante es contexto: no es bueno ni malo por sí solo.</p>
    <div class="hi-acciones">
      <a class="pill pill--claro" href="${raiz}comparar/?a=${m.codigo}">Comparar con otro</a>
      <button type="button" class="pill" data-compartir-cap>Compartir</button>
      <button type="button" class="pill" data-siguiente-muni>Siguiente municipio <span aria-hidden="true">→</span></button>
    </div>`;
}

function html(cap, m, ctx) {
  if (cap === 'portada') return portada(m, ctx);
  if (cap === 'contexto') return contexto(m, ctx);
  if (cap === 'resumen') return resumen(m, ctx);
  return pilar(cap, CAPITULOS.indexOf(cap), m, ctx);
}

// --- hoja de método ----------------------------------------------------------------------------
function metodo(id, m, { idx }) {
  if (id === 'indice') {
    return `<p>El índice resume los cuatro pilares con sus pesos (${idx.pilares.map((p) => `${esc(p.nombre)} ${num(p.peso, 0)} %`).join(', ')}). Si no reportó su ejecución presupuestal, queda en 39,9 como máximo.</p>`;
  }
  const p = idx.pilares.find((x) => x.id === id);
  const comp = p.componentes
    .map((c) => `<li>${esc(c.nombre)} <small>(${c.puntaje === 'pares' ? 'puntaje entre pares: percentil dentro de su grupo' : 'escala absoluta'})</small></li>`)
    .join('');
  return `<p>${esc(p.descripcion)}</p><p>Pesa ${num(p.peso, 0)} % del índice y se compone de:</p><ul>${comp}</ul>`;
}

// --- capa ----------------------------------------------------------------------------------------
function cerrarHoja() {
  document.querySelector('.hi-hoja')?.remove();
  if (abierta) pausa(abierta.pausadoPorHoja ? false : abierta.pausado, true);
  if (abierta) abierta.pausadoPorHoja = false;
}

function abrirHoja(titulo, cuerpo) {
  cerrarHoja();
  const h = document.createElement('div');
  h.className = 'hi-hoja';
  h.setAttribute('role', 'dialog');
  h.setAttribute('aria-modal', 'true');
  h.setAttribute('aria-label', titulo);
  h.innerHTML = `<button type="button" class="hi-x" data-hoja-x aria-label="Cerrar">✕</button><h3>${esc(titulo)}</h3>${cuerpo}
    <p><a href="${raiz}metodologia/">Ver la metodología completa</a></p><button type="button" class="pill pill--claro" data-hoja-x>Entendido</button>`;
  abierta.capa.append(h);
  if (!abierta.pausado) {
    abierta.pausadoPorHoja = true;
    pausa(true, true);
  }
  h.querySelectorAll('[data-hoja-x]').forEach((b) => b.addEventListener('click', cerrarHoja));
  h.querySelector('.pill').focus();
}

function pausa(v, silencioso) {
  if (!abierta) return;
  abierta.pausado = v;
  abierta.capa.classList.toggle('hi-pausa', v);
  const b = abierta.capa.querySelector('[data-pausa]');
  if (b) {
    b.textContent = v ? '▶' : '❚❚';
    b.setAttribute('aria-label', v ? 'Seguir' : 'Pausar');
  }
  void silencioso;
}

function mostrar(i, dir = 1) {
  const a = abierta;
  if (!a) return;
  const n = Math.max(0, Math.min(CAPITULOS.length - 1, i));
  a.i = n;
  const cap = CAPITULOS[n];
  const cuerpo = a.capa.querySelector('[data-cuerpo]');
  cuerpo.innerHTML = `<article class="hi-cap" data-cap="${cap}" style="--dir:${dir}">${html(cap, a.m, a.ctx)}</article>`;
  cuerpo.scrollTop = 0;
  a.capa.classList.toggle('hi-oscura', n >= 1);
  a.capa.querySelectorAll('.hi-prog i').forEach((barra, j) => {
    barra.className = j < n ? 'hecho' : '';
    if (j === n) {
      void barra.offsetWidth;
      barra.className = 'activo';
    }
  });
  a.capa.querySelector('[data-titulo-cap]').textContent = TITULOS[cap];
  const fondo = a.capa.querySelector('.hi-bg');
  fondo.style.animation = 'none';
  void fondo.offsetWidth;
  fondo.style.animation = '';
  fondo.dataset.k = String(n % 4);
  cuerpo.querySelectorAll('[data-cuenta]').forEach(contar);
  if (cuerpo.querySelector('[data-pedir]')) {
    estilosPedidos();
    mostrarPedidos();
  }
  cuerpo.querySelectorAll('.hi-cap > *').forEach((el, k) => el.style.setProperty('--k', k));
}

function contar(el) {
  if (SIN_MOVIMIENTO) return;
  const final = el.textContent;
  const hasta = Number(el.dataset.cuenta);
  if (!Number.isFinite(hasta) || hasta === 0) return;
  const t0 = performance.now();
  const paso = (t) => {
    if (!el.isConnected) return;
    const p = Math.min(1, (t - t0) / 1300);
    const v = hasta * (1 - (1 - p) ** 3);
    el.textContent = p < 1 ? final.replace(/[\d.,]+/, hasta >= 1000 ? num(Math.round(v), 0) : num(v)) : final;
    if (p < 1) requestAnimationFrame(paso);
  };
  requestAnimationFrame(paso);
}

function siguiente() {
  if (!abierta) return;
  if (abierta.i < CAPITULOS.length - 1) mostrar(abierta.i + 1, 1);
  else vecino(1);
}

function anterior() {
  if (!abierta) return;
  if (abierta.i > 0) mostrar(abierta.i - 1, -1);
  else vecino(-1);
}

async function vecino(d) {
  const { orden } = await base();
  const k = orden.findIndex((o) => o.codigo === abierta.m.codigo);
  const o = orden[(k + d + orden.length) % orden.length];
  const origen = abierta.origen;
  cerrar(true);
  abrirHistoria(o.codigo, 0, origen);
}

async function compartirActual(boton) {
  const { m, ctx, i } = abierta;
  const cap = CAPITULOS[i];
  const pilarCap = ctx.idx.pilares.find((p) => p.id === cap);
  const info = pilarCap ? m.pilares[cap] : null;
  const valorPilar = info?.valido ? info.puntaje : null;
  const compartePilar = pilarCap && valorPilar !== null;
  const hayPausa = abierta.pausado;
  if (!hayPausa) pausa(true, true); // la historia no avanza mientras está abierta la hoja
  await compartir(
    {
      nombre: m.nombre,
      slug: compartePilar ? `${m.codigo}-${cap.toLowerCase()}` : m.codigo,
      etiqueta: compartePilar ? pilarCap.nombre : '',
      valor: compartePilar ? valorPilar : m.indice,
      semaforo: compartePilar ? estado(valorPilar, ctx.idx) : m.semaforo,
      puesto: !compartePilar && m.puesto ? String(m.puesto.nacional) : '',
      foto: m.foto ? new URL(`${raiz}assets/fotos/${m.codigo}-1080.webp`, location.href).href : null,
      url: new URL(`${raiz}m/${m.slug}/`, location.href).href,
    },
    boton,
  );
  if (abierta && !hayPausa) pausa(false, true);
}

function cerrar(sinFoco) {
  const a = abierta;
  if (!a) return;
  a.capa.remove();
  abierta = null;
  document.removeEventListener('keydown', teclas, true);
  document.documentElement.classList.remove('lock');
  if (!sinFoco) {
    history.replaceState(null, '', location.pathname + location.search);
    a.origen?.focus?.();
  }
}

function teclas(e) {
  if (!abierta || document.querySelector('.sheet')) return; // la hoja de compartir tiene sus propias teclas
  if (e.key === 'Escape') {
    e.preventDefault();
    return document.querySelector('.hi-hoja') ? cerrarHoja() : cerrar();
  }
  if (document.querySelector('.hi-hoja') || document.querySelector('.sheet')) return;
  if (e.key === 'ArrowRight' || (e.key === ' ' && !e.target.closest('button, a'))) {
    e.preventDefault();
    siguiente();
  } else if (e.key === 'ArrowLeft') {
    e.preventDefault();
    anterior();
  } else if (e.key === 'Tab') {
    const f = [...abierta.capa.querySelectorAll('button, a[href]')].filter((x) => x.offsetParent !== null);
    if (!f.length) return;
    const primero = f[0];
    const ultimo = f[f.length - 1];
    if (e.shiftKey && document.activeElement === primero) {
      e.preventDefault();
      ultimo.focus();
    } else if (!e.shiftKey && document.activeElement === ultimo) {
      e.preventDefault();
      primero.focus();
    }
  }
}

function gestos(capa) {
  let g = null;
  let retencion = 0;
  let sostenido = false;
  let ultimaRueda = 0;
  capa.addEventListener('pointerdown', (e) => {
    if (e.target.closest('button, a, .hi-hoja, [data-cuerpo] .tchips')) return;
    g = { x: e.clientX, y: e.clientY, t: performance.now() };
    sostenido = false;
    retencion = setTimeout(() => {
      sostenido = true;
      if (!abierta.pausado) {
        abierta.sostener = true;
        pausa(true, true);
      }
    }, 240);
  });
  const fin = (e) => {
    if (!g) return;
    clearTimeout(retencion);
    const dx = e.clientX - g.x;
    const dy = e.clientY - g.y;
    const rapido = performance.now() - g.t < 400;
    g = null;
    if (abierta?.sostener) {
      abierta.sostener = false;
      pausa(false, true);
    }
    if (Math.abs(dx) < 10 && Math.abs(dy) < 10) {
      if (!sostenido && rapido) (e.clientX < innerWidth * 0.3 ? anterior : siguiente)();
      return;
    }
    if (dy > 120 && dy > Math.abs(dx)) cerrar();
    else if (Math.abs(dx) > 60) (dx < 0 ? siguiente : anterior)();
  };
  capa.addEventListener('pointerup', fin);
  capa.addEventListener('pointercancel', () => {
    clearTimeout(retencion);
    g = null;
  });
  capa.addEventListener(
    'wheel',
    (e) => {
      const cuerpo = capa.querySelector('[data-cuerpo]');
      const puedeBajar = cuerpo.scrollHeight > cuerpo.clientHeight + 4;
      if (puedeBajar && cuerpo.contains(e.target)) return; // el capítulo tiene su propio desplazamiento
      const ahora = performance.now();
      if (ahora - ultimaRueda < 750 || Math.abs(e.deltaY + e.deltaX) < 40) return;
      ultimaRueda = ahora;
      (e.deltaY + e.deltaX > 0 ? siguiente : anterior)();
    },
    { passive: true },
  );
}

export async function abrirHistoria(clave, capitulo = 0, origen = null) {
  if (abierta) cerrar(true);
  const [ctx] = await Promise.all([base(), cargarEstilos()]);
  const codigo = ctx.porSlug[clave] ?? clave;
  let m;
  try {
    m = await cargarJSON(`data/m/${codigo}.json`);
  } catch {
    return;
  }
  const capa = document.createElement('div');
  capa.id = 'story';
  capa.className = 'hi';
  capa.setAttribute('role', 'dialog');
  capa.setAttribute('aria-modal', 'true');
  capa.setAttribute('aria-label', `Historia de ${m.nombre}`);
  const foto = m.foto ? `url('${raiz}assets/fotos/${codigo}-1080.webp')` : '';
  capa.innerHTML = `
    <div class="hi-bg${foto ? '' : ' hi-bg--sin'}" ${foto ? `style="background-image:${foto}"` : ''} aria-hidden="true"></div>
    <div class="hi-velo" aria-hidden="true"></div>
    <div class="hi-ui">
      <div class="hi-prog" style="--dur:${DURACION / 1000}s" aria-hidden="true">${CAPITULOS.map(() => '<span><i></i></span>').join('')}</div>
      <div class="hi-cab">
        <span class="hi-cab__n"><b>${esc(m.nombre)}</b><small data-titulo-cap></small></span>
        <span class="hi-cab__pausa mono">En pausa</span>
        <button type="button" class="hi-ico" data-pausa aria-label="Pausar">❚❚</button>
        <button type="button" class="hi-ico" data-cerrar aria-label="Cerrar">✕</button>
      </div>
      <div class="hi-cuerpo" data-cuerpo></div>
    </div>`;
  document.body.append(capa);
  document.documentElement.classList.add('lock');
  abierta = { capa, m, ctx, i: 0, pausado: false, origen };
  try {
    history.replaceState(null, '', `#${m.slug}`);
  } catch {
    /* sin historial */
  }

  capa.querySelectorAll('.hi-prog span').forEach((s, j) => {
    s.addEventListener('animationend', (e) => {
      if (e.target.tagName === 'I' && abierta && j === abierta.i) siguiente();
    });
  });
  capa.addEventListener('click', (e) => {
    const b = e.target.closest('button, a');
    if (!b) return;
    if (b.matches('[data-cerrar]')) cerrar();
    else if (b.matches('[data-pausa]')) pausa(!abierta.pausado);
    else if (b.dataset.ir) mostrar(Number(b.dataset.ir));
    else if (b.matches('[data-siguiente-muni]')) vecino(1);
    else if (b.matches('[data-compartir-cap]')) compartirActual(b);
    else if (b.matches('[data-pedir]')) pedirActual(b);
    else if (b.matches('[data-reportar]')) window.open(m.reportar, '_blank', 'noopener');
    else if (b.dataset.metodo) abrirHoja(`Cómo se calcula: ${b.closest('li').textContent.split('·')[0].trim()}`, metodo(b.dataset.metodo, m, ctx));
  });
  gestos(capa);
  if (!foto) dibujarSilueta(m.departamento_slug, m.codigo, capa.querySelector('.hi-bg'), 'hi-silueta');
  document.addEventListener('keydown', teclas, true);
  mostrar(Math.min(capitulo, CAPITULOS.length - 1));
  capa.querySelector('[data-pausa]').focus({ preventScroll: true });
}

/** Abre la historia indicada por el hash de la URL (`#departamento--municipio`), si existe. */
export async function abrirDesdeHash() {
  const hash = location.hash.slice(1);
  const { porSlug } = await base();
  if (hash && porSlug[hash]) abrirHistoria(hash);
}
