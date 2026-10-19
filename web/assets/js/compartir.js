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
      document.fonts.load('300 96px Geist'),
      document.fonts.load('800 300px Geist'),
      document.fonts.load('600 32px "Geist Mono"'),
    ]);
  } catch {
    /* si las fuentes no cargan, se dibuja con la del sistema */
  }
}

/** Dibuja la tarjeta (ancho × alto) en un contexto ya listo: sin esperas y sin red. */
function dibujar(ctx, info, ancho, alto, foto) {
  const color = COLORES[info.semaforo] ?? COLORES.sin;
  ctx.fillStyle = '#0a0d12';
  ctx.fillRect(0, 0, ancho, alto);

  if (foto) {
    const altoFoto = Math.round(alto * 0.46);
    const escala = Math.max(ancho / foto.width, altoFoto / foto.height);
    const w = foto.width * escala;
    const h = foto.height * escala;
    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, ancho, altoFoto); // la foto no se sale de su franja
    ctx.clip();
    ctx.drawImage(foto, (ancho - w) / 2, (altoFoto - h) / 2, w, h);
    ctx.restore();
    const degradado = ctx.createLinearGradient(0, 0, 0, altoFoto);
    degradado.addColorStop(0, 'rgba(10,13,18,0.15)');
    degradado.addColorStop(1, 'rgba(10,13,18,1)');
    ctx.fillStyle = degradado;
    ctx.fillRect(0, 0, ancho, altoFoto);
  }

  ctx.fillStyle = color;
  ctx.fillRect(0, 0, ancho, 18);

  const margen = 84;
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = '#97a3b8';
  ctx.font = '600 32px "Geist Mono", monospace';
  ctx.fillText('MUNICIPIOS · COLOMBIA', margen, 158);

  const base = foto ? Math.round(alto * 0.4) : Math.round(alto * 0.3);
  ctx.fillStyle = '#f4f5f7';
  ctx.font = '300 96px "Geist", system-ui, sans-serif';
  const n = lineas(ctx, envolver(info.nombre, 28).split(' '), margen, base, ancho - margen * 2, 104);

  ctx.fillStyle = color;
  ctx.font = '800 300px "Geist", system-ui, sans-serif';
  ctx.fillText(formatoNumero(info.valor), margen, base + n * 104 + 240);

  ctx.fillStyle = '#97a3b8';
  ctx.font = '600 44px "Geist Mono", monospace';
  const etiqueta = info.etiqueta ? `${info.etiqueta.toUpperCase()} · ` : '';
  const estado = (TEXTO[info.semaforo] ?? TEXTO.sin).toUpperCase();
  ctx.fillText(`${etiqueta}/ 100 · ${estado}`, margen, base + n * 104 + 320);

  if (info.puesto) {
    ctx.fillStyle = '#f4f5f7';
    ctx.font = '400 48px "Geist", system-ui, sans-serif';
    ctx.fillText(`Puesto ${info.puesto} del país`, margen, base + n * 104 + 420);
  }

  ctx.fillStyle = '#97a3b8';
  ctx.font = '400 32px "Geist", system-ui, sans-serif';
  ctx.fillText('Cada cifra con su fuente oficial', margen, alto - 170);
  ctx.fillStyle = '#f4f5f7';
  ctx.font = '600 34px "Geist Mono", monospace';
  ctx.fillText(info.url.replace(/^https?:\/\//, ''), margen, alto - 104);
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
