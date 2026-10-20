// Tarjeta para compartir: hoja con dos formatos (feed e historias) dibujados en <canvas>.
import { formatoNumero } from './comun.js';

const COLORES = { verde: '#22C55E', amarillo: '#EAB308', rojo: '#EF4444', sin: '#97a3b8' };
const TEXTO = { verde: 'Verde', amarillo: 'Amarillo', rojo: 'Rojo', sin: 'Sin índice' };
const FORMATOS = [
  { id: 'feed', nombre: 'Feed', ancho: 1080, alto: 1350 },
  { id: 'historias', nombre: 'Historias', ancho: 1080, alto: 1920 },
];

async function cargarFoto(src) {
  if (!src) return null;
  try {
    const resp = await fetch(src);
    if (!resp.ok) return null;
    return await createImageBitmap(await resp.blob());
  } catch {
    return null;
  }
}

function envolver(texto, maximo) {
  return texto.length <= maximo ? texto : texto.slice(0, maximo - 1).trimEnd() + '…';
}

function lineas(ctx, palabras, x, y, maxAncho, alto) {
  let linea = '';
  const salida = [];
  for (const palabra of palabras) {
    const prueba = linea ? `${linea} ${palabra}` : palabra;
    if (ctx.measureText(prueba).width > maxAncho && linea) {
      salida.push(linea);
      linea = palabra;
    } else {
      linea = prueba;
    }
  }
  if (linea) salida.push(linea);
  salida.forEach((l, i) => ctx.fillText(l, x, y + i * alto));
  return salida.length;
}

const fotos = new Map(); // las fotos ya descargadas se reutilizan entre formatos

function fotoDe(src) {
  if (!src) return Promise.resolve(null);
  if (!fotos.has(src)) fotos.set(src, cargarFoto(src));
  return fotos.get(src);
}

async function prepararFuentes() {
  try {
    await document.fonts.ready;
    await Promise.all([
      document.fonts.load('400 38px Geist'),
      document.fonts.load('600 38px Geist'),
      document.fonts.load('800 150px Geist'),
      document.fonts.load('500 32px "Geist Mono"'),
      document.fonts.load('600 38px "Geist Mono"'),
    ]);
  } catch {
    /* si las fuentes no cargan, se dibuja con la del sistema */
  }
}

const PILARES_CORTOS = { T: 'Transparencia', S: 'Servicios y seguridad', G: 'Gestión fiscal', C: 'Control' };
const estadoDe = (v, semaforo) =>
  v === null || v === undefined ? 'sin' : v < semaforo.rojo_menor_a ? 'rojo' : v >= semaforo.verde_desde ? 'verde' : 'amarillo';

/**
 * Datos de la tarjeta a partir de la ficha (data/m/<código>.json), indice.json y pais.json.
 * `extra` puede traer { url, foto, slug, etiqueta, valor, semaforo } para sustituir el índice por
 * el de un pilar (al compartir un capítulo de la historia).
 */
export function infoTarjeta(m, idx, pais, extra = {}) {
  const poblacion = m.datos?.poblacion?.valor;
  const detalle = [
    poblacion ? `${formatoNumero(poblacion, 0)} habitantes` : null,
    m.grupo ? (pais.grupos?.[m.grupo] ?? m.grupo) : null,
  ].filter(Boolean);
  const p = m.puesto;
  return {
    nombre: m.nombre,
    departamento: m.departamento,
    detalle: detalle.join(' · '),
    alcalde: m.alcalde?.nombre ?? null,
    valor: m.indice,
    semaforo: m.semaforo,
    puestos: p
      ? [
          p.departamento ? `Puesto ${p.departamento} de ${formatoNumero(p.departamento_de, 0)} en ${m.departamento}` : null,
          p.nacional ? `Puesto ${formatoNumero(p.nacional, 0)} de ${formatoNumero(p.nacional_de, 0)} en el país` : null,
        ].filter(Boolean)
      : [],
    pilares: idx.pilares.map((x) => {
      const v = m.pilares?.[x.id]?.valido ? m.pilares[x.id].puntaje : null;
      return { nombre: PILARES_CORTOS[x.id] ?? x.nombre, valor: v, semaforo: estadoDe(v, idx.semaforo) };
    }),
    ...extra,
  };
}

function rectRedondeado(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function fondo(ctx, ancho, alto, foto, color) {
  ctx.fillStyle = '#0a0d12';
  ctx.fillRect(0, 0, ancho, alto);
  if (foto) {
    const escala = Math.max(ancho / foto.width, alto / foto.height);
    const w = foto.width * escala;
    const h = foto.height * escala;
    ctx.drawImage(foto, (ancho - w) / 2, (alto - h) / 2, w, h);
  } else {
    const halo = ctx.createRadialGradient(ancho / 2, alto * 0.4, 40, ancho / 2, alto * 0.4, ancho);
    halo.addColorStop(0, `${color}33`);
    halo.addColorStop(1, 'rgba(10,13,18,0)');
    ctx.fillStyle = halo;
    ctx.fillRect(0, 0, ancho, alto);
  }
  const velo = ctx.createLinearGradient(0, 0, 0, alto);
  velo.addColorStop(0, 'rgba(10,13,18,0.30)');
  velo.addColorStop(0.45, 'rgba(10,13,18,0.50)');
  velo.addColorStop(0.7, 'rgba(10,13,18,0.90)');
  velo.addColorStop(1, 'rgba(10,13,18,0.97)');
  ctx.fillStyle = velo;
  ctx.fillRect(0, 0, ancho, alto);
}

/** Medidor semicircular: pista tenue, arco de rojo a verde hasta el valor y una perilla. */
function medidor(ctx, cx, cy, radio, valor, color) {
  ctx.lineCap = 'round';
  ctx.lineWidth = 46;
  ctx.strokeStyle = 'rgba(255,255,255,0.14)';
  ctx.beginPath();
  ctx.arc(cx, cy, radio, Math.PI, 2 * Math.PI);
  ctx.stroke();
  if (valor === null || valor === undefined) return;
  const fin = Math.PI + (Math.PI * Math.min(Math.max(valor, 0), 100)) / 100;
  const degradado = ctx.createLinearGradient(cx - radio, 0, cx + radio, 0);
  degradado.addColorStop(0, '#EF4444');
  degradado.addColorStop(0.5, '#EAB308');
  degradado.addColorStop(1, '#22C55E');
  ctx.strokeStyle = degradado;
  ctx.beginPath();
  ctx.arc(cx, cy, radio, Math.PI, fin);
  ctx.stroke();
  const x = cx + radio * Math.cos(fin);
  const y = cy + radio * Math.sin(fin);
  ctx.fillStyle = '#ffffff';
  ctx.beginPath();
  ctx.arc(x, y, 31, 0, 2 * Math.PI);
  ctx.fill();
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, 19, 0, 2 * Math.PI);
  ctx.fill();
}

/** Dibuja la tarjeta (ancho × alto) en un contexto ya listo: sin esperas y sin red. */
function dibujar(ctx, info, ancho, alto, foto) {
  const color = COLORES[info.semaforo] ?? COLORES.sin;
  const margen = 72;
  const interior = ancho - margen * 2;
  const sobra = Math.max(alto - 1350, 0); // en historias sobra alto: se reparte entre bloques
  const bajoCabecera = Math.round(sobra * 0.22);
  const bajoMedidor = Math.round(sobra * 0.5);
  fondo(ctx, ancho, alto, foto, color);
  ctx.textBaseline = 'alphabetic';
  ctx.textAlign = 'left';

  // Cabecera: marca y departamento.
  [36, 52, 68].forEach((h, i) => {
    ctx.fillStyle = '#f4f5f7';
    rectRedondeado(ctx, margen + i * 30, 124 - h, 22, h, 6);
    ctx.fill();
  });
  ctx.fillStyle = '#f4f5f7';
  ctx.font = '600 38px "Geist", system-ui, sans-serif';
  ctx.fillText('Municipios Colombia', margen + 104, 120);
  ctx.fillStyle = '#b7c0cf';
  ctx.font = '500 32px "Geist Mono", monospace';
  ctx.textAlign = 'right';
  ctx.fillText((info.departamento ?? '').toUpperCase(), ancho - margen, 118);
  ctx.textAlign = 'left';

  // Nombre: el cuerpo más grande en que cabe en una línea.
  let cuerpo = 150;
  const nombre = envolver(info.nombre, 34);
  ctx.font = `800 ${cuerpo}px "Geist", system-ui, sans-serif`;
  while (ctx.measureText(nombre).width > interior && cuerpo > 60) {
    cuerpo -= 4;
    ctx.font = `800 ${cuerpo}px "Geist", system-ui, sans-serif`;
  }
  const yNombre = 252 + bajoCabecera;
  ctx.fillStyle = '#ffffff';
  ctx.fillText(nombre, margen, yNombre);
  ctx.fillStyle = '#c3cad6';
  ctx.font = '400 38px "Geist", system-ui, sans-serif';
  if (info.detalle) ctx.fillText(info.detalle, margen, yNombre + 62);
  if (info.alcalde) {
    const y = yNombre + 116;
    ctx.font = '500 28px "Geist Mono", monospace';
    ctx.fillStyle = '#9aa5b6';
    const rotulo = 'ALCALDÍA 2024-2027  ';
    ctx.fillText(rotulo, margen, y);
    const anchoRotulo = ctx.measureText(rotulo).width;
    ctx.fillStyle = '#ffffff';
    ctx.font = '600 38px "Geist", system-ui, sans-serif';
    ctx.fillText(envolver(info.alcalde, 30), margen + anchoRotulo, y);
  }

  // Medidor con el valor al centro.
  const cx = ancho / 2;
  const cy = 690 + bajoCabecera + Math.round(bajoMedidor * 0.4);
  medidor(ctx, cx, cy, 262, info.valor, color);
  ctx.textAlign = 'center';
  ctx.fillStyle = '#ffffff';
  ctx.font = '800 150px "Geist", system-ui, sans-serif';
  ctx.fillText(info.valor === null || info.valor === undefined ? '—' : formatoNumero(info.valor), cx, cy - 18);
  ctx.fillStyle = '#b7c0cf';
  ctx.font = '500 34px "Geist Mono", monospace';
  ctx.fillText(info.etiqueta ? `${info.etiqueta.toUpperCase()} SOBRE 100` : 'ÍNDICE MUNICIPAL SOBRE 100', cx, cy + 64);
  ctx.fillStyle = '#ffffff';
  ctx.font = '600 44px "Geist", system-ui, sans-serif';
  const puestos = info.etiqueta ? [] : (info.puestos ?? []);
  puestos.forEach((linea, i) => ctx.fillText(linea, cx, cy + 126 + i * 54));
  ctx.textAlign = 'left';

  // Los cuatro pilares.
  const alturaCaja = 112;
  const anchoCaja = (interior - 24) / 2;
  const y0 = cy + 126 + Math.max(puestos.length, 1) * 54 + 30 + Math.round(bajoMedidor * 0.15);
  (info.pilares ?? []).slice(0, 4).forEach((p, i) => {
    const x = margen + (i % 2) * (anchoCaja + 24);
    const y = y0 + Math.floor(i / 2) * (alturaCaja + 14);
    ctx.fillStyle = 'rgba(20,25,34,0.78)';
    rectRedondeado(ctx, x, y, anchoCaja, alturaCaja, 26);
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.12)';
    ctx.lineWidth = 2;
    ctx.stroke();
    const c = COLORES[p.semaforo] ?? COLORES.sin;
    ctx.fillStyle = c;
    ctx.beginPath();
    ctx.arc(x + 38, y + 38, 11, 0, 2 * Math.PI);
    ctx.fill();
    ctx.fillStyle = '#d9dee7';
    ctx.font = '400 32px "Geist", system-ui, sans-serif';
    ctx.fillText(envolver(p.nombre, 24), x + 62, y + 49);
    ctx.fillStyle = c;
    ctx.font = '800 56px "Geist", system-ui, sans-serif';
    ctx.fillText(p.valor === null || p.valor === undefined ? 'Sin dato' : `${formatoNumero(p.valor, 0)}/100`, x + 30, y + 98);
  });

  // Pie: aviso y dirección.
  ctx.fillStyle = '#9aa5b6';
  ctx.font = '400 30px "Geist", system-ui, sans-serif';
  ctx.fillText('Datos públicos y fuentes oficiales. Lectura de datos, no una acusación.', margen, alto - 104);
  ctx.fillStyle = '#ffffff';
  ctx.font = '600 38px "Geist Mono", monospace';
  ctx.fillText(info.url.replace(/^https?:\/\//, '').replace(/\/$/, ''), margen, alto - 52);
}

/** Vista previa rápida: la misma tarjeta a escala pequeña y sin codificar PNG. */
export async function vistaPrevia(lienzo, info, ancho, alto, anchoVista = 300) {
  const [foto] = await Promise.all([fotoDe(info.foto), prepararFuentes()]);
  const escala = anchoVista / ancho;
  lienzo.width = anchoVista;
  lienzo.height = Math.round(alto * escala);
  const ctx = lienzo.getContext('2d');
  ctx.scale(escala, escala);
  dibujar(ctx, info, ancho, alto, foto);
}

/** Dibuja la tarjeta completa (ancho × alto) y devuelve un Blob JPEG (≈ 5 veces más liviano que PNG: se comparte más rápido). */
export async function tarjeta(info, ancho = 1080, alto = 1350) {
  const [foto] = await Promise.all([fotoDe(info.foto), prepararFuentes()]);
  const lienzo = document.createElement('canvas');
  lienzo.width = ancho;
  lienzo.height = alto;
  dibujar(lienzo.getContext('2d'), info, ancho, alto, foto);
  return new Promise((resolver) => lienzo.toBlob(resolver, 'image/jpeg', 0.92));
}

function descargar(blob, nombre) {
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = nombre;
  enlace.click();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

/**
 * Hoja de compartir: vista previa inmediata e imagen preparada de antemano, para que «Compartir»
 * llame a la hoja del sistema sin esperas (los navegadores móviles exigen que se invoque pegada
 * al toque). Devuelve una promesa que se cumple al cerrar la hoja.
 */
function abrirHoja(info, boton) {
  return new Promise((resolverCierre) => {
    const fondo = document.createElement('div');
    fondo.className = 'fondo-hoja';
    const hoja = document.createElement('div');
    hoja.className = 'sheet';
    hoja.setAttribute('role', 'dialog');
    hoja.setAttribute('aria-modal', 'true');
    hoja.setAttribute('aria-label', `Compartir ${info.nombre}`);
    const pestanas = FORMATOS.map(
      (f, i) => `<button type="button" role="tab" data-formato="${f.id}" aria-selected="${i === 0}">${f.nombre}</button>`,
    ).join('');
    hoja.innerHTML = `
      <div class="sheet__cabecera"><h2>Compartir</h2>
        <button type="button" class="st-btn" data-cerrar aria-label="Cerrar">✕</button></div>
      <div class="sheet__tabs" role="tablist">${pestanas}</div>
      <div class="sheet__vista"><canvas data-vista width="300" height="375" role="img" aria-label="Vista previa de la tarjeta"></canvas></div>
      <div class="sheet__acciones">
        <button type="button" class="pill pill--claro" data-accion="compartir" disabled>Compartir</button>
        <button type="button" class="pill" data-accion="descargar" disabled>Descargar</button>
        <button type="button" class="pill" data-accion="copiar">Copiar enlace</button>
      </div>
      <p class="nota" data-aviso role="status">Preparando la tarjeta…</p>`;

    let formato = FORMATOS[0];
    const listos = new Map(); // formato -> Blob ya generado
    let turno = 0;
    const vista = hoja.querySelector('[data-vista]');
    const aviso = hoja.querySelector('[data-aviso]');
    const botonesImagen = hoja.querySelectorAll('[data-accion="compartir"], [data-accion="descargar"]');
    const avisar = (texto, ms = 0) => {
      aviso.textContent = texto;
      if (ms) setTimeout(() => aviso.textContent === texto && (aviso.textContent = ''), ms);
    };

    const preparar = async () => {
      const yo = ++turno;
      const f = formato;
      botonesImagen.forEach((b) => (b.disabled = !listos.has(f.id)));
      await vistaPrevia(vista, info, f.ancho, f.alto);
      if (yo !== turno) return;
      if (!listos.has(f.id)) {
        avisar('Preparando la tarjeta…');
        listos.set(f.id, await tarjeta(info, f.ancho, f.alto));
      }
      if (yo !== turno) return;
      botonesImagen.forEach((b) => (b.disabled = false));
      avisar('');
    };

    const teclas = (e) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        cerrar();
      }
    };
    function cerrar() {
      turno += 1;
      fondo.remove();
      hoja.remove();
      document.removeEventListener('keydown', teclas, true);
      boton?.focus?.();
      resolverCierre();
    }

    fondo.addEventListener('click', cerrar);
    hoja.querySelector('[data-cerrar]').addEventListener('click', cerrar);
    document.addEventListener('keydown', teclas, true);
    hoja.querySelectorAll('[data-formato]').forEach((b) =>
      b.addEventListener('click', () => {
        formato = FORMATOS.find((f) => f.id === b.dataset.formato) ?? FORMATOS[0];
        hoja.querySelectorAll('[data-formato]').forEach((o) => o.setAttribute('aria-selected', String(o === b)));
        preparar().catch(() => avisar('No se pudo generar la tarjeta'));
      }),
    );

    hoja.querySelectorAll('[data-accion]').forEach((b) =>
      b.addEventListener('click', async () => {
        try {
          if (b.dataset.accion === 'copiar') {
            await navigator.clipboard.writeText(info.url);
            avisar('Enlace copiado', 2600);
            return;
          }
          const blob = listos.get(formato.id);
          if (!blob) return;
          const archivo = new File([blob], `${info.slug || 'municipio'}-${formato.id}.jpg`, { type: 'image/jpeg' });
          if (b.dataset.accion === 'compartir' && navigator.canShare?.({ files: [archivo] })) {
            try {
              await navigator.share({ files: [archivo], title: info.nombre, url: info.url });
              return;
            } catch (error) {
              if (error?.name === 'AbortError') return; // la persona canceló
            }
          }
          descargar(blob, archivo.name);
          avisar('Tarjeta descargada', 2600);
        } catch {
          avisar('No se pudo completar la acción', 2600);
        }
      }),
    );

    document.body.append(fondo, hoja);
    hoja.querySelector('[data-cerrar]')?.focus();
    preparar().catch(() => avisar('No se pudo generar la tarjeta'));
  });
}

/** Punto de entrada: abre la hoja de compartir; la promesa se cumple al cerrarla. */
export function compartir(info, boton) {
  return abrirHoja(info, boton);
}
