// Ranking completo (e2e/09): pestañas por indicador, filtros, «Ver más» y apertura de la historia en su sitio.
import { formatoNumero, normalizar } from './comun.js';
import { enlazarHistorias } from './historia.js';

const lista = document.querySelector('[data-rk]');
const controles = document.querySelector('[data-rk-controles]');
const POR_PAGINA = 50;
const INICIAL = 100;

const estado = { campo: 'indice', texto: '', dep: '', grupo: '', sem: '', visibles: INICIAL };

const filas = lista ? [...lista.children] : [];
const nombres = new Map(filas.map((f) => [f, normalizar(f.querySelector('b').textContent)]));
const valor = (fila, campo) => {
  const v = parseFloat(fila.dataset[campo.toLowerCase()]);
  return Number.isNaN(v) ? null : v;
};
const clase = (v) => (v === null ? 'sin' : v < 40 ? 'rojo' : v >= 70 ? 'verde' : 'amarillo');

function pasa(fila) {
  return (
    (!estado.texto || nombres.get(fila).includes(estado.texto)) &&
    (!estado.dep || fila.dataset.dep === estado.dep) &&
    (!estado.grupo || fila.dataset.grupo === estado.grupo) &&
    (!estado.sem || fila.dataset.semaforo === estado.sem)
  );
}

function pintar() {
  const campo = estado.campo;
  const ordenadas = filas
    .map((f) => [f, valor(f, campo)])
    .sort((a, b) => (b[1] ?? -1) - (a[1] ?? -1))
    .map(([f]) => f);
  const coinciden = ordenadas.filter(pasa);
  const mostrar = new Set(coinciden.slice(0, estado.visibles));
  lista.append(...ordenadas);
  let puesto = 0;
  for (const fila of ordenadas) {
    const ok = pasa(fila);
    fila.hidden = !mostrar.has(fila);
    if (!ok) continue;
    puesto += 1;
    const v = valor(fila, campo);
    fila.querySelector('.rk__puesto').textContent = String(puesto).padStart(2, '0');
    fila.querySelector('.rk__valor').textContent = v === null ? '—' : formatoNumero(v, 0);
    const barra = fila.querySelector('.bar2__f');
    barra.style.width = `${Math.max(v ?? 0, 1)}%`;
    barra.className = `bar2__f bar2__f--${clase(v)}`;
  }
  document.querySelector('[data-rk-conteo]').textContent =
    `${formatoNumero(coinciden.length, 0)} municipios` +
    (coinciden.length > mostrar.size ? ` · mostrando ${formatoNumero(mostrar.size, 0)}` : '');
  const mas = document.querySelector('[data-rk-mas]');
  const quedan = coinciden.length - mostrar.size;
  mas.hidden = quedan <= 0;
  mas.querySelector('small').textContent = `+${Math.min(POR_PAGINA, quedan)}`;
}

function cambiar(parcial) {
  Object.assign(estado, parcial, { visibles: INICIAL });
  pintar();
}

function iniciar() {
  if (!lista || !controles) return;
  controles.hidden = false;
  enlazarHistorias();

  controles.querySelectorAll('[data-campo]').forEach((b) =>
    b.addEventListener('click', () => {
      controles.querySelectorAll('[data-campo]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      cambiar({ campo: b.dataset.campo });
    }),
  );
  controles.querySelectorAll('[data-sem]').forEach((b) =>
    b.addEventListener('click', () => {
      controles.querySelectorAll('[data-sem]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      cambiar({ sem: b.dataset.sem });
    }),
  );
  controles.querySelector('[data-rk-dep]').addEventListener('change', (e) => cambiar({ dep: e.target.value }));
  controles.querySelector('[data-rk-grupo]').addEventListener('change', (e) => cambiar({ grupo: e.target.value }));
  const texto = controles.querySelector('[data-rk-texto]');
  texto.addEventListener('input', () => cambiar({ texto: normalizar(texto.value) }));
  document.querySelector('[data-rk-mas]').addEventListener('click', () => {
    estado.visibles += POR_PAGINA;
    pintar();
  });

  const q = new URLSearchParams(location.search).get('q');
  if (q) {
    texto.value = q;
    estado.texto = normalizar(q);
  }
  pintar();
}

iniciar();
