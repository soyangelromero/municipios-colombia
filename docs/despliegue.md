# Despliegue

El sitio es estático y funciona igual en cualquier hosting. Solo si quieres los formularios
activos necesitas PHP. Elige una de las dos vías.

## Vía 1: GitHub Pages (sin servidor, sin formularios)

Es la que está activa hoy en <https://soyangelromero.github.io/municipios-colombia/>.

- El workflow `.github/workflows/pages.yml` corre en cada push a `main`, el día 1 de cada mes
  y a mano.
- Corre el pipeline completo (`python -m municipios --tolerante todo`), genera `dist/` y lo publica.
- Las fotos van versionadas en `datos/fotos/`, así que el build no depende de la red para la web.
- Las descargas pesadas (MGN y Excel del DANE) quedan en la caché de Actions; para renovarlas,
  sube la versión de la clave `crudos-pesados-vN` en el workflow.
- En esta vía los formularios **no envían a un servidor**: caen al issue de GitHub prellenado
  o al correo del proyecto. No hace falta configurar nada.

## Vía 2: hosting propio con PHP (formularios activos)

Requisitos: PHP 8.1 o superior con `pdo_sqlite`, y un servidor web (Apache, Nginx, LiteSpeed…).

### Estructura en el servidor

La carpeta **pública** es `dist/` (lo generado). La configuración y la base SQLite viven en
`privado/`, **fuera** de la carpeta pública, un nivel más arriba:

```
/home/tucuenta/
├── privado/
│   ├── config.php      ← lo creas tú, nunca se versiona
│   └── datos.sqlite    ← se crea solo
└── public_html/        ← aquí va el contenido de dist/
    ├── api/reportes.php
    ├── api/contacto.php
    ├── api/pedidos.php
    └── …
```

`web/api/lib/comun.php` busca `privado/config.php` subiendo tres niveles desde `api/lib/`
(`dirname(__DIR__, 3)`). Si tu estructura es distinta, define la variable de entorno
`MUNICIPIOS_CONFIG` con la ruta absoluta al archivo.

```bash
# Ejemplo de despliegue manual
python -m municipios --tolerante todo     # genera dist/
rsync -av --delete dist/ usuario@servidor:/home/tucuenta/public_html/
```

### Configurar

Copia `privado/config.example.php` a `privado/config.php` y ajústalo:

| Clave | Qué es |
|---|---|
| `ruta_base` | Ruta a la base SQLite (fuera de la carpeta pública). |
| `sal` | Clave larga y aleatoria. Con ella se cifra (HMAC) la IP antes de guardarla. Cámbiala con `php -r "echo bin2hex(random_bytes(32));"`. |
| `correo` | Correo de contacto del proyecto. |
| `origen` | Dominio público del sitio (p. ej. `https://municipios.example`). Bloquea envíos desde otros dominios. |
| `dias_retencion` | Días que se conservan los envíos antes de borrarse (por defecto 30). |
| `max_por_hora` | Envíos permitidos por IP en una hora. |

El archivo `privado/config.php` **no** se versiona (`.gitignore` solo deja pasar el ejemplo).

### Qué guarda y qué no

- Guarda: tipo, municipio, asunto, mensaje, contacto (si lo dan) y `hash_hmac('sha256', ip, sal)`.
- **Nunca** guarda la IP ni datos personales sin pedirlo.
- Los envíos se borran solos al pasar `dias_retencion`.
- Protección contra abuso: campo trampa (honeypot), tiempo mínimo de llenado, límite por IP,
  comprobación de origen y validación de longitud. Todas las respuestas son JSON.

### Despliegue automático por SFTP (opcional)

`.github/workflows/deploy.yml` (manual, `workflow_dispatch`) construye el sitio y lo sube por
SFTP. Antes de usarlo, crea estos *secrets* en GitHub:

| Secret | Ejemplo |
|---|---|
| `SFTP_SERVIDOR` | `sftp.mihost.com` |
| `SFTP_USUARIO` | `usuario` |
| `SFTP_PUERTO` | `22` |
| `SFTP_CLAVE` | (la contraseña, o `SFTP_LLAVE` con la clave privada) |
| `SFTP_RUTA` | `/home/tucuenta/public_html/` |

Sube solo el contenido de `dist/` y **borra lo que ya no existe** (`mirror --delete`): `SFTP_RUTA` debe ser la carpeta pública y nada más (nunca la raíz de la cuenta, donde vive `privado/`). El primer despliegue debe crear a mano `privado/config.php`
en el servidor: el workflow nunca lo toca.

## Comprobaciones tras desplegar

- Abre una ficha y reporta un error de prueba; debe aparecer «Gracias. Recibimos tu mensaje.».
- Con `MUNICIPIOS_CONFIG` apuntando a una base local puedes probar todo sin publicar:
  `php -S 127.0.0.1:8765 -t dist` y luego `POST` a `/api/reportes.php` con cabecera `Origin`
  igual a tu `origen`.

## Actualización mensual

Los datos oficiales cambian: el pipeline se corre cada mes y se vuelve a publicar.

- **GitHub Pages**: ya es automática (`pages.yml`, el día 1 de cada mes a las 9:00 UTC); también se lanza a mano desde la pestaña *Actions*.
- **Hosting propio**:
  1. En tu PC: `python -m municipios --tolerante todo` (o lanza el workflow *Desplegar por SFTP* a mano).
  2. Revisa que no haya enlaces rotos: `python -m municipios enlaces`.
  3. Sube `dist/` con `rsync` o SFTP. `privado/` no se toca.
  4. Con `cron` en el servidor puedes repetir 1 y 3 si el hosting permite Python; si no, usa el workflow.
- Para actualizar la revisión automática de transparencia de las capitales (no está en `todo`): `python -m municipios relevamiento` (necesita `scrapling install`) y haz commit de `datos/relevamiento/`.
- Para actualizar las fotos de los municipios: `python -m municipios fotos` y haz commit de `datos/fotos/`.

## Revisión antes de publicar

`python -m municipios enlaces` recorre `dist/` y falla si algún enlace o ancla interna apunta a algo que no existe.

## Buscadores (SEO)

Lo que ya hace el sitio: una página estática por municipio con las cifras en el HTML, título y descripción únicos, `canonical`, Open Graph y Twitter con imagen, datos estructurados (JSON-LD: sitio, conjunto de datos, migas y área administrativa), `sitemap.xml` con todas las páginas, `robots.txt` y `noindex` solo en la 404.

Lo que depende de ti:

1. **Dominio propio.** `soyangelromero.github.io/municipios-colombia/` comparte dominio con otros proyectos y le cuesta más posicionar. Con un dominio propio, cambia `url_base` en `pipeline/config/sitio.toml` y sube de nuevo.
2. **Google Search Console** y **Bing Webmaster Tools**: verifica el sitio y envía `…/sitemap.xml`.
3. **Enlaces desde fuera**: notas de prensa, universidades, organizaciones de veeduría y la propia fuente (datos.gov.co) que enlacen a las fichas.
4. Tras cada actualización mensual, el `lastmod` del sitemap se renueva solo.
