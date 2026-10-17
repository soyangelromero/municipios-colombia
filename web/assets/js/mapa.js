// Interacción de los mapas SVG: dato al pasar el cursor o enfocar, y clic para navegar.
// Los colores iniciales ya vienen en el HTML (funcionan sin JavaScript); aquí solo se agrega
// la interacción y, si se pide, el cambio de capa.
import { raiz, tramo } from './comun.js';

/**
 * @param {HTMLElement} figura  contenedor .mapa con el <svg> adentro
 * @param {object} opciones
 * @param {(codigo: string) => string} opciones.texto   texto del dato para cada entidad
 * @param {(codigo: string) => string|null} opciones.enlace  URL al tocar la entidad
 */
export function activarMapa(figura, { texto, enlace }) {
  const svg = figura.querySelector('svg');
  if (!svg) return;
  const globo = document.createElement('div');
  globo.className = 'mapa__dato';
  globo.hidden = true;
  globo.setAttribute('role', 'status');
  figura.append(globo);

  const mostrarPanel = (figura, textoPanel, destino) => {
    figura.querySelector('.mapa__panel')?.remove();
    const panel = document.createElement('div');
    panel.className = 'mapa__panel';
    panel.innerHTML = `<p class="mapa__panel__texto">${textoPanel}</p><a class="pill pill--claro" href="${destino}">Abrir ficha</a>`;
    figura.append(panel);
    setTimeout(() => panel.classList.add('is-visible'), 10);
    setTimeout(() => panel.remove(), 900);
  };

  const mostrar = (camino, x, y) => {
    globo.textContent = texto(camino.dataset.codigo);
    globo.hidden = false;
    camino.classList.add('is-hover');
    const caja = figura.getBoundingClientRect();
    globo.style.left = `${x - caja.left}px`;
    globo.style.top = `${y - caja.top}px`;
  };

  const ocultar = (camino) => {
    globo.hidden = true;
    if (camino) camino.classList.remove('is-hover');
  };

  svg.querySelectorAll('path[data-codigo]').forEach((camino) => {
    const destino = enlace(camino.dataset.codigo);
    camino.setAttribute('tabindex', '0');
    camino.setAttribute('role', destino ? 'link' : 'img');
    camino.setAttribute('aria-label', texto(camino.dataset.codigo));
    camino.querySelector('title')?.remove(); // el globo reemplaza el título nativo
    camino.addEventListener('pointerenter', () => camino.classList.add('is-hover'));
    camino.addEventListener('pointermove', (e) => mostrar(camino, e.clientX, e.clientY));
    camino.addEventListener('pointerleave', () => ocultar(camino));
    camino.addEventListener('focus', () => {
      const r = camino.getBoundingClientRect();
      mostrar(camino, r.left + r.width / 2, r.top);
    });
    camino.addEventListener('blur', () => ocultar(camino));
    if (destino) {
      camino.style.cursor = 'pointer';
      const ir = () => (window.location.href = destino);
      camino.addEventListener('click', (e) => {
        e.preventDefault();
        const hero = document.querySelector('.hero__texto');
        if (hero) hero.classList.add('is-saliendo');
        mostrarPanel(figura, texto(camino.dataset.codigo), destino);
        setTimeout(ir, 900);
      });
      camino.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') ir();
      });
    }
  });
}

/** Pinta cada entidad según `valores[codigo]` con la escala de cinco tramos. */
export function colorear(figura, valores) {
  figura.querySelectorAll('path[data-codigo]').forEach((camino) => {
    camino.style.fill = `var(--escala-${tramo(valores[camino.dataset.codigo])})`;
  });
}

/** Carga el SVG de un mapa (por ejemplo «antioquia») dentro del contenedor. */
export async function insertarMapa(contenedor, nombre) {
  const respuesta = await fetch(`${raiz}data/mapas/${nombre}.svg`);
  if (!respuesta.ok) throw new Error(`Mapa ${nombre} no disponible`);
  const texto = await respuesta.text();
  const plantilla = document.createElement('template');
  plantilla.innerHTML = texto.trim();
  const svg = plantilla.content.querySelector('svg');
  svg.classList.add('mapa__svg');
  svg.setAttribute('focusable', 'false');
  contenedor.replaceChildren(svg);
  return contenedor;
}

