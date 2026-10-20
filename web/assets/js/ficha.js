// Ficha de municipio: mapa del departamento, compartir y modo historia.
import { cargarJSON, formatoNumero, municipios, raiz } from './comun.js';
import { activarMapa, colorear, insertarMapa } from './mapa.js';
import { compartir, infoTarjeta } from './compartir.js';
const abrirHistoria = (codigo, cap, origen) => import('./historia.js').then((m) => m.abrirHistoria(codigo, cap, origen));

const ficha = document.querySelector('.ficha');

/** Datos de la ficha para la tarjeta de compartir: salen de los JSON del sitio. */
async function infoFicha() {
  const codigo = ficha?.dataset.codigo ?? '';
  const [m, idx, pais] = await Promise.all([
    cargarJSON(`data/m/${codigo}.json`),
    cargarJSON('data/indice.json'),
    cargarJSON('data/pais.json'),
  ]);
  return infoTarjeta(m, idx, pais, { slug: codigo, foto: ficha?.dataset.foto ?? null, url: window.location.href });
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
  boton.addEventListener('click', async () => {
    try {
      compartir(await infoFicha(), boton);
    } catch {
      /* sin los datos no hay tarjeta: el botón no hace nada */
    }
  });
}

compartirBoton();
const botonHistoria = document.querySelector('[data-historia]');
if (botonHistoria && ficha) {
  botonHistoria.hidden = false;
  botonHistoria.addEventListener('click', () => abrirHistoria(ficha.dataset.codigo, 0, botonHistoria));
  if (location.hash.slice(1) === ficha.dataset.codigo || location.hash.slice(1) === ficha.dataset.slug) abrirHistoria(ficha.dataset.codigo);
}
mapaDelDepartamento().catch(() => {});
