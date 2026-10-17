# -*- coding: utf-8 -*-
"""Gera o ícone do BordadoStudio (icone/BordadoStudio.ico + .png).

Desenhado do zero com QPainter: fundo azul arredondado, agulha dourada
diagonal, linha vermelha em curva e pontos de bordado brancos.

Rode:  python3 tests/make_icone.py   (precisa do ambiente .venv + stubs)
O .ico embute PNGs nos tamanhos 16/24/32/48/64/128/256.
"""

import os
import struct
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QIcon, QImage,
                           QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap)
from PySide6.QtWidgets import QApplication

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "icone")


def desenhar(tamanho: int = 256) -> QImage:
    img = QImage(tamanho, tamanho, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    u = tamanho / 256.0

    def P(x, y):
        return QPointF(x * u, y * u)

    # fundo: quadrado azul arredondado com leve brilho
    grad = QLinearGradient(P(0, 0), P(0, 256))
    grad.setColorAt(0.0, QColor(56, 132, 232))
    grad.setColorAt(0.55, QColor(36, 96, 200))
    grad.setColorAt(1.0, QColor(24, 64, 152))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(QRectF(P(8, 8), P(248, 248)), 48 * u, 48 * u)

    brilho = QLinearGradient(P(0, 10), P(0, 130))
    brilho.setColorAt(0.0, QColor(255, 255, 255, 70))
    brilho.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(QBrush(brilho))
    p.drawRoundedRect(QRectF(P(16, 16), P(240, 132)), 36 * u, 36 * u)

    # agulha dourada (diagonal, ponta para baixo-esquerda)
    p.save()
    p.translate(P(128, 128))
    p.rotate(-45)
    ouro = QColor(255, 210, 90)
    ouro_esc = QColor(196, 148, 32)
    p.setPen(QPen(ouro_esc, 3 * u))
    p.setBrush(QBrush(ouro))
    corpo = QPainterPath()
    corpo.moveTo(P(-4, -86))
    corpo.lineTo(P(4, -86))
    corpo.lineTo(P(4, 62))
    corpo.lineTo(P(0, 86))
    corpo.lineTo(P(-4, 62))
    corpo.closeSubpath()
    p.drawPath(corpo)
    # olho da agulha
    p.setBrush(QBrush(QColor(24, 64, 152)))
    p.setPen(QPen(ouro_esc, 2 * u))
    p.drawEllipse(QRectF(P(-2.6, -74), P(2.6, -58)))
    # brilho do metal
    p.setPen(QPen(QColor(255, 240, 190), 2 * u))
    p.drawLine(P(-1.5, -80), P(-1.5, 58))
    p.restore()

    # linha vermelha saindo do olho e formando um coração
    vermelho = QColor(230, 60, 60)
    p.setPen(QPen(vermelho, 11 * u, Qt.SolidLine, Qt.RoundCap))
    linha = QPainterPath(P(70, 70))
    linha.cubicTo(P(30, 40), P(28, 118), P(74, 128))
    linha.cubicTo(P(118, 138), P(120, 196), P(78, 214))
    linha.cubicTo(P(52, 224), P(40, 196), P(52, 182))
    p.drawPath(linha)

    # pontos de bordado brancos (traço costurado)
    p.setPen(QPen(QColor(255, 255, 255), 8 * u, Qt.SolidLine, Qt.RoundCap))
    for x, y in ((150, 60), (178, 78), (204, 100)):
        p.drawEllipse(P(x, y), 1.5 * u, 1.5 * u)
    pontos = QPainterPath(P(150, 60))
    pontos.cubicTo(P(176, 74), P(192, 84), P(206, 102))
    p.setPen(QPen(QColor(255, 255, 255), 7 * u, Qt.SolidLine, Qt.RoundCap))
    p.drawPath(pontos)

    # "B" discreto no canto inferior direito
    fonte = QFont("Segoe UI", int(64 * u))
    fonte.setBold(True)
    p.setFont(fonte)
    p.setPen(QPen(QColor(255, 255, 255, 220), 3 * u))
    p.drawText(QRectF(P(158, 158), P(236, 236)), Qt.AlignCenter, "B")

    p.end()
    return img


def fazer_ico(imagens):
    """imagens: [(tamanho, QImage)] → grava o .ico com PNGs embutidos."""
    import tempfile

    def png_bytes(img):
        tmp = os.path.join(tempfile.mkdtemp(), "x.png")
        img.save(tmp, "PNG")
        with open(tmp, "rb") as f:
            return f.read()

    blocos = []
    for tam, img in imagens:
        blocos.append((tam, png_bytes(img)))
    cab = struct.pack("<HHH", 0, 1, len(blocos))
    corpo = b""
    offset = 6 + 16 * len(blocos)
    for tam, dados in blocos:
        lado = 0 if tam >= 256 else tam
        cab += struct.pack("<BBBBHHII", lado, lado, 0, 0, 1, 32,
                           len(dados), offset)
        corpo += dados
        offset += len(dados)
    return cab + corpo


def main():
    app = QApplication.instance() or QApplication([])
    os.makedirs(SAIDA, exist_ok=True)
    tamanhos = (16, 24, 32, 48, 64, 128, 256)
    imagens = [(t, desenhar(t)) for t in tamanhos]
    ico = fazer_ico(imagens)
    caminho_ico = os.path.join(SAIDA, "BordadoStudio.ico")
    with open(caminho_ico, "wb") as f:
        f.write(ico)
    imagens[-1][1].save(os.path.join(SAIDA, "BordadoStudio.png"))
    print("ícone gravado em", caminho_ico, f"({len(ico)} bytes)")


if __name__ == "__main__":
    main()
