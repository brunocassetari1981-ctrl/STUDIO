#!/usr/bin/env python3
"""Gera exemplos/tipos.bds + tipos.dst — catálogo dos 21 tipos de costura."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bordadostudio import stitcher
from bordadostudio.formats_io import export_document
from bordadostudio.model import Document
from bordadostudio.threads import ThreadColor

VERM = ThreadColor("Vermelho", 0xD62828)
AZUL = ThreadColor("Azul", 0x1F5FC4)

CONTORNOS = [
    ("Linha", "run"), ("Ponto duplo", "run2"), ("Ondulado", "zigzag"),
    ("Bico", "scallop"), ("Mola", "spring"), ("Ponto motivo", "motif_run"),
    ("Haste", "stem"), ("Cadeia", "chain"), ("Ponto atrás", "backstitch"),
    ("Satin", "satin"),
]
ENCHIMENTOS = [
    ("Tatami", "fill"), ("Contorno", "fill_contour"), ("Radial", "fill_radial"),
    ("Rede", "fill_mesh"), ("Espiral", "fill_spiral"), ("Tijolinho", "fill_brick"),
    ("Ponto cruz", "cross"), ("Lantejoula", "sequin"),
    ("Motivo cruz", "motif_cross"), ("Motivo estrela", "motif_star"),
    ("Aplique", "applique"),
]


def main():
    doc = Document()
    doc.title = "Catálogo de pontos"
    doc.hoop = [1250, 2600]   # 125 × 260 mm

    cols = 6
    w, h = 160, 130
    x0, y0 = 50, 40
    todas = ([(n, k, "contorno") for n, k in CONTORNOS]
             + [(n, k, "enchimento") for n, k in ENCHIMENTOS])
    for i, (nome, chave, _grupo) in enumerate(todas):
        col, row = i % cols, i // cols
        cx = x0 + col * (w + 25) + w / 2
        cy = y0 + row * (h + 40) + h / 2
        pts = stitcher.ellipse_points(cx, cy, w / 2, h / 2)
        cor = VERM if _grupo == "contorno" else AZUL
        obj = doc.new_object_from_points(
            "polygon", pts, thread=cor, name=nome,
            params={"stitch_type": chave})
        print(f"{nome:15s} {chave:13s} {obj.stitch_count():4d} pts")

    base = os.path.join(os.path.dirname(__file__), "..", "exemplos")
    os.makedirs(base, exist_ok=True)
    doc.save_file(os.path.join(base, "tipos.bds"))
    n = export_document(doc, os.path.join(base, "tipos.dst"))
    print(f"tipos.bds salvo · tipos.dst com {n} comandos")


if __name__ == "__main__":
    main()
