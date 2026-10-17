<?php

declare(strict_types=1);

// Reportar un error en un dato de una ficha de municipio.

require __DIR__ . '/lib/comun.php';

$config = municipios_config();
$datos = municipios_entrada($config);

if (!municipios_es_humano($datos)) {
    municipios_json(400, ['error' => 'No pudimos verificar el envío. Recarga la página e inténtalo otra vez.']);
    exit;
}

$mensaje = municipios_texto($datos, 'mensaje', 2000);
if (mb_strlen($mensaje) < 5) {
    municipios_json(422, ['error' => 'Cuéntanos un poco más sobre el error (mínimo 5 caracteres).']);
    exit;
}

$pdo = municipios_db($config);
municipios_limpiar($pdo, (int) $config['dias_retencion']);
municipios_limitar($pdo, municipios_ip_hash($config), (int) $config['max_por_hora']);

municipios_guardar($pdo, $config, 'reporte', [
    'municipio' => municipios_texto($datos, 'municipio', 120),
    'asunto' => municipios_texto($datos, 'asunto', 160),
    'mensaje' => $mensaje,
    'contacto' => municipios_texto($datos, 'contacto', 120),
], municipios_ip_hash($config));
