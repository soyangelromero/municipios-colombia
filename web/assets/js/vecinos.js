// Portada: «Lo que más le piden los vecinos». Municipios con más pedidos de datos que no encontramos en su sitio web.
// Los conteos vienen de la API PHP opcional; sin ella se muestra el buscador para elegir un municipio.
import { cargarJSON, escapar as esc, formatoNumero as num, municipios, normalizar, raiz } from './comun.js';
import { CRITERIOS, cargarEstilos, hayServidor, htmlCompartir, manejarRed, ranking, sumar } from './pedidos.js';

const POR_PAGINA = 8;
const nombreDato = (id) => CRITERIOS[id] ?? id.replace(/_/g, ' ');
const plural = (n, uno, varios) => `${num(n, 0)} ${n === 1 ? uno : varios}`;

const estado = { lista: [], dep: '', visibles: POR_PAGINA };
let muni = new Map();
let deps = {};
let cuerpo;

const urlDe = (m) => new URL(`${raiz}m/${m.slug}/`, location.href).href;
const textoCompartir = (x, m) => {
  const [dato] = Object.keys(x.porDato);
  return `${plural(x.total, 'vecino pide', 'vecinos piden')} que ${m.nombre} publique ${nombreDato(dato).toLowerCase()}. Súmate.`;
};

function barras(x) {
  const filas = Object.entries(x.porDato);
  const maximo = Math.max(1, ...filas.map(([, n]) => n));
  return `<div class="vp-barras">${filas
    .map(([d, n]) => `<div class="vp-barra"><span>${esc(nombreDato(d))}</span><span class="num">${num(n, 0)}</span><i style="--w:${((n / maximo) * 100).toFixed(1)}%"></i></div>`)
    .join('')}</div>`;
}

function tarjeta(x, i) {
  const m = muni.get(x.codigo);
  const [top, topN] = Object.entries(x.porDato)[0];
  return `<li class="vp-card" data-cod="${x.codigo}" data-dato="${esc(top)}">
    <img class="vp-card__foto" src="${raiz}assets/fotos/${x.codigo}-480.webp" srcset="${raiz}assets/fotos/${x.codigo}-480.webp 480w, ${raiz}assets/fotos/${x.codigo}-1080.webp 1080w" sizes="(max-width: 900px) 100vw, 33vw" alt="" loading="lazy" decoding="async">
    <div class="vp-card__cab"><span class="vp-card__rango">${i + 1}</span>${x.hoy ? `<span class="vp-hoy">+${num(x.hoy, 0)} hoy</span>` : ''}</div>
    <h3><a href="${raiz}m/${m.slug}/" data-historia="${m.slug}">${esc(m.nombre)}</a></h3>
    <p class="vp-card__dep">${esc(deps[m.dep] ?? '')}</p>
    <p class="vp-card__n num" data-total>${num(x.total, 0)}</p>
    <p class="vp-card__q">${x.total === 1 ? 'pedido de vecinos' : 'pedidos de vecinos'}. El más pedido: <b>${esc(nombreDato(top).toLowerCase())}</b> (${num(topN, 0)}).</p>
    ${barras(x)}
    <button type="button" class="vp-btn" data-sumar>Súmate al reclamo</button>
    <p class="vp-aviso" role="status"></p>
    ${htmlCompartir(urlDe(m), textoCompartir(x, m))}
  </li>`;
}

function fila(x, i) {
  const m = muni.get(x.codigo);
  const [top] = Object.keys(x.porDato);
  return `<li class="vp-li" data-cod="${x.codigo}" data-dato="${esc(top)}">
    <span class="vp-li__r">${i + 1}</span>
    <span class="vp-li__nm"><b><a href="${raiz}m/${m.slug}/" data-historia="${m.slug}">${esc(m.nombre)}</a></b>
      <small>${esc(deps[m.dep] ?? '')} · más pedido: ${esc(nombreDato(top).toLowerCase())}</small></span>
    <b class="vp-li__t num" data-total>${num(x.total, 0)}${x.hoy ? `<small>+${num(x.hoy, 0)} hoy</small>` : ''}</b>
    <div class="vp-li__acc"><button type="button" class="vp-btn" data-sumar>Súmate al reclamo</button>${htmlCompartir(urlDe(m), textoCompartir(x, m))}</div>
    <p class="vp-aviso" role="status"></p>
  </li>`;
}

function vacio() {
  return `<div class="vp-vacio"><h3>Sé el primero: <span>elige tu municipio</span></h3>
    <p>Todavía hay pocos pedidos${estado.dep ? ' en este departamento' : ''}. Busca tu municipio, mira qué datos no encontramos en su sitio y súmate al pedido.</p>
    <div class="vp-buscar"><input type="search" data-vp-q placeholder="Escribe el nombre de tu municipio" autocomplete="off" aria-label="Buscar municipio"><ul data-vp-ql hidden></ul></div></div>`;
}

function pintar() {
  const lista = estado.lista.filter((x) => muni.has(x.codigo) && (!estado.dep || x.codigo.startsWith(estado.dep)));
  if (!lista.length) {
    cuerpo.innerHTML = vacio();
    return;
  }
  const resto = lista.slice(3);
  const mostrar = resto.slice(0, estado.visibles - POR_PAGINA + POR_PAGINA);
  cuerpo.innerHTML = `<ol class="vp-podio">${lista.slice(0, 3).map(tarjeta).join('')}</ol>
    ${mostrar.length ? `<ol class="vp-lista" start="4">${mostrar.map((x, i) => fila(x, i + 3)).join('')}</ol>` : ''}
    <div class="vp-mas" ${resto.length > mostrar.length ? '' : 'hidden'}><button type="button" class="pill" data-vp-mas>Cargar más <span class="mono">+${Math.min(POR_PAGINA, resto.length - mostrar.length)}</span></button></div>`;
  cuerpo.querySelectorAll('.vp-card__foto').forEach((img) => img.addEventListener('error', () => img.remove(), { once: true }));
}

function cinta(reciente) {
  const caja = document.querySelector('[data-vp-cinta]');
  const m = reciente && muni.get(reciente.municipio);
  if (!caja || !m) return;
  const minutos = Math.max(0, Math.round((Date.now() - Date.parse(reciente.creado)) / 60000));
  const cuando = minutos < 2 ? 'recién' : minutos < 60 ? `hace ${minutos} min` : minutos < 1440 ? `hace ${Math.round(minutos / 60)} h` : 'hace días';
  caja.innerHTML = `<span class="vp-vivo" aria-hidden="true"></span><span>Alguien de <b>${esc(m.nombre)}</b> acaba de pedir ${esc(nombreDato(reciente.dato).toLowerCase())}</span> <small>${cuando}</small>`;
  caja.hidden = false;
}

async function sumarDesde(boton) {
  const item = boton.closest('[data-cod]');
  const aviso = item.querySelector('.vp-aviso');
  boton.disabled = true;
  boton.textContent = 'Sumando tu pedido…';
  try {
    const r = await sumar(item.dataset.cod, item.dataset.dato);
    boton.textContent = '✓ Ya te sumaste';
    aviso.textContent = r.yaPedido ? 'Ya lo habías pedido: cada persona cuenta una vez.' : `Eres el vecino número ${num(r.total, 0)} que lo pide.`;
    const x = estado.lista.find((y) => y.codigo === item.dataset.cod);
    if (x && !r.yaPedido) {
      x.total += 1;
      x.porDato[item.dataset.dato] = r.total;
      item.querySelector('[data-total]').firstChild.textContent = num(x.total, 0);
    }
  } catch (error) {
    boton.disabled = false;
    boton.textContent = 'Súmate al reclamo';
    aviso.textContent = error.message;
  }
}

function buscar(entrada) {
  const lista = cuerpo.querySelector('[data-vp-ql]');
  const q = normalizar(entrada.value.trim());
  if (q.length < 2) {
    lista.hidden = true;
    return;
  }
  const hallados = [...muni.values()].filter((m) => normalizar(m.nombre).includes(q)).slice(0, 8);
  lista.innerHTML = hallados
    .map((m) => `<li><a href="${raiz}m/${m.slug}/" data-historia="${m.slug}">${esc(m.nombre)} <small>${esc(deps[m.dep] ?? '')}</small></a></li>`)
    .join('');
  lista.hidden = hallados.length === 0;
}

export async function iniciar(seccion) {
  cuerpo = seccion.querySelector('[data-vp-cuerpo]');
  await cargarEstilos();
  const [lista, depsJson, respuesta] = await Promise.all([municipios(), cargarJSON('data/departamentos.json'), ranking()]);
  muni = new Map(lista.map((m) => [m.codigo, m]));
  deps = Object.fromEntries(Object.entries(depsJson.departamentos).map(([c, d]) => [c, d.nombre]));
  estado.lista = respuesta?.municipios ?? [];

  const selector = seccion.querySelector('[data-vp-dep]');
  selector.innerHTML += Object.entries(deps)
    .sort((a, b) => a[1].localeCompare(b[1], 'es'))
    .map(([c, n]) => `<option value="${c}">${esc(n)}</option>`)
    .join('');
  selector.addEventListener('change', () => {
    estado.dep = selector.value;
    estado.visibles = POR_PAGINA;
    pintar();
  });
  seccion.addEventListener('click', async (e) => {
    const red = e.target.closest('[data-red]');
    const sumarBtn = e.target.closest('[data-sumar]');
    const mas = e.target.closest('[data-vp-mas]');
    if (red) {
      const aviso = red.closest('[data-cod]')?.querySelector('.vp-aviso');
      const texto = await manejarRed(red);
      if (aviso) aviso.textContent = texto;
    } else if (sumarBtn) sumarDesde(sumarBtn);
    else if (mas) {
      estado.visibles += POR_PAGINA;
      pintar();
    }
  });
  seccion.addEventListener('input', (e) => e.target.matches('[data-vp-q]') && buscar(e.target));
  pintar();
  if (hayServidor) cinta(respuesta?.reciente);
}
