// Ficha de municipio: mapa del departamento, compartir y modo historia.
import { formatoNumero, municipios, raiz } from './comun.js';
import { activarMapa, colorear, insertarMapa } from './mapa.js';
import { compartir } from './compartir.js';

const ficha = document.querySelector('.ficha');

/** Datos de la ficha para la tarjeta de compartir, leídos del propio HTML. */
function infoFicha() {
  const color = document.querySelector('.indice-grande')?.className.match(/indice-grande--(\w+)/);
  const valor = document.querySelector('.indice-grande__valor')?.textContent.trim() ?? '';
  return {
    nombre: ficha?.dataset.nombre ?? document.title,
    slug: ficha?.dataset.codigo ?? '',
    valor: valor === '—' ? null : Number(valor.replace(',', '.')),
    semaforo: color ? color[1] : null,
    puesto: document.querySelector('.puestos dd')?.textContent.trim() ?? '',
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
    const fondo = ficha?.dataset.foto
      ? `<div class="historia__fondo" style="background-image:url('${ficha.dataset.foto}')"></div>`
      : '';
    capa.innerHTML = `
      ${fondo}
      <div>
        <div class="historia__progreso">${capitulos.map(() => '<span></span>').join('')}</div>
        <div class="historia__barra"><strong data-titulo></strong>
          <span>
            <button type="button" class="boton boton--secundario" data-compartir-historia>Compartir</button>
            <button type="button" class="boton boton--secundario" data-cerrar>Cerrar</button>
          </span></div>
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

    barras.forEach((b, j) => b.addEventListener('click', () => mostrar(j)));
    capa.querySelector('[data-cerrar]').addEventListener('click', cerrar);
    capa.querySelector('[data-anterior]').addEventListener('click', () => mostrar(actual - 1));
    capa.querySelector('[data-siguiente]').addEventListener('click', () =>
      actual === capitulos.length - 1 ? cerrar() : mostrar(actual + 1),
    );
    capa.querySelector('[data-compartir-historia]').addEventListener('click', (e) => compartir(infoFicha(), e.target));
    // Un toque en el contenido (fuera de enlaces y botones) avanza de capítulo.
    contenido.addEventListener('click', (e) => {
      if (e.target.closest('a, button')) return;
      if (actual < capitulos.length - 1) mostrar(actual + 1);
    });
    document.addEventListener('keydown', teclas);
    document.body.style.overflow = 'hidden';
    document.body.append(capa);
    mostrar(0);
  });
}

compartirBoton();
historia();
mapaDelDepartamento().catch(() => {});
