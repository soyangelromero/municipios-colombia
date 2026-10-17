// Formularios opcionales. Con endpoint en config.js envían a PHP; sin él, caen a GitHub o correo.
import { CONFIG } from './config.js';

const endpoint = CONFIG.endpoint ? CONFIG.endpoint.replace(/\/$/, '') : null;

async function enviar(datos, tipo) {
  const respuesta = await fetch(`${endpoint}/${tipo}.php`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(datos),
  });
  const cuerpo = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) throw new Error(cuerpo.error || 'No se pudo enviar. Inténtalo más tarde.');
  return cuerpo;
}

/** Sin servidor: abre un issue de GitHub (reporte) o el correo del proyecto. */
function alterno(form, datos, tipo) {
  if (tipo === 'reporte' && form.dataset.repo) {
    const url =
      `${form.dataset.repo}/issues/new?` +
      new URLSearchParams({
        template: 'error-en-dato.yml',
        title: `[Dato] ${datos.municipio || 'Municipio'}: `,
        municipio: datos.municipio || '',
        body: `${datos.mensaje || ''}\n\nContacto: ${datos.contacto || '—'}`,
      });
    window.open(url, '_blank', 'noopener');
    return 'Se abrió GitHub para enviar el reporte.';
  }
  const asunto = datos.asunto || (tipo === 'pedido' ? 'Petición de un dato' : 'Contacto');
  const url =
    `mailto:${form.dataset.correo}?` +
    new URLSearchParams({ subject: `[${datos.municipio || 'Municipios'}] ${asunto}`, body: datos.mensaje || '' });
  window.location.href = url;
  return 'Se abrió tu correo para enviar el mensaje.';
}

for (const form of document.querySelectorAll('[data-formulario]')) {
  const tiempo = form.querySelector('[data-tiempo]');
  if (tiempo) tiempo.value = String(Date.now());

  form.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const aviso = form.querySelector('[data-aviso]');
    const boton = form.querySelector('button[type="submit"]');
    const tipo = form.dataset.formulario;
    const datos = Object.fromEntries(new FormData(form));
    if (datos.web) return; // campo trampa: es un robot

    boton.disabled = true;
    try {
      if (endpoint) {
        const respuesta = await enviar(datos, tipo);
        aviso.textContent = respuesta.mensaje || 'Enviado. Gracias.';
      } else {
        aviso.textContent = alterno(form, datos, tipo);
      }
      form.querySelectorAll('textarea, input[type="email"], input[type="text"]').forEach((campo) => {
        if (campo.name !== 'web') campo.value = '';
      });
    } catch (error) {
      aviso.textContent = error.message;
    } finally {
      boton.disabled = false;
    }
  });
}
