"""Modelo do documento de bordado: objetos, cores, desfazer/refazer, projeto .bds."""

from __future__ import annotations

import copy
import json
import uuid
from dataclasses import dataclass, field

from . import stitcher
from .threads import ThreadColor

PROJECT_VERSION = 1
DEFAULT_HOOP = (1000.0, 1000.0)  # 100 mm x 100 mm em unidades


@dataclass
class DesignObject:
    """Um objeto do desenho (forma editável ou bloco importado)."""

    name: str
    kind: str = "shape"                  # 'shape' | 'import'
    shape: str = "polygon"               # polygon|freehand|rect|ellipse|satin|import
    points: list = field(default_factory=list)   # geometria em unidades
    params: dict = field(default_factory=dict)
    thread: ThreadColor = field(default_factory=lambda: ThreadColor("Vermelho", 0xD62828))
    visible: bool = True
    stitches: list = field(default_factory=list)  # comandos compilados (cache)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "shape": self.shape,
            "points": [[float(x), float(y)] for x, y in self.points],
            "params": dict(self.params),
            "thread": self.thread.to_dict(),
            "visible": self.visible,
            "stitches": [[float(x), float(y), int(c)] for x, y, c in self.stitches],
        }

    @staticmethod
    def from_dict(d):
        obj = DesignObject(
            name=d.get("name", "Objeto"),
            kind=d.get("kind", "shape"),
            shape=d.get("shape", "polygon"),
            points=[(float(x), float(y)) for x, y in d.get("points", [])],
            params=dict(d.get("params", {})),
            thread=ThreadColor.from_dict(d.get("thread", {})),
            visible=bool(d.get("visible", True)),
            id=d.get("id", uuid.uuid4().hex[:8]),
        )
        obj.stitches = [(float(x), float(y), int(c)) for x, y, c in d.get("stitches", [])]
        return obj

    def recompile(self):
        """Regenera os pontos de costura a partir da geometria."""
        if self.kind == "import":
            return
        self.stitches = stitcher.compile_shape(self.shape, self.points, self.params)

    def translate(self, dx: float, dy: float):
        self.points = [(x + dx, y + dy) for x, y in self.points]
        self.stitches = stitcher.translate_cmds(self.stitches, dx, dy)

    def bounds(self):
        return stitcher.bounds_of(self.stitches)

    def stitch_count(self):
        return stitcher.stitch_count(self.stitches)


class Document:
    """Documento de bordado com histórico de desfazer/refazer."""

    def __init__(self):
        self.title = "Sem título"
        self.objects: list[DesignObject] = []
        self.hoop = list(DEFAULT_HOOP)
        self._undo: list[str] = []
        self._redo: list[str] = []
        self.modified = False

    # ---------- serialização ----------
    def to_dict(self):
        return {
            "app": "BordadoStudio",
            "version": PROJECT_VERSION,
            "title": self.title,
            "hoop": list(self.hoop),
            "objects": [o.to_dict() for o in self.objects],
        }

    @staticmethod
    def from_dict(d):
        doc = Document()
        doc.title = d.get("title", "Sem título")
        doc.hoop = list(d.get("hoop", DEFAULT_HOOP))
        doc.objects = [DesignObject.from_dict(o) for o in d.get("objects", [])]
        return doc

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=1)

    @staticmethod
    def from_json(text):
        return Document.from_dict(json.loads(text))

    def save_file(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        self.modified = False

    @staticmethod
    def load_file(path):
        with open(path, "r", encoding="utf-8") as f:
            doc = Document.from_json(f.read())
        doc.modified = False
        return doc

    # ---------- desfazer / refazer ----------
    def snapshot(self):
        """Registra estado atual para desfazer (chamar ANTES de cada mutação)."""
        self._undo.append(self.to_json())
        if len(self._undo) > 50:
            self._undo.pop(0)
        self._redo.clear()
        self.modified = True

    def can_undo(self):
        return bool(self._undo)

    def can_redo(self):
        return bool(self._redo)

    def undo(self):
        if not self._undo:
            return False
        self._redo.append(self.to_json())
        state = self._undo.pop()
        self._restore(state)
        return True

    def redo(self):
        if not self._redo:
            return False
        self._undo.append(self.to_json())
        state = self._redo.pop()
        self._restore(state)
        return True

    def _restore(self, state):
        d = json.loads(state)
        self.title = d.get("title", self.title)
        self.hoop = list(d.get("hoop", self.hoop))
        self.objects = [DesignObject.from_dict(o) for o in d.get("objects", [])]
        self.modified = True

    # ---------- objetos ----------
    def add_object(self, obj: DesignObject, snapshot: bool = True):
        if snapshot:
            self.snapshot()
        if obj.kind != "import":
            obj.recompile()
        self.objects.append(obj)
        return obj

    def remove_object(self, obj: DesignObject):
        if obj in self.objects:
            self.snapshot()
            self.objects.remove(obj)

    def find(self, obj_id: str):
        for o in self.objects:
            if o.id == obj_id:
                return o
        return None

    def move_object(self, obj: DesignObject, delta: int):
        """Reordena (delta=-1 sobe, +1 desce) na ordem de costura."""
        idx = self.objects.index(obj)
        new = max(0, min(len(self.objects) - 1, idx + delta))
        if new != idx:
            self.snapshot()
            self.objects.pop(idx)
            self.objects.insert(new, obj)

    def total_stitches(self):
        return sum(o.stitch_count() for o in self.objects if o.visible)

    def bounds(self):
        boxes = [o.bounds() for o in self.objects if o.visible and o.stitches]
        if not boxes:
            return (0.0, 0.0, 0.0, 0.0)
        return (
            min(b[0] for b in boxes),
            min(b[1] for b in boxes),
            max(b[2] for b in boxes),
            max(b[3] for b in boxes),
        )

    def new_object_from_points(self, shape: str, points, params=None,
                               thread: ThreadColor | None = None, name=""):
        defaults = {
            "stitch_type": "fill",
            "stitch_length": stitcher.DEFAULT_STITCH_LENGTH,
            "spacing": stitcher.DEFAULT_FILL_SPACING,
            "angle": 0.0,
            "width": stitcher.DEFAULT_SATIN_WIDTH,
            "density": stitcher.DEFAULT_SATIN_DENSITY,
            "edge_underlay": True,
            "closed": True,
        }
        if shape == "satin":
            defaults["stitch_type"] = "satin"
        if shape == "freehand":
            defaults["stitch_type"] = "run"
        defaults.update(params or {})
        names = {
            "polygon": "Preenchimento",
            "freehand": "Linha",
            "rect": "Retângulo",
            "ellipse": "Elipse",
            "satin": "Satin",
        }
        obj = DesignObject(
            name=name or names.get(shape, "Objeto"),
            kind="shape",
            shape=shape,
            points=[(float(x), float(y)) for x, y in points],
            params=defaults,
            thread=thread or ThreadColor("Vermelho", 0xD62828),
        )
        return self.add_object(obj)
