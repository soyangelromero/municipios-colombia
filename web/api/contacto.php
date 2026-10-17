<?php

declare(strict_types=1);

// Contacto general: preguntas, propuestas o avisos.

require __DIR__ . '/lib/comun.php';

$config = municipios_config();
$datos = municipios_entrada($config);

if (!municipios_es_humano($datos)) {
    municipios_json(400, ['error' => 'No pudimos verificar el envío. Recarga la página e inténtalo otra vez.']);
    exit;
}

$mensaje = municipios_texto($datos, 'mensaje', 2000);
if (mb_strlen($mensaje) < 5) {
    municipios_json(422, ['error' => 'Escribe un mensaje un poco más largo (mínimo 5 caracteres).']);
    exit;
}

$pdo = municipios_db($config);
municipios_limpiar($pdo, (int) $config['dias_retencion']);
municipios_limitar($pdo, municipios_ip_hash($config), (int) $config['max_por_hora']);

municipios_guardar($pdo, $config, 'contacto', [
    'municipio' => '',
    'asunto' => municipios_texto($datos, 'asunto', 160),
    'mensaje' => $mensaje,
    'contacto' => municipios_texto($datos, 'contacto', 120),
], municipios_ip_hash($config));
