// Ficha de municipio: mapa del departamento, compartir y modo historia.
import { formatoNumero, municipios, raiz } from './comun.js';
import { activarMapa, colorear, insertarMapa } from './mapa.js';

const ficha = document.querySelector('.ficha');

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

function compartir() {
  const boton = document.querySelector('[data-compartir]');
  if (!boton) return;
  boton.hidden = false;
  boton.addEventListener('click', async () => {
    const datos = { title: document.title, url: window.location.href };
    if (navigator.share) {
      try {
        await navigator.share(datos);
      } catch {
        /* la persona canceló */
      }
      return;
    }
    try {
      await navigator.clipboard.writeText(datos.url);
      boton.textContent = 'Enlace copiado';
      setTimeout(() => (boton.textContent = 'Compartir'), 2500);
    } catch {
      window.prompt('Copia este enlace:', datos.url);
    }
  });
}

/** Modo historia: recorre los capítulos de la ficha a pantalla completa, uno por uno. */
function historia() {
  const boton = document.querySelector('[data-historia]');
  const capitulos = [...document.querySelectorAll('[data-capitulo]')];
  if (!boton || capitulos.length < 2) return;
  boton.hidden = false;

  boton.addEventListener('click', () => {
    let actual = 0;
    const capa = document.createElement('div');
    capa.className = 'historia';
    capa.setAttribute('role', 'dialog');
    capa.setAttribute('aria-modal', 'true');
    capa.setAttribute('aria-label', `Historia de ${ficha?.dataset.nombre ?? 'municipio'}`);
    capa.innerHTML = `
      <div>
        <div class="historia__progreso">${capitulos.map(() => '<span></span>').join('')}</div>
        <div class="historia__barra"><strong data-titulo></strong>
          <button type="button" class="boton boton--secundario" data-cerrar>Cerrar</button></div>
      </div>
      <div class="historia__contenido" data-contenido tabindex="-1"></div>
      <div class="historia__nav">
        <button type="button" class="boton boton--secundario" data-anterior>Anterior</button>
        <button type="button" class="boton" data-siguiente>Siguiente</button>
      </div>`;
    const contenido = capa.querySelector('[data-contenido]');
    const barras = capa.querySelectorAll('.historia__progreso span');

    const mostrar = (i) => {
      actual = Math.max(0, Math.min(capitulos.length - 1, i));
      const copia = capitulos[actual].cloneNode(true);
      copia.querySelectorAll('[id]').forEach((el) => el.removeAttribute('id'));
      copia.querySelectorAll('.acciones').forEach((el) => el.remove());
      contenido.replaceChildren(copia);
      contenido.scrollTop = 0;
      barras.forEach((b, j) => b.toggleAttribute('data-hecho', j <= actual));
      capa.querySelector('[data-titulo]').textContent = `${actual + 1} de ${capitulos.length} · ${capitulos[actual].dataset.capitulo}`;
      capa.querySelector('[data-anterior]').disabled = actual === 0;
      capa.querySelector('[data-siguiente]').textContent = actual === capitulos.length - 1 ? 'Terminar' : 'Siguiente';
      contenido.focus();
    };
    const cerrar = () => {
      capa.remove();
      document.removeEventListener('keydown', teclas);
      document.body.style.overflow = '';
      boton.focus();
    };
    const teclas = (e) => {
      if (e.key === 'Escape') cerrar();
      if (e.key === 'ArrowRight') mostrar(actual + 1);
      if (e.key === 'ArrowLeft') mostrar(actual - 1);
    };

    capa.querySelector('[data-cerrar]').addEventListener('click', cerrar);
    capa.querySelector('[data-anterior]').addEventListener('click', () => mostrar(actual - 1));
    capa.querySelector('[data-siguiente]').addEventListener('click', () =>
      actual === capitulos.length - 1 ? cerrar() : mostrar(actual + 1),
    );
    document.addEventListener('keydown', teclas);
    document.body.style.overflow = 'hidden';
    document.body.append(capa);
    mostrar(0);
  });
}

compartir();
historia();
mapaDelDepartamento().catch(() => {});
