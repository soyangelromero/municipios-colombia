// Pruebas del Worker con una base SQLite en memoria que imita la API de D1 (node:test, sin dependencias).
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
import { test } from 'node:test';
import { manejar } from '../src/index.js';

const ORIGEN = 'https://sitio.test';

function nuevoEntorno(extra = {}) {
  const bd = new DatabaseSync(':memory:');
  bd.exec(readFileSync(new URL('../schema.sql', import.meta.url), 'utf8'));
  const DB = {
    prepare(sql) {
      const sentencia = bd.prepare(sql);
      let args = [];
      const api = {
        bind(...a) {
          args = a;
          return api;
        },
        async run() {
          return { meta: { changes: Number(sentencia.run(...args).changes) } };
        },
        async first() {
          return sentencia.get(...args) ?? null;
        },
        async all() {
          return { results: sentencia.all(...args) };
        },
      };
      return api;
    },
  };
  return { bd, env: { DB, ORIGEN, SAL: 'sal-de-prueba', DIAS_APOYOS: '365', MAX_APOYOS_HORA: '30', ...extra } };
}

const AHORA = Date.parse('2026-10-19T18:00:00Z');
const pedido = (cuerpo, { ip = '1.1.1.1', origen = ORIGEN, metodo = 'POST' } = {}) =>
  new Request('https://api.test/apoyos.php', {
    method: metodo,
    headers: { 'Content-Type': 'application/json', Origin: origen, 'CF-Connecting-IP': ip },
    body: metodo === 'POST' ? JSON.stringify(cuerpo) : undefined,
  });
const valido = (extra = {}) => ({ t: AHORA - 5000, municipio: '05001', dato: 'ejecucion', ...extra });
const json = async (respuesta) => [respuesta.status, await respuesta.json()];

test('cuenta una sola vez por persona y no guarda la IP', async () => {
  const { bd, env } = nuevoEntorno();
  assert.deepEqual(await json(await manejar(pedido(valido()), env, AHORA)), [200, { ok: true, yaPedido: false, total: 1 }]);
  assert.deepEqual(await json(await manejar(pedido(valido()), env, AHORA)), [200, { ok: true, yaPedido: true, total: 1 }]);
  const { ip_hash: hash } = bd.prepare('SELECT ip_hash FROM apoyos').get();
  assert.equal(hash.length, 64);
  assert.ok(!hash.includes('1.1.1.1'));
});

test('valida municipio, dato, robots y origen', async () => {
  const { env } = nuevoEntorno();
  assert.equal((await manejar(pedido(valido({ municipio: 'abc' })), env, AHORA)).status, 422);
  assert.equal((await manejar(pedido(valido({ dato: 'Dato Raro!' })), env, AHORA)).status, 422);
  assert.equal((await manejar(pedido(valido({ web: 'robot' })), env, AHORA)).status, 400);
  assert.equal((await manejar(pedido({ municipio: '05001', dato: 'x' }), env, AHORA)).status, 400);
  assert.equal((await manejar(pedido(valido({ t: AHORA - 500 })), env, AHORA)).status, 400);
  assert.equal((await manejar(pedido(valido(), { origen: 'https://otro.test' }), env, AHORA)).status, 403);
  assert.equal((await manejar(pedido(null, { metodo: 'GET' }), env, AHORA)).status, 405);
});

test('ranking ordena, detalla por municipio y marca los pedidos propios', async () => {
  const { bd, env } = nuevoEntorno();
  await manejar(pedido(valido({ dato: 'sueldos' })), env, AHORA);
  await manejar(pedido(valido({ dato: 'compras' })), env, AHORA);
  await manejar(pedido(valido({ municipio: '15759', dato: 'sueldos' })), env, AHORA);
  bd.prepare("INSERT INTO apoyos VALUES ('05001', 'sueldos', 'otra-persona', ?)").run(new Date(AHORA - 1000).toISOString());

  const lista = await (await manejar(new Request('https://api.test/pedidos-ranking.php'), env, AHORA)).json();
  assert.deepEqual(lista.municipios.map((m) => m.codigo), ['05001', '15759']);
  assert.equal(lista.municipios[0].total, 3);
  assert.equal(lista.municipios[0].porDato.sueldos, 2);
  assert.equal(lista.municipios[0].hoy, 3);
  assert.equal(lista.reciente.municipio.length, 5);

  const detalle = await (
    await manejar(new Request('https://api.test/pedidos-ranking.php?municipio=05001', { headers: { 'CF-Connecting-IP': '1.1.1.1' } }), env, AHORA)
  ).json();
  assert.deepEqual(detalle.porDato, { sueldos: 2, compras: 1 });
  assert.deepEqual(detalle.mios.sort(), ['compras', 'sueldos']);
});

test('borra lo viejo y limita por IP y hora', async () => {
  const { bd, env } = nuevoEntorno({ MAX_APOYOS_HORA: '3' });
  bd.prepare("INSERT INTO apoyos VALUES ('05001', 'viejo', 'x', ?)").run(new Date(AHORA - 400 * 86400 * 1000).toISOString());
  await manejar(pedido(valido({ dato: 'a' })), env, AHORA);
  assert.equal(bd.prepare("SELECT COUNT(*) AS n FROM apoyos WHERE dato = 'viejo'").get().n, 0);
  const estados = [];
  for (const dato of ['b', 'c', 'd', 'e']) estados.push((await manejar(pedido(valido({ dato })), env, AHORA)).status);
  assert.deepEqual(estados, [200, 200, 429, 429]);
});

test('responde el preflight de CORS solo para el origen del sitio', async () => {
  const { env } = nuevoEntorno();
  const respuesta = await manejar(new Request('https://api.test/apoyos.php', { method: 'OPTIONS' }), env, AHORA);
  assert.equal(respuesta.status, 204);
  assert.equal(respuesta.headers.get('Access-Control-Allow-Origin'), ORIGEN);
});
