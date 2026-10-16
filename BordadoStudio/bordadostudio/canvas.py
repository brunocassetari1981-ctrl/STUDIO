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

    def paint(self, painter: QPainter, option, widget=None):
        painter.setPen(QPen(QColor(30, 30, 30), 1))
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
        run: list[tuple[float, float]] = []

        def flush():
            if len(run) >= 2:
                path.moveTo(run[0][0], run[0][1])
                for px, py in run[1:]:
                    path.lineTo(px, py)

        for x, y, c in self.obj.stitches:
            if c == stitcher.STITCH:
                run.append((x, y))
            else:
                flush()
                run = []
        flush()
        self._path = path
        rect = path.boundingRect()
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
        return stroker.createStroke(self._path)

    def paint(self, painter: QPainter, option, widget=None):
        if not self.obj.visible:
            return
        color = _qcolor(self.obj.thread.hex_color)
        selected = self.canvas.selected_id == self.obj.id
        pen = QPen(color, 1.6 if selected else 1.1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self._path)
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
        self.setBackgroundBrush(QColor(43, 43, 43))
        self._panning = False
        self._pan_start = QPointF()
        self._space = False

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

    def __init__(self, doc, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.tool = "select"
        self.selected_id = ""
        self.show_grid = True
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
            obj = self.doc.new_object_from_points(shape, list(self._digitize_points))
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

        if self.tool in ("rect", "ellipse"):
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
            if self.tool == "rect":
                pts = stitcher.rect_points(x0, y0, w, h)
            else:
                pts = stitcher.ellipse_points(x0 + w / 2, y0 + h / 2, w / 2, h / 2)
            obj = self.doc.new_object_from_points(
                "rect" if self.tool == "rect" else "ellipse", pts)
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
                obj = self.doc.new_object_from_points("freehand", pts)
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

    # ---------------------------------------------------------- fundo
    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.fillRect(rect, QColor(43, 43, 43))
        if self.show_grid:
            step = 100.0  # 10 mm
            big = 500.0   # 50 mm
            left = math.floor(rect.left() / step) * step
            top = math.floor(rect.top() / step) * step
            pen_small = QPen(QColor(60, 60, 60))
            pen_big = QPen(QColor(80, 80, 80))
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
        painter.drawRect(QRectF(0, 0, self.doc.hoop[0], self.doc.hoop[1]))
