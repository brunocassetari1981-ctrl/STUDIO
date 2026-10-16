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


if __name__ == "__main__":
    unittest.main(verbosity=2)
