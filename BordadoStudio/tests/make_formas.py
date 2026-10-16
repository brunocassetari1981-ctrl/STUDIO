#!/usr/bin/env python3
"""Gera exemplos/formas.bds + formas.dst — vitrine das formas prontas."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bordadostudio import stitcher
from bordadostudio.formats_io import export_document
from bordadostudio.model import Document
from bordadostudio.threads import ThreadColor

CORES = [
    ThreadColor("Vermelho", 0xD62828),
    ThreadColor("Amarelo", 0xF4D35E),
    ThreadColor("Azul", 0x1F5FC4),
    ThreadColor("Verde", 0x2BA84A),
    ThreadColor("Laranja", 0xF08C28),
    ThreadColor("Roxo", 0x8C3CBE),
]

FORMAS = [
    ("Coração", "heart", stitcher.heart_points(190, 300, 140, 130)),
    ("Estrela", "star", stitcher.star_points(540, 300, 150, 140)),
    ("Losango", "diamond", stitcher.diamond_points(870, 300, 130, 130)),
    ("Cruz", "cross", stitcher.cross_points(190, 720, 130, 130)),
    ("Triângulo", "triangle", stitcher.triangle_points(540, 720, 150, 140)),
    ("Hexágono", "hexagon", stitcher.hexagon_points(870, 720, 140, 140)),
]


def main():
    doc = Document()
    doc.title = "Formas prontas"
    for (nome, chave, pts), cor in zip(FORMAS, CORES):
        obj = doc.new_object_from_points(chave, pts, thread=cor, name=nome)
        print(f"{nome}: {obj.stitch_count()} pontos")
    base = os.path.join(os.path.dirname(__file__), "..", "exemplos")
    os.makedirs(base, exist_ok=True)
    doc.save_file(os.path.join(base, "formas.bds"))
    n = export_document(doc, os.path.join(base, "formas.dst"))
    print(f"formas.bds salvo · formas.dst com {n} comandos")


if __name__ == "__main__":
    main()
