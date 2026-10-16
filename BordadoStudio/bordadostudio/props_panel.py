"""Painel de propriedades do objeto selecionado."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from .threads import PALETTES, ThreadColor

STITCH_TYPES = [
    ("fill", "Preenchimento (tatami)"),
    ("run", "Linha simples"),
    ("satin", "Bordado satin"),
    ("cross", "✝ Ponto cruz"),
    ("chain", "⛓ Cadeia (à mão)"),
    ("backstitch", "🪡 Ponto atrás (à mão)"),
    ("stem", "🌿 Ponto haste (à mão)"),
    ("sequin", "✨ Lantejoula"),
    ("motif_cross", "✦ Motivo cruz"),
    ("motif_star", "★ Motivo estrela"),
]

# rótulos dinâmicos por tipo de costura: (espaçamento, largura)
PARAM_LABELS = {
    "fill": ("Espaçamento:", "Largura (satin):"),
    "run": ("Espaçamento:", "Largura:"),
    "satin": ("Espaçamento:", "Largura do satin:"),
    "cross": ("Tamanho da célula:", "Largura:"),
    "chain": ("Tamanho do elo:", "Largura do elo:"),
    "backstitch": ("Passo:", "Largura:"),
    "stem": ("Passo:", "Largura da trança:"),
    "sequin": ("Distância:", "Tamanho da lantejoula:"),
    "motif_cross": ("Distância:", "Tamanho do motivo:"),
    "motif_star": ("Distância:", "Tamanho do motivo:"),
}


def _swatch_icon(hex_color: int) -> QIcon:
    pix = QPixmap(16, 16)
    pix.fill(QColor((hex_color >> 16) & 255, (hex_color >> 8) & 255, hex_color & 255))
    return QIcon(pix)


class PropertiesPanel(QWidget):
    """Propriedades do objeto selecionado (cor, costura, densidade...)."""

    def __init__(self, win):
        super().__init__()
        self.win = win
        self._obj = None
        self._loading = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)
        body = QWidget()
        scroll.setWidget(body)
        layout = QVBoxLayout(body)

        self.none_label = QLabel("Nenhum objeto selecionado.\n\n"
                                 "Use as ferramentas acima para desenhar, "
                                 "ou importe um arquivo de bordado.")
        self.none_label.setWordWrap(True)
        layout.addWidget(self.none_label)

        # ---- identificação
        self.box = QGroupBox("Objeto")
        form = QFormLayout(self.box)
        self.name_edit = QLineEdit()
        self.name_edit.editingFinished.connect(self._apply_name)
        form.addRow("Nome:", self.name_edit)

        self.kind_label = QLabel("-")
        form.addRow("Tipo:", self.kind_label)

        # ---- cor
        color_row = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(64, 24)
        self.color_btn.clicked.connect(self._pick_color)
        color_row.addWidget(self.color_btn)
        self.palette_combo = QComboBox()
        for palette_name, colors in PALETTES.items():
            self.palette_combo.addItem(palette_name)
            for c in colors:
                self.palette_combo.addItem(f"    {c.name}", c)
        self.palette_combo.currentIndexChanged.connect(self._palette_choice)
        color_row.addWidget(self.palette_combo, 1)
        form.addRow("Linha:", color_row)

        # ---- costura
        self.stitch_combo = QComboBox()
        for key, label in STITCH_TYPES:
            self.stitch_combo.addItem(label, key)
        self.stitch_combo.currentIndexChanged.connect(self._apply_stitch_type)
        form.addRow("Costura:", self.stitch_combo)

        self.spacing = QSlider(Qt.Horizontal)
        self.spacing.setRange(6, 60)          # 0,6 mm a 6 mm
        self.spacing.valueChanged.connect(self._apply_param("spacing"))
        self.spacing.sliderReleased.connect(self._commit)
        self.spacing_label = QLabel("-")
        self.spacing_name = QLabel("Espaçamento:")
        form.addRow(self.spacing_name, self._slider_row(self.spacing, self.spacing_label))

        self.angle = QDoubleSpinBox()
        self.angle.setRange(0, 180)
        self.angle.setSingleStep(15)
        self.angle.setSuffix("°")
        self.angle.valueChanged.connect(self._apply_param("angle"))
        form.addRow("Ângulo:", self.angle)

        self.stitch_len = QDoubleSpinBox()
        self.stitch_len.setRange(0.8, 10.0)
        self.stitch_len.setSingleStep(0.1)
        self.stitch_len.setSuffix(" mm")
        self.stitch_len.valueChanged.connect(self._apply_param("stitch_length", 10.0))
        form.addRow("Ponto:", self.stitch_len)

        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0.5, 50.0)
        self.width_spin.setSingleStep(0.5)
        self.width_spin.setSuffix(" mm")
        self.width_spin.valueChanged.connect(self._apply_param("width", 10.0))
        self.width_name = QLabel("Largura:")
        form.addRow(self.width_name, self.width_spin)

        self.density = QDoubleSpinBox()
        self.density.setRange(0.3, 10.0)
        self.density.setSingleStep(0.1)
        self.density.setSuffix(" mm")
        self.density.valueChanged.connect(self._apply_param("density", 10.0))
        form.addRow("Densidade (satin):", self.density)

        layout.addWidget(self.box)

        info = QLabel("Dica: arraste os quadradinhos brancos para ajustar "
                      "os pontos da forma. Ctrl+Z desfaz.")
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(info)
        layout.addStretch(1)

        self._set_enabled(False)

    # ---------------------------------------------------------- UI utils
    def _slider_row(self, slider, label):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(slider, 1)
        h.addWidget(label)
        return w

    def _set_enabled(self, on: bool):
        self.box.setVisible(on)
        self.none_label.setVisible(not on)

    # ---------------------------------------------------------- carga
    def load_object(self, obj):
        self._obj = obj
        self._loading = True
        try:
            if obj is None:
                self._set_enabled(False)
                return
            self._set_enabled(True)
            self.name_edit.setText(obj.name)
            kind_names = {
                "polygon": "Forma (preenchimento)",
                "freehand": "Linha desenhada",
                "rect": "Retângulo",
                "ellipse": "Elipse",
                "satin": "Coluna satin",
                "import": "Arquivo importado",
            }
            self.kind_label.setText(kind_names.get(obj.shape, obj.shape))
            self.color_btn.setIcon(_swatch_icon(obj.thread.hex_color))

            st = obj.params.get("stitch_type", "fill")
            idx = [k for k, _ in STITCH_TYPES].index(st) if st in dict(STITCH_TYPES) else 0
            self.stitch_combo.setCurrentIndex(idx)
            editable = obj.kind == "shape"
            self.stitch_combo.setEnabled(editable and obj.shape != "satin")

            sp_name, wd_name = PARAM_LABELS.get(st, ("Espaçamento:", "Largura:"))
            self.spacing_name.setText(sp_name)
            self.width_name.setText(wd_name)

            self.spacing.setValue(int(float(obj.params.get("spacing", 18))))
            self.spacing_label.setText(f"{self.spacing.value() / 10:.1f} mm")
            self.angle.setValue(float(obj.params.get("angle", 0)))
            self.stitch_len.setValue(float(obj.params.get("stitch_length", 25)) / 10.0)
            self.width_spin.setValue(float(obj.params.get("width", 40)) / 10.0)
            self.density.setValue(float(obj.params.get("density", 8)) / 10.0)

            for w in (self.spacing, self.angle, self.stitch_len,
                      self.width_spin, self.density):
                w.setEnabled(editable)
        finally:
            self._loading = False

    # ---------------------------------------------------------- ações
    def _apply_name(self):
        if self._loading or not self._obj:
            return
        text = self.name_edit.text().strip()
        if text and text != self._obj.name:
            self.win.doc.snapshot()
            self._obj.name = text
            self.win.refresh_panels()

    def _pick_color(self):
        if not self._obj:
            return
        initial = QColor((self._obj.thread.hex_color >> 16) & 255,
                         (self._obj.thread.hex_color >> 8) & 255,
                         self._obj.thread.hex_color & 255)
        color = QColorDialog.getColor(initial, self, "Escolher cor da linha")
        if color.isValid():
            self.win.doc.snapshot()
            self._obj.thread = ThreadColor(
                self._obj.thread.name if self._obj.thread.brand != "Personalizada"
                else "Personalizada",
                (color.red() << 16) | (color.green() << 8) | color.blue(),
                self._obj.thread.code, self._obj.thread.brand)
            self.win.refresh_panels()

    def _palette_choice(self, index):
        if self._loading or not self._obj:
            return
        data = self.palette_combo.itemData(index)
        if data is None:
            return
        self.win.doc.snapshot()
        self._obj.thread = ThreadColor(
            data.name, data.hex_color, data.code, data.brand)
        self.win.refresh_panels()

    def _apply_stitch_type(self):
        if self._loading or not self._obj or self._obj.kind != "shape":
            return
        key = self.stitch_combo.currentData()
        if key and key != self._obj.params.get("stitch_type"):
            self.win.doc.snapshot()
            self._obj.params["stitch_type"] = key
            sp_name, wd_name = PARAM_LABELS.get(key, ("Espaçamento:", "Largura:"))
            self.spacing_name.setText(sp_name)
            self.width_name.setText(wd_name)
            self._obj.recompile()
            self.win.refresh_panels()

    def _apply_param(self, name, scale=1.0):
        def handler(value):
            if self._loading or not self._obj or self._obj.kind != "shape":
                return
            self._obj.params[name] = float(value) / scale
            if name == "spacing":
                self.spacing_label.setText(f"{value / 10:.1f} mm")
            self._obj.recompile()
            self.win.canvas.refresh_object(self._obj)
            self.win.update_status()
        return handler

    def _commit(self):
        """Registra o snapshot ao soltar o slider (uma ação = um desfazer)."""
        if self._obj:
            self.win.doc.snapshot()
