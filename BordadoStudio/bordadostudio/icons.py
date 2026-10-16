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
