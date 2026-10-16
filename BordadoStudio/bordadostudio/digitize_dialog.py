"""Diálogo de auto-digitização: foto/imagem → bordado."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from . import digitize


class DigitizeDialog(QDialog):
    """Escolhe a imagem, ajusta o limiar e vê o resultado antes de inserir."""

    def __init__(self, path: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Digitalizar imagem (auto-digitização)")
        self.resize(760, 580)
        self._shapes: list = []
        self._base: QImage | None = None

        lay = QVBoxLayout(self)

        linha = QHBoxLayout()
        linha.addWidget(QLabel("Imagem:"))
        self.path_edit = QLineEdit(path)
        self.path_edit.setReadOnly(True)
        linha.addWidget(self.path_edit, 1)
        btn_procurar = QPushButton("Procurar...")
        btn_procurar.clicked.connect(self._procurar)
        linha.addWidget(btn_procurar)
        lay.addLayout(linha)

        corpo = QHBoxLayout()
        self.preview = QLabel("Escolha uma imagem para digitalizar.")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(420, 340)
        self.preview.setFrameShape(QLabel.StyledPanel)
        self.preview.setStyleSheet("background: #2b2b2b; color: #ddd;")
        corpo.addWidget(self.preview, 1)

        form = QFormLayout()
        self.limiar = QSlider(Qt.Horizontal)
        self.limiar.setRange(0, 255)
        self.limiar.setValue(128)
        self.limiar.valueChanged.connect(self._rebuild)
        form.addRow("Limiar:", self.limiar)
        self.inverter = QCheckBox("Inverter (forma clara)")
        self.inverter.toggled.connect(self._rebuild)
        form.addRow("", self.inverter)
        self.suavizar = QDoubleSpinBox()
        self.suavizar.setRange(0.0, 20.0)
        self.suavizar.setDecimals(1)
        self.suavizar.setValue(2.0)
        self.suavizar.setSuffix(" px")
        self.suavizar.valueChanged.connect(self._rebuild)
        form.addRow("Suavização:", self.suavizar)
        self.area_min = QSpinBox()
        self.area_min.setRange(4, 20000)
        self.area_min.setValue(60)
        self.area_min.setSuffix(" px²")
        self.area_min.valueChanged.connect(self._rebuild)
        form.addRow("Área mínima:", self.area_min)
        self.largura = QDoubleSpinBox()
        self.largura.setRange(10.0, 500.0)
        self.largura.setValue(100.0)
        self.largura.setSuffix(" mm")
        form.addRow("Largura do bordado:", self.largura)
        self.modo = QComboBox()
        self.modo.addItems(["Preenchimento (tatami)", "Contorno (linha dupla)"])
        form.addRow("Modo:", self.modo)
        self.usar_cores = QCheckBox("Usar as cores da imagem")
        self.usar_cores.setChecked(True)
        form.addRow("", self.usar_cores)
        self.info = QLabel("")
        self.info.setWordWrap(True)
        form.addRow("", self.info)
        caixa = QWidget()
        caixa.setLayout(form)
        corpo.addWidget(caixa)
        lay.addLayout(corpo, 1)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Inserir no desenho")
        bb.button(QDialogButtonBox.Cancel).setText("Cancelar")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

        self._ok_btn = bb.button(QDialogButtonBox.Ok)
        self._ok_btn.setEnabled(False)
        if path:
            self._rebuild()

    # ---------------------------------------------------------- ações
    def _procurar(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Escolher imagem", "",
            "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        if caminho:
            self.path_edit.setText(caminho)
            self._rebuild()

    def _rebuild(self, *_):
        caminho = self.path_edit.text().strip()
        if not caminho:
            return
        try:
            w, h, formas = digitize.trace_image(
                caminho,
                limiar=self.limiar.value(),
                inverter=self.inverter.isChecked(),
                suavizar=self.suavizar.value(),
                min_area=self.area_min.value())
        except Exception as e:  # imagem inválida
            self._shapes = []
            self._base = None
            self.preview.setText(f"Erro: {e}")
            self._ok_btn.setEnabled(False)
            return
        self._shapes = formas
        self._base = QImage(caminho)
        if max(w, h) > 0 and not self._base.isNull():
            if max(self._base.width(), self._base.height()) != max(w, h):
                self._base = self._base.scaled(
                    w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        n = len(formas)
        self.info.setText(
            f"{n} forma(s) encontrada(s)." if n else
            "Nenhuma forma encontrada — ajuste o limiar.")
        self._ok_btn.setEnabled(n > 0)
        self._draw_preview()

    def _draw_preview(self):
        if self._base is None or self._base.isNull():
            return
        img = self._base.copy()
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        for i, f in enumerate(self._shapes):
            pts = f["points_px"]
            pen = QPen(QColor(255, 200, 40), 1)
            p.setPen(pen)
            for j in range(len(pts)):
                x1, y1 = pts[j]
                x2, y2 = pts[(j + 1) % len(pts)]
                p.drawLine(int(x1), int(y1), int(x2), int(y2))
        p.end()
        self._preview_img = img
        self._fit_preview()

    def _fit_preview(self):
        img = getattr(self, "_preview_img", None)
        if img is None or img.isNull():
            return
        self.preview.setPixmap(QPixmap.fromImage(img).scaled(
            self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_preview()

    # ---------------------------------------------------------- resultado
    def result_shapes(self):
        """Formas em coordenadas de pixels da imagem de trabalho."""
        return list(self._shapes)

    def result_options(self):
        return {
            "largura_mm": self.largura.value(),
            "preencher": self.modo.currentIndex() == 0,
            "usar_cores": self.usar_cores.isChecked(),
        }
