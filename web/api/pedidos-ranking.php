<?php

declare(strict_types=1);

// Lectura pública: los municipios con más pedidos de datos (o el detalle de uno solo con ?municipio=).

require __DIR__ . '/lib/comun.php';

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'GET') {
    municipios_json(405, ['error' => 'Método no permitido.']);
    exit;
}

$config = municipios_config();
$pdo = municipios_db($config);
$ipHash = municipios_ip_hash($config);
header('Cache-Control: private, max-age=20');

$municipio = (string) ($_GET['municipio'] ?? '');
if ($municipio !== '') {
    if (preg_match('/^\d{5}$/', $municipio) !== 1) {
        municipios_json(422, ['error' => 'Municipio no válido.']);
        exit;
    }
    $filas = $pdo->prepare('SELECT dato, COUNT(*) AS n FROM apoyos WHERE municipio = ? GROUP BY dato');
    $filas->execute([$municipio]);
    $porDato = [];
    foreach ($filas->fetchAll() as $fila) {
        $porDato[$fila['dato']] = (int) $fila['n'];
    }
    $mios = $pdo->prepare('SELECT dato FROM apoyos WHERE municipio = ? AND ip_hash = ?');
    $mios->execute([$municipio, $ipHash]);
    municipios_json(200, [
        'ok' => true,
        'porDato' => (object) $porDato,
        'mios' => $mios->fetchAll(PDO::FETCH_COLUMN),
    ]);
    exit;
}

$hoy = gmdate('c', time() - 86400);
$consulta = $pdo->prepare(
    'SELECT municipio, dato, COUNT(*) AS n, SUM(creado >= ?) AS hoy FROM apoyos GROUP BY municipio, dato'
);
$consulta->execute([$hoy]);

$porMunicipio = [];
foreach ($consulta->fetchAll() as $fila) {
    $m = $fila['municipio'];
    $porMunicipio[$m] ??= ['codigo' => $m, 'total' => 0, 'hoy' => 0, 'porDato' => []];
    $porMunicipio[$m]['total'] += (int) $fila['n'];
    $porMunicipio[$m]['hoy'] += (int) $fila['hoy'];
    $porMunicipio[$m]['porDato'][$fila['dato']] = (int) $fila['n'];
}
$lista = array_values($porMunicipio);
usort($lista, static fn (array $a, array $b): int => $b['total'] <=> $a['total']);
$lista = array_slice($lista, 0, 200);
foreach ($lista as &$item) {
    arsort($item['porDato']);
    $item['porDato'] = (object) array_slice($item['porDato'], 0, 3, true);
}
unset($item);

$reciente = $pdo->query('SELECT municipio, dato, creado FROM apoyos ORDER BY creado DESC LIMIT 1')->fetch();

municipios_json(200, ['ok' => true, 'municipios' => $lista, 'reciente' => $reciente ?: null]);
