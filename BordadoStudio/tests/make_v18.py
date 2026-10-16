# -*- coding: utf-8 -*-
"""Gera exemplos v1.8 (mistura multi-fio e clipart) + capturas de tela."""
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication

from bordadostudio import clipart
from bordadostudio.formats_io import export_document
from bordadostudio import stitcher
from bordadostudio.model import Document, ThreadColor

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXEMPLOS = os.path.join(RAIZ, "exemplos")
DOCS = os.path.join(RAIZ, "docs")


def _doc_mistura():
    doc = Document()
    doc.hoop_name = "Médida A"
    vermelho = ThreadColor("Vermelho", 0xD62828)
    azul = ThreadColor("Azul", 0x2856D6)
    doc.new_object_from_points(
        "ellipse", stitcher.ellipse_points(2500, 1100, 300, 200),
        thread=vermelho, name="Mistura 1",
        params={"stitch_type": "fill_blend", "blend_color": azul.hex_color,
                "gradient": 0.7, "stitch_length": 45.0, "spacing": 20.0})
    doc.new_object_from_points(
        "ellipse", stitcher.ellipse_points(1000, 1100, 300, 200),
        thread=azul, name="Mistura 2",
        params={"stitch_type": "fill_blend", "blend_color": vermelho.hex_color,
                "gradient": 0.5, "stitch_length": 45.0, "spacing": 20.0})
    return doc


def _doc_clipart():
    doc = Document()
    doc.hoop_name = "Médida A"
    cores = [ThreadColor("Vermelho", 0xD62828), ThreadColor("Verde", 0x2E8B57),
             ThreadColor("Azul", 0x2856D6)]
    for i, cont in enumerate(clipart.build("Árvore", 80.0, 700, 1200)):
        doc.new_object_from_points("polygon", cont, thread=cores[1], name="Árvore")
    for cont in clipart.build("Flor", 70.0, 2200, 1200):
        doc.new_object_from_points("polygon", cont, thread=cores[0], name="Flor")
    return doc


def main():
    os.makedirs(EXEMPLOS, exist_ok=True)
    os.makedirs(DOCS, exist_ok=True)
    p1 = os.path.join(EXEMPLOS, "mistura.bds")
    d1 = _doc_mistura()
    d1.save_file(p1)
    export_document(d1, os.path.join(EXEMPLOS, "mistura.dst"))
    n1 = sum(o.stitch_count() for o in d1.objects)
    p2 = os.path.join(EXEMPLOS, "clipart.bds")
    d2 = _doc_clipart()
    d2.save_file(p2)
    export_document(d2, os.path.join(EXEMPLOS, "clipart.dst"))
    n2 = sum(o.stitch_count() for o in d2.objects)
    print("exemplos:", os.path.basename(p1), n1, "pontos /", os.path.basename(p2), n2, "pontos")

    app = QApplication.instance() or QApplication([])
    from bordadostudio.main_window import MainWindow
    win = MainWindow()
    win.resize(1360, 860)
    win.load_document(d1, p1)
    win.canvas.select("")
    win.canvas.fit_view()
    win.grab().save(os.path.join(DOCS, "preview_mistura.png"))
    win.load_document(d2, p2)
    win.canvas.select("")
    win.canvas.fit_view()
    win.grab().save(os.path.join(DOCS, "preview_clipart.png"))
    app.processEvents()
    print("screenshots em docs/preview_mistura.png e docs/preview_clipart.png")


if __name__ == "__main__":
    main()
