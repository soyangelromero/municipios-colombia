// Utilidades compartidas: rutas, carga de datos, formato y texto.

/** Ruta relativa hasta la raíz del sitio («», «../», «../../»), la escribe cada página. */
export const raiz = document.querySelector('meta[name="raiz"]')?.content ?? '';

const cache = new Map();

/** Carga un JSON del sitio (una sola vez por página). */
export function cargarJSON(ruta) {
  if (!cache.has(ruta)) {
    cache.set(
      ruta,
      fetch(raiz + ruta).then((respuesta) => {
        if (!respuesta.ok) throw new Error(`No se pudo cargar ${ruta}`);
        return respuesta.json();
      }),
    );
  }
  return cache.get(ruta);
}

/** Lista de municipios del resumen nacional, como objetos { codigo, nombre, slug, … }. */
export async function municipios() {
  const pais = await cargarJSON('data/pais.json');
  return pais.municipios.map((fila) => Object.fromEntries(pais.campos.map((c, i) => [c, fila[i]])));
}

const numero = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 });
const entero = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });

export function formatoNumero(valor, decimales = 1) {
  if (valor === null || valor === undefined) return '—';
  return (decimales === 0 ? entero : numero).format(valor);
}

/** «1 millón» (singular), «1,4 millones», «12 millones»: un decimal solo por debajo de 10. */
function cantidad(valor, singular, plural) {
  const redondo = Math.abs(valor) < 10 ? Math.round(valor * 10) / 10 : Math.round(valor);
  if (redondo === 1) return `1 ${singular}`;
  const decimales = Math.abs(valor) < 10 && !Number.isInteger(redondo) ? 1 : 0;
  return `${formatoNumero(redondo, decimales)} ${plural}`;
}

/** Igual criterio que pipeline/municipios/exportar/formato.py: según la unidad del indicador. */
export function formatoSegunUnidad(valor, unidad = '') {
  if (valor === null || valor === undefined) return '—';
  const u = unidad.toLowerCase();
  if (u === 'sí/no') return valor >= 50 ? 'Sí' : 'No';
  if (u.includes('peso')) {
    if (u.includes('por habitante')) return `$ ${formatoNumero(valor, 0)}`;
    if (Math.abs(valor) >= 1e12) return `$ ${cantidad(valor / 1e12, 'billón', 'billones')}`;
    if (Math.abs(valor) >= 1e9) return `$ ${formatoNumero(valor / 1e9, 0)} mil millones`;
    if (Math.abs(valor) >= 1e6) return `$ ${cantidad(valor / 1e6, 'millón', 'millones')}`;
    return `$ ${formatoNumero(valor, 0)}`;
  }
  if (u.startsWith('%')) return `${formatoNumero(valor)} %`;
  if (u.includes('por km²')) return `${formatoNumero(valor, 0)} hab./km²`;
  if (u.includes('km²')) return `${formatoNumero(valor, 0)} km²`;
  return formatoNumero(valor, Number.isInteger(valor) ? 0 : 1);
}

/** «Bogotá, D.C.» → «bogota, d.c.» para buscar sin tildes ni mayúsculas. */
export function normalizar(texto) {
  return texto.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase().trim();
}

export function escapar(texto) {
  return String(texto ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

/** Tramo de color de la escala de los mapas (igual que en el pipeline). */
export function tramo(valor) {
  if (valor === null || valor === undefined) return 'sin';
  if (valor < 40) return 'e1';
  if (valor < 50) return 'e2';
  if (valor < 60) return 'e3';
  if (valor < 70) return 'e4';
  return 'e5';
}

export const TEXTO_SEMAFORO = { verde: 'Verde', amarillo: 'Amarillo', rojo: 'Rojo' };

export function pildoraSemaforo(semaforo, valor) {
  if (!semaforo) return '<span class="semaforo semaforo--sin">Sin índice</span>';
  const numeroTexto = valor === null || valor === undefined ? '' : `${formatoNumero(valor)} · `;
  return `<span class="semaforo semaforo--${semaforo}">${numeroTexto}${TEXTO_SEMAFORO[semaforo]}</span>`;
}

/** Sin foto libre: dibuja el contorno del municipio, tomado del mapa SVG de su departamento. */
export async function dibujarSilueta(departamentoSlug, codigo, contenedor, clase) {
  try {
    const r = await fetch(`${raiz}data/mapas/${departamentoSlug}.svg`);
    if (!r.ok) return;
    const doc = new DOMParser().parseFromString(await r.text(), 'image/svg+xml');
    const trazo = doc.getElementById(`e-${codigo}`);
    if (!trazo || !contenedor.isConnected) return;
    contenedor.querySelector(`.${clase}`)?.remove();
    const NS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('class', clase);
    svg.setAttribute('aria-hidden', 'true');
    svg.append(document.importNode(trazo, true));
    contenedor.append(svg); // debe estar en el documento para poder medirla
    const b = svg.firstChild.getBBox();
    svg.setAttribute('viewBox', `${b.x} ${b.y} ${b.width} ${b.height}`);
  } catch {
    /* sin silueta queda el degradado */
  }
}
