<?php

declare(strict_types=1);

// Copia este archivo a privado/config.php y completa los valores.
// privado/ queda FUERA de la carpeta pública web/ y nunca se versiona con valores.
// En el hosting, coloca privado/ junto a la carpeta pública, no dentro.

return [
    // Ruta del archivo SQLite (fuera de la carpeta pública). Por defecto, junto a config.php.
    'ruta_base' => __DIR__ . '/datos.sqlite',

    // Cadena larga y aleatoria para hashear la IP. Nunca se guarda la IP, solo este hash.
    'sal' => 'cambia-esto-por-una-cadena-larga-y-aleatoria',

    // Correo de contacto del proyecto (para avisos y el pie del sitio).
    'correo' => 'contacto@example.com',

    // Origen permitido de los envíos (sin barra final). Evita que otros sitios usen el formulario.
    'origen' => 'https://tu-dominio.example',

    // Cuántos días se conservan los envíos y cuántos se aceptan por IP y hora.
    'dias_retencion' => 30,
    'max_por_hora' => 10,

    // «Súmate al pedido»: días que se conserva cada apoyo (hash de IP + municipio + dato)
    // y cuántos se aceptan por IP y hora.
    'dias_apoyos' => 365,
    'max_apoyos_hora' => 30,
];
