"""Importação e exportação de arquivos de bordado via pyembroidery."""

from __future__ import annotations

import os

import pyembroidery as pe

from .model import DesignObject, Document
from .threads import ThreadColor, find_color

# Formatos de exportação oferecidos no diálogo
EXPORT_FORMATS = [
    ("dst", "Tajima DST (.dst) — mais compatível"),
    ("pes", "Brother PES (.pes)"),
    ("pec", "Brother PEC (.pec)"),
    ("exp", "Melco EXP (.exp)"),
    ("jef", "Janome JEF (.jef)"),
    ("vp3", "Pfaff VP3 (.vp3)"),
    ("xxx", "Singer XXX (.xxx)"),
    ("u01", "Barudan U01 (.u01)"),
    ("tbf", "Tajima TBF (.tbf)"),
    ("svg", "Vetor SVG (.svg) — visualização"),
    ("csv", "CSV (.csv) — análise"),
    ("png", "Imagem PNG (.png) — visualização"),
]

# Extensões que conseguimos abrir (leitura)
READABLE_EXTS = {
    "dst", "pes", "pec", "exp", "jef", "vp3", "xxx", "u01", "tbf", "sew",
    "hus", "shv", "dat", "dsb", "dsz", "emd", "exy", "fxy", "gt", "inb",
    "ksm", "tap", "spx", "stx", "phb", "phc", "new", "max", "mit", "pcd",
    "pcq", "pcm", "pcs", "jpx", "stc", "zhs", "zxy", "bro", "10o", "100",
    "csv", "json",
}


def import_filter_string():
    exts = " ".join(f"*.{e}" for e in sorted(READABLE_EXTS))
    return f"Arquivos de bordado ({exts})"


def export_filter_string():
    return ";;".join(f"{desc} (*.{ext})" for ext, desc in EXPORT_FORMATS)


def pattern_to_objects(pattern, name_hint="Importado"):
    """Converte um EmbPattern em objetos do editor (um por bloco de cor)."""
    objects = []
    blocks = list(pattern.get_as_colorblocks())
    if not blocks:
        # sem blocos de cor: um objeto só
        stitches = [(float(x), float(y), int(c)) for x, y, c in pattern.stitches]
        if stitches:
            thread = ThreadColor("Importado", 0x808080)
            objects.append(DesignObject(
                name=name_hint, kind="import", shape="import",
                stitches=stitches, thread=thread,
            ))
        return objects

    for i, (stitches, thread) in enumerate(blocks, start=1):
        cmds = [(float(x), float(y), int(c)) for x, y, c in stitches
                if (c & 255) in (pe.STITCH, pe.JUMP, pe.TRIM)]
        if not cmds:
            continue
        color = int(getattr(thread, "color", 0x808080) or 0x808080) & 0xFFFFFF
        desc = getattr(thread, "description", "") or f"Cor {i}"
        brand = getattr(thread, "brand", "") or ""
        code = getattr(thread, "catalog_number", "") or ""
        tc = ThreadColor(name=desc, hex_color=color, code=str(code), brand=brand)
        objects.append(DesignObject(
            name=f"{name_hint} {i}" if len(blocks) > 1 else name_hint,
            kind="import", shape="import",
            stitches=cmds, thread=tc,
            params={"stitch_type": "import"},
        ))
    return objects


def import_file(path):
    """Abre arquivo de bordado e retorna lista de objetos do editor."""
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    if ext not in READABLE_EXTS:
        raise ValueError(f"Formato .{ext} não suportado para leitura.")
    pattern = pe.read(path)
    if pattern is None:
        raise ValueError("Não foi possível ler o arquivo.")
    name_hint = os.path.splitext(os.path.basename(path))[0]
    return pattern_to_objects(pattern, name_hint)


def document_to_pattern(doc: Document):
    """Monta um EmbPattern a partir dos objetos visíveis do documento."""
    p = pe.EmbPattern()
    first = True
    for obj in doc.objects:
        if not obj.visible or not obj.stitches:
            continue
        p.add_thread({
            "color": obj.thread.hex_color & 0xFFFFFF,
            "description": obj.thread.name,
            "catalog_number": obj.thread.code,
            "brand": obj.thread.brand,
        })
        if not first:
            p.add_command(pe.COLOR_CHANGE)
        first = False
        for x, y, c in obj.stitches:
            cmd = int(c) & 255
            if cmd not in (pe.STITCH, pe.JUMP, pe.TRIM):
                cmd = pe.STITCH
            p.add_stitch_absolute(cmd, x, y)
        # pequeno pulo final evita costura final sobre o próximo bloco
        last_x, last_y = obj.stitches[-1][0], obj.stitches[-1][1]
        p.add_stitch_absolute(pe.JUMP, last_x, last_y)
    p.add_command(pe.END)
    return p


def export_document(doc: Document, path, ext: str | None = None):
    """Exporta o documento para arquivo de máquina. Retorna nº de pontos."""
    if ext is None:
        ext = os.path.splitext(path)[1].lstrip(".").lower()
    ext = ext.lower()
    writable = {e for e, _ in EXPORT_FORMATS}
    if ext not in writable:
        raise ValueError(f"Formato .{ext} não suportado para gravação.")
    p = document_to_pattern(doc)
    if p.count_stitch_commands(pe.STITCH) == 0:
        raise ValueError("O desenho está vazio — nada para exportar.")
    pe.write(p, path)
    return p.count_stitches()
