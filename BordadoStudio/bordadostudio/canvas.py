"""Canvas de edição: cena, ferramentas de digitalização, itens de costura e alças."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsObject,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsView,
)

from . import stitcher

HANDLE_SIZE = 7.0
SELECT_COLOR = QColor(255, 200, 40)
RUBBER_COLOR = QColor(80, 180, 255)


def _qcolor(hex_color: int) -> QColor:
    return QColor((hex_color >> 16) & 255, (hex_color >> 8) & 255, hex_color & 255)


def _shade(color: QColor, factor: float) -> QColor:
    """Clareia (factor>1) ou escurece (factor<1) uma cor."""
    return QColor(
        max(0, min(255, int(color.red() * factor))),
        max(0, min(255, int(color.green() * factor))),
        max(0, min(255, int(color.blue() * factor))),
    )


def paint_stitches_3d(painter: QPainter, path: QPainterPath, color: QColor):
    """Desenha os pontos com volume (efeito visualização 3D)."""
    shadow = QPen(_shade(color, 0.38), 3.4)
    shadow.setCosmetic(True)
    shadow.setCapStyle(Qt.RoundCap)
    body = QPen(color, 2.3)
    body.setCosmetic(True)
    body.setCapStyle(Qt.RoundCap)
    shine = QPen(_shade(color, 1.45), 0.9)
    shine.setCosmetic(True)
    shine.setCapStyle(Qt.RoundCap)

    painter.save()
    painter.translate(1.6, 2.1)
    painter.setPen(shadow)
    painter.drawPath(path)
    painter.restore()

    painter.setPen(body)
    painter.drawPath(path)

    painter.save()
    painter.translate(-0.5, -0.7)
    painter.setPen(shine)
    painter.drawPath(path)
    painter.restore()


class VertexHandle(QGraphicsObject):
    """Alça de vértice para editar a geometria de um objeto."""

    def __init__(self, obj, index: int):
        super().__init__()
        self.obj = obj
        self.index = index
        self.setZValue(20)
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        return QRectF(-HANDLE_SIZE / 2, -HANDLE_SIZE / 2, HANDLE_SIZE, HANDLE_SIZE)

    def is_curved(self) -> bool:
        curvas = (self.obj.params or {}).get("curves") or []
        return self.index in curvas

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        if self.is_curved():
            # vértice com segmento curvo: losango cheio
            painter.setBrush(QBrush(QColor(255, 200, 60)))
            h = HANDLE_SIZE / 2
            painter.drawPolygon([QPointF(0, -h), QPointF(h, 0),
                                 QPointF(0, h), QPointF(-h, 0)])
        else:
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawRect(self.boundingRect())


class StitchGraphicsItem(QGraphicsObject):
    """Representação gráfica de um objeto (desenha os pontos reais)."""

    def __init__(self, obj, canvas):
        super().__init__()
        self.obj = obj
        self.canvas = canvas
        self._rect = QRectF()
        self._path = QPainterPath()
        self._handles: list[VertexHandle] = []
        self._refresh_geometry()

    # ---- geometria / pintura ----
    def _refresh_geometry(self):
        self.prepareGeometryChange()
        path = QPainterPath()
        path2 = QPainterPath()
        cur = path
        run: list[tuple[float, float]] = []

        def flush():
            if len(run) >= 2:
                cur.moveTo(run[0][0], run[0][1])
                for px, py in run[1:]:
                    cur.lineTo(px, py)

        for x, y, c in self.obj.stitches:
            if c in (stitcher.STITCH, stitcher.COLOR_CHANGE):
                if c == stitcher.COLOR_CHANGE:
                    # marca de mistura: alterna entre cor principal e cor 2
                    flush()
                    run = []
                    cur = path2 if cur is path else path
                run.append((x, y))
            else:
                flush()
                run = []
        flush()
        self._path = path
        self._path2 = path2
        rect = path.boundingRect().united(path2.boundingRect())
        if rect.isNull() or rect.isEmpty():
            rect = QRectF(-20, -20, 40, 40)
        self._rect = rect.adjusted(-20, -20, 20, 20)
        self.update()

    def refresh(self):
        """Chamar após o modelo mudar."""
        self._refresh_geometry()
        self._sync_handles()

    def boundingRect(self):
        return self._rect

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(14)
        s = stroker.createStroke(self._path)
        s.addPath(stroker.createStroke(self._path2))
        return s

    def paint(self, painter: QPainter, option, widget=None):
        if not self.obj.visible:
            return
        color = _qcolor(self.obj.thread.hex_color)
        blend_hex = (self.obj.params or {}).get("blend_color")
        color2 = _qcolor(blend_hex) if blend_hex else _shade(color, 0.55)
        selected = self.canvas.selected_id == self.obj.id
        if self.canvas.view_3d:
            paint_stitches_3d(painter, self._path, color)
            if not self._path2.isEmpty():
                paint_stitches_3d(painter, self._path2, color2)
        else:
            pen = QPen(color, 1.6 if selected else 1.1)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(self._path)
            if not self._path2.isEmpty():
                pen2 = QPen(color2, 1.6 if selected else 1.1)
                pen2.setCosmetic(True)
                painter.setPen(pen2)
                painter.drawPath(self._path2)
        if selected:
            halo = QPen(SELECT_COLOR, 3.2)
            halo.setCosmetic(True)
            painter.setPen(halo)
            painter.setOpacity(0.35)
            painter.drawPath(self._path)
            painter.setOpacity(1.0)

    # ---- alças ----
    def _sync_handles(self):
        show = (
            self.canvas.selected_id == self.obj.id
            and self.obj.kind == "shape"
            and self.canvas.tool == "select"
        )
        wanted = len(self.obj.points) if show else 0
        scene = self.scene()
        while len(self._handles) < wanted:
            h = VertexHandle(self.obj, len(self._handles))
            h.setZValue(20)
            self._handles.append(h)
            if scene is not None:
                scene.addItem(h)
        while len(self._handles) > wanted:
            h = self._handles.pop()
            if h.scene() is not None:
                h.scene().removeItem(h)
        for i, h in enumerate(self._handles):
            h.index = i
            h.obj = self.obj
            x, y = self.obj.points[i]
            h.setPos(x, y)
            h.setVisible(True)

    def dispose(self):
        """Remove o item e suas alças da cena."""
        for h in self._handles:
            if h.scene() is not None:
                h.scene().removeItem(h)
        self._handles.clear()
        if self.scene() is not None:
            self.scene().removeItem(self)


class CanvasView(QGraphicsView):
    """Vista com zoom na roda, pan com botão do meio/espaço."""

    def __init__(self, scene, canvas):
        super().__init__(scene)
        self.canvas = canvas
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        # NÃO usar setBackgroundBrush: ele anula o drawBackground da cena.
        self._panning = False
        self._pan_start = QPointF()
        self._space = False
        self.show_rulers = True
        self.units = "mm"   # 'mm' | 'in'

    # ---- réguas (mm) desenhadas sobre a viewport ----
    RULER = 22  # px

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.show_rulers:
            return
        from PySide6.QtGui import QColor, QFont, QPen
        p = QPainter(self.viewport())
        r = self.RULER
        w, h = self.viewport().width(), self.viewport().height()
        p.fillRect(0, 0, w, r, QColor(245, 245, 245))
        p.fillRect(0, 0, r, h, QColor(245, 245, 245))
        p.setPen(QPen(QColor(160, 160, 160), 1))
        p.drawLine(r, 0, r, h)
        p.drawLine(0, r, w, r)
        p.fillRect(0, 0, r, r, QColor(225, 225, 225))

        font = QFont()
        font.setPixelSize(9)
        p.setFont(font)
        pen_minor = QPen(QColor(120, 120, 120), 1)
        pen_major = QPen(QColor(70, 70, 70), 1)

        # escala: 10 unidades de cena = 1 mm
        tl = self.mapToScene(r, r)
        br = self.mapToScene(w, h)
        mm_x0, mm_x1 = tl.x() / 10.0, br.x() / 10.0
        mm_y0, mm_y1 = tl.y() / 10.0, br.y() / 10.0

        import math
        if self.units == "in":
            # 1 pol = 254 unidades; passos em frações de polegada
            step = 0.25 if self.transform().m11() > 1.2 else (
                1.0 if self.transform().m11() > 0.35 else 5.0)
            def label_of(mm):
                return f"{mm / 25.4:.2f}".rstrip("0").rstrip(".")
            def is_major(mm):
                return abs((mm / 25.4) % 1.0) < 1e-6
            def is_medium(mm):
                return abs((mm / 25.4) % 0.5) < 1e-6
            step_mm = step * 25.4
        else:
            step = 1.0 if self.transform().m11() > 1.2 else (
                5.0 if self.transform().m11() > 0.35 else 10.0)
            def label_of(mm):
                return f"{mm:.0f}"
            def is_major(mm):
                return abs(mm % 50.0) < 1e-6
            def is_medium(mm):
                return abs(mm % 10.0) < 1e-6
            step_mm = step
        first = math.floor(mm_x0 / step_mm) * step_mm
        mm = first
        while mm <= mm_x1:
            x = int(self.mapFromScene(mm * 10.0, 0).x())
            if x >= r:
                major = is_major(mm)
                medium = is_medium(mm)
                p.setPen(pen_major if (major or medium) else pen_minor)
                tick = r if major else (8 if medium else 4)
                p.drawLine(x, r - tick, x, r)
                if major:
                    p.drawText(x + 2, 12, label_of(mm))
            mm += step_mm
        first = math.floor(mm_y0 / step_mm) * step_mm
        mm = first
        while mm <= mm_y1:
            y = int(self.mapFromScene(0, mm * 10.0).y())
            if y >= r:
                major = is_major(mm)
                medium = is_medium(mm)
                p.setPen(pen_major if (major or medium) else pen_minor)
                tick = r if major else (8 if medium else 4)
                p.drawLine(r - tick, y, r, y)
                if major:
                    p.save()
                    p.translate(10, y - 3)
                    p.rotate(-90)
                    p.drawText(0, 0, label_of(mm))
                    p.restore()
            mm += step_mm

    def wheelEvent(self, event):
        factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        self.scale(factor, factor)
        self.canvas.zoom_changed.emit(self.transform().m11())

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton or (
            event.button() == Qt.LeftButton and self._space
        ):
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(
                int(self.verticalScrollBar().value() - delta.y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._panning and event.button() in (Qt.MiddleButton, Qt.LeftButton):
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self._space = True
            self.setCursor(Qt.OpenHandCursor)
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self._space = False
            if not self._panning:
                self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().keyReleaseEvent(event)


class EditorCanvas(QGraphicsScene):
    """Cena de edição com ferramentas de digitalização.

    Emite:
        object_selected(str)  -> id do objeto ou ""
        document_changed()    -> modelo alterado (recarregar painéis)
        tool_changed(str)     -> ferramenta ativa
        zoom_changed(float)   -> fator de escala
        cursor_moved(float,float) -> posição em mm
    """

    object_selected = Signal(str)
    document_changed = Signal()
    tool_changed = Signal(str)
    zoom_changed = Signal(float)
    cursor_moved = Signal(float, float)
    text_requested = Signal(float, float)   # ferramenta Texto: posição em unidades

    def __init__(self, doc, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.tool = "select"
        self.selected_id = ""
        self.show_grid = True
        self.view_3d = False
        self.fabric_color = QColor(43, 43, 43)   # cor do tecido (fundo)
        self.default_thread = None   # ThreadColor para objetos novos (opcional)
        self._items: dict[str, StitchGraphicsItem] = {}
        self._drag = None            # ('move', obj, last_scene_pos) | ('vertex', handle, ...)
        self._rubber: QGraphicsPathItem | None = None
        self._digitize_points: list[tuple[float, float]] = []
        self._tool_preview_point: tuple[float, float] | None = None
        self._pending_snapshot = False

        self.view = CanvasView(self, self)
        self.view.setMouseTracking(True)
        self.rebuild()

    # ---------------------------------------------------------- cena
    def rebuild(self):
        """Recria todos os itens a partir do documento."""
        for item in self._items.values():
            item.dispose()
        self._items.clear()
        # âmbito da cena = área do bastidor + margem (garante centro/scroll)
        self.setSceneRect(QRectF(-150, -150,
                                 self.doc.hoop[0] + 300,
                                 self.doc.hoop[1] + 300))
        for obj in self.doc.objects:
            item = StitchGraphicsItem(obj, self)
            self.addItem(item)
            self._items[obj.id] = item
            item._sync_handles()
        self._refresh_selection()
        self.update()

    def refresh_object(self, obj):
        item = self._items.get(obj.id)
        if item:
            item.refresh()

    def refresh_all(self):
        for obj in self.doc.objects:
            self.refresh_object(obj)
        self._refresh_selection()

    def bounds_scene(self):
        b = self.doc.bounds()
        if b[2] - b[0] < 1 and b[3] - b[1] < 1:
            return QRectF(-50, -50, self.doc.hoop[0] + 100, self.doc.hoop[1] + 100)
        return QRectF(b[0], b[1], b[2] - b[0], b[3] - b[1])

    def fit_view(self):
        rect = self.bounds_scene().adjusted(-80, -80, 80, 80)
        self.view.fitInView(rect, Qt.KeepAspectRatio)
        self.zoom_changed.emit(self.view.transform().m11())

    def set_view_3d(self, on: bool):
        """Alterna a visualização 3D dos pontos."""
        self.view_3d = bool(on)
        self.update()

    def set_show_rulers(self, on: bool):
        """Alterna as réguas em mm da borda da tela."""
        self.view.show_rulers = bool(on)
        self.view.viewport().update()

    def set_fabric_color(self, color: QColor):
        """Muda a cor do tecido (fundo da área de desenho)."""
        self.fabric_color = QColor(color)
        self.update()

    # ---------------------------------------------------------- seleção
    def select(self, obj_id: str, emit: bool = True):
        self.selected_id = obj_id if (obj_id and self.doc.find(obj_id)) else ""
        self._refresh_selection()
        if emit:
            self.object_selected.emit(self.selected_id)

    def _refresh_selection(self):
        for oid, item in self._items.items():
            item._sync_handles()
            item.update()

    def selected_object(self):
        return self.doc.find(self.selected_id) if self.selected_id else None

    # ---------------------------------------------------------- ferramentas
    def set_tool(self, tool: str):
        self.cancel_digitize()
        self.tool = tool
        self.tool_changed.emit(tool)
        self._refresh_selection()

    def cancel_digitize(self):
        self._digitize_points.clear()
        self._tool_preview_point = None
        self._remove_rubber()

    def finish_digitize(self):
        if self.tool in ("polygon", "satin") and len(self._digitize_points) >= 2:
            if self.tool == "polygon" and len(self._digitize_points) < 3:
                self.cancel_digitize()
                return
            shape = "polygon" if self.tool == "polygon" else "satin"
            obj = self.doc.new_object_from_points(
                shape, list(self._digitize_points),
                thread=self.default_thread)
            self.cancel_digitize()
            self.rebuild()
            self.select(obj.id)
            self.document_changed.emit()
        elif self.tool == "freehand":
            self.cancel_digitize()

    # ---------------------------------------------------------- mouse
    def mousePressEvent(self, event):
        pos = event.scenePos()
        if event.button() == Qt.RightButton:
            self.cancel_digitize()
            return
        if event.button() != Qt.LeftButton:
            return

        if self.tool == "select":
            for item in self.items(pos):
                if isinstance(item, VertexHandle):
                    if event.button() == Qt.RightButton:
                        self.delete_vertex(item)
                        return
                    self._begin_snapshot()
                    self._drag = ("vertex", item, (pos.x(), pos.y()))
                    return
                if isinstance(item, StitchGraphicsItem) and item.obj.visible:
                    self.select(item.obj.id)
                    self._begin_snapshot()
                    self._drag = ("move", item.obj, (pos.x(), pos.y()))
                    return
            self.select("")
            return

        if self.tool == "text":
            self.text_requested.emit(pos.x(), pos.y())
            return

        if self.tool in ("rect", "ellipse", "heart", "star", "diamond",
                         "cross", "triangle", "hexagon", "pentagon",
                         "octagon", "arrow", "crescent", "flower", "cloud",
                         "arc", "wave", "zigzag", "spiral"):
            self._digitize_points = [(pos.x(), pos.y())]
            self._drag = ("rubber", None, (pos.x(), pos.y()))
            return

        if self.tool in ("polygon", "satin"):
            self._digitize_points.append((pos.x(), pos.y()))
            self._update_rubber()
            return

        if self.tool == "freehand":
            self._begin_snapshot()
            self._digitize_points = [(pos.x(), pos.y())]
            self._drag = ("freehand", None, (pos.x(), pos.y()))
            return

    def mouseMoveEvent(self, event):
        pos = event.scenePos()
        self.cursor_moved.emit(pos.x() / 10.0, pos.y() / 10.0)

        if self._drag and self._drag[0] == "move":
            _, obj, last = self._drag
            dx, dy = pos.x() - last[0], pos.y() - last[1]
            if dx or dy:
                self._commit_snapshot()
                obj.translate(dx, dy)
                self.refresh_object(obj)
                self._drag = ("move", obj, (pos.x(), pos.y()))
                self.document_changed.emit()
            return

        if self._drag and self._drag[0] == "vertex":
            _, handle, _ = self._drag
            obj = handle.obj
            if 0 <= handle.index < len(obj.points):
                self._commit_snapshot()
                obj.points[handle.index] = (pos.x(), pos.y())
                obj.recompile()
                self.refresh_object(obj)
                self.document_changed.emit()
            return

        if self._drag and self._drag[0] == "rubber":
            self._tool_preview_point = (pos.x(), pos.y())
            self._update_rubber()
            return

        if self._drag and self._drag[0] == "freehand":
            pts = self._digitize_points
            lx, ly = pts[-1]
            if math.hypot(pos.x() - lx, pos.y() - ly) >= 6:
                pts.append((pos.x(), pos.y()))
                self._update_rubber()
            return

        if self.tool in ("polygon", "satin") and self._digitize_points:
            self._tool_preview_point = (pos.x(), pos.y())
            self._update_rubber()

    def mouseDoubleClickEvent(self, event):
        if self.tool in ("polygon", "satin"):
            # o último clique do duplo já foi adicionado — remove duplicata
            if len(self._digitize_points) >= 2:
                self._digitize_points.pop()
            self.finish_digitize()
            return
        if self.tool == "select" and event.button() == Qt.LeftButton:
            pos = event.scenePos()
            for item in self.items(pos):
                if isinstance(item, VertexHandle):
                    self.toggle_vertex_curve(item)
                    return
                if isinstance(item, StitchGraphicsItem) and item.obj.visible:
                    self.insert_vertex(item.obj, pos.x(), pos.y())
                    return

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if self._drag and self._drag[0] == "rubber":
            x0, y0 = self._digitize_points[0]
            x1, y1 = event.scenePos().x(), event.scenePos().y()
            self._drag = None
            self._remove_rubber()
            self._digitize_points.clear()
            w, h = x1 - x0, y1 - y0
            if abs(w) < 5 or abs(h) < 5:
                return
            if w < 0:
                x0, w = x0 + w, -w
            if h < 0:
                y0, h = y0 + h, -h
            cx, cy = x0 + w / 2, y0 + h / 2
            geradores = {
                "rect": lambda: stitcher.rect_points(x0, y0, w, h),
                "ellipse": lambda: stitcher.ellipse_points(cx, cy, w / 2, h / 2),
                "heart": lambda: stitcher.heart_points(cx, cy, w / 2, h / 2),
                "star": lambda: stitcher.star_points(cx, cy, w / 2, h / 2),
                "diamond": lambda: stitcher.diamond_points(cx, cy, w / 2, h / 2),
                "cross": lambda: stitcher.cross_points(cx, cy, w / 2, h / 2),
                "triangle": lambda: stitcher.triangle_points(cx, cy, w / 2, h / 2),
                "hexagon": lambda: stitcher.hexagon_points(cx, cy, w / 2, h / 2),
                "pentagon": lambda: stitcher.pentagon_points(cx, cy, w / 2, h / 2),
                "octagon": lambda: stitcher.octagon_points(cx, cy, w / 2, h / 2),
                "arrow": lambda: stitcher.arrow_points(cx, cy, w / 2, h / 2),
                "crescent": lambda: stitcher.crescent_points(cx, cy, w / 2, h / 2),
                "flower": lambda: stitcher.flower_points(cx, cy, w / 2, h / 2),
                "cloud": lambda: stitcher.cloud_points(cx, cy, w / 2, h / 2),
                "arc": lambda: stitcher.arc_points(cx, cy, w / 2, h / 2),
                "wave": lambda: stitcher.wave_points(cx, cy, w / 2, h / 2),
                "zigzag": lambda: stitcher.zigzag_points(cx, cy, w / 2, h / 2),
                "spiral": lambda: stitcher.spiral_points(cx, cy, w / 2, h / 2),
            }
            pts = geradores.get(self.tool, geradores["rect"])()
            abertas = ("arc", "wave", "zigzag", "spiral")
            if self.tool in abertas:
                obj = self.doc.new_object_from_points(
                    "freehand", pts, thread=self.default_thread,
                    params={"closed": False, "stitch_type": "run2"})
            else:
                obj = self.doc.new_object_from_points(
                    self.tool, pts, thread=self.default_thread)
            self.rebuild()
            self.select(obj.id)
            self.document_changed.emit()
            return

        if self._drag and self._drag[0] == "freehand":
            self._drag = None
            self._remove_rubber()
            pts = list(self._digitize_points)
            self._digitize_points.clear()
            if len(pts) >= 2:
                obj = self.doc.new_object_from_points(
                    "freehand", pts, thread=self.default_thread)
                self.rebuild()
                self.select(obj.id)
                self.document_changed.emit()
            return

        if self._drag and self._drag[0] in ("move", "vertex"):
            self._drag = None
            self.document_changed.emit()

    # ---------------------------------------------------------- teclado
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.cancel_digitize()
            return
        if key in (Qt.Key_Return, Qt.Key_Enter):
            self.finish_digitize()
            return
        if key == Qt.Key_Backspace and self.tool in ("polygon", "satin"):
            if self._digitize_points:
                self._digitize_points.pop()
                self._update_rubber()
            return
        super().keyPressEvent(event)

    # ---------------------------------------------------------- borracha de desenho
    def _remove_rubber(self):
        if self._rubber is not None:
            self.removeItem(self._rubber)
            self._rubber = None

    def _update_rubber(self):
        self._remove_rubber()
        path = QPainterPath()
        pts = list(self._digitize_points)
        if self._tool_preview_point and self.tool in ("polygon", "satin"):
            pts = pts + [self._tool_preview_point]
        if pts:
            path.moveTo(pts[0][0], pts[0][1])
            for x, y in pts[1:]:
                path.lineTo(x, y)
        item = QGraphicsPathItem(path)
        pen = QPen(RUBBER_COLOR, 1.4)
        pen.setCosmetic(True)
        pen.setStyle(Qt.DashLine)
        item.setPen(pen)
        item.setZValue(50)
        self._rubber = item
        self.addItem(item)

    # ---------------------------------------------------------- snapshots
    def _begin_snapshot(self):
        """Snapshot preguiçoso: registrado apenas na primeira mutação real."""
        self._pending_snapshot = True

    def _commit_snapshot(self):
        if self._pending_snapshot:
            self.doc.snapshot()
            self._pending_snapshot = False

    # ---------------------------------------------------------- edição de nós
    @staticmethod
    def _editar(obj) -> bool:
        return (obj is not None and obj.kind != "import"
                and obj.shape != "text" and len(obj.points) >= 3)

    def delete_vertex(self, handle):
        """Exclui um vértice (clique direito na alça)."""
        obj = handle.obj
        if not self._editar(obj) or len(obj.points) <= 3:
            return
        self._begin_snapshot()
        self._commit_snapshot()
        i = handle.index
        n = len(obj.points)
        del obj.points[i]
        novas = []
        for c in obj.params.get("curves", []):
            if c == i or c == (i - 1) % n:
                continue          # segmentos vizinhos viram reta
            novas.append(c - 1 if c > i else c)
        obj.params["curves"] = sorted(novas)
        obj.recompile()
        self.refresh_object(obj)
        self.document_changed.emit()

    def toggle_vertex_curve(self, handle):
        """Alterna o segmento que sai do vértice entre reta e curva."""
        obj = handle.obj
        if not self._editar(obj):
            return
        self._begin_snapshot()
        self._commit_snapshot()
        curvas = list(obj.params.get("curves", []))
        i = handle.index
        if i in curvas:
            curvas.remove(i)
        else:
            curvas.append(i)
        obj.params["curves"] = sorted(curvas)
        obj.recompile()
        self.refresh_object(obj)
        self.document_changed.emit()

    def insert_vertex(self, obj, x: float, y: float):
        """Insere um vértice no segmento mais próximo de (x, y)."""
        if not self._editar(obj):
            return
        pts = obj.points
        n = len(pts)
        melhor, melhor_d2, melhor_t = 0, None, 0.5
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            dx, dy = bx - ax, by - ay
            comp2 = dx * dx + dy * dy
            if comp2 <= 0:
                continue
            t = ((x - ax) * dx + (y - ay) * dy) / comp2
            t = max(0.0, min(1.0, t))
            px, py = ax + dx * t, ay + dy * t
            d2 = (x - px) ** 2 + (y - py) ** 2
            if melhor_d2 is None or d2 < melhor_d2:
                melhor, melhor_d2, melhor_t = i, d2, t
        ax, ay = pts[melhor]
        bx, by = pts[(melhor + 1) % n]
        novo = (ax + (bx - ax) * melhor_t, ay + (by - ay) * melhor_t)
        self._begin_snapshot()
        self._commit_snapshot()
        ins = melhor + 1
        obj.points.insert(ins, novo)
        curvas = list(obj.params.get("curves", []))
        era_curvo = melhor in curvas
        # desloca as marcas a partir do ponto de inserção
        curvas = [(c + 1 if c >= ins else c) for c in curvas]
        if era_curvo:
            # o segmento curvo dividido continua curvo nos dois pedaços
            curvas.append(ins)
        obj.params["curves"] = sorted(curvas)
        obj.recompile()
        self.refresh_object(obj)
        self.select(obj.id)
        self.document_changed.emit()

    # ---------------------------------------------------------- fundo
    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.fillRect(rect, self.fabric_color)
        # cores adaptadas à luminosidade do tecido
        lum = (0.299 * self.fabric_color.red() + 0.587 * self.fabric_color.green()
               + 0.114 * self.fabric_color.blue())
        on_light = lum > 140
        text_color = QColor(70, 70, 70) if on_light else QColor(175, 175, 175)
        grid_small = QColor(200, 200, 200) if on_light else QColor(72, 72, 72)
        grid_big = QColor(170, 170, 170) if on_light else QColor(96, 96, 96)
        if not self.doc.objects:
            # boas-vindas quando o desenho está vazio (tamanho constante na tela)
            painter.setPen(text_color)
            font = painter.font()
            scale = max(0.05, painter.transform().m11())
            font.setPointSizeF(min(28.0, 13.0 / scale))
            painter.setFont(font)
            painter.drawText(
                rect.adjusted(40, 40, -40, -40),
                Qt.AlignCenter | Qt.TextWordWrap,
                "🧵  Bem-vindo ao BordadoStudio 1.7!\n\n"
                "1) Desenhe com as ferramentas acima:\n"
                "Preenchimento · Linha · Retângulo · Elipse · Satin · Texto\n\n"
                "2) Escolha o TIPO DE COSTURA no painel Propriedades\n"
                "— são 22 estilos (tatami, satin, ponto cruz, ondulado, bico,\n"
                "mola, espiral, rede, tijolinho, radial, lantejoula, aplique…):\n"
                "✝ Ponto cruz · ⛓ Cadeia · 🪡 Ponto atrás\n"
                "🌿 Ponto haste · ✨ Lantejoula · ✦ Motivo cruz\n"
                "★ Motivo estrela · Preenchimento · Linha · Satin\n\n"
                "3) F6 liga a visualização 3D · F5 simula a costura\n"
                "4) Arquivo → Relatório de produção mostra tempo e custo\n\n"
                "Ajuda → Ver exemplo de efeitos (vê tudo pronto!)",
            )
        if self.show_grid:
            step = 100.0  # 10 mm
            big = 500.0   # 50 mm
            left = math.floor(rect.left() / step) * step
            top = math.floor(rect.top() / step) * step
            pen_small = QPen(grid_small)
            pen_big = QPen(grid_big)
            pen_small.setCosmetic(True)
            pen_big.setCosmetic(True)
            x = left
            while x < rect.right():
                pen = pen_big if abs(x % big) < 0.001 else pen_small
                painter.setPen(pen)
                painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
                x += step
            y = top
            while y < rect.bottom():
                pen = pen_big if abs(y % big) < 0.001 else pen_small
                painter.setPen(pen)
                painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
                y += step
        # área do bastidor
        hoop_pen = QPen(QColor(120, 160, 200), 1.6)
        hoop_pen.setCosmetic(True)
        painter.setPen(hoop_pen)
        painter.setBrush(Qt.NoBrush)
        if getattr(self.doc, "hoop_shape", "rect") == "circle":
            painter.drawEllipse(QRectF(0, 0, self.doc.hoop[0], self.doc.hoop[1]))
        else:
            painter.drawRect(QRectF(0, 0, self.doc.hoop[0], self.doc.hoop[1]))
