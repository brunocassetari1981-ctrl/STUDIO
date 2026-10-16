"""Biblioteca de bastidores (áreas de bordado) do BordadoStudio.

Cada bastidor tem nome, forma ('rect' ou 'circle') e tamanho em
unidades (10 unidades = 1 mm).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Hoop:
    name: str
    width: int          # unidades
    height: int         # unidades
    shape: str = "rect"  # 'rect' | 'circle'

    @property
    def label(self) -> str:
        w = self.width / 10.0
        h = self.height / 10.0
        if self.shape == "circle":
            return f"{self.name} (Ø {w:.0f} mm)"
        return f"{self.name} ({w:.0f} × {h:.0f} mm)"


HOOPS: list[Hoop] = [
    Hoop("Redonda pequena", 1000, 1000, "circle"),
    Hoop("Redonda média", 1300, 1300, "circle"),
    Hoop("Redonda grande", 1600, 1600, "circle"),
    Hoop("Quadrada", 1000, 1000),
    Hoop("Quadrada média", 1200, 1200),
    Hoop("Quadrada grande", 1600, 1600),
    Hoop("Retangular 16×10", 1600, 1000),
    Hoop("Retangular 20×14", 2000, 1400),
    Hoop("Retangular 30×20", 3000, 2000),
    Hoop("Faixa 36×10", 3600, 1000),
]


def find_hoop(name: str) -> Hoop | None:
    for h in HOOPS:
        if h.name == name:
            return h
    return None


def match_hoop(width: int, height: int) -> Hoop | None:
    """Acha o bastidor da biblioteca com o mesmo tamanho (em unidades)."""
    for h in HOOPS:
        if h.width == width and h.height == height:
            return h
    return None
