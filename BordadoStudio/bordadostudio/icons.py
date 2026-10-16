"""Ícones originais do BordadoStudio, desenhados com QPainter.

Nada de arte de terceiros: cada ícone é uma forma geométrica simples
desenhada em código, com o mesmo estilo visual (traço cinza, detalhes
coloridos).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)

INK = QColor(64, 64, 72)
ACCENT = QColor(31, 95, 196)
RED = QColor(214, 40, 40)
GREEN = QColor(43, 168, 74)
ORANGE = QColor(240, 140, 40)
PURPLE = QColor(140, 60, 190)

_cache: dict[str, QIcon] = {}


def _painter(pix: QPixmap) -> QPainter:
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    return p


def _pen(color=INK, w=1.8):
    pen = QPen(color, w)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen


def _draw(name: str, p: QPainter, s: float):
    """Desenha o glifo `name` em um canvas lógico de tamanho s (22)."""
    u = s / 22.0  # unidade

    def P(x, y):
        return QPointF(x * u, y * u)

    if name == "new":
        p.setPen(_pen(INK, 1.6))
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.drawRoundedRect(QRectF(P(5, 3), P(17, 19)), 1.5 * u, 1.5 * u)
        p.setPen(_pen(ACCENT, 1.6))
        p.drawLine(P(8, 3), P(8, 1))
        p.drawLine(P(8, 1), P(18, 1))
        p.drawLine(P(18, 1), P(18, 16))
    elif name == "open":
        p.setPen(_pen(INK, 1.6))
        p.setBrush(QBrush(QColor(255, 214, 102)))
        path = QPainterPath(P(2, 6))
        path.lineTo(P(9, 6))
        path.lineTo(P(11, 8))
        path.lineTo(P(20, 8))
        path.lineTo(P(18, 19))
        path.lineTo(P(2, 19))
        path.closeSubpath()
        p.drawPath(path)
    elif name == "save":
        p.setPen(_pen(INK, 1.6))
        p.setBrush(QBrush(ACCENT))
        p.drawRoundedRect(QRectF(P(3, 2), P(19, 20)), 1.5 * u, 1.5 * u)
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.drawRect(QRectF(P(7, 2), P(15, 8)))
        p.drawRect(QRectF(P(6, 12), P(16, 20)))
    elif name == "import":
        p.setPen(_pen(INK, 1.8))
        p.drawLine(P(11, 2), P(11, 13))
        p.drawLine(P(6, 8), P(11, 13))
        p.drawLine(P(16, 8), P(11, 13))
        p.drawLine(P(3, 18), P(19, 18))
    elif name == "export":
        p.setPen(_pen(INK, 1.8))
        p.drawLine(P(11, 15), P(11, 4))
        p.drawLine(P(6, 9), P(11, 4))
        p.drawLine(P(16, 9), P(11, 4))
        p.drawLine(P(3, 18), P(19, 18))
    elif name == "undo":
        p.setPen(_pen(ORANGE, 2.0))
        path = QPainterPath(P(6, 5))
        path.cubicTo(P(2, 8), P(2, 13), P(7, 14))
        p.drawPath(path)
        p.setBrush(QBrush(ORANGE))
        p.setPen(_pen(ORANGE, 1.0))
        p.drawPolygon([P(3, 2), P(9, 5), P(3, 8)])
    elif name == "redo":
        p.setPen(_pen(ACCENT, 2.0))
        path = QPainterPath(P(16, 5))
        path.cubicTo(P(20, 8), P(20, 13), P(15, 14))
        p.drawPath(path)
        p.setBrush(QBrush(ACCENT))
        p.setPen(_pen(ACCENT, 1.0))
        p.drawPolygon([P(19, 2), P(13, 5), P(19, 8)])
    elif name == "delete":
        p.setPen(_pen(RED, 1.8))
        p.drawLine(P(5, 5), P(17, 17))
        p.drawLine(P(17, 5), P(5, 17))
    elif name == "select":
        p.setPen(_pen(INK, 1.6))
        p.setBrush(QBrush(QColor(255, 255, 255)))
        path = QPainterPath(P(5, 2))
        path.lineTo(P(5, 18))
        path.lineTo(P(9, 14))
        path.lineTo(P(12, 20))
        path.lineTo(P(14.5, 18.5))
        path.lineTo(P(11.5, 13))
        path.lineTo(P(17, 12.5))
        path.closeSubpath()
        p.drawPath(path)
    elif name == "polygon":
        p.setPen(_pen(INK, 1.6))
        p.setBrush(QBrush(QColor(240, 140, 40, 120)))
        p.drawPolygon([P(4, 16), P(7, 5), P(15, 3), P(19, 11), P(13, 19)])
    elif name == "freehand":
        p.setPen(_pen(ACCENT, 2.0))
        path = QPainterPath(P(3, 15))
        path.cubicTo(P(7, 4), P(11, 20), P(15, 8))
        path.cubicTo(P(17, 3), P(19, 6), P(19, 6))
        p.drawPath(path)
    elif name == "rect":
        p.setPen(_pen(INK, 1.8))
        p.setBrush(QBrush(QColor(31, 95, 196, 60)))
        p.drawRect(QRectF(P(4, 5), P(18, 16)))
    elif name == "ellipse":
        p.setPen(_pen(INK, 1.8))
        p.setBrush(QBrush(QColor(43, 168, 74, 60)))
        p.drawEllipse(QRectF(P(3, 5), P(19, 16)))
    elif name == "satin":
        p.setPen(_pen(PURPLE, 1.6))
        for i in range(5):
            x = 5 + i * 3
            p.drawLine(P(x, 4), P(x + 2, 17))
            p.drawLine(P(x + 2, 17), P(x + 3.5, 4))
    elif name == "text":
        p.setPen(_pen(INK, 2.2))
        p.drawLine(P(6, 18), P(11, 4))
        p.drawLine(P(11, 4), P(16, 18))
        p.drawLine(P(8, 13), P(14, 13))
    elif name == "simulate":
        p.setPen(_pen(GREEN, 1.6))
        p.setBrush(QBrush(GREEN))
        p.drawPolygon([P(7, 4), P(18, 11), P(7, 18)])
    elif name == "view3d":
        p.setPen(_pen(ACCENT, 1.7))
        p.setBrush(QBrush(QColor(31, 95, 196, 70)))
        p.drawPolygon([P(11, 2), P(19, 7), P(11, 12), P(3, 7)])
        p.drawLine(P(3, 7), P(3, 15))
        p.drawLine(P(11, 12), P(11, 20))
        p.drawLine(P(19, 7), P(19, 15))
        p.drawLine(P(3, 15), P(11, 20))
        p.drawLine(P(19, 15), P(11, 20))
    elif name == "grid":
        p.setPen(_pen(QColor(120, 120, 130), 1.2))
        for i in range(4):
            p.drawLine(P(4 + i * 5, 3), P(4 + i * 5, 19))
            p.drawLine(P(3, 4 + i * 5), P(19, 4 + i * 5))
    elif name == "fit":
        p.setPen(_pen(INK, 1.7))
        p.setBrush(QBrush(QColor(255, 255, 255, 40)))
        p.drawEllipse(QRectF(P(3, 3), P(15, 15)))
        p.drawLine(P(13, 13), P(19, 19))
        p.drawLine(P(6, 9), P(12, 9))
        p.drawLine(P(9, 6), P(9, 12))
    elif name == "zoom_in":
        p.setPen(_pen(INK, 1.7))
        p.drawEllipse(QRectF(P(3, 3), P(15, 15)))
        p.drawLine(P(13, 13), P(19, 19))
        p.drawLine(P(6, 9), P(12, 9))
        p.drawLine(P(9, 6), P(9, 12))
    elif name == "zoom_out":
        p.setPen(_pen(INK, 1.7))
        p.drawEllipse(QRectF(P(3, 3), P(15, 15)))
        p.drawLine(P(13, 13), P(19, 19))
        p.drawLine(P(6, 9), P(12, 9))
    elif name == "mirror_h":
        p.setPen(_pen(ACCENT, 1.7))
        p.drawLine(P(11, 2), P(11, 20))
        p.setBrush(QBrush(QColor(31, 95, 196, 90)))
        p.drawPolygon([P(9, 5), P(2, 11), P(9, 17)])
        p.setBrush(QBrush(QColor(31, 95, 196, 40)))
        p.drawPolygon([P(13, 5), P(20, 11), P(13, 17)])
    elif name == "mirror_v":
        p.setPen(_pen(ACCENT, 1.7))
        p.drawLine(P(2, 11), P(20, 11))
        p.setBrush(QBrush(QColor(31, 95, 196, 90)))
        p.drawPolygon([P(5, 9), P(11, 2), P(17, 9)])
        p.setBrush(QBrush(QColor(31, 95, 196, 40)))
        p.drawPolygon([P(5, 13), P(11, 20), P(17, 13)])
    elif name == "rotate":
        p.setPen(_pen(ORANGE, 1.9))
        path = QPainterPath(P(18, 8))
        path.arcTo(QRectF(P(3, 3), P(19, 19)), 270, -230)
        p.drawPath(path)
        p.setBrush(QBrush(ORANGE))
        p.drawPolygon([P(18, 2), P(18, 9), P(13, 6)])
    elif name == "scale":
        p.setPen(_pen(INK, 1.7))
        p.drawRect(QRectF(P(3, 3), P(13, 13)))
        p.drawLine(P(13, 13), P(19, 19))
        p.drawLine(P(13, 19), P(19, 19))
        p.drawLine(P(19, 13), P(19, 19))
    elif name == "report":
        p.setPen(_pen(INK, 1.6))
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.drawRoundedRect(QRectF(P(5, 2), P(17, 20)), 1.5 * u, 1.5 * u)
        p.setPen(_pen(ACCENT, 1.7))
        p.drawLine(P(8, 7), P(14, 7))
        p.drawLine(P(8, 11), P(14, 11))
        p.drawLine(P(8, 15), P(11, 15))
    elif name == "props":
        p.setPen(_pen(INK, 1.7))
        p.drawRoundedRect(QRectF(P(3, 4), P(19, 8)), 2 * u, 2 * u)
        p.drawRoundedRect(QRectF(P(3, 13), P(19, 17)), 2 * u, 2 * u)
        p.setBrush(QBrush(ACCENT))
        p.drawEllipse(QRectF(P(6, 5), P(10, 9)))
        p.setBrush(QBrush(ORANGE))
        p.drawEllipse(QRectF(P(12, 14), P(16, 18)))
    elif name == "hoop":
        p.setPen(_pen(GREEN, 1.8))
        p.drawEllipse(QRectF(P(3, 3), P(19, 19)))
        p.setPen(_pen(QColor(150, 150, 160), 1.2))
        p.drawEllipse(QRectF(P(6, 6), P(16, 16)))
    elif name == "manual":
        p.setPen(_pen(INK, 1.6))
        p.setBrush(QBrush(QColor(255, 214, 102)))
        p.drawRoundedRect(QRectF(P(4, 2), P(18, 20)), 1.5 * u, 1.5 * u)
        p.drawLine(P(8, 2), P(8, 20))
        p.setPen(_pen(QColor(120, 100, 40), 1.3))
        p.drawLine(P(11, 7), P(15, 7))
        p.drawLine(P(11, 11), P(15, 11))
        p.drawLine(P(11, 15), P(15, 15))
    elif name == "run2":
        p.setPen(_pen(INK, 1.4))
        p.drawLine(P(3, 8), P(8, 8))
        p.drawLine(P(11, 8), P(16, 8))
        p.drawLine(P(6, 14), P(11, 14))
        p.drawLine(P(14, 14), P(19, 14))
    elif name == "zigzag":
        p.setPen(_pen(ACCENT, 1.8))
        path = QPainterPath(P(2, 15))
        x = 2
        up = True
        while x < 19:
            path.lineTo(P(x + 3, 8 if up else 15))
            x += 3
            up = not up
        p.drawPath(path)
    elif name == "scallop":
        p.setPen(_pen(ORANGE, 1.7))
        path = QPainterPath(P(2, 15))
        for i in range(4):
            x = 2 + i * 4.5
            path.cubicTo(P(x + 0.5, 5), P(x + 4, 5), P(x + 4.5, 15))
        p.drawPath(path)
    elif name == "spring":
        p.setPen(_pen(PURPLE, 1.6))
        for i in range(4):
            x = 3 + i * 4.5
            p.drawArc(QRectF(P(x, 6), P(x + 4.5, 16)), 0, 360 * 16)
    elif name == "motif_run":
        p.setPen(_pen(GREEN, 1.4))
        for i in range(4):
            x = 4 + i * 5
            p.drawEllipse(QRectF(P(x - 1.5, 9), P(x + 1.5, 13)))
    elif name == "fill_contour":
        p.setPen(_pen(ACCENT, 1.3))
        p.setBrush(Qt.NoBrush)
        for k in range(3):
            p.drawEllipse(QRectF(P(3 + k * 2.5, 3 + k * 2.5),
                                 P(19 - k * 2.5, 19 - k * 2.5)))
    elif name == "fill_radial":
        p.setPen(_pen(ORANGE, 1.4))
        import math as _m
        for i in range(12):
            a = 2 * _m.pi * i / 12
            p.drawLine(P(11, 11), P(11 + _m.cos(a) * 9, 11 + _m.sin(a) * 9))
    elif name == "fill_mesh":
        p.setPen(_pen(QColor(80, 130, 200), 1.2))
        for i in range(5):
            p.drawLine(P(3 + i * 4, 3), P(3 + i * 4, 19))
            p.drawLine(P(3, 3 + i * 4), P(19, 3 + i * 4))
    elif name == "fill_spiral":
        p.setPen(_pen(PURPLE, 1.5))
        path = QPainterPath(P(11, 11))
        import math as _m
        r = 0.5
        a = 0.0
        while r < 9.5:
            r += 0.45
            a += 0.9
            path.lineTo(P(11 + _m.cos(a) * r, 11 + _m.sin(a) * r))
        p.drawPath(path)
    elif name == "fill_brick":
        p.setPen(_pen(RED, 1.3))
        for row in range(3):
            y = 4 + row * 5.5
            off = 2.5 if row % 2 else 0
            for col in range(3):
                x = 2.5 + off + col * 6
                if x < 18:
                    p.drawLine(P(x, y), P(x + 5, y))
                    p.drawLine(P(x, y), P(x, y + 2.5))
    elif name == "fill_blend":
        p.setPen(_pen(INK, 1.3))
        p.setBrush(QBrush(QColor(214, 40, 40, 200)))
        path = QPainterPath(P(3, 3))
        path.lineTo(P(11, 3))
        path.cubicTo(P(8, 8), P(14, 12), P(11, 19))
        path.lineTo(P(3, 19))
        path.closeSubpath()
        p.drawPath(path)
        p.setBrush(QBrush(QColor(40, 100, 220, 200)))
        path2 = QPainterPath(P(11, 3))
        path2.lineTo(P(19, 3))
        path2.lineTo(P(19, 19))
        path2.lineTo(P(11, 19))
        path2.cubicTo(P(14, 12), P(8, 8), P(11, 3))
        p.drawPath(path2)
    elif name == "clipart":
        p.setPen(_pen(INK, 1.5))
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.drawRoundedRect(QRectF(P(2, 4), P(20, 18)), 2, 2)
        p.setBrush(QBrush(QColor(255, 214, 102)))
        p.drawEllipse(QRectF(P(6, 7), P(10, 11)))
        p.setPen(_pen(GREEN, 1.5))
        path = QPainterPath(P(4, 17))
        path.lineTo(P(9, 12))
        path.lineTo(P(13, 15))
        path.lineTo(P(16, 12))
        path.lineTo(P(18, 17))
        p.drawPath(path)
    elif name == "rulers":
        p.setPen(_pen(INK, 1.6))
        p.setBrush(QBrush(QColor(255, 214, 102, 160)))
        p.save()
        p.translate(11, 11)
        p.rotate(-45)
        p.drawRect(QRectF(P(-10, -3), P(10, 3)))
        p.setPen(_pen(INK, 1.1))
        for i in range(-9, 10, 3):
            p.drawLine(P(i, -3), P(i, 0))
        p.restore()
    elif name == "stitch_run":
        p.setPen(_pen(RED, 1.8))
        for i in range(4):
            x = 3 + i * 5
            p.drawLine(P(x, 11), P(x + 3, 11))
    elif name == "stitch_fill":
        p.setPen(_pen(GREEN, 1.4))
        for i in range(5):
            y = 5 + i * 3
            p.drawLine(P(4, y), P(18, y))
    elif name == "shape_heart":
        p.setPen(_pen(RED, 1.5))
        p.setBrush(QBrush(QColor(214, 40, 40, 110)))
        path = QPainterPath(P(11, 19))
        path.cubicTo(P(2, 12), P(3, 4), P(8, 4))
        path.cubicTo(P(10.5, 4), P(11, 7), P(11, 7))
        path.cubicTo(P(11, 7), P(11.5, 4), P(14, 4))
        path.cubicTo(P(19, 4), P(20, 12), P(11, 19))
        p.drawPath(path)
    elif name == "shape_star":
        p.setPen(_pen(QColor(200, 150, 20), 1.4))
        p.setBrush(QBrush(QColor(244, 211, 94, 150)))
        pts = []
        import math as _m
        for i in range(10):
            a = -_m.pi / 2 + _m.pi * i / 5
            k = 9.0 if i % 2 == 0 else 4.0
            pts.append(P(11 + _m.cos(a) * k, 11 + _m.sin(a) * k))
        p.drawPolygon(pts)
    elif name == "shape_diamond":
        p.setPen(_pen(ACCENT, 1.5))
        p.setBrush(QBrush(QColor(31, 95, 196, 80)))
        p.drawPolygon([P(11, 2), P(19, 11), P(11, 20), P(3, 11)])
    elif name == "shape_cross":
        p.setPen(_pen(GREEN, 1.5))
        p.setBrush(QBrush(QColor(43, 168, 74, 90)))
        p.drawPolygon([P(8, 3), P(14, 3), P(14, 8), P(19, 8), P(19, 14),
                       P(14, 14), P(14, 19), P(8, 19), P(8, 14), P(3, 14),
                       P(3, 8), P(8, 8)])
    elif name == "shape_triangle":
        p.setPen(_pen(ORANGE, 1.5))
        p.setBrush(QBrush(QColor(240, 140, 40, 100)))
        p.drawPolygon([P(11, 3), P(20, 19), P(2, 19)])
    elif name == "shape_hexagon":
        p.setPen(_pen(PURPLE, 1.5))
        p.setBrush(QBrush(QColor(140, 60, 190, 80)))
        import math as _m
        pts = []
        for i in range(6):
            a = -_m.pi / 2 + 2 * _m.pi * i / 6
            pts.append(P(11 + _m.cos(a) * 9, 11 + _m.sin(a) * 9))
        p.drawPolygon(pts)
    elif name == "scissors":
        p.setPen(_pen(INK, 1.6))
        p.drawEllipse(QRectF(P(3, 3), P(8, 8)))
        p.drawEllipse(QRectF(P(3, 14), P(8, 19)))
        p.drawLine(P(7, 7), P(19, 15))
        p.drawLine(P(7, 15), P(19, 7))
    elif name == "smooth":
        p.setPen(_pen(ACCENT, 2.0))
        path = QPainterPath(P(2, 14))
        path.cubicTo(P(6, 14), P(6, 6), P(11, 6))
        path.cubicTo(P(16, 6), P(16, 14), P(20, 14))
        p.drawPath(path)
        p.setPen(_pen(QColor(150, 150, 160), 1.2))
        p.drawPolygon([P(2, 17), P(6, 11), P(11, 11), P(15, 17)])
    elif name == "underlay":
        p.setPen(_pen(INK, 1.5))
        p.setBrush(QBrush(QColor(31, 95, 196, 60)))
        p.drawPolygon([P(11, 3), P(19, 8), P(11, 13), P(3, 8)])
        p.setBrush(QBrush(QColor(240, 140, 40, 90)))
        p.drawPolygon([P(11, 10), P(19, 15), P(11, 20), P(3, 15)])
    elif name == "stem":
        p.setPen(_pen(GREEN, 1.8))
        p.drawLine(P(11, 20), P(11, 6))
        p.setBrush(QBrush(GREEN))
        path = QPainterPath(P(11, 8))
        path.cubicTo(P(14, 2), P(19, 3), P(19, 3))
        path.cubicTo(P(19, 7), P(15, 9), P(11, 8))
        p.drawPath(path)
    elif name == "chain":
        p.setPen(_pen(INK, 1.5))
        p.setBrush(Qt.NoBrush)
        for i in range(3):
            p.drawEllipse(QRectF(P(3, 3 + i * 6), P(12, 11 + i * 6)))
        for i in range(2):
            p.drawEllipse(QRectF(P(10, 6 + i * 6), P(19, 14 + i * 6)))
    elif name == "backstitch":
        p.setPen(_pen(INK, 1.7))
        p.drawLine(P(3, 11), P(10, 11))
        p.drawLine(P(12, 11), P(19, 11))
        p.setBrush(QBrush(INK))
        p.drawPolygon([P(9, 7), P(14, 11), P(9, 15)])
    elif name == "applique":
        p.setPen(_pen(INK, 1.5))
        p.setBrush(QBrush(QColor(255, 214, 102, 120)))
        path = QPainterPath(P(6, 4))
        path.lineTo(P(9, 2.5))
        path.lineTo(P(13, 2.5))
        path.lineTo(P(16, 4))
        path.lineTo(P(18, 9))
        path.lineTo(P(15, 10))
        path.lineTo(P(15, 19))
        path.lineTo(P(7, 19))
        path.lineTo(P(7, 10))
        path.lineTo(P(4, 9))
        path.closeSubpath()
        p.drawPath(path)
    elif name == "crossstitch":
        p.setPen(_pen(RED, 1.9))
        p.drawLine(P(5, 5), P(17, 17))
        p.drawLine(P(17, 5), P(5, 17))
        p.setPen(_pen(QColor(180, 60, 60), 1.1))
        p.drawRect(QRectF(P(3, 3), P(19, 19)))
    elif name == "print":
        p.setPen(_pen(INK, 1.5))
        p.setBrush(QBrush(QColor(230, 230, 235)))
        p.drawRect(QRectF(P(5, 3), P(17, 8)))
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.drawRect(QRectF(P(3, 8), P(19, 15)))
        p.setBrush(QBrush(QColor(210, 210, 220)))
        p.drawRect(QRectF(P(6, 14), P(16, 20)))
        p.setPen(_pen(QColor(90, 90, 110), 1.1))
        p.drawLine(P(7, 17), P(15, 17))
    elif name == "cut":
        p.setPen(_pen(INK, 1.6))
        p.drawEllipse(QRectF(P(3, 14), P(8, 19)))
        p.drawEllipse(QRectF(P(14, 14), P(19, 19)))
        p.drawLine(P(7, 16), P(17, 5))
        p.drawLine(P(15, 16), P(5, 5))
    elif name == "copy":
        p.setPen(_pen(INK, 1.5))
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.drawRect(QRectF(P(4, 3), P(14, 15)))
        p.setBrush(QBrush(QColor(235, 235, 245)))
        p.drawRect(QRectF(P(8, 7), P(18, 19)))
    elif name == "paste":
        p.setPen(_pen(INK, 1.5))
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.drawRect(QRectF(P(4, 5), P(17, 19)))
        p.setBrush(QBrush(QColor(255, 214, 102)))
        p.drawRect(QRectF(P(8, 2), P(14, 7)))
        p.setPen(_pen(QColor(120, 120, 150), 1.1))
        p.drawLine(P(7, 11), P(14, 11))
        p.drawLine(P(7, 14), P(14, 14))
    elif name == "digitize":
        p.setPen(_pen(INK, 1.5))
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.drawRect(QRectF(P(3, 4), P(19, 17)))
        p.setPen(_pen(QColor(120, 170, 230), 1.3))
        path = QPainterPath(P(4, 15))
        path.cubicTo(P(8, 8), P(12, 12), P(18, 6))
        p.drawPath(path)
        p.setPen(_pen(RED, 1.7))
        p.drawEllipse(QRectF(P(12, 11), P(17, 16)))
        p.drawLine(P(17, 2), P(21, 6))
        p.drawLine(P(21, 6), P(20, 2))
    elif name == "sequin":
        p.setPen(_pen(QColor(180, 140, 20), 1.3))
        p.setBrush(QBrush(QColor(255, 214, 102, 170)))
        p.drawEllipse(QRectF(P(5, 5), P(17, 17)))
        p.setBrush(QBrush(QColor(255, 240, 180)))
        p.drawEllipse(QRectF(P(9, 8), P(13, 12)))
    elif name == "pentagon":
        p.setPen(_pen(ACCENT, 1.7))
        p.setBrush(QBrush(QColor(31, 95, 196, 60)))
        import math as _m
        pts = []
        for i in range(5):
            a = -_m.pi / 2 + 2 * _m.pi * i / 5
            pts.append(P(11 + _m.cos(a) * 8.6, 11 + _m.sin(a) * 8.6))
        p.drawPolygon(pts)
    elif name == "octagon":
        p.setPen(_pen(ACCENT, 1.7))
        p.setBrush(QBrush(QColor(31, 95, 196, 60)))
        import math as _m
        pts = []
        for i in range(8):
            a = -_m.pi / 2 - _m.pi / 8 + 2 * _m.pi * i / 8
            pts.append(P(11 + _m.cos(a) * 8.4, 11 + _m.sin(a) * 8.4))
        p.drawPolygon(pts)
    elif name == "arrow":
        p.setPen(_pen(INK, 1.6))
        p.setBrush(QBrush(QColor(255, 214, 102, 170)))
        p.drawPolygon([P(20, 11), P(9, 3), P(9, 7.5), P(3, 7.5),
                       P(3, 14.5), P(9, 14.5), P(9, 19)])
    elif name == "crescent":
        p.setPen(_pen(QColor(90, 90, 200), 1.7))
        p.setBrush(QBrush(QColor(150, 150, 230, 130)))
        path = QPainterPath(P(15, 3.2))
        path.arcTo(QRectF(P(3, 3), P(19, 19)), 60, 300)
        path2 = QPainterPath(P(15.5, 5.4))
        path2.arcTo(QRectF(P(7.4, 5), P(17.4, 17)), 78, 264)
        path.connectPath(path2)
        p.drawPath(path)
    elif name == "flower":
        p.setPen(_pen(RED, 1.5))
        p.setBrush(QBrush(QColor(255, 120, 140, 150)))
        import math as _m
        for i in range(6):
            a = 2 * _m.pi * i / 6
            cx0, cy0 = 11 + _m.cos(a) * 5.2, 11 + _m.sin(a) * 5.2
            p.drawEllipse(QRectF(P(cx0 - 3.6, cy0 - 3.6), P(cx0 + 3.6, cy0 + 3.6)))
        p.setBrush(QBrush(QColor(255, 214, 102)))
        p.drawEllipse(QRectF(P(7.5, 7.5), P(14.5, 14.5)))
    elif name == "cloud":
        p.setPen(_pen(QColor(120, 150, 210), 1.6))
        p.setBrush(QBrush(QColor(210, 225, 250, 200)))
        p.drawEllipse(QRectF(P(3, 10), P(12, 18)))
        p.drawEllipse(QRectF(P(8, 6), P(18, 15)))
        p.drawEllipse(QRectF(P(13, 10), P(20, 18)))
        p.drawRect(QRectF(P(5, 13), P(18, 17.6)))
    elif name == "arc":
        p.setPen(_pen(ACCENT, 2.0))
        path = QPainterPath(P(3, 17))
        path.cubicTo(P(5, 5), P(17, 5), P(19, 17))
        p.drawPath(path)
    elif name == "wave":
        p.setPen(_pen(QColor(40, 150, 200), 1.9))
        path = QPainterPath(P(2, 11))
        path.cubicTo(P(5, 3), P(8, 3), P(11, 11))
        path.cubicTo(P(14, 19), P(17, 19), P(20, 11))
        p.drawPath(path)
    elif name == "spiral":
        p.setPen(_pen(QColor(140, 80, 200), 1.8))
        path = QPainterPath(P(11, 11))
        import math as _m
        for i in range(1, 71):
            t = i / 70.0
            a = 2 * _m.pi * 2.4 * t
            r = 1.2 + 8.2 * t
            path.lineTo(P(11 + _m.cos(a) * r, 11 + _m.sin(a) * r))
        p.drawPath(path)
    elif name == "center":
        p.setPen(_pen(INK, 1.5))
        p.drawEllipse(QRectF(P(8.5, 8.5), P(13.5, 13.5)))
        p.drawLine(P(11, 2), P(11, 7))
        p.drawLine(P(11, 15), P(11, 20))
        p.drawLine(P(2, 11), P(7, 11))
        p.drawLine(P(15, 11), P(20, 11))
    elif name == "front":
        p.setPen(_pen(INK, 1.5))
        p.setBrush(QBrush(QColor(31, 95, 196, 60)))
        p.drawRect(QRectF(P(7, 3), P(17, 13)))
        p.setBrush(QBrush(QColor(255, 214, 102, 170)))
        p.drawRect(QRectF(P(4, 9), P(14, 19)))
        p.setPen(_pen(RED, 1.8))
        p.drawPolygon([P(11, 8), P(15, 14), P(7, 14)])
    elif name == "back":
        p.setPen(_pen(INK, 1.5))
        p.setBrush(QBrush(QColor(255, 214, 102, 170)))
        p.drawRect(QRectF(P(7, 3), P(17, 13)))
        p.setBrush(QBrush(QColor(31, 95, 196, 60)))
        p.drawRect(QRectF(P(4, 9), P(14, 19)))
        p.setPen(_pen(RED, 1.8))
        p.drawPolygon([P(11, 16), P(7, 10), P(15, 10)])
    else:  # fallback: quadrado colorido
        p.setPen(_pen(INK, 1.6))
        p.setBrush(QBrush(ACCENT))
        p.drawRoundedRect(QRectF(P(4, 4), P(18, 18)), 2 * u, 2 * u)


def icon(name: str, size: int = 22) -> QIcon:
    """Ícone nomeado (com cache)."""
    key = f"{name}@{size}"
    if key in _cache:
        return _cache[key]
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = _painter(pix)
    _draw(name, p, float(size))
    p.end()
    ico = QIcon(pix)
    _cache[key] = ico
    return ico


def thread_swatch(hex_color: int, size: int = 22, number: str | None = None) -> QIcon:
    """Ícone de amostra de cor (para a paleta inferior)."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = _painter(pix)
    col = QColor((hex_color >> 16) & 255, (hex_color >> 8) & 255, hex_color & 255)
    p.setPen(_pen(INK, 1.2))
    p.setBrush(QBrush(col))
    p.drawRoundedRect(QRectF(1, 1, size - 2, size - 2), 3, 3)
    if number:
        lum = 0.299 * col.red() + 0.587 * col.green() + 0.114 * col.blue()
        p.setPen(QColor(255, 255, 255) if lum < 140 else QColor(20, 20, 20))
        font = p.font()
        font.setPixelSize(int(size * 0.52))
        font.setBold(True)
        p.setFont(font)
        p.drawText(QRectF(1, 1, size - 2, size - 2), Qt.AlignCenter, number)
    p.end()
    return QIcon(pix)
