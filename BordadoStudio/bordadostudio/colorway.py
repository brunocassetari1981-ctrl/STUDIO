"""Barra de cores inferior (estilo \"Colorway\" dos programas profissionais).

Mostra as cores do desenho e a paleta da linha; clicar aplica a cor
ao objeto selecionado.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from . import icons
from .threads import DEFAULT_PALETTE, ThreadColor, colors_of


class ColorBar(QFrame):
    """Faixa inferior com as cores: [Colorway 1] [1][2][3]… | paleta."""

    color_picked = Signal(object)   # ThreadColor

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ColorBar")
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            "#ColorBar { background: #dcdcdc; border-top: 1px solid #b5b5b5; }"
            "QLabel#ColorwayName { font-weight: bold; padding: 0 8px;"
            " color: #333; background: #cfd8e8; border: 1px solid #a7b4cc;"
            " border-radius: 3px; }"
            "QToolButton { border: 1px solid transparent; border-radius: 3px;"
            " padding: 1px; }"
            "QToolButton:hover { border-color: #7a9ccc; }"
            "QToolButton:pressed { background: #b5c8e8; }"
        )
        outer = QHBoxLayout(self)
        outer.setContentsMargins(4, 3, 4, 3)
        outer.setSpacing(6)

        self.name_label = QLabel("Colorway 1")
        self.name_label.setObjectName("ColorwayName")
        outer.addWidget(self.name_label)

        self.count_label = QLabel("0 cores")
        self.count_label.setStyleSheet("color: #555; font-size: 11px;")
        outer.addWidget(self.count_label)

        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setStyleSheet("color: #aaa;")
        outer.addWidget(line)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFixedHeight(34)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(self._scroll, 1)

        self._inner = QWidget()
        self._row = QHBoxLayout(self._inner)
        self._row.setContentsMargins(2, 0, 2, 0)
        self._row.setSpacing(3)
        self._row.addStretch(1)
        self._scroll.setWidget(self._inner)

        self._buttons: list[QToolButton] = []
        self._threads: list[ThreadColor] = []

    # ---------------------------------------------------------- conteúdo
    def rebuild(self, doc_threads: list[ThreadColor]):
        """Recria as amostras: primeiro as cores do desenho, depois a paleta."""
        while self._row.count():
            item = self._row.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._buttons.clear()
        self._threads = []

        seen: set[int] = set()
        seq: list[ThreadColor] = []
        for t in doc_threads:
            if t.hex_color not in seen:
                seen.add(t.hex_color)
                seq.append(t)
        for t in colors_of(DEFAULT_PALETTE):
            if t.hex_color not in seen:
                seen.add(t.hex_color)
                seq.append(t)

        for i, thread in enumerate(seq):
            btn = QToolButton()
            btn.setIcon(icons.thread_swatch(thread.hex_color, 24, str(i + 1)))
            btn.setIconSize(QSize(24, 24))
            btn.setFixedSize(30, 28)
            btn.setToolTip(f"{thread.name} (#{thread.hex_color:06X})")
            btn.clicked.connect(lambda _c=False, t=thread: self.color_picked.emit(t))
            self._row.addWidget(btn)
            self._buttons.append(btn)
            self._threads.append(thread)
        self._row.addStretch(1)

        n = len({t.hex_color for t in doc_threads})
        self.count_label.setText(f"{n} no desenho · {len(seq)} na paleta")

    def threads(self) -> list[ThreadColor]:
        return list(self._threads)
