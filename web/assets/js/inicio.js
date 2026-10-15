// Portada: mapa de departamentos con capas (índice y cada pilar).
import { cargarJSON, formatoNumero, raiz } from './comun.js';
import { activarMapa, colorear } from './mapa.js';

const NOMBRES = { indice: 'Índice', T: 'Transparencia', S: 'Servicios', G: 'Gestión', C: 'Control' };

async function iniciar() {
  const bloque = document.querySelector('[data-mapa-pais]');
  const figura = bloque?.querySelector('.mapa');
  if (!figura) return;
  const pais = await cargarJSON('data/pais.json');
  const deps = pais.departamentos;
  let capa = 'indice';

  activarMapa(figura, {
    texto: (cod) => {
      const d = deps[cod];
      if (!d) return cod;
      return `${d.nombre}: ${NOMBRES[capa]} ${formatoNumero(d[capa])} (${d.municipios} municipios)`;
    },
    enlace: (cod) => (deps[cod] ? `${raiz}d/${deps[cod].slug}/` : null),
  });

  const botones = bloque.querySelectorAll('[data-capa]');
  botones.forEach((boton) =>
    boton.addEventListener('click', () => {
      capa = boton.dataset.capa;
      botones.forEach((b) => b.setAttribute('aria-pressed', String(b === boton)));
      colorear(figura, Object.fromEntries(Object.entries(deps).map(([cod, d]) => [cod, d[capa]])));
    }),
  );
}

iniciar().catch(() => {});
