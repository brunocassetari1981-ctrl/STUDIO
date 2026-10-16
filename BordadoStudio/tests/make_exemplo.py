import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

"""Gera o projeto de exemplo (exemplos/jardim.bds) e exporta exemplos/*.dst."""

from bordadostudio.formats_io import export_document
from bordadostudio.model import Document
from bordadostudio.stitcher import ellipse_points, rect_points
from bordadostudio.threads import ThreadColor

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exemplos")


def main():
    doc = Document()
    doc.title = "Jardim de Exemplo"

    # vaso (retângulo em linha simples marrom)
    vaso = doc.new_object_from_points(
        "rect", rect_points(350, 620, 300, 220),
        params={"stitch_type": "run"},
        thread=ThreadColor("Madeira Escura", 0x6D4C41, "N10"),
        name="Vaso",
    )

    # terra (preenchimento marrom)
    doc.new_object_from_points(
        "polygon", [(370, 620), (630, 620), (610, 560), (390, 560)],
        thread=ThreadColor("Terra", 0x795548, "N8"),
        name="Terra",
    )

    # caule (satin verde)
    doc.new_object_from_points(
        "satin", [(500, 560), (500, 350), (510, 250)],
        params={"width": 36},
        thread=ThreadColor("Folha", 0x558B2F, "N2"),
        name="Caule",
    )

    # pétalas (elipses em preenchimento)
    cores = [
        ThreadColor("Flor Rosa", 0xEC407A, "N13"),
        ThreadColor("Flor Amarela", 0xFFCA28, "N12"),
        ThreadColor("Flor Lilás", 0xAB47BC, "N15"),
        ThreadColor("Flor Laranja", 0xFF7043, "N16"),
    ]
    import math
    for i, cor in enumerate(cores):
        ang = math.pi / 2 + i * math.pi / 2
        cx = 505 + 95 * math.cos(ang)
        cy = 210 + 95 * math.sin(ang)
        doc.new_object_from_points(
            "ellipse", ellipse_points(cx, cy, 85, 55),
            thread=cor,
            name=f"Pétala {i + 1}",
        )

    # centro da flor
    doc.new_object_from_points(
        "ellipse", ellipse_points(505, 210, 55, 55),
        thread=ThreadColor("Amarelo", 0xF2C230, "9"),
        name="Miolo",
    )

    # folhas (elipses verdes inclinadas em preenchimento)
    doc.new_object_from_points(
        "ellipse", ellipse_points(400, 430, 80, 34),
        params={"angle": 25},
        thread=ThreadColor("Folha Clara", 0x9CCC65, "N1"),
        name="Folha esquerda",
    )
    doc.new_object_from_points(
        "ellipse", ellipse_points(615, 470, 80, 34),
        params={"angle": -25},
        thread=ThreadColor("Folha Clara", 0x9CCC65, "N1"),
        name="Folha direita",
    )

    os.makedirs(OUT, exist_ok=True)
    bds = os.path.join(OUT, "jardim.bds")
    doc.save_file(bds)
    dst = os.path.join(OUT, "jardim.dst")
    n = export_document(doc, dst)
    print(f"Exemplo gerado: {bds}")
    print(f"Exportado:      {dst} ({n} pontos)")


if __name__ == "__main__":
    main()
