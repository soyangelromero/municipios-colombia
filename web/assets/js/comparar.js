// Comparador a pantalla completa (#cmp): dos municipios, «VS» y un duelo por rubro.
// Los códigos viajan en la URL (?a=05001&b=11001) para que la comparación se comparta.
import {
  cargarJSON,
  escapar,
  formatoNumero,
  formatoSegunUnidad,
  raiz,
} from './comun.js';

const capa = document.querySelector('#cmp');
const resultado = document.querySelector('[data-cmp-resultado]');

const fichaJSON = (codigo) => cargarJSON(`data/m/${codigo}.json`);

const valor = (v) => (v === null || v === undefined ? '—' : formatoNumero(v, 1));

/** Color de un valor 0-100 (mismos cortes que el índice). */
function colorPuntaje(v) {
  if (v === null || v === undefined) return 'sin';
  return v < 40 ? 'rojo' : v >= 70 ? 'verde' : 'amarillo';
}

function fuente(indice, claves) {
  const nombres = (claves || [])
    .map((c) => indice.fuentes?.[c]?.organismo)
    .filter(Boolean);
  return [...new Set(nombres)].join(' · ') || '—';
}

function ponerFondo(lado, codigo) {
  const fondo = capa.querySelector(`[data-fondo="${lado}"]`);
  const dep = capa.querySelector(`[data-dep="${lado}"]`);
  if (!fondo) return;
  fondo.style.backgroundImage = '';
  fondo.classList.remove('cmp-fondo--silueta');
  if (!codigo) return;
  const img = new Image();
  img.onload = () => {
    fondo.style.backgroundImage = `url('${raiz}assets/fotos/${codigo}-1080.webp')`;
  };
  img.onerror = () => fondo.classList.add('cmp-fondo--silueta');
  img.src = `${raiz}assets/fotos/${codigo}-1080.webp`;
  if (dep) dep.textContent = '';
}

/** Una barra doble: A hacia la izquierda, B hacia la derecha; el ganador en verde. */
function barraDoble(pa, pb, ganaA, ganaB) {
  return `<div class="cmp-duelo__barras">
    <span class="cmp-duelo__mitad cmp-duelo__mitad--a">
      <i class="cmp-duelo__f ${ganaA ? 'cmp-duelo__f--gana' : ''}" style="width:${pa}%"></i></span>
    <span class="cmp-duelo__mitad cmp-duelo__mitad--b">
      <i class="cmp-duelo__f ${ganaB ? 'cmp-duelo__f--gana' : ''}" style="width:${pb}%"></i></span>
  </div>`;
}

function dueloMedido(rotulo, va, vb) {
  const hay = va !== null && vb !== null;
  const ganaA = hay && va > vb;
  const ganaB = hay && vb > va;
  return `<div class="cmp-duelo">
    <div class="cmp-duelo__cab"><span class="cmp-duelo__rotulo">${escapar(rotulo)}</span>
      <span class="cmp-duelo__sentido">puntaje 0 a 100, más alto es mejor</span></div>
    <div class="cmp-duelo__valores">
      <span class="cmp-duelo__valor ${ganaA ? 'cmp-duelo__valor--gana' : ''}">${va === null ? '—' : `${valor(va)}<small>/100</small>`}</span>
      <span class="cmp-duelo__valor cmp-duelo__valor--b ${ganaB ? 'cmp-duelo__valor--gana' : ''}">${vb === null ? '—' : `${valor(vb)}<small>/100</small>`}</span>
    </div>
    ${barraDoble(va ?? 0, vb ?? 0, ganaA, ganaB)}
  </div>`;
}

function dueloInfo(indice, id, a, b) {
  const da = a.datos?.[id];
  const db = b.datos?.[id];
  if (!da && !db) return '';
  const unidad = indice.indicadores?.[id]?.unidad;
  const va = da ? formatoSegunUnidad(da.valor, unidad) : '—';
  const vb = db ? formatoSegunUnidad(db.valor, unidad) : '—';
  const max = Math.max(Math.abs(da?.valor ?? 0), Math.abs(db?.valor ?? 0)) || 1;
  const pa = da ? (Math.abs(da.valor) / max) * 100 : 0;
  const pb = db ? (Math.abs(db.valor) / max) * 100 : 0;
  const fa = da ? fuente(indice, da.fuentes) : '—';
  const fb = db ? fuente(indice, db.fuentes) : '—';
  return `<div class="cmp-duelo cmp-duelo--info">
    <div class="cmp-duelo__cab"><span class="cmp-duelo__rotulo">${escapar(indice.indicadores?.[id]?.etiqueta ?? id)}</span>
      <span class="cmp-duelo__sentido">contexto, no puntúa</span></div>
    <div class="cmp-duelo__valores">
      <span class="cmp-duelo__valor">${escapar(va)}</span>
      <span class="cmp-duelo__valor cmp-duelo__valor--b">${escapar(vb)}</span>
    </div>
    ${barraDoble(pa, pb, false, false)}
    <p class="cmp-duelo__pie mono">${escapar(fa)} · ${escapar(fb)}</p>
  </div>`;
}

function titular(a, b, ganaA, ganaB, total) {
  const mejor = ganaA === ganaB ? null : ganaA > ganaB ? a : b;
  const resumen = mejor
    ? `Le va mejor a <b>${escapar(mejor.nombre)}</b> en <b>${Math.max(ganaA, ganaB)}</b> de ${total} rubros comparables.`
    : `Van parejos: cada uno gana <b>${ganaA}</b> de ${total} rubros comparables.`;
  return `<p class="cmp-titular">Índice municipal: <b>${escapar(a.nombre)}</b> ${valor(a.indice)} y
    <b>${escapar(b.nombre)}</b> ${valor(b.indice)} de 100. ${resumen}</p>`;
}

async function pintar() {
  const a = elegidos.a;
  const b = elegidos.b;
  if (!a || !b) {
    resultado.innerHTML = '<p class="nota">Elige los dos municipios para ver el duelo, rubro por rubro.</p>';
    return;
  }
  const [fa, fb, indice] = await Promise.all([
    fichaJSON(a),
    fichaJSON(b),
    cargarJSON('data/indice.json'),
  ]);
  const rubros = [
    { nombre: 'Índice municipal', va: fa.indice, vb: fb.indice },
    ...indice.pilares.map((p) => ({
      nombre: p.nombre,
      va: fa.pilares?.[p.id]?.puntaje ?? null,
      vb: fb.pilares?.[p.id]?.puntaje ?? null,
    })),
  ];
  let ganaA = 0;
  let ganaB = 0;
  let total = 0;
  for (const r of rubros) {
    if (r.va === null || r.vb === null) continue;
    total += 1;
    if (r.va > r.vb) ganaA += 1;
    else if (r.vb > r.va) ganaB += 1;
  }
  const duelos = rubros.map((r) => dueloMedido(r.nombre, r.va, r.vb)).join('');
  const info = (indice.contexto || []).map((id) => dueloInfo(indice, id, fa, fb)).join('');
  resultado.innerHTML = `${titular(fa, fb, ganaA, ganaB, total)}${duelos}${info}
    <p class="nota">El verde marca el mejor puntaje de cada rubro. Los puntajes «entre pares» comparan
    cada municipio con su propio grupo de capacidades: dos municipios de grupos distintos pueden tener
    puntajes parecidos con valores muy diferentes.</p>`;
}

const elegidos = { a: null, b: null };

async function iniciar() {
  if (!capa) return;
  const pais = await cargarJSON('data/pais.json');
  const lista = pais.municipios.map((fila) =>
    Object.fromEntries(pais.campos.map((c, i) => [c, fila[i]])),
  );
  const porCodigo = Object.fromEntries(lista.map((m) => [m.codigo, m]));
  const nombreDep = (cod) => pais.departamentos?.[cod]?.nombre ?? '';
  const parametros = new URLSearchParams(window.location.search);
  for (const campo of ['a', 'b']) {
    const codigo = parametros.get(campo);
    if (codigo && porCodigo[codigo]) {
      elegidos[campo] = codigo;
      capa.querySelector(`[data-busqueda-campo="${campo}"] input`).value = porCodigo[codigo].nombre;
      ponerFondo(campo, codigo);
      const dep = capa.querySelector(`[data-dep="${campo}"]`);
      if (dep) dep.textContent = nombreDep(porCodigo[codigo].dep);
    }
  }
  capa.addEventListener('municipio-elegido', (evento) => {
    const campo = evento.target.dataset.busquedaCampo;
    elegidos[campo] = evento.detail.codigo;
    ponerFondo(campo, evento.detail.codigo);
    const dep = capa.querySelector(`[data-dep="${campo}"]`);
    if (dep) dep.textContent = nombreDep(evento.detail.dep);
    const url = new URL(window.location.href);
    url.searchParams.set(campo, evento.detail.codigo);
    window.history.replaceState(null, '', url);
    pintar();
  });
  pintar();
}

iniciar().catch(() => {
  if (resultado) resultado.innerHTML = '<p class="nota">No se pudieron cargar los datos del comparador.</p>';
});
