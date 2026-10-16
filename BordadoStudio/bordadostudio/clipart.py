"""Biblioteca de clipart do BordadoStudio — silhuetas geradas por fórmulas.

Cada desenho devolve uma lista de contornos (cada contorno vira um objeto).
Coordenadas em unidades (10 = 1 mm), centralizadas na origem, lado ≈ `size`.
"""

from __future__ import annotations

import math


def _circle(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _polar(fn, n=96):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        r = fn(t)
        pts.append((r * math.cos(t), r * math.sin(t)))
    return pts


def flor(s):
    # 6 pétalas suaves
    return [_polar(lambda t: s * (0.42 + 0.58 * abs(math.cos(3 * t)) ** 0.65))]


def sol(s):
    return [_polar(lambda t: s * (0.78 + 0.12 * math.cos(12 * t)))]


def lua(s):
    # crescente: arco externo + arco interno deslocado
    pts = []
    n = 48
    for i in range(n + 1):
        t = math.pi / 2 + math.pi * i / n
        pts.append((s * math.cos(t), s * math.sin(t)))
    for i in range(n + 1):
        t = -math.pi / 2 + math.pi * i / n
        pts.append((s * 0.28 + s * 0.82 * math.cos(t), s * 0.82 * math.sin(t)))
    return [pts]


def borboleta(s):
    # asas superiores + inferiores espelhadas, corpo fino no meio
    pts = []
    n = 24
    for i in range(n + 1):
        t = math.pi * i / n
        x = s * 0.12 + s * 0.95 * math.sin(t) ** 1.4
        y = -s * 0.08 - s * 0.92 * math.cos(t) * math.sin(t / 2 + 0.4)
        pts.append((x, y))
    for i in range(n + 1):
        t = math.pi * i / n
        x = s * 0.22 + s * 0.62 * math.sin(t) ** 1.3
        y = s * 0.12 + s * 0.72 * math.cos(t) * math.sin(t / 2 + 0.2)
        pts.append((x, y))
    espelho = [(-x, y) for x, y in reversed(pts)]
    return [pts + espelho]


def peixe(s):
    # corpo + cauda em V
    pts = []
    n = 32
    for i in range(n + 1):
        t = -math.pi / 2 + math.pi * i / n
        pts.append((s * 0.62 * math.cos(t) * 1.15, s * 0.72 * math.sin(t)))
    pts += [(-s * 0.62, 0), (-s * 1.0, -s * 0.55), (-s * 0.78, 0),
            (-s * 1.0, s * 0.55)]
    for i in range(n + 1):
        t = math.pi / 2 + math.pi * i / n
        pts.append((s * 0.62 * math.cos(t) * 1.15, s * 0.72 * math.sin(t)))
    return [pts]


def raio(s):
    return [[(s * 0.18, -s), (s * 0.62, -s * 0.18), (s * 0.22, -s * 0.18),
             (s * 0.58, s), (s * 0.1, s * 0.12), (s * 0.45, s * 0.12)]]


def nuvem(s):
    return [_polar(lambda t: s * (0.7 + 0.14 * math.cos(5 * t)
                                  + 0.08 * math.cos(3 * t + 1.2)))]


def casa(s):
    return [[(-s * 0.7, s), (-s * 0.7, -s * 0.05), (0, -s * 0.75),
             (s * 0.7, -s * 0.05), (s * 0.7, s)]]


def carro(s):
    return [[(-s, s * 0.35), (-s * 0.92, -s * 0.1), (-s * 0.55, -s * 0.18),
             (-s * 0.38, -s * 0.62), (s * 0.22, -s * 0.62),
             (s * 0.48, -s * 0.18), (s * 0.92, -s * 0.05),
             (s, s * 0.35), (s * 0.82, s * 0.35), (s * 0.72, s * 0.05),
             (-s * 0.62, s * 0.05), (-s * 0.72, s * 0.35)]]


def aviao(s):
    return [[(0, -s), (s * 0.14, -s * 0.55), (s * 0.95, s * 0.12),
             (s * 0.95, s * 0.34), (s * 0.12, s * 0.12), (s * 0.12, s * 0.55),
             (s * 0.42, s * 0.85), (s * 0.42, s), (0, s * 0.82),
             (-s * 0.42, s), (-s * 0.42, s * 0.85), (-s * 0.12, s * 0.55),
             (-s * 0.12, s * 0.12), (-s * 0.95, s * 0.34),
             (-s * 0.95, s * 0.12), (-s * 0.14, -s * 0.55)]]


def arcoiris(s):
    ext, inte = s, s * 0.55
    pts = []
    n = 32
    for i in range(n + 1):
        t = math.pi * i / n
        pts.append((ext * math.cos(t), -ext * math.sin(t)))
    for i in range(n + 1):
        t = math.pi - math.pi * i / n
        pts.append((inte * math.cos(t), -inte * math.sin(t)))
    return [pts]


def folha(s):
    pts = []
    n = 24
    for i in range(n + 1):
        t = math.pi * i / n
        pts.append((s * 0.55 * math.sin(t), -s * math.cos(t) * 0.95))
    for i in range(n + 1):
        t = math.pi - math.pi * i / n
        pts.append((-s * 0.55 * math.sin(t), -s * math.cos(t) * 0.95))
    return [pts]


def arvore(s):
    copa = _polar(lambda t: s * (0.62 + 0.2 * math.cos(3 * t + 0.6)))
    copa = [(x, y - s * 0.18) for x, y in copa]
    tronco = [(-s * 0.13, s * 0.42), (s * 0.13, s * 0.42),
              (s * 0.13, s), (-s * 0.13, s)]
    return [copa, tronco]


def pata(s):
    partes = [_circle(0, s * 0.28, s * 0.52, 32)]
    for ang in (-1.9, -0.85, 0.85, 1.9):
        cx = s * 0.95 * math.sin(ang)
        cy = -s * 0.42 + s * 0.1 * abs(math.cos(ang))
        partes.append(_circle(cx, cy, s * 0.27, 20))
    return partes


CLIPART: list[tuple[str, object]] = [
    ("Flor", flor),
    ("Sol", sol),
    ("Lua crescente", lua),
    ("Borboleta", borboleta),
    ("Peixe", peixe),
    ("Raio", raio),
    ("Nuvem", nuvem),
    ("Casa", casa),
    ("Carro", carro),
    ("Avião", aviao),
    ("Arco-íris", arcoiris),
    ("Folha", folha),
    ("Árvore", arvore),
    ("Pata", pata),
]


def names() -> list[str]:
    return [n for n, _ in CLIPART]


def build(name: str, size_mm: float = 50.0,
          cx: float = 0.0, cy: float = 0.0) -> list[list[tuple[float, float]]]:
    """Constrói o desenho em unidades, centralizado em (cx, cy)."""
    for n, fn in CLIPART:
        if n == name:
            s = float(size_mm) * 10.0 / 2.0   # metade do lado em unidades
            return [[(x + cx, y + cy) for x, y in contorno]
                    for contorno in fn(s)]
    return []
