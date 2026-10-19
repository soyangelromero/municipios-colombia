// Ficha de municipio: mapa del departamento, compartir y modo historia.
import { formatoNumero, municipios, raiz } from './comun.js';
import { activarMapa, colorear, insertarMapa } from './mapa.js';
import { compartir } from './compartir.js';
const abrirHistoria = (codigo, cap, origen) => import('./historia.js').then((m) => m.abrirHistoria(codigo, cap, origen));

const ficha = document.querySelector('.ficha');

/** Datos de la ficha para la tarjeta de compartir, leídos del propio HTML. */
function infoFicha() {
  const indice = ficha?.dataset.indice ?? '';
  return {
    nombre: ficha?.dataset.nombre ?? document.title,
    slug: ficha?.dataset.codigo ?? '',
    valor: indice === '' ? null : Number(indice.replace(',', '.')),
    semaforo: ficha?.dataset.semaforo || null,
    puesto: document.querySelector('.puestos dd')?.childNodes[0]?.textContent.trim() ?? '',
    foto: ficha?.dataset.foto ?? null,
    url: window.location.href,
  };
}

async function mapaDelDepartamento() {
  const contenedor = document.querySelector('[data-mapa]');
  if (!contenedor) return;
  const [lista] = await Promise.all([municipios(), insertarMapa(contenedor, contenedor.dataset.mapa)]);
  const porCodigo = Object.fromEntries(lista.map((m) => [m.codigo, m]));
  colorear(contenedor, Object.fromEntries(lista.map((m) => [m.codigo, m.indice])));
  contenedor.querySelector(`path[data-codigo="${contenedor.dataset.resaltar}"]`)?.setAttribute('data-resaltado', '');
  activarMapa(contenedor, {
    texto: (cod) => {
      const m = porCodigo[cod];
      if (!m) return cod;
      return m.indice === null ? `${m.nombre}: sin índice` : `${m.nombre}: ${formatoNumero(m.indice)} · puesto ${m.puesto}`;
    },
    enlace: (cod) => (porCodigo[cod] && cod !== contenedor.dataset.resaltar ? `${raiz}m/${porCodigo[cod].slug}/` : null),
  });
}

function compartirBoton() {
  const boton = document.querySelector('[data-compartir]');
  if (!boton) return;
  boton.hidden = false;
  boton.addEventListener('click', () => compartir(infoFicha(), boton));
}

compartirBoton();
const botonHistoria = document.querySelector('[data-historia]');
if (botonHistoria && ficha) {
  botonHistoria.hidden = false;
  botonHistoria.addEventListener('click', () => abrirHistoria(ficha.dataset.codigo, 0, botonHistoria));
  if (location.hash.slice(1) === ficha.dataset.codigo || location.hash.slice(1) === ficha.dataset.slug) abrirHistoria(ficha.dataset.codigo);
}
mapaDelDepartamento().catch(() => {});
