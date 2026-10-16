"""Lista de objetos do desenho (ordem de costura)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def _color_icon(hex_color: int) -> QIcon:
    pix = QPixmap(14, 14)
    pix.fill(QColor((hex_color >> 16) & 255, (hex_color >> 8) & 255, hex_color & 255))
    return QIcon(pix)


class ObjectListPanel(QWidget):
    """Painel direito: lista de objetos na ordem de costura."""

    object_selected = Signal(str)

    def __init__(self, win):
        super().__init__()
        self.win = win
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(QLabel("Objetos (ordem de costura):"))
        self.list = QListWidget()
        self.list.currentItemChanged.connect(self._on_select)
        layout.addWidget(self.list, 1)

        row = QHBoxLayout()
        for label, slot, tip in (
            ("▲", self._move_up, "Mover para cima (costurar antes)"),
            ("▼", self._move_down, "Mover para baixo (costurar depois)"),
            ("Duplicar", self._duplicate, "Duplicar objeto"),
            ("Renomear", self._rename, "Renomear objeto"),
            ("Excluir", self._delete, "Excluir objeto"),
        ):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            row.addWidget(btn)
        layout.addLayout(row)

    # ---------------------------------------------------------- lista
    def rebuild(self):
        self._updating = True
        try:
            self.list.clear()
            for obj in self.win.doc.objects:
                item = QListWidgetItem(
                    _color_icon(obj.thread.hex_color),
                    f"{obj.name}  ({obj.stitch_count()} pts)"
                    + ("" if obj.visible else "  [oculto]"))
                item.setData(Qt.UserRole, obj.id)
                self.list.addItem(item)
                if obj.id == self.win.canvas.selected_id:
                    self.list.setCurrentItem(item)
        finally:
            self._updating = False

    def _on_select(self, current, _previous):
        if self._updating:
            return
        if current is not None:
            self.object_selected.emit(current.data(Qt.UserRole))

    def _current_obj(self):
        return self.win.canvas.selected_object()

    # ---------------------------------------------------------- botões
    def _move_up(self):
        obj = self._current_obj()
        if obj:
            self.win.doc.move_object(obj, -1)
            self.win.refresh_panels()

    def _move_down(self):
        obj = self._current_obj()
        if obj:
            self.win.doc.move_object(obj, +1)
            self.win.refresh_panels()

    def _duplicate(self):
        import copy
        obj = self._current_obj()
        if not obj:
            return
        self.win.doc.snapshot()
        clone = copy.deepcopy(obj)
        clone.id = __import__("uuid").uuid4().hex[:8]
        clone.name = obj.name + " (cópia)"
        clone.translate(40, 40)
        self.win.doc.add_object(clone, snapshot=False)
        self.win.canvas.rebuild()
        self.win.canvas.select(clone.id)
        self.win.refresh_panels()

    def _rename(self):
        obj = self._current_obj()
        if not obj:
            return
        text, ok = QInputDialog.getText(self, "Renomear", "Nome do objeto:",
                                        text=obj.name)
        if ok and text.strip():
            self.win.doc.snapshot()
            obj.name = text.strip()
            self.win.refresh_panels()

    def _delete(self):
        obj = self._current_obj()
        if not obj:
            return
        self.win.doc.remove_object(obj)
        self.win.canvas.rebuild()
        self.win.canvas.select("")
        self.win.refresh_panels()
