// Comparador: dos municipios lado a lado. Los códigos viajan en la URL (?a=05001&b=11001)
// para que la comparación se pueda compartir.
import { cargarJSON, escapar, formatoNumero, formatoSegunUnidad, municipios, pildoraSemaforo, raiz } from './comun.js';

const formulario = document.querySelector('[data-comparar]');
const resultado = document.querySelector('[data-comparar-resultado]');
const elegidos = { a: null, b: null };

const ficha = (codigo) => cargarJSON(`data/m/${codigo}.json`);

function celdaValor(f, componenteId, indicadores) {
  const dato = f.datos?.[componenteId];
  if (!dato) return '<span class="sin-dato">Sin dato</span>';
  return escapar(formatoSegunUnidad(dato.valor, indicadores[componenteId]?.unidad));
}

function marca(a, b) {
  if (a === null || a === undefined || b === null || b === undefined || a === b) return ['', ''];
  return a > b ? ['mejor', ''] : ['', 'mejor'];
}

function cabecera(f) {
  return `<div class="tarjeta">
    <p class="etiqueta">${escapar(f.departamento)}</p>
    <h2><a href="${raiz}m/${f.slug}/">${escapar(f.nombre)}</a></h2>
    <p>${pildoraSemaforo(f.semaforo, f.indice)}</p>
    <p class="nota">${f.puesto ? `Puesto ${f.puesto.nacional} de ${formatoNumero(f.puesto.nacional_de, 0)} en el país` : escapar(f.motivo_sin_indice ?? '')}</p>
  </div>`;
}

async function pintar() {
  if (!elegidos.a || !elegidos.b) {
    resultado.innerHTML = '<p class="nota">Elige los dos municipios.</p>';
    return;
  }
  const [a, b, indice] = await Promise.all([ficha(elegidos.a), ficha(elegidos.b), cargarJSON('data/indice.json')]);
  const filas = [];
  for (const pilar of indice.pilares) {
    const pa = a.pilares?.[pilar.id]?.puntaje ?? null;
    const pb = b.pilares?.[pilar.id]?.puntaje ?? null;
    const [ma, mb] = marca(pa, pb);
    filas.push(`<tr class="fila-pilar"><th scope="row"><strong>${escapar(pilar.nombre)}</strong> <small>${pilar.peso} % del índice</small></th>
      <td class="num ${ma}">${formatoNumero(pa)}</td><td class="num ${mb}">${formatoNumero(pb)}</td></tr>`);
    for (const c of pilar.componentes) {
      const sa = a.componentes?.[c.id]?.puntaje ?? null;
      const sb = b.componentes?.[c.id]?.puntaje ?? null;
      const [ca, cb] = marca(sa, sb);
      filas.push(`<tr><th scope="row">${escapar(c.nombre)}<small>puntaje ${c.puntaje === 'pares' ? 'entre pares' : 'absoluto'}</small></th>
        <td class="num ${ca}">${celdaValor(a, c.id, indice.indicadores)}<small> · ${formatoNumero(sa, 0)} pts</small></td>
        <td class="num ${cb}">${celdaValor(b, c.id, indice.indicadores)}<small> · ${formatoNumero(sb, 0)} pts</small></td></tr>`);
    }
  }
  const contexto = indice.contexto
    .filter((id) => a.datos?.[id] || b.datos?.[id])
    .map((id) => `<tr><th scope="row">${escapar(indice.indicadores[id]?.etiqueta ?? id)}<small>contexto, no puntúa</small></th>
      <td class="num">${celdaValor(a, id, indice.indicadores)}</td><td class="num">${celdaValor(b, id, indice.indicadores)}</td></tr>`)
    .join('');
  resultado.innerHTML = `
    <div class="comparar__cabecera">${cabecera(a)}${cabecera(b)}</div>
    <div class="tabla-contenedor comparar__tabla"><table class="tabla">
      <thead><tr><th scope="col">Pilar / indicador</th><th scope="col" class="num">${escapar(a.nombre)}</th><th scope="col" class="num">${escapar(b.nombre)}</th></tr></thead>
      <tbody>${filas.join('')}${contexto}</tbody></table></div>
    <p class="nota">El punto verde marca el mejor puntaje de cada fila. Los puntajes «entre pares» comparan a cada municipio con su propio grupo de capacidades, así que dos municipios de grupos distintos pueden tener puntajes parecidos con valores muy diferentes.</p>`;
}

async function iniciar() {
  if (!formulario) return;
  const lista = await municipios();
  const porCodigo = Object.fromEntries(lista.map((m) => [m.codigo, m]));
  const parametros = new URLSearchParams(window.location.search);
  for (const campo of ['a', 'b']) {
    const codigo = parametros.get(campo);
    if (codigo && porCodigo[codigo]) {
      elegidos[campo] = codigo;
      formulario.querySelector(`[data-busqueda-campo="${campo}"] input`).value = porCodigo[codigo].nombre;
    }
  }
  formulario.addEventListener('municipio-elegido', (evento) => {
    const campo = evento.target.dataset.busquedaCampo;
    elegidos[campo] = evento.detail.codigo;
    const url = new URL(window.location.href);
    url.searchParams.set(campo, evento.detail.codigo);
    window.history.replaceState(null, '', url);
    pintar();
  });
  formulario.addEventListener('submit', (e) => e.preventDefault());
  pintar();
}

iniciar().catch(() => {
  resultado.innerHTML = '<p class="nota">No se pudieron cargar los datos del comparador.</p>';
});
