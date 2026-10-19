// Enlaza tarjetas y filas de ranking con la historia sin cargarla de antemano:
// historia.js (y su CSS) se descargan al tocar, al apuntar o cuando el navegador está ocioso.
let modulo = null;
const cargar = () => (modulo ??= import('./historia.js'));

const cargaPronto = () => {
  const lanzar = () => cargar().then((m) => m.cargarEstilos());
  (window.requestIdleCallback ?? ((f) => setTimeout(f, 2500)))(lanzar, { timeout: 4000 });
};

export function enlazarHistorias(selector = 'a.card, [data-historia]') {
  document.addEventListener('click', (e) => {
    if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    const a = e.target.closest(selector);
    if (!a) return;
    const href = a.getAttribute('href') ?? '';
    const clave = a.dataset.historia ?? href.replace(/\/$/, '').split('/').pop();
    if (!clave) return;
    e.preventDefault();
    cargar().then((m) => m.abrirHistoria(clave, 0, a));
  });
  document.addEventListener('pointerover', (e) => e.target.closest?.(selector) && cargar(), { once: true });
  if (location.hash.length > 1) cargar().then((m) => m.abrirDesdeHash());
  else cargaPronto();
}
