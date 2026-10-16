"""Janela principal do BordadoStudio: menus, barra de ferramentas, diálogos."""

from __future__ import annotations

import os

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QInputDialog,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME, __version__, formats_io, hoops, icons
from .canvas import EditorCanvas
from .colorway import ColorBar
from .model import Document
from .profiles import ProfileStore
from .object_list import ObjectListPanel
from .props_panel import STITCH_TYPES, PropertiesPanel
from .simulator import SimulatorDialog
from .threads import ThreadColor

TOOLS = [
    ("select", "Selecionar", "Selecionar, mover e ajustar pontos (S)", "S"),
    ("polygon", "Preenchimento", "Desenhar forma com preenchimento — clique nos pontos, duplo-clique termina (P)", "P"),
    ("freehand", "Linha", "Desenhar linha livre à mão (L)", "L"),
    ("rect", "Retângulo", "Arrastar para criar retângulo (R)", "R"),
    ("ellipse", "Elipse", "Arrastar para criar elipse (E)", "E"),
    ("satin", "Satin", "Desenhar coluna satin — clique no centro, duplo-clique termina (B)", "B"),
    ("text", "Texto", "Digitar texto em letras de bordado (T)", "T"),
]


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
        self.units = "mm"
        self.profiles = ProfileStore()
        self.default_thread = ThreadColor("Vermelho", 0xD62828)
        self.canvas = EditorCanvas(self.doc)
        self.setCentralWidget(self.canvas.view)
        self.setWindowTitle(self._title())
        self.setWindowIcon(self._app_icon())
        self.resize(1360, 860)

        self.props = PropertiesPanel(self)
        self.obj_list = ObjectListPanel(self)
        self.color_bar = ColorBar(self)

        self.addDockWidget(Qt.LeftDockWidgetArea,
                           self._dock("Propriedades do objeto", self.props))
        self.addDockWidget(Qt.RightDockWidgetArea,
                           self._dock("Camadas", self.obj_list))
        self.addDockWidget(Qt.RightDockWidgetArea,
                           self._dock("Ajuda rápida", self._quick_help()))
        color_dock = self._dock("Cores", self.color_bar)
        color_dock.setTitleBarWidget(QWidget())
        self.addDockWidget(Qt.BottomDockWidgetArea, color_dock)

        self._build_actions()
        self._build_toolbars()
        self._build_menus()
        self._build_info_bar()
        self._build_status()

        self.canvas.object_selected.connect(self._on_selection)
        self.canvas.document_changed.connect(self._on_doc_changed)
        self.canvas.cursor_moved.connect(self._on_cursor)
        self.canvas.text_requested.connect(self.text_at)
        self.canvas.zoom_changed.connect(self._on_zoom)
        self.obj_list.object_selected.connect(self.canvas.select)
        self.color_bar.color_picked.connect(self._apply_thread)

        self.canvas.fit_view()
        self._on_doc_changed()

    # ---------------------------------------------------------- chrome
    def _dock(self, title, widget):
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setFeatures(QDockWidget.DockWidgetMovable |
                         QDockWidget.DockWidgetFloatable)
        return dock

    def _quick_help(self):
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(8, 8, 8, 8)
        lab = QLabel(
            "<b>Bem-vindo ao BordadoStudio!</b><br><br>"
            "• <b>Ferramentas</b> (esquerda): seleção, preenchimento, linha, "
            "retângulo, elipse, satin e texto.<br>"
            "• <b>Propriedades</b>: cor e tipo de ponto do objeto.<br>"
            "• <b>Camadas</b>: ordem de costura das peças.<br>"
            "• <b>Cores</b> (embaixo): clique numa cor para aplicar ao objeto "
            "selecionado.<br>"
            "• <b>F5</b> simula a costura · <b>F6</b> visualização 3D · "
            "<b>Ctrl+E</b> exporta para a máquina.<br><br>"
            "Ajuda → Manual rápido (F1) tem todos os atalhos."
        )
        lab.setWordWrap(True)
        lab.setTextFormat(Qt.RichText)
        lay.addWidget(lab)
        lay.addStretch(1)
        return box

    def _app_icon(self) -> QIcon:
        pix = QPixmap(32, 32)
        pix.fill(Qt.transparent)
        from PySide6.QtGui import QPainter
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(31, 95, 196))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(1, 1, 30, 30, 6, 6)
        p.setPen(QColor(255, 214, 102))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(7, 7, 18, 18)
        p.end()
        return QIcon(pix)

    def _title(self):
        name = os.path.basename(self.path) if self.path else "Sem título"
        return f"{name} — {APP_NAME} {__version__}"

    def _build_status(self):
        self.status_coords = QLabel("0,0 mm")
        self.status_stitch = QLabel("PONTO: —")
        self.status_hoop = QLabel("")
        self.status_zoom = QLabel("100%")
        self.status_info = QLabel("0 objetos | 0 pontos")
        sb = self.statusBar()
        sb.addWidget(self.status_coords, 1)
        sb.addPermanentWidget(self.status_stitch)
        sb.addPermanentWidget(self.status_hoop)
        sb.addPermanentWidget(self.status_zoom)
        sb.addPermanentWidget(self.status_info)

    def _build_actions(self):
        def act(icon_name, *args, **kw):
            return QAction(icons.icon(icon_name), *args, **kw) if icon_name \
                else QAction(*args, **kw)

        self.act_new = act("new", "Novo", self, shortcut=QKeySequence.New,
                           triggered=self.file_new)
        self.act_open = act("open", "Abrir projeto...", self,
                            shortcut=QKeySequence.Open,
                            triggered=self.file_open)
        self.act_save = act("save", "Salvar", self,
                            shortcut=QKeySequence.Save,
                            triggered=self.file_save)
        self.act_save_as = act("save", "Salvar como...", self,
                               shortcut=QKeySequence("Ctrl+Shift+S"),
                               triggered=self.file_save_as)
        self.act_import = act("import", "Importar arquivo de bordado...", self,
                              shortcut=QKeySequence("Ctrl+I"),
                              triggered=self.file_import)
        self.act_export = act("export", "Exportar para máquina...", self,
                              shortcut=QKeySequence("Ctrl+E"),
                              triggered=self.file_export)
        self.act_report = act("report", "Relatório de produção...", self,
                              triggered=self.file_report)
        self.act_quit = QAction("Sair", self, shortcut=QKeySequence.Quit,
                                triggered=self.close)

        self.act_undo = act("undo", "Desfazer", self,
                            shortcut=QKeySequence.Undo,
                            triggered=self.edit_undo)
        self.act_redo = act("redo", "Refazer", self,
                            shortcut=QKeySequence.Redo,
                            triggered=self.edit_redo)
        self.act_delete = act("delete", "Excluir objeto", self,
                              shortcut=QKeySequence.Delete,
                              triggered=self.obj_list._delete)
        self.act_select_all = QAction("Selecionar tudo", self,
                                      shortcut=QKeySequence.SelectAll,
                                      triggered=self.edit_select_all)

        self.act_mirror_h = act("mirror_h", "Espelhar horizontalmente", self,
                                shortcut=QKeySequence("Ctrl+H"),
                                triggered=self.obj_mirror_h)
        self.act_mirror_v = act("mirror_v", "Espelhar verticalmente", self,
                                shortcut=QKeySequence("Ctrl+Shift+H"),
                                triggered=self.obj_mirror_v)
        self.act_rot_cw = act("rotate", "Girar 90° (horário)", self,
                              shortcut=QKeySequence("Ctrl+R"),
                              triggered=lambda: self.obj_rotate(-1))
        self.act_rot_ccw = act("rotate", "Girar 90° (anti-horário)", self,
                               shortcut=QKeySequence("Ctrl+Shift+R"),
                               triggered=lambda: self.obj_rotate(1))
        self.act_scale = act("scale", "Escala...", self,
                             shortcut=QKeySequence("Ctrl+M"),
                             triggered=self.obj_scale)
        self.act_rot45 = act("rotate", "Girar 45°", self,
                             shortcut=QKeySequence("Ctrl+G"),
                             triggered=lambda: self.obj_rotate_angle(45))
        self.act_smooth = act("smooth", "Suavizar contorno", self,
                              triggered=self.obj_smooth)
        self.act_split = act("scissors", "Dividir objeto em dois", self,
                             triggered=self.obj_split)
        self.act_underlay = act("underlay", "Ligar/desligar sub-base (underlay)",
                                self, triggered=self.obj_underlay)
        self.act_clipart = act("clipart", "Biblioteca de desenhos...", self,
                               shortcut=QKeySequence("Ctrl+Shift+L"),
                               triggered=self.clipart_dialog)

        self.act_center = QAction("Centralizar na área", self,
                                  shortcut=QKeySequence("Ctrl+Shift+C"),
                                  triggered=self.obj_center)
        self.act_center_h = QAction("Centralizar horizontalmente", self,
                                    triggered=self.obj_center_h)
        self.act_center_v = QAction("Centralizar verticalmente", self,
                                    triggered=self.obj_center_v)
        self.act_to_front = QAction("Trazer para o início da ordem", self,
                                    shortcut=QKeySequence("Ctrl+Shift+]"),
                                    triggered=self.obj_to_front)
        self.act_to_back = QAction("Enviar para o fim da ordem", self,
                                   shortcut=QKeySequence("Ctrl+Shift+["),
                                   triggered=self.obj_to_back)

        self.act_simulate = act("simulate", "Simular costura", self,
                                shortcut=QKeySequence("F5"),
                                triggered=self.view_simulate)
        self.act_3d = act("view3d", "Visualização 3D", self, checkable=True,
                          shortcut=QKeySequence("F6"),
                          triggered=self.view_3d)
        self.act_fit = act("fit", "Ajustar zoom ao desenho", self,
                           shortcut=QKeySequence("Ctrl+0"),
                           triggered=self.canvas.fit_view)
        self.act_grid = act("grid", "Mostrar grade", self, checkable=True,
                            checked=True, triggered=self.view_grid)
        self.act_rulers = act("rulers", "Mostrar réguas", self,
                              checkable=True, checked=True,
                              triggered=self.view_rulers)
        self.act_zoom_in = act("zoom_in", "Aumentar zoom", self,
                               shortcut=QKeySequence.ZoomIn,
                               triggered=self.view_zoom_in)
        self.act_zoom_out = act("zoom_out", "Reduzir zoom", self,
                                shortcut=QKeySequence.ZoomOut,
                                triggered=self.view_zoom_out)

        self.act_props = act("props", "Propriedades do desenho...", self,
                             triggered=self.file_properties)
        self.act_efeitos = QAction("Ver exemplo de efeitos...", self,
                                   triggered=self.help_efeitos)
        self.act_about = QAction("Sobre o BordadoStudio", self,
                                 triggered=self.help_about)
        self.act_manual = act("manual", "Manual rápido", self,
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
        file_m.addAction(self.act_report)
        file_m.addAction(self.act_props)
        file_m.addSeparator()
        file_m.addAction(self.act_quit)

        edit_m = m.addMenu("&Editar")
        for a in (self.act_undo, self.act_redo):
            edit_m.addAction(a)
        edit_m.addSeparator()
        for a in (self.act_delete, self.act_select_all):
            edit_m.addAction(a)

        draw_m = m.addMenu("&Desenho")
        for key, label, _tip, _letter in TOOLS:
            draw_m.addAction(self._tool_actions[key])
        draw_m.addSeparator()
        for a in self._shape_actions.values():
            draw_m.addAction(a)
        draw_m.addSeparator()
        draw_m.addAction(self.act_clipart)

        obj_m = m.addMenu("&Objeto")
        for a in (self.act_mirror_h, self.act_mirror_v,
                  self.act_rot_cw, self.act_rot_ccw, self.act_rot45,
                  self.act_scale):
            obj_m.addAction(a)
        obj_m.addSeparator()
        for a in (self.act_smooth, self.act_split, self.act_underlay):
            obj_m.addAction(a)

        arr_m = m.addMenu("A&rranjar")
        for a in (self.act_center, self.act_center_h, self.act_center_v):
            arr_m.addAction(a)
        arr_m.addSeparator()
        for a in (self.act_to_front, self.act_to_back):
            arr_m.addAction(a)

        view_m = m.addMenu("&Ver")
        for a in (self.act_simulate, self.act_3d, self.act_fit):
            view_m.addAction(a)
        view_m.addSeparator()
        for a in (self.act_zoom_in, self.act_zoom_out):
            view_m.addAction(a)
        view_m.addSeparator()
        for a in (self.act_grid, self.act_rulers):
            view_m.addAction(a)

        cfg_m = m.addMenu("&Configuração")
        cfg_m.addAction(self.act_props)
        cfg_m.addSeparator()
        cfg_m.addAction(self.act_grid)
        cfg_m.addAction(self.act_rulers)
        fabric_m = cfg_m.addMenu("Cor do tecido")
        for nome, rgb in (("Escuro (padrão)", (43, 43, 43)),
                          ("Cinza", (128, 128, 128)),
                          ("Branco", (245, 245, 245)),
                          ("Jeans", (70, 100, 140)),
                          ("Cru (bege)", (222, 210, 188))):
            a = QAction(nome, self, checkable=True,
                        triggered=lambda _c=False, v=rgb: self._set_fabric(v))
            a.setChecked(rgb == (43, 43, 43))
            fabric_m.addAction(a)

        help_m = m.addMenu("Aju&da")
        help_m.addAction(self.act_efeitos)
        help_m.addSeparator()
        help_m.addAction(self.act_manual)
        help_m.addAction(self.act_about)

    def _build_toolbars(self):
        self._tool_actions = {}
        for key, label, tip, letter in TOOLS:
            a = QAction(icons.icon(key), label, self, checkable=True,
                        toolTip=tip,
                        triggered=lambda _c=False, k=key: self.canvas.set_tool(k))
            a.setShortcut(QKeySequence(letter))
            a.setShortcutContext(Qt.ApplicationShortcut)
            self._tool_actions[key] = a
        self._tool_actions["select"].setChecked(True)

        # formas prontas (arrastar para desenhar)
        self._shape_actions = {}
        for key, label in (("heart", "Coração"), ("star", "Estrela"),
                           ("diamond", "Losango"), ("cross", "Cruz"),
                           ("triangle", "Triângulo"), ("hexagon", "Hexágono")):
            a = QAction(icons.icon("shape_" + key), label, self, checkable=True,
                        toolTip=f"{label} — arraste para desenhar",
                        triggered=lambda _c=False, k=key: self.canvas.set_tool(k))
            self._shape_actions[key] = a

        # atalhos de tipo de ponto para o objeto selecionado
        self._stitch_actions = {}
        for key, label, icon_name in (
                ("run", "Linha simples", "stitch_run"),
                ("run2", "Ponto duplo", "run2"),
                ("zigzag", "Ondulado", "zigzag"),
                ("scallop", "Bico", "scallop"),
                ("spring", "Mola", "spring"),
                ("motif_run", "Ponto motivo", "motif_run"),
                ("stem", "Ponto haste", "stem"),
                ("chain", "Cadeia", "chain"),
                ("backstitch", "Ponto atrás", "backstitch"),
                ("satin", "Satin", "satin"),
                ("fill", "Preenchimento (tatami)", "stitch_fill"),
                ("fill_contour", "Contorno concêntrico", "fill_contour"),
                ("fill_radial", "Radial", "fill_radial"),
                ("fill_mesh", "Rede (malha)", "fill_mesh"),
                ("fill_spiral", "Espiral", "fill_spiral"),
                ("fill_brick", "Tijolinho", "fill_brick"),
                ("fill_blend", "Mistura multi-fio", "fill_blend"),
                ("cross", "Ponto cruz", "crossstitch"),
                ("sequin", "Lantejoula", "sequin"),
                ("motif_cross", "Motivo cruz", "shape_cross"),
                ("motif_star", "Motivo estrela", "shape_star"),
                ("applique", "Aplique", "applique")):
            a = QAction(icons.icon(icon_name), label, self,
                        toolTip=f"Aplicar «{label}» ao objeto selecionado",
                        triggered=lambda _c=False, k=key: self._set_stitch(k))
            self._stitch_actions[key] = a
        self._outline_keys = (
            "run", "run2", "zigzag", "scallop", "spring", "motif_run",
            "stem", "chain", "backstitch", "satin")
        self._fill_keys = (
            "fill", "fill_contour", "fill_radial", "fill_mesh",
            "fill_spiral", "fill_brick", "fill_blend", "cross", "sequin",
            "motif_cross", "motif_star", "applique")

        self.canvas.tool_changed.connect(self._on_tool_changed)

        # linha 1: arquivo/edição + visualização
        tb1 = QToolBar("Padrão", self)
        tb1.setMovable(False)
        tb1.setIconSize(QSize(22, 22))
        for a in (self.act_new, self.act_open, self.act_save):
            tb1.addAction(a)
        tb1.addSeparator()
        for a in (self.act_import, self.act_export, self.act_report):
            tb1.addAction(a)
        tb1.addSeparator()
        for a in (self.act_undo, self.act_redo, self.act_delete):
            tb1.addAction(a)
        self.addToolBar(tb1)

        tb3 = QToolBar("Visualização", self)
        tb3.setMovable(False)
        tb3.setIconSize(QSize(22, 22))
        for a in (self.act_grid, self.act_rulers, self.act_3d,
                  self.act_simulate, self.act_fit):
            tb3.addAction(a)
        tb3.addSeparator()
        for a in (self.act_zoom_in, self.act_zoom_out):
            tb3.addAction(a)
        self.addToolBar(tb3)

        # linha 2: catálogo de contornos e enchimentos
        self.addToolBarBreak(Qt.TopToolBarArea)
        tb4 = QToolBar("Contornos", self)
        tb4.setMovable(False)
        tb4.setIconSize(QSize(22, 22))
        for k in self._outline_keys:
            tb4.addAction(self._stitch_actions[k])
        self.addToolBar(tb4)

        tb4b = QToolBar("Enchimentos", self)
        tb4b.setMovable(False)
        tb4b.setIconSize(QSize(22, 22))
        for k in self._fill_keys:
            tb4b.addAction(self._stitch_actions[k])
        self.addToolBar(tb4b)

        # linha 3: ações + ajustes rápidos
        self.addToolBarBreak(Qt.TopToolBarArea)
        tb5 = QToolBar("Ações", self)
        tb5.setMovable(False)
        tb5.setIconSize(QSize(22, 22))
        for a in (self.act_mirror_h, self.act_mirror_v,
                  self.act_rot_cw, self.act_rot_ccw, self.act_rot45,
                  self.act_scale):
            tb5.addAction(a)
        tb5.addSeparator()
        for a in (self.act_smooth, self.act_split, self.act_underlay):
            tb5.addAction(a)
        self.addToolBar(tb5)

        tb6 = QToolBar("Ajustes", self)
        tb6.setMovable(False)
        self.addToolBar(tb6)
        tb6.addWidget(QLabel(" Comprimento:"))
        self.quick_length = QDoubleSpinBox()
        self.quick_length.setRange(0.4, 20.0)
        self.quick_length.setDecimals(1)
        self.quick_length.setValue(2.5)
        self.quick_length.setSuffix(" mm")
        self.quick_length.setFixedWidth(86)
        self.quick_length.setToolTip(
            "Comprimento do ponto do objeto selecionado")
        self.quick_length.valueChanged.connect(self._quick_params)
        tb6.addWidget(self.quick_length)
        tb6.addWidget(QLabel(" Espaçamento:"))
        self.quick_spacing = QDoubleSpinBox()
        self.quick_spacing.setRange(0.2, 20.0)
        self.quick_spacing.setDecimals(1)
        self.quick_spacing.setValue(1.8)
        self.quick_spacing.setSuffix(" mm")
        self.quick_spacing.setFixedWidth(86)
        self.quick_spacing.setToolTip(
            "Espaçamento/densidade do objeto selecionado")
        self.quick_spacing.valueChanged.connect(self._quick_params)
        tb6.addWidget(self.quick_spacing)
        tb6.addSeparator()
        tb6.addWidget(QLabel(" Unidades:"))
        self.units_combo = QComboBox()
        self.units_combo.addItems(["Métrico", "Polegadas"])
        self.units_combo.setFixedWidth(96)
        self.units_combo.currentTextChanged.connect(self._set_units)
        tb6.addWidget(self.units_combo)
        tb6.addSeparator()
        tb6.addWidget(QLabel(" Bastidor:"))
        self.hoop_combo = QComboBox()
        self.hoop_combo.setFixedWidth(190)
        self._hoop_by_label = {}
        self.hoop_combo.addItem("Personalizado (manter área)")
        for h in hoops.HOOPS:
            self.hoop_combo.addItem(h.label)
            self._hoop_by_label[h.label] = h
        self.hoop_combo.currentTextChanged.connect(self._apply_hoop)
        self.hoop_combo.setToolTip("Escolhe a área/bastidor de bordado")
        tb6.addWidget(self.hoop_combo)
        tb6.addSeparator()
        tb6.addWidget(QLabel(" Perfil:"))
        self.profile_combo = QComboBox()
        self.profile_combo.setFixedWidth(130)
        self.profile_combo.setToolTip(
            "Predefinições de costura (aplicam ao objeto selecionado)")
        self.profile_combo.activated.connect(self._profile_apply)
        tb6.addWidget(self.profile_combo)
        prof_save = QAction(icons.icon("save"), "Salvar perfil", self,
                            toolTip="Salvar os ajustes do objeto como perfil",
                            triggered=self._profile_save)
        prof_del = QAction(icons.icon("delete"), "Excluir perfil", self,
                           toolTip="Excluir o perfil atual",
                           triggered=self._profile_delete)
        tb6.addAction(prof_save)
        tb6.addAction(prof_del)
        self._refresh_profile_combo()

        # coluna esquerda: ferramentas + formas prontas
        left = QToolBar("Ferramentas", self)
        left.setOrientation(Qt.Vertical)
        left.setMovable(False)
        left.setIconSize(QSize(22, 22))
        for key, _label, _tip, _letter in TOOLS:
            left.addAction(self._tool_actions[key])
        left.addSeparator()
        for a in self._shape_actions.values():
            left.addAction(a)
        left.addSeparator()
        left.addAction(self.act_clipart)
        self.addToolBar(Qt.LeftToolBarArea, left)

    def _build_info_bar(self):
        info = QToolBar("Informações", self)
        info.setMovable(False)
        self.addToolBarBreak(Qt.TopToolBarArea)
        self.addToolBar(info)

        def field(lo=-10000.0, hi=10000.0):
            sp = QDoubleSpinBox()
            sp.setRange(lo, hi)
            sp.setDecimals(1)
            sp.setSuffix(" mm")
            sp.setKeyboardTracking(False)   # aplica só ao confirmar
            sp.setFixedWidth(92)
            sp.valueChanged.connect(self._info_edited)
            return sp

        info.addWidget(QLabel(" Posição X:"))
        self.info_x = field()
        info.addWidget(self.info_x)
        info.addWidget(QLabel("  Posição Y:"))
        self.info_y = field()
        info.addWidget(self.info_y)
        info.addSeparator()
        info.addWidget(QLabel(" Largura:"))
        self.info_w = field(1.0, 20000.0)
        info.addWidget(self.info_w)
        info.addWidget(QLabel("  Altura:"))
        self.info_h = field(1.0, 20000.0)
        info.addWidget(self.info_h)
        info.addSeparator()
        info.addWidget(QLabel(" Zoom:"))
        self.info_zoom = QSpinBox()
        self.info_zoom.setRange(5, 400)
        self.info_zoom.setValue(100)
        self.info_zoom.setSuffix(" %")
        self.info_zoom.setFixedWidth(72)
        self.info_zoom.valueChanged.connect(self._set_zoom_pct)
        info.addWidget(self.info_zoom)

    # ---------------------------------------------------------- callbacks
    def _on_tool_changed(self, tool):
        for key, act in self._tool_actions.items():
            act.setChecked(key == tool)
        for key, act in self._shape_actions.items():
            act.setChecked(key == tool)

    def _on_selection(self, obj_id):
        obj = self.canvas.selected_object()
        self.props.load_object(obj)
        self.obj_list.rebuild()
        self._update_info_object(obj)

    def _update_info_object(self, obj):
        if obj is None or not obj.stitches:
            for sp in (self.info_x, self.info_y, self.info_w, self.info_h):
                sp.blockSignals(True)
                sp.setValue(0.0)
                sp.setEnabled(False)
                sp.blockSignals(False)
            self.status_stitch.setText("PONTO: —")
            return
        for sp in (self.info_x, self.info_y, self.info_w, self.info_h):
            sp.setEnabled(True)
        min_x, min_y, max_x, max_y = obj.bbox()
        w_mm = (max_x - min_x) / 10.0
        h_mm = (max_y - min_y) / 10.0
        self._info_wh_mm = (w_mm, h_mm)
        x_mm, y_mm = min_x / 10.0, min_y / 10.0
        self._cursor_mm = (x_mm, y_mm)
        if getattr(self, "units", "mm") == "in":
            k, suf = 1.0 / 25.4, " in"
        else:
            k, suf = 1.0, " mm"
        for sp in (self.info_x, self.info_y, self.info_w, self.info_h):
            sp.blockSignals(True)
            sp.setSuffix(suf)
        self.info_x.setValue(x_mm * k)
        self.info_y.setValue(y_mm * k)
        self.info_w.setValue(w_mm * k)
        self.info_h.setValue(h_mm * k)
        for sp in (self.info_x, self.info_y, self.info_w, self.info_h):
            sp.blockSignals(False)
        # preenche os ajustes rápidos
        p = obj.params or {}
        self.quick_length.blockSignals(True)
        self.quick_spacing.blockSignals(True)
        self.quick_length.setValue(float(p.get("stitch_length", 25.0)) / 10.0)
        self.quick_spacing.setValue(float(p.get("spacing", 18.0)) / 10.0)
        self.quick_length.blockSignals(False)
        self.quick_spacing.blockSignals(False)
        st = (obj.params or {}).get("stitch_type", "run")
        label = dict(STITCH_TYPES).get(st, st)
        self.status_stitch.setText(f"PONTO: {label.upper()}")

    def _on_doc_changed(self):
        self.update_status()
        self.act_undo.setEnabled(self.doc.can_undo())
        self.act_redo.setEnabled(self.doc.can_redo())

    def _on_cursor(self, x, y):
        self._cursor_mm = (x, y)
        un = "in" if getattr(self, "units", "mm") == "in" else "mm"
        if un == "in":
            sx = f"{x / 25.4:.2f}".replace(".", ",")
            sy = f"{y / 25.4:.2f}".replace(".", ",")
        else:
            sx = f"{x:.1f}".replace(".", ",")
            sy = f"{y:.1f}".replace(".", ",")
        self.status_coords.setText(f"{sx}, {sy} {un}")

    def update_status(self):
        n = len(self.doc.objects)
        pts = self.doc.total_stitches()
        self.status_info.setText(f"{n} objetos | {pts} pontos")
        self.status_zoom.setText(
            f"{self.canvas.view.transform().m11() * 100:.0f}%")
        nome = getattr(self.doc, "hoop_name", "Personalizado")
        if getattr(self.doc, "hoop_shape", "rect") == "circle":
            dim = f"Ø {self.doc.hoop[0] / 10:.0f} mm"
        elif getattr(self, "units", "mm") == "in":
            dim = (f"{self.doc.hoop[0] / 254:.1f}×"
                   f"{self.doc.hoop[1] / 254:.1f} in")
        else:
            dim = (f"{self.doc.hoop[0] / 10:.0f}×"
                   f"{self.doc.hoop[1] / 10:.0f} mm")
        self.status_hoop.setText(f"{nome}: {dim}")
        alvo = hoops.match_hoop(self.doc.hoop[0], self.doc.hoop[1])
        rotulo = alvo.label if alvo else "Personalizado (manter área)"
        if hasattr(self, "hoop_combo") and self.hoop_combo.currentText() != rotulo:
            self.hoop_combo.blockSignals(True)
            idx = self.hoop_combo.findText(rotulo)
            self.hoop_combo.setCurrentIndex(idx if idx >= 0 else 0)
            self.hoop_combo.blockSignals(False)
        self.color_bar.rebuild(self._doc_threads())
        self._on_doc_changed_quiet()

    def _doc_threads(self):
        seen: set[int] = set()
        out = []
        for o in self.doc.objects:
            if o.thread.hex_color not in seen:
                seen.add(o.thread.hex_color)
                out.append(o.thread)
        return out

    def _apply_thread(self, thread):
        obj = self.canvas.selected_object()
        if obj is None:
            self.default_thread = thread
            self.canvas.default_thread = thread
            self.statusBar().showMessage(
                f"Cor padrão para objetos novos: {thread.name}", 4000)
            return
        self.doc.snapshot()
        obj.thread = ThreadColor(thread.name, thread.hex_color,
                                 thread.code, thread.brand)
        self.canvas.refresh_object(obj)
        self.props.load_object(obj)
        self._on_doc_changed()
        self.statusBar().showMessage(f"Cor aplicada: {thread.name}", 4000)

    def _on_zoom(self, factor):
        pct = max(5, min(400, int(round(factor * 100))))
        self.status_zoom.setText(f"{pct}%")
        self.info_zoom.blockSignals(True)
        self.info_zoom.setValue(pct)
        self.info_zoom.blockSignals(False)

    def _set_zoom_pct(self, v):
        self.canvas.view.resetTransform()
        self.canvas.view.scale(v / 100.0, v / 100.0)
        self.status_zoom.setText(f"{v}%")

    def view_zoom_in(self):
        self.canvas.view.scale(1.25, 1.25)
        self._on_zoom(self.canvas.view.transform().m11())

    def view_zoom_out(self):
        self.canvas.view.scale(0.8, 0.8)
        self._on_zoom(self.canvas.view.transform().m11())

    def view_rulers(self, on):
        self.canvas.set_show_rulers(on)

    # ---------------------------------------------------------- botões de ação
    def _set_stitch(self, key):
        """Aplica um tipo de ponto ao objeto selecionado (atalho dos Contornos)."""
        if self.canvas.selected_object() is None:
            self.statusBar().showMessage(
                "Selecione um objeto antes de aplicar o tipo de ponto.", 4000)
            return
        keys = [k for k, _ in STITCH_TYPES]
        if key in keys:
            self.props.stitch_combo.setCurrentIndex(keys.index(key))

    def obj_rotate_angle(self, degrees):
        obj = self.canvas.selected_object()
        if obj is None:
            self.statusBar().showMessage("Selecione um objeto para girar.", 4000)
            return
        self.doc.snapshot()
        obj.rotate(float(degrees))
        self.canvas.refresh_object(obj)
        self.props.load_object(obj)
        self._on_doc_changed()

    def obj_smooth(self):
        obj = self.canvas.selected_object()
        if obj is None or obj.kind == "import" or obj.shape == "text" \
                or len(obj.points) < 3:
            self.statusBar().showMessage(
                "Selecione uma forma desenhada para suavizar o contorno.", 4000)
            return
        self.doc.snapshot()
        obj.smooth_points()
        self.canvas.refresh_object(obj)
        self._on_doc_changed()
        self.statusBar().showMessage("Contorno suavizado.", 4000)

    def obj_split(self):
        obj = self.canvas.selected_object()
        if obj is None:
            self.statusBar().showMessage("Selecione um objeto para dividir.", 4000)
            return
        novo = self.doc.split_object(obj)
        if novo is None:
            self.statusBar().showMessage(
                "Objeto pequeno demais para dividir.", 4000)
            return
        self.canvas.rebuild()
        self.canvas.select(novo.id)
        self._on_doc_changed()
        self.statusBar().showMessage("Objeto dividido em dois blocos.", 4000)

    def _quick_params(self, _v=None):
        """Aplica comprimento/espaçamento rápidos ao objeto selecionado."""
        obj = self.canvas.selected_object()
        if obj is None or obj.kind == "import":
            return
        self.doc.snapshot()
        obj.params["stitch_length"] = float(self.quick_length.value()) * 10.0
        obj.params["spacing"] = float(self.quick_spacing.value()) * 10.0
        obj.recompile()
        self.canvas.refresh_object(obj)
        self.props.load_object(obj)
        self._on_doc_changed()

    def _set_units(self, nome):
        """Alterna Métrico (mm) / Polegadas (in) na exibição e nas réguas."""
        self.units = "in" if nome == "Polegadas" else "mm"
        self.canvas.view.units = self.units
        self.canvas.view.viewport().update()
        self._refresh_units_display()

    def _fmt_len(self, mm: float) -> str:
        if getattr(self, "units", "mm") == "in":
            return f"{mm / 25.4:.2f} in".replace(".", ",")
        return f"{mm:.1f} mm".replace(".", ",")

    def _refresh_units_display(self):
        if hasattr(self, "_cursor_mm"):
            x, y = self._cursor_mm
            sx = self._fmt_len(x).split(" ")[0]
            sy = self._fmt_len(y).split(" ")[0]
            un = "in" if self.units == "in" else "mm"
            self.status_coords.setText(f"{sx}, {sy} {un}")
            self.info_x.setText(sx)
            self.info_y.setText(sy)
        if hasattr(self, "_info_wh_mm"):
            obj = self.canvas.selected_object()
            if obj is not None:
                self._update_info_object(obj)
        self.update_status()

    def _info_edited(self, _v):
        # Aplica posição/tamanho digitados ao objeto selecionado.
        obj = self.canvas.selected_object()
        if obj is None:
            return
        k = 25.4 if getattr(self, "units", "mm") == "in" else 1.0
        x_mm = self.info_x.value() * k
        y_mm = self.info_y.value() * k
        w_mm = self.info_w.value() * k
        h_mm = self.info_h.value() * k
        self.doc.snapshot()
        obj.resize_to(max(1.0, w_mm) * 10.0, max(1.0, h_mm) * 10.0)
        obj.move_to(x_mm * 10.0, y_mm * 10.0)
        self.canvas.refresh_object(obj)
        self._on_doc_changed()
        self._update_info_object(obj)

    def _apply_hoop(self, texto):
        h = self._hoop_by_label.get(texto)
        if h is None:
            return
        self.doc.snapshot()
        self.doc.hoop = [h.width, h.height]
        self.doc.hoop_name = h.name
        self.doc.hoop_shape = h.shape
        self.canvas.rebuild()
        self.canvas.fit_view()
        self.update_status()

    def _set_fabric(self, rgb):
        self.canvas.set_fabric_color(QColor(*rgb))

    # ---------- arranjar ----------
    def _center_obj(self, h, v):
        obj = self.canvas.selected_object()
        if obj is None:
            self.statusBar().showMessage(
                "Selecione um objeto para centralizar.", 4000)
            return
        self.doc.snapshot()
        obj.center_in(self.doc.hoop[0], self.doc.hoop[1], h, v)
        self.canvas.refresh_object(obj)
        self._on_doc_changed()

    def obj_center(self):
        self._center_obj(True, True)

    def obj_center_h(self):
        self._center_obj(True, False)

    def obj_center_v(self):
        self._center_obj(False, True)

    def obj_to_front(self):
        obj = self.canvas.selected_object()
        if obj is None:
            return
        self.doc.move_object(obj, -len(self.doc.objects))
        self.obj_list.rebuild()
        self._on_doc_changed()

    def obj_to_back(self):
        obj = self.canvas.selected_object()
        if obj is None:
            return
        self.doc.move_object(obj, len(self.doc.objects))
        self.obj_list.rebuild()
        self._on_doc_changed()

    # ---------- perfis ----------
    def _refresh_profile_combo(self, atual: str = ""):
        self.profile_combo.clear()
        self.profile_combo.addItems(self.profiles.names())
        if atual:
            idx = self.profile_combo.findText(atual)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)

    def _profile_apply(self, nome: str):
        params = self.profiles.get(nome)
        obj = self.canvas.selected_object()
        if not params or obj is None:
            if obj is None:
                self.statusBar().showMessage(
                    "Selecione um objeto para aplicar o perfil.", 4000)
            return
        self.doc.snapshot()
        obj.params.update(params)
        obj.recompile()
        self.canvas.refresh_object(obj)
        self.props.load_object(obj)
        self._on_doc_changed()
        self.statusBar().showMessage(f"Perfil aplicado: {nome}", 4000)

    def _profile_save(self):
        obj = self.canvas.selected_object()
        if obj is None:
            self.statusBar().showMessage(
                "Selecione um objeto para salvar os ajustes dele.", 4000)
            return
        nome, ok = QInputDialog.getText(
            self, "Salvar perfil", "Nome do perfil:",
            text=self.profile_combo.currentText() or "Meu perfil")
        if not ok or not str(nome).strip():
            return
        chaves = ("stitch_type", "stitch_length", "spacing", "angle",
                  "width", "density", "edge_underlay")
        params = {k: obj.params[k] for k in chaves if k in obj.params}
        self.profiles.set(str(nome).strip(), params)
        self._refresh_profile_combo(str(nome).strip())
        self.statusBar().showMessage(f"Perfil salvo: {nome}", 4000)

    def _profile_delete(self):
        nome = self.profile_combo.currentText()
        if not nome or nome not in self.profiles.profiles:
            return
        self.profiles.remove(nome)
        self._refresh_profile_combo()
        self.statusBar().showMessage(f"Perfil excluído: {nome}", 4000)

    # ---------- biblioteca de clipart ----------
    def clipart_dialog(self):
        from . import clipart
        dlg = QDialog(self)
        dlg.setWindowTitle("Biblioteca de desenhos")
        lay = QVBoxLayout(dlg)
        lab = QLabel("Escolha um desenho pronto para inserir no centro da tela:")
        lab.setWordWrap(True)
        lay.addWidget(lab)
        lst = QListWidget()
        lst.addItems(clipart.names())
        lst.setCurrentRow(0)
        lay.addWidget(lst)
        row = QHBoxLayout()
        row.addWidget(QLabel("Tamanho:"))
        size = QDoubleSpinBox()
        size.setRange(5.0, 300.0)
        size.setValue(60.0)
        size.setSuffix(" mm")
        row.addWidget(size)
        row.addStretch(1)
        lay.addLayout(row)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        dlg.resize(320, 420)
        if dlg.exec() != QDialog.Accepted:
            return
        item = lst.currentItem()
        if item is None:
            return
        self.insert_clipart(item.text(), size.value())

    def insert_clipart(self, name: str, size_mm: float):
        from . import clipart
        centro = self.canvas.view.mapToScene(
            self.canvas.view.viewport().rect().center())
        partes = clipart.build(name, size_mm, centro.x(), centro.y())
        if not partes:
            return
        criados = []
        for i, pts in enumerate(partes):
            nome = name if i == 0 else f"{name} ({i + 1})"
            obj = self.doc.new_object_from_points(
                "polygon", pts, thread=self.default_thread, name=nome)
            criados.append(obj)
        self.canvas.rebuild()
        self.canvas.select(criados[0].id)
        self.refresh_panels()
        self.statusBar().showMessage(
            f"Clipart «{name}» inserido ({len(criados)} peça(s)).", 4000)

    def obj_underlay(self):
        obj = self.canvas.selected_object()
        if obj is None or obj.kind == "import":
            self.statusBar().showMessage(
                "Selecione uma forma para mudar a sub-base.", 4000)
            return
        self.doc.snapshot()
        atual = bool(obj.params.get("edge_underlay", True))
        obj.params["edge_underlay"] = not atual
        obj.recompile()
        self.canvas.refresh_object(obj)
        self.props.load_object(obj)
        self._on_doc_changed()
        self.statusBar().showMessage(
            "Sub-base (underlay): " + ("LIGADA" if not atual else "DESLIGADA"),
            4000)

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

    def load_document(self, doc: Document, path: str | None = None):
        """Carrega um documento já montado (testes/exemplos)."""
        self.doc = doc
        self.path = path
        self.canvas.doc = doc
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

    def file_report(self):
        """Relatório de produção (pontos, linha, tempo e custo)."""
        if not self.doc.objects:
            QMessageBox.information(
                self, "Relatório",
                "Desenhe ou importe algo antes de gerar o relatório.")
            return
        from .report_dialog import ReportDialog
        dlg = ReportDialog(self.doc, self)
        dlg.exec()

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

    # ---------------------------------------------------------- objeto
    def _selected_or_info(self):
        obj = self.canvas.selected_object()
        if obj is None:
            QMessageBox.information(
                self, "Objeto",
                "Selecione um objeto primeiro (ferramenta Selecionar).")
        return obj

    def obj_mirror_h(self):
        obj = self._selected_or_info()
        if obj:
            self.doc.snapshot()
            obj.mirror_h()
            self.refresh_panels()

    def obj_mirror_v(self):
        obj = self._selected_or_info()
        if obj:
            self.doc.snapshot()
            obj.mirror_v()
            self.refresh_panels()

    def obj_rotate(self, steps: int):
        obj = self._selected_or_info()
        if obj:
            self.doc.snapshot()
            obj.rotate90(steps)
            self.refresh_panels()

    def obj_scale(self):
        obj = self._selected_or_info()
        if not obj:
            return
        from PySide6.QtWidgets import QInputDialog
        pct, ok = QInputDialog.getDouble(
            self, "Escala", "Tamanho (%):", 100.0, 10.0, 500.0, 1)
        if ok and abs(pct - 100.0) > 0.01:
            self.doc.snapshot()
            obj.scale(pct / 100.0)
            self.refresh_panels()

    # ---------------------------------------------------------- texto
    def text_at(self, x: float, y: float):
        """Ferramenta Texto: pede o texto e cria o objeto na posição."""
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(
            self, "Texto bordado",
            "Digite o texto (várias linhas são permitidas):")
        if not ok or not text.strip():
            return
        from .threads import ThreadColor
        obj = self.doc.new_object_from_points(
            "text", [(x, y)],
            params={"text": text, "size": 100.0},
            thread=ThreadColor("Azul", 0x1F5FC4, "14"),
            name=f"Texto: {text.splitlines()[0][:16]}")
        self.canvas.rebuild()
        self.canvas.select(obj.id)
        self.canvas.set_tool("select")
        self.refresh_panels()

    # ---------------------------------------------------------- ver
    def view_simulate(self):
        if not self.doc.objects:
            QMessageBox.information(self, "Simular",
                                    "Desenhe ou importe algo antes de simular.")
            return
        dlg = SimulatorDialog(self.doc, self)
        dlg.exec()

    def view_3d(self, on):
        self.canvas.set_view_3d(on)

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
            "são 22 estilos: Preenchimento, Linha simples, Satin, "
            "✝ Ponto cruz, ⛓ Cadeia (à mão), 🪡 Ponto atrás, 🌿 Ponto haste, "
            "✨ Lantejoula, ✦ Motivo cruz, ★ Motivo estrela e 🧵 Aplique. "
            "Também dá para ajustar espaçamento, ângulo, largura e densidade.\n\n"
            "3) LETRAS (T): clique na tela, digite o texto e a altura em "
            "milímetros. Dá para mudar texto, altura e tipo de ponto no "
            "painel — inclusive letras com acento (Ç, Ã, Õ…).\n\n"
            "4) OBJETOS (direita): ordem de costura, duplicar, renomear, "
            "excluir. Menu Objeto: espelhar (Ctrl+H), girar (Ctrl+R) e "
            "escalar (Ctrl+M) o desenho selecionado.\n\n"
            "5) FORMAS PRONTAS (coluna da esquerda): coração, estrela, losango, "
            "cruz, triângulo e hexágono — arraste para desenhar. "
            "As barras Contornos e Ações aplicam ponto, espelham, giram, "
            "suavizam o contorno e dividem o objeto.\n\n"
            "6) SIMULAR (F5): veja a costura acontecer antes de exportar. "
            "Visualização 3D (F6): deixa os pontos com volume de fio real.\n\n"
            "7) RELATÓRIO (menu Arquivo): pontos, metros de linha, tempo e "
            "custo do seu bordado, com opção de salvar em .txt.\n\n"
            "8) EXPORTAR (Ctrl+E): gere o arquivo da sua máquina "
            "(DST, PES, EXP, JEF, VP3...). Use Ctrl+S para salvar o "
            "projeto e continuar depois.\n\n"
            "Atalhos: S=selecionar, P=preenchimento, L=linha, R=retângulo, "
            "E=elipse, B=satin, T=texto, Ctrl+Z=desfazer, "
            "Espaço+arrastar=mover a tela, roda=zoom.")

    def closeEvent(self, event):
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()
