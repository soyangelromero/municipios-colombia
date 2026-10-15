# Seguridad

## Reportar una vulnerabilidad

**No abras un *issue* público.** Usa la opción de [reporte privado de vulnerabilidades de GitHub](https://docs.github.com/es/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability), en la pestaña *Security* del repositorio, o escribe a **[correo de contacto del proyecto — pendiente]**.

Incluye:
- una descripción del problema,
- cómo reproducirlo,
- su posible impacto.

Respondemos en un máximo de 7 días.

## Alcance

- Los formularios en PHP (`web/api/`): inyección, XSS, abuso de envíos.
- La exposición accidental de secretos o de datos personales.
- El pipeline, cuando procesa contenido descargado de terceros.

## Prácticas del proyecto

- Ningún secreto en el repositorio: se usan `.env`, `privado/config.php` (fuera de `web/`) y los *secrets* de GitHub. El CI corre gitleaks.
- PHP: consultas preparadas, salida escapada y límite de envíos por IP. La IP se guarda solo como hash con clave secreta y se borra a los 30 días.
- El sitio publicado no carga scripts de terceros.
