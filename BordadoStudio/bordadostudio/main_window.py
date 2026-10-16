"""Janela principal do BordadoStudio: menus, barra de ferramentas, diálogos."""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME, __version__, formats_io
from .canvas import EditorCanvas
from .model import Document
from .object_list import ObjectListPanel
from .props_panel import PropertiesPanel
from .simulator import SimulatorDialog
from .threads import ThreadColor

TOOLS = [
    ("select", "Selecionar", "Selecionar, mover e ajustar pontos (S)", "S"),
    ("polygon", "Preenchimento", "Desenhar forma com preenchimento — clique nos pontos, duplo-clique termina (P)", "P"),
    ("freehand", "Linha", "Desenhar linha livre à mão (L)", "L"),
    ("rect", "Retângulo", "Arrastar para criar retângulo (R)", "R"),
    ("ellipse", "Elipse", "Arrastar para criar elipse (E)", "E"),
    ("satin", "Satin", "Desenhar coluna satin — clique no centro, duplo-clique termina (B)", "B"),
]


def _icon_from_text(text: str) -> QIcon:
    pix = QPixmap(24, 24)
    pix.fill(Qt.transparent)
    return QIcon(pix)


class ProjectDialog(QDialog):
    """Propriedades do desenho (título e área de bordado)."""

    def __init__(self, doc, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Propriedades do desenho")
        form = QFormLayout(self)
        self.title_edit = QLineEdit(doc.title)
        form.addRow("Título:", self.title_edit)
        self.w_spin = QDoubleSpinBox()
        self.w_spin.setRange(5.0, 200.0)
        self.w_spin.setValue(doc.hoop[0] / 10.0)
        self.w_spin.setSuffix(" mm")
        self.h_spin = QDoubleSpinBox()
        self.h_spin.setRange(5.0, 200.0)
        self.h_spin.setValue(doc.hoop[1] / 10.0)
        self.h_spin.setSuffix(" mm")
        form.addRow("Largura da área:", self.w_spin)
        form.addRow("Altura da área:", self.h_spin)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.doc = Document()
        self.path: str | None = None
        self.canvas = EditorCanvas(self.doc)
        self.setCentralWidget(self.canvas.view)
        self.setWindowTitle(self._title())
        self.setWindowIcon(self._app_icon())

        self.props = PropertiesPanel(self)
        self.obj_list = ObjectListPanel(self)

        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.addWidget(self.props)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._dock("Propriedades", left))

        self.addDockWidget(Qt.RightDockWidgetArea,
                           self._dock("Objetos", self.obj_list))

        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self._build_status()

        self.canvas.object_selected.connect(self._on_selection)
        self.canvas.document_changed.connect(self._on_doc_changed)
        self.canvas.cursor_moved.connect(self._on_cursor)
        self.obj_list.object_selected.connect(self.canvas.select)

        self.canvas.fit_view()
        self._on_doc_changed()

    # ---------------------------------------------------------- chrome
    def _dock(self, title, widget):
        from PySide6.QtWidgets import QDockWidget
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        return dock

    def _app_icon(self) -> QIcon:
        pix = QPixmap(32, 32)
        pix.fill(QColor(31, 95, 196))
        return QIcon(pix)

    def _title(self):
        name = os.path.basename(self.path) if self.path else "Sem título"
        return f"{name} — {APP_NAME} {__version__}"

    def _build_status(self):
        self.status_coords = QLabel("0,0 mm")
        self.status_zoom = QLabel("100%")
        self.status_info = QLabel("0 objetos | 0 pontos")
        sb = self.statusBar()
        sb.addWidget(self.status_coords, 1)
        sb.addPermanentWidget(self.status_zoom)
        sb.addPermanentWidget(self.status_info)

    def _build_actions(self):
        self.act_new = QAction("Novo", self, shortcut=QKeySequence.New,
                               triggered=self.file_new)
        self.act_open = QAction("Abrir projeto...", self, shortcut=QKeySequence.Open,
                                triggered=self.file_open)
        self.act_save = QAction("Salvar", self, shortcut=QKeySequence.Save,
                                triggered=self.file_save)
        self.act_save_as = QAction("Salvar como...", self,
                                   shortcut=QKeySequence("Ctrl+Shift+S"),
                                   triggered=self.file_save_as)
        self.act_import = QAction("Importar arquivo de bordado...", self,
                                  shortcut=QKeySequence("Ctrl+I"),
                                  triggered=self.file_import)
        self.act_export = QAction("Exportar para máquina...", self,
                                  shortcut=QKeySequence("Ctrl+E"),
                                  triggered=self.file_export)
        self.act_quit = QAction("Sair", self, shortcut=QKeySequence.Quit,
                                triggered=self.close)

        self.act_undo = QAction("Desfazer", self, shortcut=QKeySequence.Undo,
                                triggered=self.edit_undo)
        self.act_redo = QAction("Refazer", self, shortcut=QKeySequence.Redo,
                                triggered=self.edit_redo)
        self.act_delete = QAction("Excluir objeto", self,
                                  shortcut=QKeySequence.Delete,
                                  triggered=self.obj_list._delete)
        self.act_select_all = QAction("Selecionar tudo", self,
                                      shortcut=QKeySequence.SelectAll,
                                      triggered=self.edit_select_all)

        self.act_simulate = QAction("Simular costura", self,
                                    shortcut=QKeySequence("F5"),
                                    triggered=self.view_simulate)
        self.act_fit = QAction("Ajustar zoom ao desenho", self,
                               shortcut=QKeySequence("Ctrl+0"),
                               triggered=self.canvas.fit_view)
        self.act_grid = QAction("Mostrar grade", self, checkable=True,
                                checked=True, triggered=self.view_grid)

        self.act_props = QAction("Propriedades do desenho...", self,
                                 triggered=self.file_properties)
        self.act_efeitos = QAction("Ver exemplo de efeitos...", self,
                                   triggered=self.help_efeitos)
        self.act_about = QAction("Sobre o BordadoStudio", self,
                                 triggered=self.help_about)
        self.act_manual = QAction("Manual rápido", self,
                                  shortcut=QKeySequence("F1"),
                                  triggered=self.help_manual)

    def _build_menus(self):
        m = self.menuBar()
        file_m = m.addMenu("&Arquivo")
        for a in (self.act_new, self.act_open, self.act_save, self.act_save_as):
            file_m.addAction(a)
        file_m.addSeparator()
        file_m.addAction(self.act_import)
        file_m.addAction(self.act_export)
        file_m.addSeparator()
        file_m.addAction(self.act_props)
        file_m.addSeparator()
        file_m.addAction(self.act_quit)

        edit_m = m.addMenu("&Editar")
        for a in (self.act_undo, self.act_redo):
            edit_m.addAction(a)
        edit_m.addSeparator()
        for a in (self.act_delete, self.act_select_all):
            edit_m.addAction(a)

        view_m = m.addMenu("&Ver")
        view_m.addAction(self.act_simulate)
        view_m.addAction(self.act_fit)
        view_m.addSeparator()
        view_m.addAction(self.act_grid)

        help_m = m.addMenu("Aju&da")
        help_m.addAction(self.act_efeitos)
        help_m.addSeparator()
        help_m.addAction(self.act_manual)
        help_m.addAction(self.act_about)

    def _build_toolbar(self):
        tb = QToolBar("Ferramentas")
        tb.setMovable(False)
        self.addToolBar(tb)
        self._tool_actions = {}
        for key, label, tip, letter in TOOLS:
            act = QAction(label, self, checkable=True, toolTip=tip,
                          triggered=lambda _c=False, k=key: self.canvas.set_tool(k))
            act.setShortcut(QKeySequence(letter))
            act.setShortcutContext(Qt.ApplicationShortcut)
            tb.addAction(act)
            self._tool_actions[key] = act
        self._tool_actions["select"].setChecked(True)
        tb.addSeparator()
        tb.addAction(self.act_undo)
        tb.addAction(self.act_redo)
        tb.addSeparator()
        tb.addAction(self.act_simulate)
        tb.addAction(self.act_export)
        self.canvas.tool_changed.connect(self._on_tool_changed)

    # ---------------------------------------------------------- callbacks
    def _on_tool_changed(self, tool):
        for key, act in self._tool_actions.items():
            act.setChecked(key == tool)

    def _on_selection(self, obj_id):
        self.props.load_object(self.canvas.selected_object())
        self.obj_list.rebuild()

    def _on_doc_changed(self):
        self.update_status()
        self.act_undo.setEnabled(self.doc.can_undo())
        self.act_redo.setEnabled(self.doc.can_redo())

    def _on_cursor(self, x, y):
        self.status_coords.setText(f"{x:.1f}, {y:.1f} mm")

    def update_status(self):
        n = len(self.doc.objects)
        pts = self.doc.total_stitches()
        self.status_info.setText(f"{n} objetos | {pts} pontos")
        self.status_zoom.setText(
            f"{self.canvas.view.transform().m11() * 100:.0f}%")
        self._on_doc_changed_quiet()

    def _on_doc_changed_quiet(self):
        self.act_undo.setEnabled(self.doc.can_undo())
        self.act_redo.setEnabled(self.doc.can_redo())

    def refresh_panels(self):
        self.canvas.refresh_all()
        self.obj_list.rebuild()
        self.props.load_object(self.canvas.selected_object())
        self.update_status()

    # ---------------------------------------------------------- arquivo
    def _confirm_discard(self):
        if not self.doc.modified:
            return True
        r = QMessageBox.question(
            self, "Alterações não salvas",
            "O desenho tem alterações não salvas. Continuar mesmo assim?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if r == QMessageBox.Save:
            return self.file_save()
        return r == QMessageBox.Discard

    def file_new(self):
        if not self._confirm_discard():
            return
        self.doc = Document()
        self.canvas.doc = self.doc
        self.path = None
        self.canvas.rebuild()
        self.canvas.select("")
        self.refresh_panels()
        self.setWindowTitle(self._title())
        self.canvas.fit_view()

    def file_open(self):
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir projeto", "", f"{APP_NAME} (*.bds)")
        if not path:
            return
        try:
            self.doc = Document.load_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao abrir", str(e))
            return
        self.path = path
        self.canvas.doc = self.doc
        self.canvas.rebuild()
        self.canvas.select("")
        self.refresh_panels()
        self.setWindowTitle(self._title())
        self.canvas.fit_view()

    def file_save(self):
        if not self.path:
            return self.file_save_as()
        try:
            self.doc.save_file(self.path)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", str(e))
            return False
        self.statusBar().showMessage("Projeto salvo.", 4000)
        return True

    def file_save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar projeto", f"{self.doc.title}.bds",
            f"{APP_NAME} (*.bds)")
        if not path:
            return False
        if not path.endswith(".bds"):
            path += ".bds"
        self.path = path
        self.setWindowTitle(self._title())
        return self.file_save()

    def file_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar arquivo de bordado", "",
            formats_io.import_filter_string())
        if not path:
            return
        try:
            objects = formats_io.import_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao importar", str(e))
            return
        if not objects:
            QMessageBox.warning(self, "Importar",
                                "Nenhum ponto encontrado no arquivo.")
            return
        self.doc.snapshot()
        for obj in objects:
            self.doc.add_object(obj, snapshot=False)
        self.canvas.rebuild()
        self.canvas.select(objects[0].id)
        self.refresh_panels()
        self.canvas.fit_view()
        self.statusBar().showMessage(
            f"Importado: {os.path.basename(path)} ({len(objects)} objeto(s)).", 5000)

    def file_export(self):
        path, selected = QFileDialog.getSaveFileName(
            self, "Exportar para máquina", f"{self.doc.title}.dst",
            formats_io.export_filter_string())
        if not path:
            return
        ext = os.path.splitext(path)[1].lstrip(".").lower()
        if not ext:
            # extensão vem do filtro escolhido
            for e, desc in formats_io.EXPORT_FORMATS:
                if desc.split("(")[0].strip() in selected or f".{e}" in selected:
                    ext = e
                    path += f".{e}"
                    break
            if not ext:
                ext = "dst"
                path += ".dst"
        try:
            n = formats_io.export_document(self.doc, path, ext)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao exportar", str(e))
            return
        QMessageBox.information(
            self, "Exportar",
            f"Exportado com sucesso!\n\n{os.path.basename(path)}\n"
            f"{n} pontos de costura.\n\n"
            "O arquivo já pode ser copiado para o pendrive da sua máquina.")

    def file_properties(self):
        dlg = ProjectDialog(self.doc, self)
        if dlg.exec() == QDialog.Accepted:
            self.doc.snapshot()
            self.doc.title = dlg.title_edit.text().strip() or "Sem título"
            self.doc.hoop = [dlg.w_spin.value() * 10, dlg.h_spin.value() * 10]
            self.canvas.update()
            self.update_status()

    # ---------------------------------------------------------- editar
    def edit_undo(self):
        if self.doc.undo():
            self.canvas.rebuild()
            self.canvas.select("")
            self.refresh_panels()

    def edit_redo(self):
        if self.doc.redo():
            self.canvas.rebuild()
            self.canvas.select("")
            self.refresh_panels()

    def edit_select_all(self):
        if self.doc.objects:
            self.canvas.select(self.doc.objects[-1].id)

    # ---------------------------------------------------------- ver
    def view_simulate(self):
        if not self.doc.objects:
            QMessageBox.information(self, "Simular",
                                    "Desenhe ou importe algo antes de simular.")
            return
        dlg = SimulatorDialog(self.doc, self)
        dlg.exec()

    def view_grid(self, on):
        self.canvas.show_grid = on
        self.canvas.update()

    # ---------------------------------------------------------- ajuda
    def help_efeitos(self):
        """Abre o projeto de exemplo com os 10 tipos de costura."""
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, "exemplos", "efeitos.bds")
        if not os.path.exists(path):
            QMessageBox.warning(
                self, "Exemplo",
                f"Arquivo de exemplo não encontrado:\n{path}")
            return
        try:
            self.doc = Document.load_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao abrir", str(e))
            return
        self.path = path
        self.canvas.doc = self.doc
        self.canvas.rebuild()
        self.canvas.select("")
        self.refresh_panels()
        self.setWindowTitle(self._title())
        self.canvas.fit_view()
        QMessageBox.information(
            self, "Exemplo de efeitos",
            "Este desenho tem um objeto para cada tipo de costura:\n\n"
            "✝ Ponto cruz · ⛓ Cadeia · 🪡 Ponto atrás · 🌿 Ponto haste\n"
            "✨ Lantejoula · ✦ Motivo cruz · ★ Motivo estrela\n"
            "＋ Preenchimento · Linha simples · Satin\n\n"
            "Clique em cada objeto e veja os ajustes no painel "
            "Propriedades. Use F5 para simular a costura!")

    def help_about(self):
        QMessageBox.about(
            self, f"Sobre o {APP_NAME}",
            f"<h3>{APP_NAME} {__version__}</h3>"
            "<p>Software livre de digitalização de bordado.</p>"
            "<p>Criado do zero — sem login, sem ativação, sem limitações. "
            "Instalou, usou.</p>"
            "<p>Desenhe formas, gere pontos automaticamente, importe e "
            "exporte arquivos DST, PES, EXP, JEF, VP3 e mais.</p>")

    def help_manual(self):
        QMessageBox.information(
            self, "Manual rápido",
            "COMO USAR O BORDADOSTUDIO:\n\n"
            "1) FERRAMENTAS (barra superior):\n"
            "   • Selecionar: clique no objeto para mover; arraste os "
            "quadradinhos brancos para ajustar os pontos.\n"
            "   • Preenchimento: clique para desenhar uma forma fechada "
            "(duplo-clique termina).\n"
            "   • Linha: desenhe à mão livre.\n"
            "   • Retângulo / Elipse: arraste na tela.\n"
            "   • Satin: clique ao longo do centro da faixa (duplo-clique "
            "termina) e ajuste a largura em Propriedades.\n\n"
            "2) PROPRIEDADES (esquerda): cor da linha e o TIPO DE COSTURA — "
            "são 10 estilos: Preenchimento, Linha simples, Satin, "
            "✝ Ponto cruz, ⛓ Cadeia (à mão), 🪡 Ponto atrás, 🌿 Ponto haste, "
            "✨ Lantejoula, ✦ Motivo cruz e ★ Motivo estrela. "
            "Também dá para ajustar espaçamento, ângulo, largura e densidade.\n\n"
            "3) OBJETOS (direita): ordem de costura, duplicar, renomear, "
            "excluir.\n\n"
            "4) SIMULAR (F5): veja a costura acontecer antes de exportar.\n\n"
            "5) EXPORTAR (Ctrl+E): gere o arquivo da sua máquina "
            "(DST, PES, EXP, JEF, VP3...). Use Ctrl+S para salvar o "
            "projeto e continuar depois.\n\n"
            "Atalhos: S=selecionar, P=preenchimento, L=linha, R=retângulo, "
            "E=elipse, B=satin, Ctrl+Z=desfazer, Espaço+arrastar=mover a tela, "
            "roda=zoom.")

    def closeEvent(self, event):
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()
