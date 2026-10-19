<?php

declare(strict_types=1);

/**
 * Utilidades compartidas de los formularios (PHP opcional).
 *
 * Guarda los envíos en SQLite (fuera de la carpeta pública), limita los envíos por IP sin
 * guardar la IP (solo un hash HMAC con sal secreta) y borra lo viejo. Sin dependencias ni Composer.
 */

/** Carga privado/config.php (fuera de web/) desde la variable de entorno o su ruta habitual. */
function municipios_config(): array
{
    $rutas = [];
    $desdeEntorno = getenv('MUNICIPIOS_CONFIG');
    if (is_string($desdeEntorno) && $desdeEntorno !== '') {
        $rutas[] = $desdeEntorno;
    }
    // web/api/lib → subir tres niveles deja la raíz: privado/ junto a web/.
    $rutas[] = dirname(__DIR__, 3) . '/privado/config.php';

    foreach ($rutas as $ruta) {
        if (is_file($ruta)) {
            $config = require $ruta;
            if (is_array($config)) {
                return $config;
            }
        }
    }

    municipios_json(503, ['error' => 'El formulario no está configurado en este servidor.']);
    exit;
}

/** Devuelve una respuesta JSON con el código HTTP indicado y termina. */
function municipios_json(int $codigo, array $datos): void
{
    http_response_code($codigo);
    header('Content-Type: application/json; charset=utf-8');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($datos, JSON_UNESCAPED_UNICODE);
}

/** Conexión SQLite con el esquema creado (tabla «envios»). */
function municipios_db(array $config): PDO
{
    $pdo = new PDO('sqlite:' . $config['ruta_base'], null, null, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
    $pdo->exec('PRAGMA journal_mode = WAL');
    $pdo->exec(
        'CREATE TABLE IF NOT EXISTS envios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            municipio TEXT NOT NULL DEFAULT "",
            asunto TEXT NOT NULL DEFAULT "",
            mensaje TEXT NOT NULL,
            contacto TEXT NOT NULL DEFAULT "",
            ip_hash TEXT NOT NULL,
            creado TEXT NOT NULL
        )'
    );
    // Un apoyo = una persona (hash de IP) que pide un dato de un municipio. No guarda texto ni contacto.
    $pdo->exec(
        'CREATE TABLE IF NOT EXISTS apoyos (
            municipio TEXT NOT NULL,
            dato TEXT NOT NULL,
            ip_hash TEXT NOT NULL,
            creado TEXT NOT NULL,
            PRIMARY KEY (municipio, dato, ip_hash)
        )'
    );
    return $pdo;
}

/** Hash de la IP con la sal secreta: nunca se guarda la IP en claro. */
function municipios_ip_hash(array $config): string
{
    $ip = (string) ($_SERVER['REMOTE_ADDR'] ?? '');
    return hash_hmac('sha256', $ip, (string) $config['sal']);
}

/** Corta si la IP superó el máximo de envíos por hora (responde 429). */
function municipios_limitar(PDO $pdo, string $ipHash, int $maximo): void
{
    $desde = gmdate('c', time() - 3600);
    $sentencia = $pdo->prepare('SELECT COUNT(*) FROM envios WHERE ip_hash = ? AND creado >= ?');
    $sentencia->execute([$ipHash, $desde]);
    if ((int) $sentencia->fetchColumn() >= $maximo) {
        municipios_json(429, ['error' => 'Demasiados envíos seguidos. Inténtalo más tarde.']);
        exit;
    }
}

/** Borra los envíos más viejos que el número de días de retención. */
function municipios_limpiar(PDO $pdo, int $dias): void
{
    $limite = gmdate('c', time() - $dias * 86400);
    $pdo->prepare('DELETE FROM envios WHERE creado < ?')->execute([$limite]);
}

/** Corta si la IP superó el máximo de apoyos por hora (responde 429). */
function municipios_limitar_apoyos(PDO $pdo, string $ipHash, int $maximo): void
{
    $sentencia = $pdo->prepare('SELECT COUNT(*) FROM apoyos WHERE ip_hash = ? AND creado >= ?');
    $sentencia->execute([$ipHash, gmdate('c', time() - 3600)]);
    if ((int) $sentencia->fetchColumn() >= $maximo) {
        municipios_json(429, ['error' => 'Hiciste muchos pedidos seguidos. Inténtalo en un rato.']);
        exit;
    }
}

/** Borra los apoyos más viejos que el número de días indicado. */
function municipios_limpiar_apoyos(PDO $pdo, int $dias): void
{
    $pdo->prepare('DELETE FROM apoyos WHERE creado < ?')->execute([gmdate('c', time() - $dias * 86400)]);
}

/** Exige POST, JSON y un origen permitido; devuelve el cuerpo como arreglo. */
function municipios_entrada(array $config): array
{
    if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
        municipios_json(405, ['error' => 'Método no permitido.']);
        exit;
    }
    if (!municipios_origen_valido($config)) {
        municipios_json(403, ['error' => 'Origen no permitido.']);
        exit;
    }
    $cuerpo = file_get_contents('php://input') ?: '';
    if (strlen($cuerpo) > 20000) {
        municipios_json(413, ['error' => 'El contenido es demasiado grande.']);
        exit;
    }
    $datos = json_decode($cuerpo, true);
    if (!is_array($datos)) {
        municipios_json(400, ['error' => 'Formato de datos inválido.']);
        exit;
    }
    return $datos;
}

/** Comprueba que el envío venga del mismo sitio (cabecera Origin o Referer). */
function municipios_origen_valido(array $config): bool
{
    $esperado = rtrim((string) ($config['origen'] ?? ''), '/');
    if ($esperado === '') {
        return true;
    }
    $hostEsperado = parse_url($esperado, PHP_URL_HOST);
    foreach (['HTTP_ORIGIN', 'HTTP_REFERER'] as $clave) {
        $valor = $_SERVER[$clave] ?? '';
        if ($valor !== '' && parse_url((string) $valor, PHP_URL_HOST) === $hostEsperado) {
            return true;
        }
    }
    return false;
}

/** Descarta envíos de robots: campo trampa vacío y al menos unos segundos desde el render. */
function municipios_es_humano(array $datos): bool
{
    if (($datos['web'] ?? '') !== '') {
        return false;
    }
    $render = (int) ($datos['t'] ?? 0);
    $transcurrido = (int) round(microtime(true) * 1000) - $render;
    return $render > 0 && $transcurrido > 3000 && $transcurrido < 6 * 3600 * 1000;
}

/** Sanea y recorta un campo de texto del envío. */
function municipios_texto(array $datos, string $clave, int $largo): string
{
    $valor = trim((string) ($datos[$clave] ?? ''));
    $valor = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F]/u', '', $valor) ?? '';
    return mb_substr($valor, 0, $largo);
}

/** Guarda un envío validado y responde con éxito. */
function municipios_guardar(PDO $pdo, array $config, string $tipo, array $campos, string $ipHash): void
{
    $sentencia = $pdo->prepare(
        'INSERT INTO envios (tipo, municipio, asunto, mensaje, contacto, ip_hash, creado)
         VALUES (:tipo, :municipio, :asunto, :mensaje, :contacto, :ip_hash, :creado)'
    );
    $sentencia->execute([
        ':tipo' => $tipo,
        ':municipio' => $campos['municipio'],
        ':asunto' => $campos['asunto'],
        ':mensaje' => $campos['mensaje'],
        ':contacto' => $campos['contacto'],
        ':ip_hash' => $ipHash,
        ':creado' => gmdate('c'),
    ]);
    municipios_json(200, ['ok' => true, 'mensaje' => 'Gracias. Recibimos tu mensaje.']);
}
