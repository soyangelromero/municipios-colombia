// «Súmate al pedido»: cliente de la API PHP opcional (apoyos.php, pedidos-ranking.php) y hoja para elegir el dato.
// Cada persona cuenta una vez por municipio y dato (el servidor lo controla con un hash de la IP).
import { CONFIG } from './config.js';
import { escapar as esc, formatoNumero as num, raiz } from './comun.js';

const direccion = CONFIG.pedidos ?? CONFIG.endpoint;
const servidor = direccion ? direccion.replace(/\/$/, '') : null;
const cargada = Date.now();
const GUARDADO = 'pedidos-mios';

/** Sin servidor (sitio solo estático) no se pueden contar pedidos: se ofrece el formulario de la ficha. */
export const hayServidor = servidor !== null;

export const ICONO_ALTAVOZ =
  '<svg class="ico" viewBox="0 0 20 20" aria-hidden="true"><path d="M3 8v4h3l5 4V4L6 8zM14 7.5a3.5 3.5 0 0 1 0 5M16 5a7 7 0 0 1 0 10"/></svg>';

/** Nombre legible de cada dato que se puede pedir (criterios del relevamiento de transparencia). */
export const CRITERIOS = {
  presupuesto: 'Presupuesto vigente',
  ejecucion: 'Ejecución presupuestal',
  plan_desarrollo: 'Plan de desarrollo',
  plan_adquisiciones: 'Plan de adquisiciones',
  contratacion: 'Contratación (SECOP)',
  directorio: 'Directorio y salarios',
  control: 'Informes de control',
  pqrsd: 'Peticiones (PQRSD)',
  datos_abiertos: 'Datos abiertos',
  declaraciones: 'Declaración de bienes',
};

let estilos = null;
/** La hoja de estilos de los pedidos se descarga la primera vez que hace falta. */
export function cargarEstilos() {
  estilos ??= new Promise((resolver) => {
    const enlace = document.createElement('link');
    enlace.rel = 'stylesheet';
    enlace.href = new URL('../css/pedidos.css', import.meta.url).href;
    enlace.onload = enlace.onerror = () => resolver();
    document.head.append(enlace);
  });
  return estilos;
}

// --- memoria local: qué pedidos ya hizo esta persona en este navegador --------------------------
function leerMios() {
  try {
    return new Set(JSON.parse(localStorage.getItem(GUARDADO) ?? '[]'));
  } catch {
    return new Set();
  }
}
function recordar(codigo, dato) {
  const mios = leerMios().add(`${codigo}:${dato}`);
  try {
    localStorage.setItem(GUARDADO, JSON.stringify([...mios]));
  } catch {
    /* sin almacenamiento: el servidor igual cuenta una sola vez */
  }
}

// --- API ------------------------------------------------------------------------------------------
async function leer(ruta) {
  if (!servidor) return null;
  try {
    const respuesta = await fetch(`${servidor}/${ruta}`, { cache: 'no-cache', headers: { Accept: 'application/json' } });
    const cuerpo = await respuesta.json();
    return respuesta.ok && cuerpo.ok ? cuerpo : null;
  } catch {
    return null;
  }
}

/** Municipios con más pedidos (y el más reciente), o null si no hay servidor. */
export const ranking = () => leer('pedidos-ranking.php');

/** Pedidos de un municipio: { porDato, mios, total }, o null si no hay servidor. */
export async function detalle(codigo) {
  const r = await leer(`pedidos-ranking.php?municipio=${encodeURIComponent(codigo)}`);
  if (!r) return null;
  const mios = new Set([...r.mios, ...[...leerMios()].filter((x) => x.startsWith(`${codigo}:`)).map((x) => x.slice(6))]);
  return { porDato: r.porDato, mios, total: Object.values(r.porDato).reduce((a, b) => a + b, 0) };
}

/** Suma un pedido. Devuelve { yaPedido, total }; lanza un Error con mensaje legible si falla. */
export async function sumar(codigo, dato) {
  if (!servidor) throw new Error('Este sitio no tiene servidor para contar pedidos.');
  // El servidor descarta envíos de menos de 3 s desde que se pintó la página (robots).
  await new Promise((r) => setTimeout(r, Math.max(0, 3300 - (Date.now() - cargada))));
  let respuesta;
  try {
    respuesta = await fetch(`${servidor}/apoyos.php`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ t: cargada, municipio: codigo, dato, web: '' }),
    });
  } catch {
    throw new Error('Sin conexión: no pudimos sumar tu pedido.');
  }
  const cuerpo = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) throw new Error(cuerpo.error || 'No pudimos sumar tu pedido. Inténtalo de nuevo.');
  recordar(codigo, dato);
  return { yaPedido: cuerpo.yaPedido, total: cuerpo.total };
}

// --- compartir el reclamo (enlaces de la web, sin SDK ni rastreadores) -------------------------------
const I = (d) => `<svg viewBox="0 0 20 20" aria-hidden="true">${d}</svg>`;
const REDES = [
  { id: 'whatsapp', nombre: 'WhatsApp', icono: I('<path d="M3 17l1.2-3.8A7 7 0 1 1 7.5 15.5z"/><path d="M7.5 8c.5 2 2.5 4 4.5 4.5"/>'), url: (u, t) => `https://wa.me/?text=${encodeURIComponent(`${t} ${u}`)}` },
  { id: 'instagram', nombre: 'Instagram', icono: I('<rect x="3" y="3" width="14" height="14" rx="4"/><circle cx="10" cy="10" r="3.2"/><path d="M14.2 5.8h.01"/>'), copia: 'Enlace copiado: pégalo en tu historia o publicación de Instagram.' },
  { id: 'facebook', nombre: 'Facebook', icono: I('<path d="M11 17v-6h2.5l.5-3H11V6.5c0-.9.4-1.5 1.5-1.5H14V2.3A12 12 0 0 0 12 2C9.8 2 8 3.3 8 5.8V8H5.5v3H8v6z"/>'), url: (u) => `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(u)}` },
  { id: 'x', nombre: 'X', icono: I('<path d="M4 4l12 12M16 4L4 16"/>'), url: (u, t) => `https://twitter.com/intent/tweet?text=${encodeURIComponent(t)}&url=${encodeURIComponent(u)}` },
  { id: 'threads', nombre: 'Threads', icono: I('<path d="M13.5 7.5C13 5.8 11.800 5 10 5 7.500 5 6 6.800 6 10s1.500 5 4 5c2 0 3.500-1 3.500-2.700 0-1.600-1.400-2.300-3.500-2.300-1.300 0-2 .6-2 1.400 0 .9.700 1.400 1.700 1.400 1.500 0 2.300-1 2.300-3z"/>'), url: (u, t) => `https://www.threads.net/intent/post?text=${encodeURIComponent(`${t} ${u}`)}` },
  { id: 'telegram', nombre: 'Telegram', icono: I('<path d="M17 3L3 9l4 2 1.5 5 2.5-3 4 3z"/>'), url: (u, t) => `https://t.me/share/url?url=${encodeURIComponent(u)}&text=${encodeURIComponent(t)}` },
  { id: 'copiar', nombre: 'Copiar', icono: I('<path d="M8.5 11.5a3 3 0 0 0 4 0l2.5-2.5a3 3 0 0 0-4-4L10 6M11.5 8.5a3 3 0 0 0-4 0L5 11a3 3 0 0 0 4 4L10 14"/>'), copia: 'Enlace copiado.' },
  { id: 'mas', nombre: 'Más', icono: I('<path d="M10 12V3M6.5 6.5L10 3l3.5 3.5M4 11v5h12v-5"/>') },
];

/** Fila de botones para compartir un pedido (se maneja con `manejarRed` sobre el contenedor). */
export function htmlCompartir(url, texto) {
  const botones = REDES.map(
    (r) => `<button type="button" class="red" data-red="${r.id}" data-url="${esc(url)}" data-texto="${esc(texto)}">
      <span class="red__ico">${r.icono}</span><span class="red__t">${r.nombre}</span></button>`,
  ).join('');
  return `<div class="redes" role="group" aria-label="Compartir el reclamo">${botones}</div>`;
}

/** Atiende el clic en un botón de red; devuelve el aviso a mostrar (o '' si se abrió la red). */
export async function manejarRed(boton) {
  const red = REDES.find((r) => r.id === boton.dataset.red);
  if (!red) return '';
  const { url, texto } = boton.dataset;
  if (red.url) {
    window.open(red.url(url, texto), '_blank', 'noopener');
    return '';
  }
  if (red.id === 'mas' && navigator.share) {
    try {
      await navigator.share({ title: texto, text: texto, url });
    } catch {
      /* la persona canceló */
    }
    return '';
  }
  try {
    await navigator.clipboard.writeText(url);
    return red.copia ?? 'Enlace copiado.';
  } catch {
    return 'No se pudo copiar el enlace.';
  }
}

// --- hoja: elegir qué dato pedir --------------------------------------------------------------------
/**
 * Abre la hoja «Lo que no publica» con los datos pendientes; cada fila tiene su botón.
 * `m` = { codigo, nombre, slug }, `opciones` = [{ id, nombre }]. La promesa se cumple al cerrar.
 */
export async function abrirHojaPedido(m, opciones, origen = null) {
  await cargarEstilos();
  return new Promise((cerrada) => {
    const fondo = document.createElement('div');
    fondo.className = 'fondo-hoja';
    const hoja = document.createElement('div');
    hoja.className = 'sheet sheet--pedir';
    hoja.setAttribute('role', 'dialog');
    hoja.setAttribute('aria-modal', 'true');
    hoja.setAttribute('aria-label', `Datos que ${m.nombre} no publica`);
    const urlFicha = new URL(`${raiz}m/${m.slug}/`, location.href).href;
    const filas = opciones
      .map(
        (o) => `<li class="pedir-fila" data-fila="${esc(o.id)}">
          <div class="pedir-fila__t"><span>${esc(o.nombre)}</span><b class="num" data-n></b></div>
          <div class="pedir-fila__acc"><button type="button" class="pedir-btn" data-dato="${esc(o.id)}">Quiero que lo publiquen</button></div></li>`,
      )
      .join('');
    const sinServidor = hayServidor
      ? ''
      : `<p class="nota">Este sitio todavía no cuenta pedidos. Por ahora puedes pedirlo con el <a href="${raiz}m/${esc(m.slug)}/#reportar">formulario de la ficha</a>.</p>`;
    hoja.innerHTML = `
      <div class="sheet__cabecera"><h2>Lo que no publica</h2>
        <button type="button" class="st-btn" data-cerrar aria-label="Cerrar">✕</button></div>
      <p class="nota">Súmate al pedido: cada persona cuenta una vez y el total muestra cuánta gente quiere que ${esc(m.nombre)} publique ese dato. No mide calidad ni acusa a nadie.</p>
      ${sinServidor}
      <ul class="pedir-lista">${filas || '<li class="pedir-fila"><span>No hay datos pendientes que pedir.</span></li>'}</ul>
      <p class="nota" data-aviso role="status"></p>`;
    const aviso = hoja.querySelector('[data-aviso]');
    const nombreDe = (id) => opciones.find((o) => o.id === id)?.nombre ?? id;
    const plural = (n) => `${num(n, 0)} ${n === 1 ? 'vecino lo pide' : 'vecinos lo piden'}`;

    const marcar = (id, yaPedido, n, numero) => {
      const fila = hoja.querySelector(`[data-fila="${CSS.escape(id)}"]`);
      if (!fila) return;
      if (n !== undefined) fila.querySelector('[data-n]').textContent = n > 0 ? plural(n) : '';
      const acc = fila.querySelector('.pedir-fila__acc');
      if (!yaPedido) {
        const b = acc.querySelector('button');
        if (b) {
          b.disabled = !hayServidor;
          b.textContent = 'Quiero que lo publiquen';
        }
        return;
      }
      const quien = n ? `${num(n, 0)} ${n === 1 ? 'vecino pide' : 'vecinos piden'}` : 'Pido';
      const texto = `${quien} que ${m.nombre} publique ${nombreDe(id).toLowerCase()}. Súmate.`;
      acc.innerHTML = `<div class="pedir-ok"><span class="pedir-ok__chip" role="status">✓ Ya lo pediste</span>
        <small>${numero ? `Eres el vecino número ${num(numero, 0)} que lo pide` : 'Tu pedido ya está contado'}</small></div>
        <p class="pedir-comp">Comparte el reclamo</p>${htmlCompartir(urlFicha, texto)}`;
    };
    detalle(m.codigo).then((d) => {
      if (!d) return;
      opciones.forEach((o) => marcar(o.id, d.mios.has(o.id), d.porDato[o.id] ?? 0));
    });

    const teclas = (e) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        cerrar();
      }
    };
    function cerrar() {
      fondo.remove();
      hoja.remove();
      document.removeEventListener('keydown', teclas, true);
      origen?.focus?.();
      cerrada();
    }
    fondo.addEventListener('click', cerrar);
    hoja.querySelector('[data-cerrar]').addEventListener('click', cerrar);
    document.addEventListener('keydown', teclas, true);
    hoja.addEventListener('click', async (e) => {
      const red = e.target.closest('[data-red]');
      if (red) {
        aviso.textContent = await manejarRed(red);
        return;
      }
      const boton = e.target.closest('[data-dato]');
      if (!boton) return;
      const id = boton.dataset.dato;
      boton.disabled = true;
      boton.textContent = 'Sumando tu pedido…';
      try {
        const r = await sumar(m.codigo, id);
        marcar(id, true, r.total, r.yaPedido ? 0 : r.total);
        aviso.textContent = '';
        origen?.dispatchEvent(new CustomEvent('pedido'));
      } catch (error) {
        marcar(id, false);
        aviso.textContent = error.message;
      }
    });
    document.body.append(fondo, hoja);
    hoja.querySelector('[data-cerrar]').focus();
  });
}
