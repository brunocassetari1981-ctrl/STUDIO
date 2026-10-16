"""Smoke test da interface — roda sem tela (QT_QPA_PLATFORM=offscreen)."""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtCore import QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from bordadostudio.main_window import MainWindow


def view_pos(view, scene_x, scene_y):
    return view.mapFromScene(QPointF(scene_x, scene_y))


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.resize(1280, 820)
    win.show()
    app.processEvents()

    view = win.canvas.view
    scene = win.canvas

    # --- ferramenta retângulo: press/move/release
    scene.set_tool("rect")
    p1 = view_pos(view, 100, 100)
    p2 = view_pos(view, 500, 400)
    QTest.mousePress(view.viewport(), Qt.LeftButton, pos=p1)
    QTest.mouseMove(view.viewport(), p2, delay=10)
    QTest.mouseRelease(view.viewport(), Qt.LeftButton, pos=p2)
    app.processEvents()
    assert len(win.doc.objects) == 1, "retângulo não criado"
    print("OK  retângulo criado:", win.doc.objects[0].name,
          win.doc.objects[0].stitch_count(), "pontos")

    # --- ferramenta preenchimento (polígono) com duplo-clique
    scene.set_tool("polygon")
    for sx, sy in [(600, 100), (900, 150), (850, 450), (650, 400)]:
        QTest.mouseClick(view.viewport(), Qt.LeftButton, pos=view_pos(view, sx, sy))
    QTest.mouseDClick(view.viewport(), Qt.LeftButton, pos=view_pos(view, 650, 400))
    app.processEvents()
    assert len(win.doc.objects) == 2, "polígono não criado"
    print("OK  polígono criado:", win.doc.objects[1].stitch_count(), "pontos")

    # --- ferramenta satin
    scene.set_tool("satin")
    for sx, sy in [(150, 600), (450, 650), (750, 600)]:
        QTest.mouseClick(view.viewport(), Qt.LeftButton, pos=view_pos(view, sx, sy))
    QTest.mouseDClick(view.viewport(), Qt.LeftButton, pos=view_pos(view, 750, 600))
    app.processEvents()
    assert len(win.doc.objects) == 3, "satin não criado"
    print("OK  satin criado:", win.doc.objects[2].stitch_count(), "pontos")

    # --- seleção + propriedades
    scene.set_tool("select")
    scene.select(win.doc.objects[0].id)
    win.props.load_object(scene.selected_object())
    win.props.stitch_combo.setCurrentIndex(1)  # linha simples
    app.processEvents()
    print("OK  seleção e propriedades")

    # --- desfazer / refazer
    n = len(win.doc.objects)
    win.doc.remove_object(win.doc.objects[0])
    win.canvas.rebuild()
    assert len(win.doc.objects) == n - 1
    win.edit_undo()
    assert len(win.doc.objects) == n, "desfazer falhou"
    print("OK  desfazer/refazer")

    # --- salvar projeto
    outdir = os.environ.get("BS_SMOKE_OUT", "/tmp")
    bds = os.path.join(outdir, "smoke.bds")
    win.doc.save_file(bds)
    assert os.path.getsize(bds) > 100
    print("OK  projeto salvo:", bds)

    # --- exportar DST
    from bordadostudio.formats_io import export_document, import_file
    dst = os.path.join(outdir, "smoke.dst")
    n = export_document(win.doc, dst)
    assert n > 10
    objs = import_file(dst)
    assert objs
    print(f"OK  exportado DST com {n} comandos; reimport: {len(objs)} objeto(s)")

    # --- simulador
    from bordadostudio.simulator import SimulatorDialog
    dlg = SimulatorDialog(win.doc)
    dlg._tick()
    dlg.close()
    print("OK  simulador")

    # --- captura de tela
    png = os.path.join(outdir, "smoke_tela.png")
    win.grab().save(png)
    print("OK  screenshot:", png)

    win.doc.modified = False  # evita diálogo modal em offscreen
    win.close()
    print("\nSMOKE TEST PASSOU ✔")


if __name__ == "__main__":
    main()
