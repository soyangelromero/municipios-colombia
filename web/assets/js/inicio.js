// Portada: intro, mapa de departamentos con capas, carrusel y apariciones al desplazar.
import { cargarJSON, formatoNumero, raiz } from './comun.js';
import { activarMapa, colorear } from './mapa.js';
import { enlazarHistorias } from './historia-enlaces.js';

const NOMBRES = { indice: 'Índice', T: 'Transparencia', S: 'Servicios', G: 'Gestión', C: 'Control' };

function contar(elemento, hasta, ms) {
  const arranque = performance.now();
  const paso = (t) => {
    const p = Math.min(1, (t - arranque) / ms);
    elemento.textContent = formatoNumero(Math.round(hasta * (1 - (1 - p) ** 3)), 0);
    if (p < 1) requestAnimationFrame(paso);
  };
  requestAnimationFrame(paso);
}

/** Intro de la portada: se muestra solo la primera vez y con «Saltar» siempre visible. */
function intro() {
  const capa = document.querySelector('[data-intro]');
  if (!capa) return;
  if (!document.documentElement.classList.contains('con-intro')) {
    capa.remove();
    return;
  }
  const terminar = () => {
    if (!capa.isConnected) return;
    capa.remove();
    document.documentElement.classList.remove('con-intro');
    try {
      localStorage.setItem('intro-vista', '1');
    } catch {
      /* sin almacenamiento: la intro se verá de nuevo */
    }
  };
  capa.querySelector('[data-intro-salto]')?.addEventListener('click', terminar);
  // El mapa de la intro es una copia del de la portada (así el HTML no lo trae dos veces).
  const origen = document.querySelector('.hero__mapa .mapa');
  const destino = capa.querySelector('[data-intro-mapa]');
  if (origen && destino) {
    const copia = origen.cloneNode(true);
    copia.querySelectorAll('style, figcaption').forEach((n) => n.remove());
    destino.append(copia);
  }
  capa.querySelectorAll('[data-contar]').forEach((el) => contar(el, Number(el.dataset.contar), 1000));
  // Cascada de departamentos en el mapa de la intro.
  const caminos = capa.querySelectorAll('.intro__mapa path[data-codigo]');
  caminos.forEach((p, i) => {
    p.style.opacity = '0';
    p.style.transition = 'opacity 0.6s var(--ease)';
    setTimeout(() => (p.style.opacity = '1'), 600 + i * 18);
  });
  setTimeout(terminar, 4600);
}

function carrusel() {
  const pista = document.querySelector('[data-carrusel]');
  if (!pista) return;
  const botones = document.querySelectorAll('[data-carrusel-nav]');
  // Los botones se apagan en los extremos de la pista (y al filtrar, cuando cambia lo que cabe).
  const actualizar = () => {
    const final = pista.scrollWidth - pista.clientWidth - 2;
    botones.forEach((b) => {
      b.disabled = b.dataset.carruselNav === 'ant' ? pista.scrollLeft <= 2 : pista.scrollLeft >= final;
    });
  };
  botones.forEach((boton) => {
    boton.addEventListener('click', () => {
      const paso = pista.clientWidth * 0.8 * (boton.dataset.carruselNav === 'sig' ? 1 : -1);
      pista.scrollBy({ left: paso, behavior: 'smooth' });
    });
  });
  pista.addEventListener('scroll', actualizar, { passive: true });
  pista.addEventListener('scrollend', actualizar);
  addEventListener('resize', actualizar);
  document.querySelectorAll('.rail__filtros select').forEach((s) => s.addEventListener('change', () => requestAnimationFrame(actualizar)));
  actualizar();
}

/** Aparición suave de los elementos con la clase «revela» (desactivada con reduced motion). */
function apariciones() {
  const elementos = document.querySelectorAll('.revela');
  if (!('IntersectionObserver' in window)) {
    elementos.forEach((el) => el.classList.add('visible'));
    return;
  }
  const observador = new IntersectionObserver(
    (entradas) => {
      entradas.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          observador.unobserve(e.target);
        }
      });
    },
    { rootMargin: '0px 0px -8% 0px' },
  );
  elementos.forEach((el) => observador.observe(el));
}

async function mapa() {
  const bloque = document.querySelector('[data-mapa-pais]');
  const figura = bloque?.querySelector('.mapa');
  if (!figura) return;
  const pais = await cargarJSON('data/departamentos.json');
  const deps = pais.departamentos;
  let capa = 'indice';

  activarMapa(figura, {
    texto: (cod) => {
      const d = deps[cod];
      if (!d) return cod;
      return `${d.nombre}: ${NOMBRES[capa]} ${formatoNumero(d[capa])} (${d.municipios} ${d.municipios === 1 ? 'municipio' : 'municipios'})`;
    },
    enlace: (cod) => (deps[cod] ? `${raiz}d/${deps[cod].slug}/` : null),
  });

  const botones = bloque.querySelectorAll('[data-capa]');
  const th = bloque.querySelector('.mseg__th');
  const moverTh = (boton) => {
    if (!th || !boton) return;
    th.style.left = `${boton.offsetLeft}px`;
    th.style.width = `${boton.offsetWidth}px`;
  };
  moverTh(bloque.querySelector('[aria-pressed="true"]'));
  botones.forEach((boton) =>
    boton.addEventListener('click', () => {
      capa = boton.dataset.capa;
      botones.forEach((b) => b.setAttribute('aria-pressed', String(b === boton)));
      moverTh(boton);
      colorear(figura, Object.fromEntries(Object.entries(deps).map(([cod, d]) => [cod, d[capa]])));
    }),
  );
}

enlazarHistorias();
/** «Lo que más le piden los vecinos» se descarga (JS, CSS y datos) solo al acercarse a esa sección. */
function vecinos() {
  const seccion = document.querySelector('[data-vecinos]');
  if (!seccion) return;
  const cargar = () => import('./vecinos.js').then((m) => m.iniciar(seccion));
  if (!('IntersectionObserver' in window)) return void cargar();
  const observador = new IntersectionObserver(
    (entradas) => {
      if (!entradas.some((e) => e.isIntersecting)) return;
      observador.disconnect();
      cargar();
    },
    { rootMargin: '600px 0px' },
  );
  observador.observe(seccion);
}

intro();
carrusel();
apariciones();
vecinos();
mapa().catch(() => {});
