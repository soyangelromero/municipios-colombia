"""Geometría plana mínima para preparar mapas (coordenadas en metros, Web Mercator).

Sin dependencias: solo lo necesario para simplificar contornos y descartar islotes invisibles.
"""

Punto = tuple[float, float]
Anillo = list[Punto]
Poligono = list[Anillo]  # el primer anillo es el exterior; los siguientes, huecos


def caja(poligonos: list[Poligono]) -> tuple[float, float, float, float]:
    """(xmin, ymin, xmax, ymax) de un conjunto de polígonos."""
    xs = [x for p in poligonos for anillo in p for x, _ in anillo]
    ys = [y for p in poligonos for anillo in p for _, y in anillo]
    return min(xs), min(ys), max(xs), max(ys)


def area(anillo: Anillo) -> float:
    """Área absoluta (fórmula del zapato)."""
    suma = 0.0
    for (x1, y1), (x2, y2) in zip(anillo, anillo[1:] + anillo[:1], strict=True):
        suma += x1 * y2 - x2 * y1
    return abs(suma) / 2


def _distancia_a_segmento(p: Punto, a: Punto, b: Punto) -> float:
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    largo2 = dx * dx + dy * dy
    if largo2 == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / largo2))
    cx, cy = ax + t * dx, ay + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def douglas_peucker(puntos: list[Punto], tolerancia: float) -> list[Punto]:
    """Simplifica una línea conservando los puntos que se alejan más de `tolerancia`.

    Versión iterativa (con pila) para no agotar la recursión en contornos de miles de puntos.
    """
    if len(puntos) < 3:
        return list(puntos)
    conservar = [False] * len(puntos)
    conservar[0] = conservar[-1] = True
    pila = [(0, len(puntos) - 1)]
    while pila:
        inicio, fin = pila.pop()
        max_dist, indice = 0.0, -1
        for i in range(inicio + 1, fin):
            d = _distancia_a_segmento(puntos[i], puntos[inicio], puntos[fin])
            if d > max_dist:
                max_dist, indice = d, i
        if max_dist > tolerancia:
            conservar[indice] = True
            pila.extend([(inicio, indice), (indice, fin)])
    return [p for p, sirve in zip(puntos, conservar, strict=True) if sirve]


def simplificar_anillo(anillo: Anillo, tolerancia: float) -> Anillo | None:
    """Simplifica un anillo cerrado. Devuelve None si queda degenerado (menos de 3 vértices)."""
    abierto = anillo[:-1] if len(anillo) > 1 and anillo[0] == anillo[-1] else anillo
    if len(abierto) < 3:
        return None
    # Se parte el anillo en dos mitades para que el primer punto no quede fijo como «esquina».
    mitad = len(abierto) // 2
    resultado = (
        douglas_peucker(abierto[: mitad + 1], tolerancia)[:-1]
        + douglas_peucker(abierto[mitad:] + abierto[:1], tolerancia)[:-1]
    )
    return resultado if len(resultado) >= 3 else None


def simplificar(poligonos: list[Poligono], tolerancia: float, area_minima: float) -> list[Poligono]:
    """Simplifica todos los anillos y descarta islotes y huecos más chicos que `area_minima`.

    Nunca deja una entidad vacía: si todo es más chico que el mínimo, conserva su polígono
    más grande (así un municipio diminuto sigue apareciendo en el mapa).
    """
    resultado: list[Poligono] = []
    for poligono in poligonos:
        exterior = simplificar_anillo(poligono[0], tolerancia)
        if exterior is None or area(exterior) < area_minima:
            continue
        huecos = [
            h
            for h in (simplificar_anillo(a, tolerancia) for a in poligono[1:])
            if h is not None and area(h) >= area_minima
        ]
        resultado.append([exterior, *huecos])
    if resultado or not poligonos:
        return resultado
    mayor = max(poligonos, key=lambda p: area(p[0]))
    exterior = simplificar_anillo(mayor[0], tolerancia) or mayor[0]
    return [[exterior]]
