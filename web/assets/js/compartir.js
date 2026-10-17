// Tarjeta para compartir: dibuja en <canvas> el municipio con su índice y semáforo.
import { formatoNumero } from './comun.js';

const COLORES = { verde: '#4ade80', amarillo: '#fbbf24', rojo: '#f87171', sin: '#97a3b8' };
const TEXTO = { verde: 'Verde', amarillo: 'Amarillo', rojo: 'Rojo', sin: 'Sin índice' };

function frase(ctx, palabras, x, y, maxAncho, alto) {
  let linea = '';
  const lineas = [];
  for (const palabra of palabras) {
    const prueba = linea ? `${linea} ${palabra}` : palabra;
    if (ctx.measureText(prueba).width > maxAncho && linea) {
      lineas.push(linea);
      linea = palabra;
    } else {
      linea = prueba;
    }
  }
  if (linea) lineas.push(linea);
  lineas.forEach((l, i) => ctx.fillText(l, x, y + i * alto));
  return lineas.length;
}

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

/** Dibuja la tarjeta (1080×1350) y devuelve un Blob PNG. */
export async function tarjeta(info, alto = 1350) {
  const ancho = 1080;
  const lienzo = document.createElement('canvas');
  lienzo.width = ancho;
  lienzo.height = alto;
  const ctx = lienzo.getContext('2d');
  const color = COLORES[info.semaforo] ?? COLORES.sin;

  try {
    await document.fonts.ready;
    await document.fonts.load('900 120px Geist');
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
  ctx.fillRect(0, 0, ancho, 16);

  const margen = 80;
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = '#97a3b8';
  ctx.font = '600 30px "Geist Mono", monospace';
  ctx.fillText('MUNICIPIOS · COLOMBIA', margen, 150);

  const baseFoto = foto ? Math.round(alto * 0.4) : 230;
  ctx.fillStyle = '#f3f6fb';
  ctx.font = '300 92px "Geist", system-ui, sans-serif';
  const lineasNombre = frase(
    ctx,
    envolver(info.nombre, 30).split(' '),
    margen,
    baseFoto,
    ancho - margen * 2,
    100,
  );

  ctx.fillStyle = color;
  ctx.font = '900 260px "Geist", system-ui, sans-serif';
  ctx.fillText(formatoNumero(info.valor), margen, baseFoto + lineasNombre * 100 + 210);

  ctx.fillStyle = '#97a3b8';
  ctx.font = '600 40px "Geist Mono", monospace';
  ctx.fillText(`/ 100 · ${(TEXTO[info.semaforo] ?? TEXTO.sin).toUpperCase()}`, margen, baseFoto + lineasNombre * 100 + 285);

  if (info.puesto) {
    ctx.fillStyle = '#f3f6fb';
    ctx.font = '400 44px "Geist", system-ui, sans-serif';
    ctx.fillText(`Puesto ${info.puesto} del país`, margen, baseFoto + lineasNombre * 100 + 375);
  }

  ctx.fillStyle = '#97a3b8';
  ctx.font = '400 30px "Geist", system-ui, sans-serif';
  ctx.fillText('Cada cifra con su fuente oficial', margen, alto - 150);
  ctx.fillStyle = '#f3f6fb';
  ctx.font = '600 32px "Geist Mono", monospace';
  ctx.fillText(info.url.replace(/^https?:\/\//, ''), margen, alto - 90);

  return new Promise((resolver) => lienzo.toBlob(resolver, 'image/png'));
}

/** Comparte la tarjeta nativa si se puede; si no, la descarga y copia el enlace. */
export async function compartir(info, boton) {
  const texto = boton.textContent;
  try {
    const blob = await tarjeta(info);
    const archivo = new File([blob], `${info.slug || 'municipio'}-municipios-colombia.png`, {
      type: 'image/png',
    });
    if (navigator.canShare?.({ files: [archivo] })) {
      try {
        await navigator.share({ files: [archivo], title: info.nombre, url: info.url });
        return;
      } catch {
        /* la persona canceló */
      }
    }
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = archivo.name;
    enlace.click();
    URL.revokeObjectURL(url);
    boton.textContent = 'Tarjeta descargada';
  } catch {
    try {
      await navigator.clipboard.writeText(info.url);
      boton.textContent = 'Enlace copiado';
    } catch {
      window.prompt('Copia este enlace:', info.url);
    }
  } finally {
    setTimeout(() => (boton.textContent = texto), 2600);
  }
}
