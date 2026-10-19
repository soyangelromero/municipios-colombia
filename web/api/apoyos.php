<?php

declare(strict_types=1);

// «Súmate al pedido»: una persona cuenta una sola vez por municipio y dato (por hash de IP).

require __DIR__ . '/lib/comun.php';

$config = municipios_config();
$datos = municipios_entrada($config);

if (!municipios_es_humano($datos)) {
    municipios_json(400, ['error' => 'No pudimos verificar el envío. Recarga la página e inténtalo otra vez.']);
    exit;
}

$municipio = municipios_texto($datos, 'municipio', 5);
$dato = municipios_texto($datos, 'dato', 60);
if (preg_match('/^\d{5}$/', $municipio) !== 1 || preg_match('/^[a-z0-9_]{1,60}$/', $dato) !== 1) {
    municipios_json(422, ['error' => 'Municipio o dato no válido.']);
    exit;
}

$pdo = municipios_db($config);
municipios_limpiar_apoyos($pdo, (int) ($config['dias_apoyos'] ?? 365));
$ipHash = municipios_ip_hash($config);
municipios_limitar_apoyos($pdo, $ipHash, (int) ($config['max_apoyos_hora'] ?? 30));

$insertar = $pdo->prepare(
    'INSERT OR IGNORE INTO apoyos (municipio, dato, ip_hash, creado) VALUES (?, ?, ?, ?)'
);
$insertar->execute([$municipio, $dato, $ipHash, gmdate('c')]);
$nuevo = $insertar->rowCount() === 1;

$total = $pdo->prepare('SELECT COUNT(*) FROM apoyos WHERE municipio = ? AND dato = ?');
$total->execute([$municipio, $dato]);

municipios_json(200, [
    'ok' => true,
    'yaPedido' => !$nuevo,
    'total' => (int) $total->fetchColumn(),
]);
