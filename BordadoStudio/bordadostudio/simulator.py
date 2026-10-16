"""Simulação animada da costura — ver como a máquina vai bordar."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from . import stitcher


def flatten_stitches(doc):
    """Achata o desenho em segmentos [(x1,y1,x2,y2,cor)]."""
    segments = []
    for obj in doc.objects:
        if not obj.visible:
            continue
        prev = None
        cores = [obj.thread.hex_color]
        blend_hex = (obj.params or {}).get("blend_color")
        cores.append(blend_hex if blend_hex else (obj.thread.hex_color >> 1) & 0x7F7F7F)
        idx = 0

        def _qc(hx):
            return QColor((hx >> 16) & 255, (hx >> 8) & 255, hx & 255)

        color = _qc(cores[0])
        for x, y, c in obj.stitches:
            if c == stitcher.COLOR_CHANGE:
                # marca de mistura: passa a desenhar com a outra cor
                idx = 1 - idx
                color = _qc(cores[idx])
                if prev is not None:
                    segments.append((prev[0], prev[1], x, y, color))
                prev = (x, y)
                continue
            if c == stitcher.STITCH and prev is not None:
                segments.append((prev[0], prev[1], x, y, color))
            prev = (x, y)
    return segments


class SimScene(QGraphicsScene):
    def __init__(self, doc):
        super().__init__()
        self.doc = doc
        self.segments = flatten_stitches(doc)
        self.progress = 0
        b = doc.bounds()
        self.setSceneRect(QRectF(b[0] - 50, b[1] - 50,
                                 max(100, b[2] - b[0] + 100),
                                 max(100, b[3] - b[1] + 100)))

    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.fillRect(rect, QColor(35, 35, 35))
        hoop_pen = QPen(QColor(120, 160, 200), 1.4)
        hoop_pen.setCosmetic(True)
        painter.setPen(hoop_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRectF(0, 0, self.doc.hoop[0], self.doc.hoop[1]))

    def drawForeground(self, painter: QPainter, rect: QRectF):
        n = min(self.progress, len(self.segments))
        last = None
        for i in range(n):
            x1, y1, x2, y2, color = self.segments[i]
            painter.setPen(QPen(color, 1.3))
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            last = (x2, y2)
        if last is not None and n < len(self.segments):
            # posição da agulha
            painter.setPen(QPen(QColor(255, 255, 255), 1.2))
            x, y = last
            painter.drawLine(QPointF(x - 25, y), QPointF(x + 25, y))
            painter.drawLine(QPointF(x, y - 25), QPointF(x, y + 25))


class SimulatorDialog(QDialog):
    """Janela de simulação com play/pause e velocidade."""

    def __init__(self, doc, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Simulação de costura — BordadoStudio")
        self.resize(860, 640)

        layout = QVBoxLayout(self)
        self.scene = SimScene(doc)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        layout.addWidget(self.view, 1)

        controls = QHBoxLayout()
        self.play_btn = QPushButton("▶  Iniciar")
        self.play_btn.clicked.connect(self.toggle)
        controls.addWidget(self.play_btn)

        restart = QPushButton("⏮  Reiniciar")
        restart.clicked.connect(self.restart)
        controls.addWidget(restart)

        controls.addWidget(QLabel("Velocidade:"))
        self.speed = QSlider(Qt.Horizontal)
        self.speed.setRange(1, 400)
        self.speed.setValue(60)
        controls.addWidget(self.speed, 1)

        self.info = QLabel("")
        controls.addWidget(self.info)
        layout.addLayout(controls)

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)
        self._update_info()

    def toggle(self):
        if self.timer.isActive():
            self.timer.stop()
            self.play_btn.setText("▶  Continuar")
        else:
            if self.scene.progress >= len(self.scene.segments):
                self.scene.progress = 0
            self.timer.start()
            self.play_btn.setText("⏸  Pausar")

    def restart(self):
        self.scene.progress = 0
        self.scene.update()
        self._update_info()

    def _tick(self):
        self.scene.progress += self.speed.value()
        self.scene.update()
        self._update_info()
        if self.scene.progress >= len(self.scene.segments):
            self.timer.stop()
            self.play_btn.setText("▶  Reiniciar")

    def _update_info(self):
        total = len(self.scene.segments)
        done = min(self.scene.progress, total)
        self.info.setText(f"Pontos: {done} / {total}")

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)
