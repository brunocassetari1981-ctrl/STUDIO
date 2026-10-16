"""Gera exemplos/efeitos.bds — todos os tipos de costura em um só desenho."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from bordadostudio.formats_io import export_document
from bordadostudio.model import Document
from bordadostudio.stitcher import rect_points
from bordadostudio.threads import ThreadColor

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exemplos")

CORES = [
    ThreadColor("Vermelho", 0xD62828, "5"),
    ThreadColor("Azul", 0x1F5FC4, "14"),
    ThreadColor("Verde", 0x2E9E3F, "11"),
    ThreadColor("Amarelo", 0xF2C230, "9"),
    ThreadColor("Roxo", 0x7B3FA0, "16"),
    ThreadColor("Laranja", 0xF26A1B, "8"),
    ThreadColor("Rosa", 0xF2789F, "7"),
    ThreadColor("Ouro", 0xD4AF37, "M1"),
    ThreadColor("Prata", 0xC0C0C0, "M2"),
    ThreadColor("Marrom", 0x8B5A2B, "17"),
]

EFEITOS = [
    ("Preenchimento", "fill", {}),
    ("Linha simples", "run", {}),
    ("Satin", "satin", {"width": 40}),
    ("Ponto cruz", "cross", {"spacing": 30}),
    ("Cadeia (à mão)", "chain", {"spacing": 34, "width": 40}),
    ("Ponto atrás", "backstitch", {"spacing": 24}),
    ("Ponto haste", "stem", {"spacing": 18, "width": 40}),
    ("Lantejoula", "sequin", {"spacing": 48, "width": 32}),
    ("Motivo cruz", "motif_cross", {"spacing": 48, "width": 36}),
    ("Motivo estrela", "motif_star", {"spacing": 55, "width": 40}),
]


def main():
    doc = Document()
    doc.title = "Efeitos de Costura"
    doc.hoop = [2000.0, 1200.0]

    for i, (nome, tipo, params) in enumerate(EFEITOS):
        col, row = i % 5, i // 5
        x = 60 + col * 390
        y = 60 + row * 520
        pts = rect_points(x, y, 320, 420) if tipo != "satin" else \
            [(x + 160, y + 30), (x + 160, y + 390)]
        p = {"stitch_type": tipo}
        p.update(params)
        doc.new_object_from_points(
            "satin" if tipo == "satin" else "rect", pts,
            params=p, thread=CORES[i], name=nome)

    os.makedirs(OUT, exist_ok=True)
    bds = os.path.join(OUT, "efeitos.bds")
    doc.save_file(bds)
    dst = os.path.join(OUT, "efeitos.dst")
    n = export_document(doc, dst)
    print(f"Efeitos gerados: {bds}")
    print(f"Exportado:       {dst} ({n} pontos)")


if __name__ == "__main__":
    main()
