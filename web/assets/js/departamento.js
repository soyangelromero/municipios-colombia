// Página de departamento: interacción del mapa de municipios.
import { formatoNumero, municipios, raiz } from './comun.js';
import { activarMapa } from './mapa.js';

async function iniciar() {
  const figura = document.querySelector('[data-mapa-departamento] .mapa');
  if (!figura) return;
  const porCodigo = Object.fromEntries((await municipios()).map((m) => [m.codigo, m]));
  activarMapa(figura, {
    texto: (cod) => {
      const m = porCodigo[cod];
      if (!m) return cod;
      return m.indice === null ? `${m.nombre}: sin índice` : `${m.nombre}: ${formatoNumero(m.indice)} · puesto ${m.puesto}`;
    },
    enlace: (cod) => (porCodigo[cod] ? `${raiz}m/${porCodigo[cod].slug}/` : null),
  });
}

iniciar().catch(() => {});
