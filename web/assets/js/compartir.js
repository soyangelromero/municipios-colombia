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

/** Dibuja la tarjeta (1080 × alto) y devuelve un Blob PNG. */
export async function tarjeta(info, ancho = 1080, alto = 1350) {
  const lienzo = document.createElement('canvas');
  lienzo.width = ancho;
  lienzo.height = alto;
  const ctx = lienzo.getContext('2d');
  const color = COLORES[info.semaforo] ?? COLORES.sin;

  try {
    await document.fonts.ready;
    await document.fonts.load('900 160px Geist');
  } catch {
    /* si las fuentes no cargan, se dibuja con la del sistema */
  }

  ctx.fillStyle = '#0a0d12';
  ctx.fillRect(0, 0, ancho, alto);

  const foto = await cargarFoto(info.foto);
  if (foto) {
    const altoFoto = Math.round(alto * 0.46);
    const escala = Math.max(ancho / foto.width, altoFoto / foto.height);
    const w = foto.width * escala;
    const h = foto.height * escala;
    ctx.drawImage(foto, (ancho - w) / 2, (altoFoto - h) / 2, w, h);
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
  ctx.fillText(`/ 100 · ${(TEXTO[info.semaforo] ?? TEXTO.sin).toUpperCase()}`, margen, base + n * 104 + 320);

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

  return new Promise((resolver) => lienzo.toBlob(resolver, 'image/png'));
}

function descargar(blob, nombre) {
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = nombre;
  enlace.click();
  URL.revokeObjectURL(url);
}

/** Hoja de compartir: elige formato, previsualiza y ofrece compartir, descargar o copiar. */
function abrirHoja(info, boton) {
  const fondo = document.createElement('div');
  fondo.className = 'fondo-hoja';
  const hoja = document.createElement('div');
  hoja.className = 'sheet';
  hoja.setAttribute('role', 'dialog');
  hoja.setAttribute('aria-modal', 'true');
  hoja.setAttribute('aria-label', `Compartir ${info.nombre}`);
  hoja.innerHTML = `
    <div class="sheet__cabecera"><h2>Compartir</h2>
      <button type="button" class="st-btn" data-cerrar aria-label="Cerrar">\u2715</button></div>
    <div class="sheet__tabs" role="tablist">
      ${FORMATOS.map((f, i) => `<button type="button" role="tab" data-formato="${f.id}" aria-selected="${i === 0}">${f.nombre}</button>`).join('')}
    </div>
    <div class="sheet__vista"><canvas data-vista width="300" height="375"></canvas></div>
    <div class="sheet__acciones">
      <button type="button" class="pill pill--claro" data-accion="compartir">Compartir</button>
      <button type="button" class="pill" data-accion="descargar">Descargar</button>
      <button type="button" class="pill" data-accion="copiar">Copiar enlace</button>
    </div>
    <p class="nota" data-aviso role="status"></p>`;

  let formato = FORMATOS[0];
  let blob = null;
  const vista = hoja.querySelector('[data-vista]');

  const pintarVista = () => {
    const reduccion = 300 / formato.ancho;
    vista.width = 300;
    vista.height = Math.round(formato.alto * reduccion);
    const ctx = vista.getContext('2d');
    ctx.fillStyle = '#0a0d12';
    ctx.fillRect(0, 0, vista.width, vista.height);
    if (blob) {
      createImageBitmap(blob).then((img) => ctx.drawImage(img, 0, 0, vista.width, vista.height));
    }
  };

  const generar = async () => {
    blob = await tarjeta(info, formato.ancho, formato.alto);
    pintarVista();
  };

  const cerrar = () => {
    fondo.remove();
    hoja.remove();
    document.removeEventListener('keydown', teclas);
    boton?.focus?.();
  };
  const teclas = (e) => {
    if (e.key === 'Escape') cerrar();
  };

  fondo.addEventListener('click', cerrar);
  hoja.querySelector('[data-cerrar]').addEventListener('click', cerrar);
  document.addEventListener('keydown', teclas);
  hoja.querySelectorAll('[data-formato]').forEach((b) =>
    b.addEventListener('click', () => {
      formato = FORMATOS.find((f) => f.id === b.dataset.formato) ?? FORMATOS[0];
      hoja.querySelectorAll('[data-formato]').forEach((o) => o.setAttribute('aria-selected', String(o === b)));
      generar().catch(() => {});
    }),
  );
  const aviso = hoja.querySelector('[data-aviso]');
  hoja.querySelectorAll('[data-accion]').forEach((b) =>
    b.addEventListener('click', async () => {
      const avisar = (texto) => {
        aviso.textContent = texto;
        setTimeout(() => (aviso.textContent = ''), 2600);
      };
      try {
        if (b.dataset.accion === 'copiar') {
          await navigator.clipboard.writeText(info.url);
          avisar('Enlace copiado');
          return;
        }
        if (!blob) await generar();
        const archivo = new File([blob], `${info.slug || 'municipio'}-${formato.id}.png`, { type: 'image/png' });
        if (b.dataset.accion === 'compartir' && navigator.canShare?.({ files: [archivo] })) {
          try {
            await navigator.share({ files: [archivo], title: info.nombre, url: info.url });
            return;
          } catch {
            /* la persona canceló */
          }
        }
        descargar(blob, archivo.name);
        avisar('Tarjeta descargada');
      } catch {
        avisar('No se pudo generar la tarjeta');
      }
    }),
  );

  document.body.append(fondo, hoja);
  hoja.querySelector('[data-accion="compartir"]')?.focus();
  generar().catch(() => {});
}

/** Punto de entrada: abre la hoja de compartir. */
export async function compartir(info, boton) {
  abrirHoja(info, boton);
}
