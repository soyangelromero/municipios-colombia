// Configuración compartida de la interfaz.
// endpoint: ruta de la API en PHP que recibe formularios. null = sitio solo estático, sin formularios.
export const CONFIG = Object.freeze({
  endpoint: null,
  // pedidos: servicio que cuenta «Súmate al pedido» (Worker de Cloudflare, ver docs/cloudflare.md).
  // Si es null se usa `endpoint` (la API PHP, que también lo atiende).
  pedidos: 'https://municipios-pedidos.municipios-colombia.workers.dev',
  version: '0.1.0',
});
