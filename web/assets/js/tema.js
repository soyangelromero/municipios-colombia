// Cambio entre modo oscuro (por defecto) y claro, con la preferencia guardada.
const boton = document.querySelector('[data-tema-boton]');
const raiz = document.documentElement;

if (boton) {
  boton.hidden = false;
  boton.addEventListener('click', () => {
    const claro = raiz.dataset.tema === 'claro';
    const nuevo = claro ? 'oscuro' : 'claro';
    raiz.dataset.tema = nuevo;
    try {
      localStorage.setItem('tema', nuevo);
    } catch {
      /* sin almacenamiento: el cambio vale solo para esta página */
    }
    boton.setAttribute(
      'aria-label',
      nuevo === 'claro' ? 'Cambiar a modo oscuro' : 'Cambiar a modo claro',
    );
  });
}
