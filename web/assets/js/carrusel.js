// Portada: filtros del carrusel de municipios y un leve efecto 3D al pasar el cursor.
const track = document.querySelector('[data-carrusel]');
const filtroDep = document.querySelector('[data-filtro-dep]');
const filtroGrupo = document.querySelector('[data-filtro-grupo]');

/** Muestra solo las tarjetas del departamento y el grupo elegidos. */
function filtrar() {
  if (!track) return;
  const dep = filtroDep?.value ?? '';
  const grupo = filtroGrupo?.value ?? '';
  track.querySelectorAll('.card').forEach((tarjeta) => {
    const coincide =
      (!dep || tarjeta.dataset.dep === dep) && (!grupo || tarjeta.dataset.grupo === grupo);
    tarjeta.hidden = !coincide;
  });
  track.scrollLeft = 0;
}

filtroDep?.addEventListener('change', filtrar);
filtroGrupo?.addEventListener('change', filtrar);

// Inclinación 3D sutil bajo el cursor (solo con ratón y sin reducir movimiento).
const conRaton = matchMedia('(hover: hover) and (pointer: fine)').matches;
const sinMovimiento = matchMedia('(prefers-reduced-motion: reduce)').matches;
if (track && conRaton && !sinMovimiento) {
  track.querySelectorAll('.card').forEach((tarjeta) => {
    let marco = 0;
    tarjeta.addEventListener('pointermove', (evento) => {
      if (marco) return;
      marco = requestAnimationFrame(() => {
        marco = 0;
        const caja = tarjeta.getBoundingClientRect();
        const x = (evento.clientX - caja.left) / caja.width - 0.5;
        const y = (evento.clientY - caja.top) / caja.height - 0.5;
        tarjeta.style.transform = `rotateY(${(x * 10).toFixed(2)}deg) rotateX(${(-y * 8).toFixed(2)}deg)`;
      });
    });
    tarjeta.addEventListener('pointerleave', () => {
      tarjeta.style.transform = '';
    });
  });
}
