var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// src/index.js
var RE_MUNICIPIO = /^\d{5}$/;
var RE_DATO = /^[a-z0-9_]{1,60}$/;
function cabeceras(env, extra = {}) {
  return {
    "Content-Type": "application/json; charset=utf-8",
    "X-Content-Type-Options": "nosniff",
    "Access-Control-Allow-Origin": env.ORIGEN,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    Vary: "Origin",
    ...extra
  };
}
__name(cabeceras, "cabeceras");
function responder(env, codigo, cuerpo, extra) {
  return new Response(JSON.stringify(cuerpo), { status: codigo, headers: cabeceras(env, extra) });
}
__name(responder, "responder");
async function hashIp(ip, sal) {
  const clave = await crypto.subtle.importKey("raw", new TextEncoder().encode(sal), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const firma = await crypto.subtle.sign("HMAC", clave, new TextEncoder().encode(ip));
  return [...new Uint8Array(firma)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
__name(hashIp, "hashIp");
function esHumano(datos, ahora = Date.now()) {
  if ((datos.web ?? "") !== "") return false;
  const t = Number(datos.t) || 0;
  const transcurrido = ahora - t;
  return t > 0 && transcurrido > 3e3 && transcurrido < 6 * 3600 * 1e3;
}
__name(esHumano, "esHumano");
var hace = /* @__PURE__ */ __name((segundos, ahora) => new Date(ahora - segundos * 1e3).toISOString(), "hace");
async function sumar(request, env, ahora) {
  if (request.headers.get("Origin") !== env.ORIGEN) return responder(env, 403, { error: "Origen no permitido." });
  const texto = await request.text();
  if (texto.length > 2e4) return responder(env, 413, { error: "El contenido es demasiado grande." });
  let datos;
  try {
    datos = JSON.parse(texto);
  } catch {
    datos = null;
  }
  if (datos === null || typeof datos !== "object" || Array.isArray(datos)) return responder(env, 400, { error: "Formato de datos inv\xE1lido." });
  if (!esHumano(datos, ahora)) {
    return responder(env, 400, { error: "No pudimos verificar el env\xEDo. Recarga la p\xE1gina e int\xE9ntalo otra vez." });
  }
  const municipio = String(datos.municipio ?? "").trim();
  const dato = String(datos.dato ?? "").trim();
  if (!RE_MUNICIPIO.test(municipio) || !RE_DATO.test(dato)) return responder(env, 422, { error: "Municipio o dato no v\xE1lido." });
  const ip = await hashIp(request.headers.get("CF-Connecting-IP") ?? "", env.SAL);
  const dias = Number(env.DIAS_APOYOS) || 365;
  const maximo = Number(env.MAX_APOYOS_HORA) || 30;
  await env.DB.prepare("DELETE FROM apoyos WHERE creado < ?").bind(hace(dias * 86400, ahora)).run();
  const recientes = await env.DB.prepare("SELECT COUNT(*) AS n FROM apoyos WHERE ip_hash = ? AND creado >= ?").bind(ip, hace(3600, ahora)).first();
  if (recientes.n >= maximo) return responder(env, 429, { error: "Hiciste muchos pedidos seguidos. Int\xE9ntalo en un rato." });
  const insercion = await env.DB.prepare("INSERT OR IGNORE INTO apoyos (municipio, dato, ip_hash, creado) VALUES (?, ?, ?, ?)").bind(municipio, dato, ip, new Date(ahora).toISOString()).run();
  const total = await env.DB.prepare("SELECT COUNT(*) AS n FROM apoyos WHERE municipio = ? AND dato = ?").bind(municipio, dato).first();
  return responder(env, 200, { ok: true, yaPedido: insercion.meta.changes === 0, total: total.n });
}
__name(sumar, "sumar");
async function detalleMunicipio(url, request, env) {
  const municipio = url.searchParams.get("municipio");
  if (!RE_MUNICIPIO.test(municipio)) return responder(env, 422, { error: "Municipio no v\xE1lido." });
  const ip = await hashIp(request.headers.get("CF-Connecting-IP") ?? "", env.SAL);
  const filas = await env.DB.prepare("SELECT dato, COUNT(*) AS n FROM apoyos WHERE municipio = ? GROUP BY dato").bind(municipio).all();
  const mios = await env.DB.prepare("SELECT dato FROM apoyos WHERE municipio = ? AND ip_hash = ?").bind(municipio, ip).all();
  return responder(env, 200, {
    ok: true,
    porDato: Object.fromEntries(filas.results.map((f) => [f.dato, f.n])),
    mios: mios.results.map((f) => f.dato)
  });
}
__name(detalleMunicipio, "detalleMunicipio");
async function ranking(env, ahora) {
  const filas = await env.DB.prepare("SELECT municipio, dato, COUNT(*) AS n, SUM(creado >= ?) AS hoy FROM apoyos GROUP BY municipio, dato").bind(hace(86400, ahora)).all();
  const porMunicipio = /* @__PURE__ */ new Map();
  for (const f of filas.results) {
    const m = porMunicipio.get(f.municipio) ?? { codigo: f.municipio, total: 0, hoy: 0, porDato: {} };
    m.total += f.n;
    m.hoy += f.hoy;
    m.porDato[f.dato] = f.n;
    porMunicipio.set(f.municipio, m);
  }
  const lista = [...porMunicipio.values()].sort((a, b) => b.total - a.total).slice(0, 200).map((m) => ({ ...m, porDato: Object.fromEntries(Object.entries(m.porDato).sort((a, b) => b[1] - a[1]).slice(0, 3)) }));
  const reciente = await env.DB.prepare("SELECT municipio, dato, creado FROM apoyos ORDER BY creado DESC LIMIT 1").first();
  return responder(env, 200, { ok: true, municipios: lista, reciente: reciente ?? null });
}
__name(ranking, "ranking");
async function manejar(request, env, ahora = Date.now()) {
  const url = new URL(request.url);
  const ruta = url.pathname.replace(/\/+$/, "");
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cabeceras(env, { "Access-Control-Max-Age": "86400" }) });
  if (ruta.endsWith("/apoyos.php")) {
    return request.method === "POST" ? sumar(request, env, ahora) : responder(env, 405, { error: "M\xE9todo no permitido." });
  }
  if (ruta.endsWith("/pedidos-ranking.php")) {
    if (request.method !== "GET") return responder(env, 405, { error: "M\xE9todo no permitido." });
    return url.searchParams.has("municipio") ? detalleMunicipio(url, request, env) : ranking(env, ahora);
  }
  return responder(env, 404, { error: "No encontrado." });
}
__name(manejar, "manejar");
var index_default = { fetch: /* @__PURE__ */ __name((request, env) => manejar(request, env), "fetch") };
export {
  index_default as default,
  esHumano,
  hashIp,
  manejar
};
//# sourceMappingURL=index.js.map
