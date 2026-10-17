// Modo historia (#story): recorre los capítulos de la ficha a pantalla completa.
import { compartir } from './compartir.js';

const DURACION = 9000;
const SENSIBILIDAD = 40;

function recogerCapas() {
  const ficha = document.querySelector('.ficha');
  if (!ficha) return null;
  const defs = [];
  const portada = ficha.querySelector('.ficha__heroe .heroe__cuerpo');
  if (portada) defs.push({ nombre: 'Portada', origen: portada });
  ficha.querySelectorAll('.cap[data-capitulo]').forEach((s) => {
    defs.push({ nombre: s.dataset.capitulo || '', origen: s });
  });
  return defs.length < 2 ? null : { ficha, defs };
}

function infoFicha(ficha) {
  const indice = ficha.dataset.indice ?? '';
  return {
    nombre: ficha.dataset.nombre ?? document.title,
    slug: ficha.dataset.codigo ?? '',
    valor: indice === '' ? null : Number(indice.replace(',', '.')),
    semaforo: ficha.dataset.semaforo || null,
    puesto: document.querySelector('.puestos dd')?.childNodes[0]?.textContent.trim() ?? '',
    foto: ficha.dataset.foto ?? null,
    url: window.location.href,
  };
}

function limpiar(nodo) {
  nodo.querySelectorAll('[id]').forEach((el) => el.removeAttribute('id'));
  nodo.querySelectorAll('.acciones').forEach((el) => el.remove());
  nodo.classList.add('cap');
}

export function activarHistoria() {
  const boton = document.querySelector('[data-historia]');
  if (!boton) return;
  const datos = recogerCapas();
  if (!datos) return;
  boton.hidden = false;
  const { ficha, defs } = datos;
  const info = infoFicha(ficha);

  let capa = null;
  let indice = 0;
  let reloj = null;
  let pausado = false;
  let arrastre = null;
  let bloqueoRueda = 0;
  let huboGesto = false;

  const cuerpo = () => capa?.querySelector('[data-cuerpo]');

  function reiniciarReloj() {
    clearTimeout(reloj);
    if (pausado || indice >= defs.length - 1) return;
    reloj = setTimeout(() => mostrar(indice + 1), DURACION);
  }

  function botonOjo(copia, etiqueta, texto, accion) {
    const ojo = copia.querySelector('.ojo');
    if (!ojo) return null;
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'st-btn st-btn--ojo';
    b.textContent = texto;
    b.setAttribute('aria-label', etiqueta);
    b.addEventListener('click', accion);
    ojo.append(b);
    return b;
  }

  function mostrar(n) {
    if (!capa) return;
    indice = Math.max(0, Math.min(defs.length - 1, n));
    const copia = defs[indice].origen.cloneNode(true);
    limpiar(copia);
    const contenedor = cuerpo();
    contenedor.replaceChildren(copia);
    contenedor.scrollTop = 0;

    capa.querySelector('.st-shade').classList.toggle('dim', indice >= 1);
    capa.querySelectorAll('.prog i').forEach((barra, j) => {
      barra.classList.toggle('hecho', j < indice);
      barra.classList.remove('activo');
      if (j === indice) {
        void barra.offsetWidth;
        barra.classList.add('activo');
      }
    });
    capa.querySelector('[data-nombre-cap]').textContent = defs[indice].nombre;

    const fondo = capa.querySelector('.st-bg');
    if (fondo) {
      fondo.style.animation = 'none';
      void fondo.offsetWidth;
      fondo.style.animation = '';
    }
    const anterior = capa.querySelector('[data-anterior]');
    const siguiente = capa.querySelector('[data-siguiente]');
    if (anterior) anterior.disabled = indice === 0;
    if (siguiente) siguiente.textContent = indice === defs.length - 1 ? 'Terminar' : 'Siguiente';

    const esPortada = indice === 0;
    const esResumen = indice === defs.length - 1;
    if (!esPortada && !esResumen) {
      const b = botonOjo(copia, `Compartir esta parte: ${defs[indice].nombre}`, '\u2197', () =>
        compartir(info, b),
      );
    }
    botonOjo(copia, 'Reportar un error en este capítulo', '\u2691', () => {
      cerrar();
      document.querySelector('#reportar')?.scrollIntoView();
    });
    reiniciarReloj();
  }

  function pausar(forzar) {
    pausado = forzar ?? !pausado;
    capa.querySelector('.prog')?.classList.toggle('pausado', pausado);
    capa.querySelector('.st-head')?.classList.toggle('pausado', pausado);
    const b = capa.querySelector('[data-pausa]');
    if (b) {
      b.textContent = pausado ? '\u25B6' : '\u275A\u275A';
      b.setAttribute('aria-label', pausado ? 'Seguir' : 'Pausar');
    }
    if (pausado) clearTimeout(reloj);
    else reiniciarReloj();
  }

  function abrir() {
    capa = document.createElement('div');
    capa.id = 'story';
    capa.setAttribute('role', 'dialog');
    capa.setAttribute('aria-modal', 'true');
    capa.setAttribute('aria-label', `Historia de ${info.nombre}`);
    const barras = defs.map(() => '<i><b></b></i>').join('');
    const fondo = info.foto
      ? `<div class="st-bg" style="background-image:url('${info.foto}')"></div>`
      : '<div class="st-bg st-bg--silueta"></div>';
    capa.innerHTML = `
      ${fondo}
      <div class="st-shade" aria-hidden="true"></div>
      <div class="st-ui">
        <div class="prog" data-prog style="--dur:${DURACION / 1000}s">${barras}</div>
        <div class="st-head">
          <span class="st-head__nombre"><b>${info.nombre}</b><small data-nombre-cap></small></span>
          <span class="st-head__pausa mono">En pausa</span>
          <button type="button" class="st-btn" data-pausa aria-label="Pausar">\u275A\u275A</button>
          <button type="button" class="st-btn" data-cerrar aria-label="Cerrar">\u2715</button>
        </div>
        <div class="st-body" data-cuerpo></div>
        <div class="st-nav">
          <button type="button" class="st-btn" data-anterior aria-label="Capítulo anterior">\u2039</button>
          <button type="button" class="st-btn st-btn--ancho" data-siguiente>Siguiente</button>
        </div>
      </div>`;
    document.body.append(capa);
    document.body.style.overflow = 'hidden';
    history.replaceState(null, '', `#${info.slug}`);

    capa.querySelector('[data-cerrar]').addEventListener('click', cerrar);
    capa.querySelector('[data-pausa]').addEventListener('click', () => pausar());
    capa.querySelector('[data-anterior]').addEventListener('click', () => mostrar(indice - 1));
    capa.querySelector('[data-siguiente]').addEventListener('click', () => {
      if (indice >= defs.length - 1) cerrar();
      else mostrar(indice + 1);
    });
    capa.querySelector('[data-prog]').addEventListener('click', (e) => {
      const barra = e.target.closest('i');
      if (barra) mostrar([...barra.parentElement.children].indexOf(barra));
    });
    capa.addEventListener('pointerdown', (e) => {
      if (e.target.closest('a, button')) return;
      arrastre = { x: e.clientX, y: e.clientY, ancho: window.innerWidth };
    });
    capa.addEventListener('pointerup', (e) => {
      if (!arrastre) return;
      const dx = e.clientX - arrastre.x;
      const dy = e.clientY - arrastre.y;
      arrastre = null;
      if (Math.abs(dx) < 60 && dy < 120) return;
      huboGesto = true;
      if (dy > 120 && Math.abs(dy) > Math.abs(dx)) return cerrar();
      mostrar(indice + (dx < 0 ? 1 : -1));
    });
    capa.addEventListener('wheel', rueda, { passive: true });
    document.addEventListener('keydown', teclas);
    capa.querySelector('[data-cuerpo]').addEventListener('click', (e) => {
      if (huboGesto) {
        huboGesto = false;
        return;
      }
      if (e.target.closest('a, button')) return;
      mostrar(indice + 1);
    });
    mostrar(0);
    capa.querySelector('[data-pausa]')?.focus();
  }

  function rueda(e) {
    const ahora = performance.now();
    if (ahora - bloqueoRueda < 750 || Math.abs(e.deltaY) < SENSIBILIDAD) return;
    bloqueoRueda = ahora;
    mostrar(indice + (e.deltaY > 0 ? 1 : -1));
  }

  function teclas(e) {
    if (e.key === 'Escape') return cerrar();
    if (e.key === 'ArrowRight' || e.key === ' ') return mostrar(indice + 1);
    if (e.key === 'ArrowLeft') return mostrar(indice - 1);
  }

  function cerrar() {
    if (!capa) return;
    clearTimeout(reloj);
    capa.remove();
    capa = null;
    document.removeEventListener('keydown', teclas);
    document.body.style.overflow = '';
    history.replaceState(null, '', window.location.pathname + window.location.search);
    boton.focus();
  }

  boton.addEventListener('click', abrir);
  if (window.location.hash === `#${info.slug}`) abrir();
}
