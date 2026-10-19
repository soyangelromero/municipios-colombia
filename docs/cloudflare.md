# Pedidos con Cloudflare Workers (gratis, sin hosting propio)

GitHub Pages solo sirve archivos, así que «Súmate al pedido» necesita un servicio que guarde los
conteos. Este Worker hace lo mismo que `web/api/apoyos.php` y `web/api/pedidos-ranking.php`
(mismas rutas y respuestas) sobre el plan gratuito de Cloudflare. Si tienes hosting con PHP, usa
mejor ese (ver `docs/despliegue.md`); no hacen falta los dos.

**Qué guarda:** municipio, dato y un hash HMAC de la IP (con una sal secreta). Nunca la IP, ni
texto, ni contacto. Cada persona cuenta una vez por municipio y dato; los apoyos se borran a los
365 días. Cloudflare sí ve la IP de quien consulta el servicio: por eso la página de privacidad lo
declara.

**Costo:** el plan gratuito incluye 100.000 peticiones al día en Workers y D1 (5 GB). Sobra.

## Pasos (una sola vez, unos 10 minutos)

Necesitas Node.js 20 o superior (`node --version`). `wrangler` se ejecuta con `npx`, no se instala
nada en el proyecto.

1. **Cuenta gratuita**: crea una en <https://dash.cloudflare.com/sign-up> (no pide tarjeta).
2. **Inicia sesión desde la terminal** (se abre el navegador para autorizar):

   ```bash
   cd worker
   npx wrangler login
   ```

3. **Crea la base de datos** y copia el `database_id` que imprime en `worker/wrangler.toml`
   (reemplaza `REEMPLAZA-CON-EL-ID-DE-D1`):

   ```bash
   npx wrangler d1 create municipios-pedidos
   ```

4. **Crea la tabla** en la base real:

   ```bash
   npx wrangler d1 execute municipios-pedidos --remote --file=schema.sql
   ```

5. **Guarda la sal secreta** (una cadena larga y aleatoria; wrangler te la pide, no se muestra ni se
   versiona). Genera una con `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"`:

   ```bash
   npx wrangler secret put SAL
   ```

6. **Publica el Worker**. Al terminar imprime su URL, del estilo
   `https://municipios-pedidos.TU-USUARIO.workers.dev`:

   ```bash
   npx wrangler deploy
   ```

7. **Conecta el sitio**: en `web/assets/js/config.js` pon esa URL (sin barra final) en `endpoint`,
   haz commit y push. En 9 minutos «Publicar sitio» lo despliega.

   ```js
   endpoint: 'https://municipios-pedidos.TU-USUARIO.workers.dev',
   ```

8. **Comprueba** (debe responder `{"ok":true,"municipios":[],"reciente":null}`):

   ```bash
   curl https://municipios-pedidos.TU-USUARIO.workers.dev/pedidos-ranking.php
   ```

Si usas dominio propio, cambia `ORIGEN` en `worker/wrangler.toml` y vuelve a hacer `npx wrangler deploy`:
el Worker solo acepta pedidos que vengan de ese origen.

## Ajustes

En `worker/wrangler.toml`, sección `[vars]`: `DIAS_APOYOS` (cuánto se conserva cada apoyo) y
`MAX_APOYOS_HORA` (pedidos por IP y hora). Después de cambiarlos: `npx wrangler deploy`.

## Pruebas

Con Node 22.13 o superior (usa `node:sqlite` para imitar D1):

```bash
cd worker
node --test
```

## Ver o borrar lo guardado

```bash
npx wrangler d1 execute municipios-pedidos --remote --command "SELECT municipio, dato, COUNT(*) FROM apoyos GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 20"
npx wrangler d1 execute municipios-pedidos --remote --command "DELETE FROM apoyos WHERE municipio = '05001'"
```
