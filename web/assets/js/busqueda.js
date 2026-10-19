// Buscador de municipios con sugerencias accesibles (combobox). Se activa en cada [data-busqueda].
// Por defecto, elegir un municipio abre su ficha. Si el contenedor tiene data-busqueda-campo,
// en cambio emite el evento «municipio-elegido» (lo usa el comparador).
import { cargarJSON, escapar, municipios, normalizar, raiz } from './comun.js';

const MAXIMO = 8;

function coincidencias(lista, consulta) {
  const q = normalizar(consulta);
  if (q.length < 2) return [];
  const empiezan = [];
  const contienen = [];
  for (const m of lista) {
    const nombre = m._clave;
    if (nombre.startsWith(q)) empiezan.push(m);
    else if (nombre.includes(q)) contienen.push(m);
    if (empiezan.length >= MAXIMO) break;
  }
  return [...empiezan, ...contienen].slice(0, MAXIMO);
}

function activar(contenedor, lista, departamentos) {
  const entrada = contenedor.querySelector('input');
  const sugerencias = contenedor.querySelector('[role="listbox"]');
  let actuales = [];
  let seleccion = -1;

  const cerrar = () => {
    sugerencias.hidden = true;
    entrada.setAttribute('aria-expanded', 'false');
    entrada.removeAttribute('aria-activedescendant');
    seleccion = -1;
  };

  const elegir = (m) => {
    if (contenedor.dataset.busquedaCampo) {
      entrada.value = m.nombre;
      cerrar();
      contenedor.dispatchEvent(new CustomEvent('municipio-elegido', { detail: m, bubbles: true }));
    } else {
      window.location.href = `${raiz}m/${m.slug}/`;
    }
  };

  const pintar = () => {
    sugerencias.innerHTML = actuales
      .map(
        (m, i) =>
          `<li role="option" id="${sugerencias.id}-${i}" aria-selected="${i === seleccion}" data-i="${i}">` +
          `<span>${escapar(m.nombre)}</span><small>${escapar(departamentos[m.dep]?.nombre ?? '')}</small></li>`,
      )
      .join('');
    if (!actuales.length && entrada.value.trim().length >= 2) {
      sugerencias.innerHTML = '<li aria-disabled="true">Ningún municipio con ese nombre</li>';
    }
    const visible = sugerencias.innerHTML !== '';
    sugerencias.hidden = !visible;
    entrada.setAttribute('aria-expanded', String(visible));
    if (seleccion >= 0) entrada.setAttribute('aria-activedescendant', `${sugerencias.id}-${seleccion}`);
  };

  entrada.addEventListener('input', () => {
    actuales = coincidencias(lista, entrada.value);
    seleccion = actuales.length ? 0 : -1;
    pintar();
  });

  entrada.addEventListener('keydown', (evento) => {
    if (evento.key === 'ArrowDown' || evento.key === 'ArrowUp') {
      if (!actuales.length) return;
      evento.preventDefault();
      const paso = evento.key === 'ArrowDown' ? 1 : -1;
      seleccion = (seleccion + paso + actuales.length) % actuales.length;
      pintar();
    } else if (evento.key === 'Enter') {
      if (seleccion >= 0 && actuales[seleccion]) {
        evento.preventDefault();
        elegir(actuales[seleccion]);
      }
    } else if (evento.key === 'Escape') {
      cerrar();
    }
  });

  sugerencias.addEventListener('mousedown', (evento) => {
    const item = evento.target.closest('[data-i]');
    if (item) {
      evento.preventDefault();
      elegir(actuales[Number(item.dataset.i)]);
    }
  });

  entrada.addEventListener('blur', () => setTimeout(cerrar, 120));
}

let cargando = null;

/** Descarga el listado de municipios solo cuando alguien usa un buscador. */
function cargar(contenedores) {
  cargando ??= (async () => {
    try {
      const [lista, pais] = await Promise.all([municipios(), cargarJSON('data/pais.json')]);
      for (const m of lista) m._clave = normalizar(m.nombre);
      lista.sort((a, b) => (b.poblacion ?? 0) - (a.poblacion ?? 0)); // los más poblados primero
      contenedores.forEach((c) => activar(c, lista, pais.departamentos));
    } catch {
      // Sin datos (por ejemplo, abierto sin servidor): el buscador simplemente no sugiere.
    }
  })();
  return cargando;
}

function iniciar() {
  const contenedores = document.querySelectorAll('[data-busqueda]');
  contenedores.forEach((c) => {
    const entrada = c.querySelector('input');
    const activarAhora = () =>
      cargar(contenedores).then(() => {
        // Lo que se alcanzó a escribir mientras cargaba también debe sugerir.
        if (entrada.value && document.activeElement === entrada) entrada.dispatchEvent(new Event('input'));
      });
    entrada.addEventListener('focus', activarAhora, { once: true });
    entrada.addEventListener('pointerenter', activarAhora, { once: true });
  });
}

iniciar();
