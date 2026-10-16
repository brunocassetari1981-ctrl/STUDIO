"""Testes do núcleo: geração de pontos, modelo e formatos."""

import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bordadostudio import stitcher
from bordadostudio.formats_io import (
    document_to_pattern,
    export_document,
    import_file,
)
from bordadostudio.model import DesignObject, Document
from bordadostudio.threads import ThreadColor


class TestStitcher(unittest.TestCase):
    def test_running_stitch(self):
        cmds = stitcher.running_stitch([(0, 0), (200, 0)], stitch_length=25)
        self.assertGreaterEqual(len(cmds), 2)
        for x, y, c in cmds:
            self.assertEqual(c, stitcher.STITCH)
            self.assertTrue(math.isfinite(x) and math.isfinite(y))
        self.assertAlmostEqual(cmds[0][0], 0, places=3)
        self.assertAlmostEqual(cmds[-1][0], 200, places=3)

    def test_fill_stitch_inside_bounds(self):
        poly = stitcher.rect_points(0, 0, 200, 200)
        cmds = stitcher.fill_stitch(poly, spacing=20, stitch_length=25)
        self.assertGreater(stitcher.stitch_count(cmds), 10)
        for x, y, c in cmds:
            self.assertGreaterEqual(x, -30)   # margem do underlay
            self.assertLessEqual(x, 230)
            self.assertGreaterEqual(y, -30)
            self.assertLessEqual(y, 230)

    def test_fill_empty_polygon(self):
        self.assertEqual(stitcher.fill_stitch([(0, 0)], spacing=20), [])

    def test_satin_stitch_width(self):
        center = [(0, 0), (200, 0)]
        cmds = stitcher.satin_stitch(center, width=40, density=8)
        ys = [y for x, y, c in cmds if c == stitcher.STITCH]
        self.assertGreater(len(ys), 4)
        # largura total ~40 unidades => y entre -20 e +20
        self.assertGreaterEqual(min(ys), -21)
        self.assertLessEqual(max(ys), 21)

    def test_ellipse(self):
        pts = stitcher.ellipse_points(100, 100, 50, 30)
        self.assertEqual(len(pts), 48)
        cmds = stitcher.compile_shape("ellipse", pts, {"stitch_type": "fill"})
        self.assertGreater(len(cmds), 10)

    def test_cross_stitch(self):
        poly = stitcher.rect_points(0, 0, 300, 300)
        cmds = stitcher.cross_stitch(poly, cell=30)
        # 10x10 células -> ~100 X's, 4 pontos cada
        self.assertGreater(stitcher.stitch_count(cmds), 200)
        # todo X dentro da área (com margem da célula)
        for x, y, c in cmds:
            self.assertGreaterEqual(x, -20)
            self.assertLessEqual(x, 320)

    def test_chain_stitch(self):
        cmds = stitcher.chain_stitch([(0, 0), (300, 0)], link=30, width=20)
        self.assertGreater(stitcher.stitch_count(cmds), 20)
        ys = [abs(y) for x, y, c in cmds]
        self.assertGreater(max(ys), 5)       # laços têm largura
        self.assertLessEqual(max(ys), 15)

    def test_backstitch(self):
        cmds = stitcher.backstitch([(0, 0), (240, 0)], step=24)
        self.assertGreater(stitcher.stitch_count(cmds), 4)
        jumps = sum(1 for x, y, c in cmds if c == stitcher.JUMP)
        self.assertGreater(jumps, 0)         # segmentos separados por pulos

    def test_stem_stitch(self):
        cmds = stitcher.stem_stitch([(0, 0), (200, 0)], step=14, width=16)
        self.assertGreater(stitcher.stitch_count(cmds), 8)
        ys = [y for x, y, c in cmds]
        self.assertGreater(max(ys) - min(ys), 10)   # trança tem largura

    def test_sequin_motif(self):
        poly = stitcher.rect_points(0, 0, 250, 250)
        cmds = stitcher.motif_fill(poly, motif="sequin", size=28, spacing=45)
        jumps = sum(1 for x, y, c in cmds if c == stitcher.JUMP)
        self.assertGreaterEqual(jumps, 4)    # várias lantejoulas
        self.assertGreater(stitcher.stitch_count(cmds), 40)

    def test_compile_all_effects(self):
        poly = [(0, 0), (200, 0), (200, 120), (0, 120)]
        for st in ("cross", "chain", "backstitch", "stem", "sequin",
                   "motif_cross", "motif_star", "applique"):
            cmds = stitcher.compile_shape("polygon", poly, {"stitch_type": st})
            self.assertGreater(len(cmds), 0, f"efeito {st} vazio")


class TestLettering(unittest.TestCase):
    def test_all_glyphs_parse(self):
        from bordadostudio import lettering
        for ch in "ABCabc123.,!-()ÁÉÍÓÚÇáéíóúçÃã":
            self.assertTrue(lettering.char_available(ch), f"caractere {ch} faltando")
            w, strokes = lettering._glyph(ch)
            self.assertGreater(w, 0)
            self.assertGreaterEqual(len(strokes), 1)

    def test_text_strokes(self):
        from bordadostudio import lettering
        strokes, w, h = lettering.text_strokes("OLA MUNDO", size=100)
        self.assertGreater(len(strokes), 8)
        self.assertGreater(w, 300)
        self.assertGreater(h, 80)

    def test_text_multiline(self):
        from bordadostudio import lettering
        s1, w1, h1 = lettering.text_strokes("A", size=100)
        s2, w2, h2 = lettering.text_strokes("A\nB", size=100)
        self.assertGreater(h2, h1)

    def test_text_compile_types(self):
        for st in ("run", "satin", "stem", "chain", "backstitch"):
            cmds = stitcher.compile_shape(
                "text", [(50, 50)],
                {"text": "BORDADO", "size": 100, "stitch_type": st})
            self.assertGreater(stitcher.stitch_count(cmds), 10, f"texto {st} vazio")

    def test_text_flip_rotate(self):
        base = stitcher.compile_shape(
            "text", [(0, 0)], {"text": "A", "size": 100, "stitch_type": "run"})
        flip = stitcher.compile_shape(
            "text", [(0, 0)],
            {"text": "A", "size": 100, "stitch_type": "run", "flip_h": True})
        rot = stitcher.compile_shape(
            "text", [(0, 0)],
            {"text": "A", "size": 100, "stitch_type": "run", "rotation": 90})
        b1 = stitcher.bounds_of(base)
        b2 = stitcher.bounds_of(flip)
        b3 = stitcher.bounds_of(rot)
        self.assertAlmostEqual(b1[2] - b1[0], b2[2] - b2[0], delta=3)
        self.assertGreater(b3[2] - b3[0], b3[3] - b3[1])  # girado 90°: largura e altura trocam


class TestTransforms(unittest.TestCase):
    def _obj(self, shape="rect"):
        doc = Document()
        obj = doc.new_object_from_points(
            shape, stitcher.rect_points(0, 0, 200, 100) if shape == "rect"
            else [(0, 0), (300, 60)],
            params={"stitch_type": "run"})
        return doc, obj

    def test_mirror_h(self):
        doc, obj = self._obj()
        b0 = obj.bounds()
        obj.mirror_h()
        b1 = obj.bounds()
        self.assertAlmostEqual(b1[0], b0[0], delta=1)
        self.assertAlmostEqual(b1[2], b0[2], delta=1)

    def test_rotate90(self):
        doc, obj = self._obj()
        b0 = obj.bounds()
        obj.rotate90(1)
        b1 = obj.bounds()
        w0, h0 = b0[2] - b0[0], b0[3] - b0[1]
        w1, h1 = b1[2] - b1[0], b1[3] - b1[1]
        self.assertAlmostEqual(w1, h0, delta=2)
        self.assertAlmostEqual(h1, w0, delta=2)

    def test_scale(self):
        doc, obj = self._obj()
        b0 = obj.bounds()
        obj.scale(2.0)
        b1 = obj.bounds()
        self.assertAlmostEqual((b1[2] - b1[0]) / (b0[2] - b0[0]), 2.0, delta=0.05)

    def test_text_transforms(self):
        doc = Document()
        obj = doc.new_object_from_points(
            "text", [(100, 100)],
            params={"text": "OI", "size": 100, "stitch_type": "run"})
        n0 = obj.stitch_count()
        obj.mirror_h()
        obj.rotate90(2)
        obj.scale(1.5)
        self.assertGreater(obj.stitch_count(), n0 * 0.5)


class TestReport(unittest.TestCase):
    def _doc(self):
        doc = Document()
        doc.title = "Teste"
        doc.new_object_from_points(
            "rect", stitcher.rect_points(0, 0, 500, 500),
            params={"stitch_type": "run"})
        doc.new_object_from_points(
            "polygon", [(0, 600), (500, 600), (250, 1000)],
            thread=ThreadColor("Azul", 0x1F5FC4))
        return doc

    def test_length_and_stitches(self):
        from bordadostudio import report
        doc = self._doc()
        data = report.build_report(doc)
        self.assertEqual(data["objects"], 2)
        self.assertEqual(data["color_changes"], 1)
        self.assertGreater(data["stitches"], 50)
        self.assertGreater(data["length_mm"], 100)
        self.assertGreater(data["thread_m"], 0)
        self.assertGreater(data["minutes"], 0)

    def test_time_formula(self):
        from bordadostudio import report
        doc = self._doc()
        data = report.build_report(doc, speed=500)
        esperado = data["stitches"] / 500 + data["color_changes"] * 0.25
        self.assertAlmostEqual(data["minutes"], esperado, places=4)

    def test_cost_formula(self):
        from bordadostudio import report
        doc = self._doc()
        data = report.build_report(doc, hourly_rate=60.0, per_color=1.5)
        esperado = data["minutes"] / 60.0 * 60.0 + data["color_changes"] * 1.5
        self.assertAlmostEqual(data["cost"], esperado, places=3)

    def test_format_report(self):
        from bordadostudio import report
        doc = self._doc()
        texto = report.format_report(report.build_report(doc, hourly_rate=50))
        self.assertIn("RELATÓRIO DE PRODUÇÃO", texto)
        self.assertIn("Pontos totais", texto)
        self.assertIn("TOTAL", texto)
        self.assertIn("Teste", texto)

    def test_hidden_objects_excluded(self):
        from bordadostudio import report
        doc = self._doc()
        doc.objects[0].visible = False
        data = report.build_report(doc)
        self.assertEqual(data["objects"], 1)
        self.assertEqual(data["color_changes"], 0)


class TestView3D(unittest.TestCase):
    def test_paint_3d_offscreen(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtGui import QImage, QPainter
        from PySide6.QtWidgets import QApplication
        from bordadostudio.canvas import EditorCanvas

        app = QApplication.instance() or QApplication([])
        doc = Document()
        doc.new_object_from_points(
            "rect", stitcher.rect_points(0, 0, 400, 300),
            params={"stitch_type": "run"},
            thread=ThreadColor("Vermelho", 0xD62828))
        canvas = EditorCanvas(doc)
        canvas.view.resize(400, 300)
        canvas.view.show()
        app.processEvents()

        def count_colored():
            img = QImage(400, 300, QImage.Format_RGB32)
            img.fill(0)
            p = QPainter(img)
            canvas.view.render(p)
            p.end()
            n = 0
            for y in range(0, 300, 2):
                for x in range(0, 400, 2):
                    c = img.pixelColor(x, y)
                    if c.red() > 90 and c.green() < 90:
                        n += 1
            return n

        canvas.set_view_3d(False)
        n_flat = count_colored()
        canvas.set_view_3d(True)
        n_3d = count_colored()
        self.assertGreater(n_flat, 10)
        # 3D desenha sombra + corpo + brilho => mais pixels cobertos
        self.assertGreater(n_3d, n_flat)


class TestModel(unittest.TestCase):
    def test_object_recompile_and_translate(self):
        doc = Document()
        obj = doc.new_object_from_points("rect", stitcher.rect_points(0, 0, 100, 100))
        self.assertGreater(obj.stitch_count(), 0)
        b0 = obj.bounds()
        obj.translate(50, 50)
        b1 = obj.bounds()
        self.assertAlmostEqual(b1[0], b0[0] + 50, places=1)

    def test_undo_redo(self):
        doc = Document()
        doc.new_object_from_points("polygon", [(0, 0), (100, 0), (100, 100)])
        self.assertEqual(len(doc.objects), 1)
        doc.new_object_from_points("polygon", [(0, 0), (50, 0), (50, 50)])
        self.assertEqual(len(doc.objects), 2)
        doc.undo()
        self.assertEqual(len(doc.objects), 1)
        doc.redo()
        self.assertEqual(len(doc.objects), 2)

    def test_json_roundtrip(self):
        doc = Document()
        doc.title = "Teste"
        obj = doc.new_object_from_points(
            "satin", [(0, 0), (150, 30)],
            params={"width": 30},
            thread=ThreadColor("Azul", 0x1F5FC4, "14"),
        )
        text = doc.to_json()
        doc2 = Document.from_json(text)
        self.assertEqual(doc2.title, "Teste")
        self.assertEqual(len(doc2.objects), 1)
        self.assertEqual(doc2.objects[0].thread.hex_color, 0x1F5FC4)
        self.assertEqual(len(doc2.objects[0].stitches), len(obj.stitches))

    def test_save_load_file(self):
        doc = Document()
        doc.new_object_from_points("rect", stitcher.rect_points(0, 0, 80, 80))
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "desenho.bds")
            doc.save_file(path)
            doc2 = Document.load_file(path)
            self.assertEqual(len(doc2.objects), 1)
            self.assertGreater(doc2.total_stitches(), 0)


class TestFormats(unittest.TestCase):
    def _sample_doc(self):
        doc = Document()
        doc.new_object_from_points(
            "polygon", [(0, 0), (200, 0), (200, 150), (0, 150)],
            thread=ThreadColor("Vermelho", 0xD62828, "5"),
        )
        doc.new_object_from_points(
            "satin", [(0, 250), (300, 250)],
            params={"width": 40},
            thread=ThreadColor("Azul", 0x1F5FC4, "14"),
        )
        return doc

    def test_export_dst(self):
        doc = self._sample_doc()
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "teste.dst")
            n = export_document(doc, path)
            self.assertGreater(n, 10)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 100)

    def test_export_pes_colors_snap_to_palette(self):
        # PES guarda índice de paleta Brother: cores sofrem aproximação.
        doc = self._sample_doc()
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "teste.pes")
            export_document(doc, path)
            objs = import_file(path)
            self.assertGreaterEqual(len(objs), 2)
            colors = [o.thread.hex_color for o in objs]
            # um bloco deve continuar avermelhado e outro azulado
            self.assertTrue(any(((c >> 16) & 255) > ((c >> 8) & 255) and
                                ((c >> 16) & 255) > (c & 255) for c in colors))
            self.assertTrue(any((c & 255) > ((c >> 16) & 255) for c in colors))

    def test_export_vp3_keeps_exact_colors(self):
        doc = self._sample_doc()
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "teste.vp3")
            export_document(doc, path)
            objs = import_file(path)
            colors = [o.thread.hex_color for o in objs]
            self.assertIn(0xD62828, colors)
            self.assertIn(0x1F5FC4, colors)

    def test_import_dst(self):
        doc = self._sample_doc()
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "teste.dst")
            export_document(doc, path)
            objs = import_file(path)
            total = sum(len(o.stitches) for o in objs)
            self.assertGreater(total, 10)

    def test_export_empty_raises(self):
        doc = Document()
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "vazio.dst")
            with self.assertRaises(ValueError):
                export_document(doc, path)

    def test_export_png_and_svg(self):
        doc = self._sample_doc()
        with tempfile.TemporaryDirectory() as td:
            for ext in ("png", "svg"):
                path = os.path.join(td, f"teste.{ext}")
                export_document(doc, path)
                self.assertTrue(os.path.exists(path))
                self.assertGreater(os.path.getsize(path), 50)


class TestCatalogoPontos(unittest.TestCase):
    """Catálogo de contornos e enchimentos (v1.6)."""

    CONTORNOS = ("run2", "zigzag", "scallop", "spring", "motif_run")
    ENCHIMENTOS = ("fill_contour", "fill_radial", "fill_mesh",
                   "fill_spiral", "fill_brick")

    def _shape(self, tipo):
        from bordadostudio import stitcher
        doc = Document()
        return doc.new_object_from_points(
            "polygon", stitcher.ellipse_points(0, 0, 300, 200),
            params={"stitch_type": tipo})

    def test_contornos_compilam(self):
        for tipo in self.CONTORNOS:
            obj = self._shape(tipo)
            self.assertGreater(obj.stitch_count(), 8, tipo)

    def test_enchimentos_compilam(self):
        for tipo in self.ENCHIMENTOS:
            obj = self._shape(tipo)
            self.assertGreater(obj.stitch_count(), 20, tipo)

    def test_todos_tipos_no_painel(self):
        from bordadostudio.props_panel import STITCH_TYPES
        keys = [k for k, _ in STITCH_TYPES]
        self.assertEqual(len(keys), len(set(keys)))
        for tipo in self.CONTORNOS + self.ENCHIMENTOS:
            self.assertIn(tipo, keys, tipo)
        self.assertEqual(len(keys), 22)

    def test_recompile_muda_com_parametros(self):
        obj = self._shape("fill_mesh")
        n1 = obj.stitch_count()
        obj.params["spacing"] = 40.0
        obj.recompile()
        self.assertLess(obj.stitch_count(), n1)

    def test_unidades_display(self):
        app = (self._app() if hasattr(self, "_app") else None)
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        from bordadostudio.main_window import MainWindow
        win = MainWindow()
        win.show()
        app.processEvents()
        self.assertEqual(win.units, "mm")
        win.units_combo.setCurrentText("Polegadas")
        app.processEvents()
        self.assertEqual(win.units, "in")
        self.assertEqual(win.canvas.view.units, "in")
        self.assertEqual(win._fmt_len(25.4), "1,00 in")
        win.units_combo.setCurrentText("Métrico")
        self.assertEqual(win._fmt_len(10.0), "10,0 mm")
        win.doc.modified = False
        win.close()


class TestInterfaceProfissional(unittest.TestCase):
    """Testes da interface estilo profissional (v1.4)."""

    def _app(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        return QApplication.instance() or QApplication([])

    def test_icons_factory(self):
        from PySide6.QtGui import QIcon
        from bordadostudio import icons
        for name in ("select", "polygon", "freehand", "rect", "ellipse",
                     "satin", "text", "new", "open", "save", "import",
                     "export", "undo", "redo", "delete", "simulate",
                     "view3d", "grid", "fit", "zoom_in", "zoom_out",
                     "mirror_h", "mirror_v", "rotate", "scale", "report",
                     "props", "hoop", "manual", "rulers"):
            ico = icons.icon(name)
            self.assertIsInstance(ico, QIcon)
            self.assertFalse(ico.isNull(), name)
        sw = icons.thread_swatch(0xD62828, 24, "1")
        self.assertFalse(sw.isNull())

    def test_color_bar_apply(self):
        self._app()
        from bordadostudio.colorway import ColorBar
        from bordadostudio.threads import ThreadColor
        doc = self._doc_with_rect()
        bar = ColorBar()
        bar.rebuild([o.thread for o in doc.objects])
        self.assertGreater(len(bar._buttons), 5)
        self.assertEqual(bar._threads[0].hex_color, doc.objects[0].thread.hex_color)
        picked = []
        bar.color_picked.connect(picked.append)
        bar._buttons[3].click()
        self.assertEqual(len(picked), 1)

    def _doc_with_rect(self):
        from bordadostudio import stitcher
        doc = Document()
        doc.new_object_from_points(
            "rect", stitcher.rect_points(0, 0, 500, 500),
            params={"stitch_type": "run"},
            thread=ThreadColor("Vermelho", 0xD62828))
        return doc

    def test_info_bar_and_rulers(self):
        app = self._app()
        from PySide6.QtGui import QImage, QPainter
        from bordadostudio.main_window import MainWindow
        win = MainWindow()
        win.doc = self._doc_with_rect()
        win.canvas.doc = win.doc
        win.canvas.rebuild()
        win.refresh_panels()
        win.show()
        app.processEvents()

        # seleção preenche largura/altura e tipo de ponto
        win.canvas.select(win.doc.objects[0].id)
        app.processEvents()
        self.assertEqual(win.info_w.value(), 50.0)
        self.assertEqual(win.info_h.value(), 50.0)
        self.assertIn("LINHA", win.status_stitch.text())

        # cor padrão sem seleção; com seleção aplica ao objeto
        from bordadostudio.threads import ThreadColor
        win.canvas.select("")
        win._apply_thread(ThreadColor("Azul", 0x1F5FC4))
        self.assertEqual(win.canvas.default_thread.hex_color, 0x1F5FC4)
        win.canvas.select(win.doc.objects[0].id)
        win._apply_thread(ThreadColor("Verde", 0x2BA84A))
        self.assertEqual(win.doc.objects[0].thread.hex_color, 0x2BA84A)

        # réguas desenham sem erro
        win.canvas.set_show_rulers(True)
        img = QImage(300, 200, QImage.Format_RGB32)
        img.fill(0)
        p = QPainter(img)
        win.canvas.view.render(p)
        p.end()
        win.doc.modified = False
        win.close()

    def test_zoom_controls(self):
        app = self._app()
        from bordadostudio.main_window import MainWindow
        win = MainWindow()
        win.show()
        app.processEvents()
        z0 = win.canvas.view.transform().m11()
        win.view_zoom_in()
        z1 = win.canvas.view.transform().m11()
        self.assertGreater(z1, z0)
        win.view_zoom_out()
        win.view_zoom_out()
        z2 = win.canvas.view.transform().m11()
        self.assertLess(z2, z1)
        win._set_zoom_pct(200)
        self.assertAlmostEqual(win.canvas.view.transform().m11(), 2.0, places=2)
        win.doc.modified = False
        win.close()


class TestFormasEAcoes(unittest.TestCase):
    """Formas prontas e botões de ação (v1.5)."""

    def test_shape_generators(self):
        from bordadostudio import stitcher
        for gen in (stitcher.heart_points, stitcher.star_points,
                    stitcher.diamond_points, stitcher.cross_points,
                    stitcher.triangle_points, stitcher.hexagon_points):
            pts = gen(100, 200, 50, 40)
            self.assertGreaterEqual(len(pts), 3, gen.__name__)
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            # deve caber na caixa pedida (com pequena folga numérica)
            self.assertGreaterEqual(min(xs), 100 - 51, gen.__name__)
            self.assertLessEqual(max(xs), 100 + 51, gen.__name__)
            self.assertGreaterEqual(min(ys), 200 - 41, gen.__name__)
            self.assertLessEqual(max(ys), 200 + 41, gen.__name__)

    def test_shape_compile(self):
        doc = Document()
        from bordadostudio import stitcher
        for nome, pts in (
                ("heart", stitcher.heart_points(0, 0, 200, 200)),
                ("star", stitcher.star_points(0, 0, 200, 200)),
                ("diamond", stitcher.diamond_points(0, 0, 200, 200)),
                ("cross", stitcher.cross_points(0, 0, 200, 200)),
                ("triangle", stitcher.triangle_points(0, 0, 200, 200)),
                ("hexagon", stitcher.hexagon_points(0, 0, 200, 200))):
            obj = doc.new_object_from_points(nome, pts)
            self.assertGreater(obj.stitch_count(), 20, nome)
            self.assertEqual(obj.shape, nome)

    def test_rotate_any_angle(self):
        from bordadostudio import stitcher
        doc = Document()
        obj = doc.new_object_from_points(
            "rect", stitcher.rect_points(0, 0, 400, 200),
            params={"stitch_type": "run"})
        x0 = obj.points[0][0]
        obj.rotate(45)
        self.assertNotAlmostEqual(obj.points[0][0], x0, places=3)
        # 360° = volta ao início
        obj.rotate(315)
        self.assertAlmostEqual(obj.points[0][0], x0, places=3)

    def test_smooth(self):
        from bordadostudio import stitcher
        doc = Document()
        # losango "espinhoso": a suavização aproxima os pontos do centro
        pts = [(0, 0), (500, 100), (500, 500), (100, 500)]
        obj = doc.new_object_from_points("polygon", list(pts),
                                         params={"stitch_type": "run"})
        ok = obj.smooth_points(iterations=3)
        self.assertTrue(ok)
        self.assertEqual(len(obj.points), 4)
        cx = sum(p[0] for p in obj.points) / 4
        for x, y in obj.points:
            self.assertNotEqual((x, y), (0, 0))

    def test_split_object(self):
        from bordadostudio import stitcher
        doc = Document()
        obj = doc.new_object_from_points(
            "rect", stitcher.rect_points(0, 0, 800, 800),
            params={"stitch_type": "run"})
        n0 = obj.stitch_count()
        novo = doc.split_object(obj)
        self.assertIsNotNone(novo)
        self.assertEqual(len(doc.objects), 2)
        self.assertEqual(doc.objects[0].id, obj.id)
        self.assertEqual(doc.objects[1].id, novo.id)
        self.assertGreater(obj.stitch_count(), 5)
        self.assertGreater(novo.stitch_count(), 5)
        self.assertLess(obj.stitch_count(), n0)
        # objeto minúsculo não divide
        tiny = doc.new_object_from_points(
            "freehand", [(0, 0), (10, 10)], params={"stitch_type": "run"})
        self.assertIsNone(doc.split_object(tiny))

    def test_underlay_toggle_recompile(self):
        from bordadostudio import stitcher
        doc = Document()
        obj = doc.new_object_from_points(
            "polygon", stitcher.rect_points(0, 0, 400, 400))
        antes = obj.stitch_count()
        obj.params["edge_underlay"] = not obj.params.get("edge_underlay", True)
        obj.recompile()
        self.assertGreater(obj.stitch_count(), 0)


class TestCompletudeV17(unittest.TestCase):
    """Bastidores, campos de precisão, arranjar, perfis, catálogos (v1.7)."""

    def test_catalogos_de_linhas(self):
        from bordadostudio.threads import PALETTES, colors_of, palette_names
        nomes = palette_names()
        for cat in ("Essenciais", "Madeira Classic", "Anchor", "Isacord",
                    "Tons de Pele", "Natureza", "Metálicas e Especiais"):
            self.assertIn(cat, nomes, cat)
            self.assertGreater(len(colors_of(cat)), 7, cat)
        for cat, cores in PALETTES.items():
            for c in cores:
                self.assertTrue(c.name, cat)

    def test_biblioteca_bastidores(self):
        from bordadostudio import hoops
        self.assertGreaterEqual(len(hoops.HOOPS), 8)
        r = hoops.match_hoop(1000, 1000)
        self.assertIsNotNone(r)
        # redonda pequena e quadrada 100×100 têm o mesmo tamanho:
        nomes = {h.name for h in hoops.HOOPS if h.width == 1000}
        self.assertIn("Redonda pequena", nomes)
        self.assertIn("Quadrada", nomes)
        c = hoops.find_hoop("Redonda pequena")
        self.assertEqual(c.shape, "circle")

    def test_move_resize_center(self):
        from bordadostudio import stitcher
        doc = Document()
        obj = doc.new_object_from_points(
            "rect", stitcher.rect_points(0, 0, 500, 250),
            params={"stitch_type": "run"})
        obj.move_to(100, 200)
        min_x, min_y, max_x, max_y = obj.bbox()
        self.assertAlmostEqual(min_x, 100, places=3)
        self.assertAlmostEqual(min_y, 200, places=3)
        obj.resize_to(1000, 1000)
        min_x, min_y, max_x, max_y = obj.bbox()
        self.assertAlmostEqual(max_x - min_x, 1000, places=1)
        self.assertAlmostEqual(max_y - min_y, 1000, places=1)
        obj.center_in(2000, 2000)
        min_x, min_y, max_x, max_y = obj.bbox()
        self.assertAlmostEqual((min_x + max_x) / 2, 1000, places=1)
        self.assertAlmostEqual((min_y + max_y) / 2, 1000, places=1)

    def test_perfil_store(self):
        import tempfile, os
        from bordadostudio.profiles import ProfileStore
        caminho = os.path.join(tempfile.mkdtemp(), "perfis.json")
        st = ProfileStore(caminho)
        self.assertIn("Padrão", st.names())
        st.set("Meu", {"stitch_type": "run", "stitch_length": 20.0})
        st2 = ProfileStore(caminho)   # recarrega do disco
        self.assertEqual(st2.get("Meu")["stitch_type"], "run")
        st2.remove("Meu")
        self.assertIsNone(ProfileStore(caminho).get("Meu"))

    def test_bastidor_no_documento(self):
        doc = Document()
        doc.hoop_name = "Redonda média"
        doc.hoop_shape = "circle"
        doc.hoop = [1300, 1300]
        d2 = Document.from_dict(doc.to_dict())
        self.assertEqual(d2.hoop_name, "Redonda média")
        self.assertEqual(d2.hoop_shape, "circle")
        # arquivos antigos continuam abrindo
        d3 = Document.from_dict({"title": "x", "hoop": [1000, 1000], "objects": []})
        self.assertEqual(d3.hoop_name, "Personalizado")
        self.assertEqual(d3.hoop_shape, "rect")


class TestV18(unittest.TestCase):
    """Mistura multi-fio, curvas de nós e clipart (v1.8)."""

    def _doc(self):
        from bordadostudio import stitcher
        doc = Document()
        obj = doc.new_object_from_points(
            "polygon", stitcher.ellipse_points(0, 0, 300, 200),
            params={"stitch_type": "fill"})
        return doc, obj

    def test_expand_curves(self):
        from bordadostudio import stitcher
        pts = [(0, 0), (100, 0), (100, 100), (0, 100)]
        dense = stitcher.expand_curves(pts, [0, 2])
        self.assertGreater(len(dense), len(pts))
        self.assertAlmostEqual(dense[0][0], 0.0)
        # sem curvas devolve igual
        self.assertEqual(stitcher.expand_curves(pts, []), pts)

    def test_curves_toggle_and_recompile(self):
        doc, obj = self._doc()
        n0 = obj.stitch_count()
        obj.params["curves"] = [0, 1, 2, 3]
        obj.recompile()
        self.assertGreater(len(obj.render_points()), len(obj.points) + 4)
        self.assertGreater(obj.stitch_count(), n0)
        obj.params["curves"] = []
        obj.recompile()
        self.assertEqual(len(obj.render_points()), len(obj.points))

    def test_fill_blend_muda_de_cor(self):
        from bordadostudio import stitcher
        doc = Document()
        obj = doc.new_object_from_points(
            "polygon", stitcher.ellipse_points(0, 0, 400, 300),
            params={"stitch_type": "fill_blend", "blend_color": 0x2222CC})
        cmds = obj.stitches
        trocas = [c for _x, _y, c in cmds if c == stitcher.COLOR_CHANGE]
        self.assertGreater(len(trocas), 2, "mistura deve trocar de cor")
        self.assertGreater(obj.stitch_count(), 50)

    def test_export_blend_leva_duas_linhas(self):
        import os, tempfile
        from bordadostudio import stitcher
        from bordadostudio.formats_io import document_to_pattern, export_document
        doc = Document()
        doc.new_object_from_points(
            "polygon", stitcher.ellipse_points(0, 0, 400, 300),
            params={"stitch_type": "fill_blend", "blend_color": 0x2222CC},
            thread=ThreadColor("Vermelho", 0xD62828))
        p = document_to_pattern(doc)
        cores = {t.color for t in p.threadlist}
        self.assertIn(0xD62828, cores)
        self.assertIn(0x2222CC, cores)
        caminho = os.path.join(tempfile.mkdtemp(), "blend.dst")
        n = export_document(doc, caminho)
        self.assertGreater(n, 50)

    def test_clipart(self):
        from bordadostudio import clipart
        self.assertGreaterEqual(len(clipart.names()), 12)
        for nome in clipart.names():
            partes = clipart.build(nome, 50.0, 100, 100)
            self.assertGreaterEqual(len(partes), 1, nome)
            for cont in partes:
                self.assertGreaterEqual(len(cont), 3, nome)
        doc = Document()
        for cont in clipart.build("Pata", 40.0):
            obj = doc.new_object_from_points("polygon", cont)
            self.assertGreater(obj.stitch_count(), 10)

    def test_nos_inserir_excluir_curva(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QPointF
        from bordadostudio.canvas import EditorCanvas
        app = QApplication.instance() or QApplication([])
        doc, obj = self._doc()
        canvas = EditorCanvas(doc)
        canvas.select(obj.id)
        n = len(obj.points)
        # inserir vértice no meio do primeiro segmento
        ax, ay = obj.points[0]
        bx, by = obj.points[1]
        canvas.insert_vertex(obj, (ax + bx) / 2, (ay + by) / 2)
        self.assertEqual(len(obj.points), n + 1)
        # alternar curva no vértice 0
        from bordadostudio.canvas import VertexHandle
        h = VertexHandle(obj, 0)
        canvas.toggle_vertex_curve(h)
        self.assertIn(0, obj.params["curves"])
        canvas.toggle_vertex_curve(h)
        self.assertNotIn(0, obj.params["curves"])
        # excluir o vértice inserido
        h2 = VertexHandle(obj, 1)
        canvas.delete_vertex(h2)
        self.assertEqual(len(obj.points), n)
        app.processEvents()


class TestV19(unittest.TestCase):
    """Auto-digitização de imagens e interface v1.9."""

    def _png(self, tmp):
        import os
        from PySide6.QtGui import QImage, QPainter, QColor, QBrush
        img = QImage(300, 220, QImage.Format_RGB32)
        img.fill(QColor(255, 255, 255))
        p = QPainter(img)
        p.setBrush(QBrush(QColor(200, 30, 30)))
        p.setPen(QColor(200, 30, 30))
        p.drawEllipse(20, 30, 120, 120)
        p.setBrush(QBrush(QColor(30, 40, 200)))
        p.setPen(QColor(30, 40, 200))
        p.drawRect(170, 60, 100, 90)
        # pontinho pequeno demais para passar da área mínima
        p.setBrush(QBrush(QColor(0, 0, 0)))
        p.drawRect(285, 5, 3, 3)
        p.end()
        caminho = os.path.join(tmp, "foto.png")
        img.save(caminho)
        return caminho

    def test_trace_image_acha_formas(self):
        import tempfile
        from bordadostudio import digitize
        caminho = self._png(tempfile.mkdtemp())
        w, h, formas = digitize.trace_image(caminho, limiar=128,
                                            min_area=50, suavizar=1.5)
        self.assertEqual((w, h), (300, 220))
        self.assertEqual(len(formas), 2, "círculo + retângulo (o pontinho sai)")
        cores = sorted(f["rgb"] for f in formas)
        # uma forma avermelhada e outra azulada
        self.assertTrue(any((c >> 16) > (c & 255) for c in cores))
        self.assertTrue(any((c & 255) > (c >> 16) for c in cores))
        for f in formas:
            self.assertGreaterEqual(len(f["points_px"]), 3)

    def test_shapes_to_design_escala(self):
        from bordadostudio import digitize
        formas = [{"points_px": [(0, 0), (200, 0), (200, 100), (0, 100)],
                   "rgb": 0x112233}]
        out = digitize.shapes_to_design(formas, 100.0, 0, 0)
        xs = [p[0] for p in out[0]["points"]]
        ys = [p[1] for p in out[0]["points"]]
        # 100 mm = 1000 unidades de largura, centrado
        self.assertAlmostEqual(max(xs) - min(xs), 1000.0, places=3)
        self.assertAlmostEqual((max(xs) + min(xs)) / 2, 0.0, places=3)
        self.assertEqual(out[0]["rgb"], 0x112233)

    def test_simplify_reduz(self):
        from bordadostudio import digitize
        import math
        pts = [(200 + 100 * math.cos(a), 200 + 100 * math.sin(a))
               for a in [i * 2 * math.pi / 60 for i in range(60)]]
        curto = digitize.simplify(pts, 3.0)
        self.assertLess(len(curto), len(pts))
        self.assertGreaterEqual(len(curto), 3)

    def test_digitize_dialog(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        import tempfile
        from PySide6.QtWidgets import QApplication
        from bordadostudio.digitize_dialog import DigitizeDialog
        app = QApplication.instance() or QApplication([])
        caminho = self._png(tempfile.mkdtemp())
        dlg = DigitizeDialog(caminho)
        opts = dlg.result_options()
        self.assertTrue(opts["preencher"])
        self.assertGreaterEqual(len(dlg.result_shapes()), 2)
        self.assertTrue(dlg._ok_btn.isEnabled())
        app.processEvents()

    def test_mainwindow_digitize_e_clipboard(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        import tempfile
        from PySide6.QtWidgets import QApplication
        from bordadostudio.main_window import MainWindow
        app = QApplication.instance() or QApplication([])
        win = MainWindow()
        self.assertTrue(hasattr(win, "act_digitize"))
        self.assertTrue(hasattr(win, "act_print"))
        self.assertTrue(hasattr(win, "doc_tab"))
        self.assertTrue(hasattr(win, "export_combo"))
        self.assertTrue(hasattr(win, "fabric_combo"))
        self.assertEqual(win.doc_tab.count(), 1)
        # copiar/colar
        from bordadostudio import stitcher
        obj = win.doc.new_object_from_points(
            "polygon", stitcher.rect_points(0, 0, 200, 150))
        win.canvas.select(obj.id)
        win.edit_copy()
        win.edit_paste()
        self.assertEqual(len(win.doc.objects), 2)
        # inserir digitalização direto
        caminho = self._png(tempfile.mkdtemp())
        from bordadostudio import digitize
        _w, _h, formas = digitize.trace_image(caminho, min_area=50)
        win._insert_digitized(formas, {"largura_mm": 80.0, "preencher": True,
                                       "usar_cores": True})
        self.assertEqual(len(win.doc.objects), 2 + len(formas))
        win.doc.modified = False
        win.close()
        app.processEvents()


class TestV20(unittest.TestCase):
    """Ferramentas ampliadas + máquina de bordado (v1.10)."""

    def test_geradores_novos(self):
        from bordadostudio import stitcher
        fechadas = ("pentagon_points", "octagon_points", "arrow_points",
                    "crescent_points", "flower_points", "cloud_points")
        abertas = ("arc_points", "wave_points", "zigzag_points",
                   "spiral_points")
        for nome in fechadas + abertas:
            fn = getattr(stitcher, nome)
            pts = fn(100, 80, 60, 45)
            self.assertGreaterEqual(len(pts), 2, nome)
            for x, y in pts:
                self.assertTrue(abs(x - 100) <= 60 * 1.35 + 1, nome)
                self.assertTrue(abs(y - 80) <= 45 * 1.35 + 1, nome)
        self.assertEqual(len(stitcher.pentagon_points(0, 0, 10, 10)), 5)
        self.assertEqual(len(stitcher.octagon_points(0, 0, 10, 10)), 8)
        self.assertEqual(len(stitcher.zigzag_points(0, 0, 50, 10, teeth=4)), 9)

    def test_todas_ferramentas_arraste_criam_objeto(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QPointF, Qt
        from PySide6.QtTest import QTest
        from bordadostudio.main_window import MainWindow
        app = QApplication.instance() or QApplication([])
        win = MainWindow()
        win.resize(1280, 820)
        win.show()
        app.processEvents()
        view = win.canvas.view
        ferramentas = ["rect", "ellipse", "heart", "star", "diamond",
                       "cross", "triangle", "hexagon", "pentagon",
                       "octagon", "arrow", "crescent", "flower", "cloud",
                       "arc", "wave", "zigzag", "spiral"]
        base = len(win.doc.objects)
        for i, key in enumerate(ferramentas):
            win.canvas.set_tool(key)
            x0 = 200 + (i % 4) * 220
            y0 = 150 + (i // 4) * 140
            p1 = view.mapFromScene(QPointF(x0, y0))
            p2 = view.mapFromScene(QPointF(x0 + 150, y0 + 110))
            QTest.mousePress(view.viewport(), Qt.LeftButton, pos=p1)
            QTest.mouseMove(view.viewport(), p2, delay=5)
            QTest.mouseRelease(view.viewport(), Qt.LeftButton, pos=p2)
            app.processEvents()
            n = len(win.doc.objects)
            self.assertEqual(n, base + i + 1,
                             f"ferramenta «{key}» não criou objeto")
            obj = win.doc.objects[-1]
            self.assertGreater(obj.stitch_count(), 5, key)
        # ferramentas de traço aberto ficam abertas
        abertos = [o for o in win.doc.objects[-4:]]
        for o in abertos:
            self.assertFalse(o.params.get("closed", True), o.name)
        win.doc.modified = False
        win.close()
        app.processEvents()

    def test_grade_tem_mais_de_40(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        from bordadostudio.main_window import MainWindow
        app = QApplication.instance() or QApplication([])
        win = MainWindow()
        self.assertGreaterEqual(len(win.left_buttons), 40)
        for b in win.left_buttons:
            a = b.defaultAction()
            self.assertIsNotNone(a)
            self.assertTrue(a.icon().isNull() is False or a.text())
        win.doc.modified = False
        win.close()
        app.processEvents()

    def test_maquinas_exportam(self):
        import os, tempfile
        from bordadostudio import stitcher, formats_io
        from bordadostudio.model import Document
        self.assertGreaterEqual(len(formats_io.MACHINES), 10)
        exts_validas = {e for e, _ in formats_io.EXPORT_FORMATS}
        for nome, ext in formats_io.MACHINES:
            self.assertIn(ext, exts_validas, nome)
        # busca por nome (como no painel)
        self.assertEqual(formats_io.machine_format("brother"), "pes")
        self.assertEqual(formats_io.machine_format("Janome / Elna / Kenmore — JEF"), "jef")
        self.assertIsNone(formats_io.machine_format("máquina inexistente xyz"))
        doc = Document()
        doc.new_object_from_points("polygon", stitcher.rect_points(0, 0, 300, 200))
        for ext in ("dst", "pes", "jef", "vp3", "exp", "xxx", "u01", "tbf", "pec"):
            caminho = os.path.join(tempfile.mkdtemp(), f"m.{ext}")
            n = formats_io.export_document(doc, caminho)
            self.assertGreater(n, 20, ext)
            self.assertTrue(os.path.exists(caminho), ext)

    def test_painel_maquina_seleciona_formato(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        from bordadostudio.main_window import MainWindow
        app = QApplication.instance() or QApplication([])
        win = MainWindow()
        self.assertGreaterEqual(win.machine_combo.count(), 10)
        idx = win.machine_combo.findText("Brother / Baby Lock — PES")
        self.assertGreaterEqual(idx, 0)
        win.machine_combo.setCurrentIndex(idx)
        self.assertEqual(win.export_combo.currentData(), "pes")
        idx = win.machine_combo.findText("Janome / Elna / Kenmore — JEF")
        win.machine_combo.setCurrentIndex(idx)
        self.assertEqual(win.export_combo.currentData(), "jef")
        win.doc.modified = False
        win.close()
        app.processEvents()


class TestV21(unittest.TestCase):
    """Barras superiores ampliadas (v1.11)."""

    def _win(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        from bordadostudio.main_window import MainWindow
        app = QApplication.instance() or QApplication([])
        win = MainWindow()
        return win, app

    def test_linha1_muitos_icones(self):
        from PySide6.QtWidgets import QToolButton
        win, app = self._win()
        tb1 = win._toolbars[0]
        acoes = [a for a in tb1.actions()
                 if not a.isSeparator()
                 and not (hasattr(a, "defaultWidget")
                          and a.defaultWidget() is not None)]
        self.assertGreaterEqual(len(acoes), 25)
        for a in acoes:
            self.assertFalse(a.icon().isNull(), a.text())
        win.doc.modified = False
        win.close()
        app.processEvents()

    def test_estilos_prontos(self):
        win, app = self._win()
        from bordadostudio import stitcher
        obj = win.doc.new_object_from_points(
            "polygon", stitcher.ellipse_points(0, 0, 300, 200))
        win.canvas.select(obj.id)
        win._apply_preset("preset_mar")
        self.assertEqual(obj.params["stitch_type"], "fill_mesh")
        self.assertEqual(obj.thread.hex_color, 0x1E5ABE)
        self.assertEqual(obj.params["blend_color"], 0x5AB4E6)
        win._apply_preset("preset_noite")
        self.assertEqual(obj.params["stitch_type"], "fill_blend")
        self.assertGreater(obj.stitch_count(), 50)
        win.doc.modified = False
        win.close()
        app.processEvents()

    def test_girar_e_escalar_pela_barra(self):
        win, app = self._win()
        from bordadostudio import stitcher
        obj = win.doc.new_object_from_points(
            "polygon", stitcher.rect_points(0, 0, 200, 100))
        win.canvas.select(obj.id)
        bx0 = obj.bbox()
        win.escala_spin.setValue(150)
        win._apply_scale_spin()
        bx1 = obj.bbox()
        self.assertAlmostEqual((bx1[2] - bx1[0]) / (bx0[2] - bx0[0]), 1.5,
                               places=3)
        win.girar_spin.setValue(90)
        win._apply_rotate_spin()
        bx2 = obj.bbox()
        # retângulo 200x100 → escala 1,5 = 300x150 → girado 90° vira 150x300
        self.assertAlmostEqual(bx2[2] - bx2[0], 150.0, delta=1.0)
        self.assertAlmostEqual(bx2[3] - bx2[1], 300.0, delta=1.0)
        win.doc.modified = False
        win.close()
        app.processEvents()


class TestInstalador(unittest.TestCase):
    """Instalador gráfico sem console (v1.11.1)."""

    RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_arquivos_do_instalador(self):
        for nome in ("instalar.bat", "instalar.vbs", "instalar_gui.pyw",
                     "instalar_console.bat"):
            caminho = os.path.join(self.RAIZ, nome)
            self.assertTrue(os.path.exists(caminho), nome)
        bat = open(os.path.join(self.RAIZ, "instalar.bat"),
                   encoding="utf-8").read()
        self.assertIn("instalar.vbs", bat)
        vbs = open(os.path.join(self.RAIZ, "instalar.vbs"),
                   encoding="utf-8").read()
        self.assertIn("instalar_gui.pyw", vbs)
        self.assertIn("pythonw", vbs)

    def test_gui_instalador_compila_e_tem_textos(self):
        import py_compile
        caminho = os.path.join(self.RAIZ, "instalar_gui.pyw")
        py_compile.compile(caminho, doraise=True)
        src = open(caminho, encoding="utf-8").read()
        for texto in ("Instalando BordadoStudio", "Instalado com sucesso",
                      "Abrir BordadoStudio", "instalar.log",
                      "requirements.txt", "pythonw"):
            self.assertIn(texto, src)
        # sem dependências externas (só biblioteca padrão)
        self.assertIn("import tkinter", src)
        self.assertNotIn("PySide6", src)

    def test_passos_da_instalacao_executam(self):
        from importlib.machinery import SourceFileLoader
        import importlib.util, tempfile
        loader = SourceFileLoader("instalar_gui",
                                  os.path.join(self.RAIZ, "instalar_gui.pyw"))
        spec = importlib.util.spec_from_loader("instalar_gui", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        self.assertTrue(callable(mod.passos_instalacao))
        self.assertTrue(mod.venv_python().endswith(
            os.path.join("Scripts", "python.exe") if os.name == "nt"
            else os.path.join("bin", "python")))


class TestControle(unittest.TestCase):
    """Notificação de instalação e bloqueio remoto (v1.12)."""

    def test_install_id_estavel(self):
        import tempfile
        from bordadostudio import controle
        raiz = tempfile.mkdtemp()
        id1 = controle.install_id(raiz)
        self.assertEqual(len(id1), 12)
        self.assertEqual(controle.install_id(raiz), id1)
        self.assertTrue(controle.existe_id(raiz))

    def test_avaliar_bloqueio(self):
        from bordadostudio import controle
        self.assertEqual(controle.avaliar_bloqueio(None, "x"), (False, ""))
        ok, motivo = controle.avaliar_bloqueio(
            {"bloquear": True, "motivo": "Licença vencida"}, "x")
        self.assertTrue(ok)
        self.assertEqual(motivo, "Licença vencida")
        ok, _ = controle.avaliar_bloqueio(
            {"bloquear": False, "bloquear_ids": ["abc", "x"]}, "x")
        self.assertTrue(ok)
        ok, _ = controle.avaliar_bloqueio(
            {"bloquear": True, "permitir_ids": ["x"]}, "x")
        self.assertFalse(ok)
        ok, _ = controle.avaliar_bloqueio(
            {"bloquear": False, "bloquear_ids": ["abc"]}, "x")
        self.assertFalse(ok)

    def test_verificar_bloqueio_falha_aberta(self):
        from unittest import mock
        from bordadostudio import controle
        with mock.patch.object(controle.urllib.request, "urlopen",
                               side_effect=OSError("sem rede")):
            self.assertEqual(controle.verificar_bloqueio("x"), (False, ""))

    def test_verificar_bloqueio_baixa_e_bloqueia(self):
        import json
        from unittest import mock
        from bordadostudio import controle
        payload = json.dumps({"bloquear": True, "motivo": "Bloqueado!"})
        class _Resp:
            def read(self):
                return payload.encode()
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
        with mock.patch.object(controle.urllib.request, "urlopen",
                               return_value=_Resp()):
            ok, motivo = controle.verificar_bloqueio("meuid")
        self.assertTrue(ok)
        self.assertEqual(motivo, "Bloqueado!")

    def test_notificar_envia_aviso(self):
        from unittest import mock
        from bordadostudio import controle
        chamadas = []
        def _fake(req, timeout=None):
            chamadas.append(req.full_url)
            class _R:
                def read(self):
                    return b"ok"
                def __enter__(self):
                    return self
                def __exit__(self, *a):
                    return False
            return _R()
        import tempfile
        raiz = tempfile.mkdtemp()
        with mock.patch.object(controle.urllib.request, "urlopen", _fake):
            controle.notificar_instalacao("9.9.9", raiz=raiz,
                                          evento="instalacao",
                                          assincrono=False)
        self.assertGreaterEqual(len(chamadas), 2)
        self.assertTrue(any("ntfy.sh" in u for u in chamadas))
        self.assertTrue(any("formsubmit.co" in u for u in chamadas))
        aviso = controle.montar_aviso("9.9.9", raiz)
        self.assertEqual(aviso["versao"], "9.9.9")
        self.assertEqual(aviso["install_id"], controle.install_id(raiz))

    def test_urls_de_controle(self):
        from bordadostudio import controle
        self.assertIn("STUDIO", controle._REPO)
        self.assertIn("controle/bloqueio.json", controle.BLOQUEIO_RAW)
        self.assertIn("BordadoStudio/controle", controle.BLOQUEIO_API)
        self.assertIn("brunocassetari1981@gmail.com", controle.EMAIL_DEV)
        self.assertIn("brunocassetari@hotmail.com", controle.EMAILS_DEV)


if __name__ == "__main__":
    unittest.main(verbosity=2)
