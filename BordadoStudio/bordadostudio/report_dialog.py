"""Diálogo do relatório de produção (com recálculo ao vivo e exportação .txt)."""

from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from . import report


class ReportDialog(QDialog):
    """Mostra o relatório de produção do desenho atual."""

    def __init__(self, doc, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.setWindowTitle("Relatório de produção — BordadoStudio")
        self.resize(640, 640)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.speed = QDoubleSpinBox()
        self.speed.setRange(50.0, 2000.0)
        self.speed.setValue(report.DEFAULT_SPEED)
        self.speed.setSuffix(" pontos/min")
        self.speed.valueChanged.connect(self.refresh)
        form.addRow("Velocidade da máquina:", self.speed)

        self.hourly = QDoubleSpinBox()
        self.hourly.setRange(0.0, 10000.0)
        self.hourly.setPrefix("R$ ")
        self.hourly.valueChanged.connect(self.refresh)
        form.addRow("Valor da hora:", self.hourly)

        self.per_color = QDoubleSpinBox()
        self.per_color.setRange(0.0, 1000.0)
        self.per_color.setPrefix("R$ ")
        self.per_color.valueChanged.connect(self.refresh)
        form.addRow("Por troca de cor:", self.per_color)
        layout.addLayout(form)

        hint = QLabel("Deixe os valores em R$ 0 para ocultar o custo.")
        hint.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(hint)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setFontFamily("Consolas")
        layout.addWidget(self.text, 1)

        row = QHBoxLayout()
        save = QPushButton("Salvar relatório (.txt)...")
        save.clicked.connect(self.save)
        row.addWidget(save)
        row.addStretch(1)
        close = QPushButton("Fechar")
        close.clicked.connect(self.accept)
        row.addWidget(close)
        layout.addLayout(row)

        self.refresh()

    def refresh(self, *_):
        data = report.build_report(
            self.doc,
            speed=self.speed.value(),
            hourly_rate=self.hourly.value(),
            per_color=self.per_color.value())
        self.text.setPlainText(report.format_report(data))

    def save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar relatório", "relatorio_bordado.txt",
            "Texto (*.txt)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text.toPlainText())
        except OSError as e:
            QMessageBox.critical(self, "Erro ao salvar", str(e))
            return
        QMessageBox.information(self, "Relatório",
                                f"Relatório salvo em:\n{path}")
