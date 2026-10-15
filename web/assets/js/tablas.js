// Tablas ordenables ([data-ordenable]) y filtros del ranking ([data-filtros]).
import { normalizar } from './comun.js';

function ordenable(tabla) {
  const cuerpo = tabla.tBodies[0];
  const encabezados = [...tabla.tHead.rows[0].cells];
  encabezados.forEach((th, columna) => {
    th.tabIndex = 0;
    th.setAttribute('role', 'button');
    th.dataset.orden ??= 'texto';
    const ordenar = () => {
      const asc = th.getAttribute('aria-sort') !== 'ascending';
      encabezados.forEach((otro) => otro.removeAttribute('aria-sort'));
      th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
      const valor = (fila) => {
        const celda = fila.cells[columna];
        if (th.dataset.orden === 'num') {
          const v = parseFloat(celda.dataset.v);
          return Number.isNaN(v) ? -Infinity : v;
        }
        return normalizar(celda.textContent);
      };
      const filas = [...cuerpo.rows].sort((a, b) => {
        const va = valor(a);
        const vb = valor(b);
        const cmp = typeof va === 'number' ? va - vb : va.localeCompare(vb, 'es');
        return asc ? cmp : -cmp;
      });
      cuerpo.append(...filas);
    };
    th.addEventListener('click', ordenar);
    th.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        ordenar();
      }
    });
  });
}

function filtros(formulario, tabla) {
  formulario.hidden = false;
  const conteo = formulario.querySelector('.filtros__conteo');
  const filas = [...tabla.tBodies[0].rows];
  const aplicar = () => {
    const datos = new FormData(formulario);
    const texto = normalizar(datos.get('texto') || '');
    let visibles = 0;
    for (const fila of filas) {
      const ok =
        (!texto || normalizar(fila.dataset.nombre).includes(texto)) &&
        (!datos.get('dep') || fila.dataset.dep === datos.get('dep')) &&
        (!datos.get('grupo') || fila.dataset.grupo === datos.get('grupo')) &&
        (!datos.get('semaforo') || fila.dataset.semaforo === datos.get('semaforo'));
      fila.hidden = !ok;
      if (ok) visibles += 1;
    }
    conteo.textContent = `${visibles} municipios`;
  };
  const consulta = new URLSearchParams(window.location.search).get('q');
  if (consulta) formulario.elements.texto.value = consulta;
  formulario.addEventListener('input', aplicar);
  formulario.addEventListener('submit', (e) => e.preventDefault());
  aplicar();
}

document.querySelectorAll('table[data-ordenable]').forEach(ordenable);
const formulario = document.querySelector('[data-filtros]');
const tabla = document.querySelector('table[data-ordenable]');
if (formulario && tabla) filtros(formulario, tabla);
