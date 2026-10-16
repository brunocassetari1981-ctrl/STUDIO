"""Auto-digitização: converte imagens raster (PNG/JPG/BMP) em bordado.

Pipeline 100% próprio, sem dependências externas:
1. reduz a imagem para um tamanho de trabalho;
2. limiariza em máscara (escuro = forma, ou invertido);
3. encontra as formas ligadas (componentes conexos);
4. traça o contorno de cada forma (Moore-neighbor);
5. simplifica com Douglas-Peucker;
6. mede a cor média de cada forma para usar no fio.

Unidades do projeto: 10 unidades de cena = 1 mm.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

MAX_SIDE = 420          # lado máximo da imagem de trabalho (px)
_TRACE_LIMIT_FACTOR = 8  # trava do contorno contra laços infinitos


# ------------------------------------------------------------------ imagem
def _load_images(path):
    img = QImage(path)
    if img.isNull():
        raise ValueError("Não foi possível abrir a imagem.")
    if max(img.width(), img.height()) > MAX_SIDE:
        img = img.scaled(MAX_SIDE, MAX_SIDE,
                         Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return img.convertToFormat(QImage.Format_Grayscale8), \
        img.convertToFormat(QImage.Format_RGB32)


def _plane(img):
    """Retorna (w, h, bytes) de um QImage com bytes por linha compactados."""
    w, h = img.width(), img.height()
    bpl = img.bytesPerLine()
    data = img.constBits()
    data = data.tobytes() if hasattr(data, "tobytes") else bytes(data)
    out = bytearray(w * h)
    for y in range(h):
        out[y * w:(y + 1) * w] = data[y * bpl:y * bpl + w]
    return w, h, out


def _rgb_bytes(img):
    w, h = img.width(), img.height()
    bpl = img.bytesPerLine()
    data = img.constBits()
    data = data.tobytes() if hasattr(data, "tobytes") else bytes(data)
    return w, h, data, bpl


# ------------------------------------------------------------- contornos
def _perp(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    return abs(dy * px - dx * py + bx * ay - by * ax) / (dx * dx + dy * dy) ** 0.5


def _rdp(pts, eps):
    """Douglas-Peucker para uma cadeia aberta."""
    if len(pts) < 3:
        return pts
    x1, y1 = pts[0]
    x2, y2 = pts[-1]
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = _perp(pts[i][0], pts[i][1], x1, y1, x2, y2)
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return _rdp(pts[:idx + 1], eps)[:-1] + _rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def simplify(points, eps: float = 2.0):
    """Simplifica um polígono fechado (Douglas-Peucker nos dois arcos)."""
    pts = [(float(x), float(y)) for x, y in points]
    if len(pts) < 4 or eps <= 0:
        return pts
    n = len(pts)
    half = n // 2
    a = _rdp(pts[:half + 1], eps)
    b = _rdp(pts[half:] + [pts[0]], eps)
    out = a[:-1] + b[:-1]
    return out if len(out) >= 3 else pts


_DIRS = [(-1, 0), (-1, -1), (0, -1), (1, -1),
         (1, 0), (1, 1), (0, 1), (-1, 1)]


def _trace_boundary(pix, w, h):
    """Contorno ordenado de um componente (rastreamento de Moore)."""
    s = set(pix)
    start = min(pix, key=lambda i: ((i // w) * 2 + (i % w)))
    contour = [start]
    cur = start
    prev_dir = 0
    first = True
    limit = len(pix) * _TRACE_LIMIT_FACTOR + 16
    while True:
        x, y = cur % w, cur // w
        found = False
        start_d = 0 if first else (prev_dir + 6) % 8
        for k in range(8):
            d = (start_d + k) % 8
            dx, dy = _DIRS[d]
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                j = ny * w + nx
                if j in s:
                    prev_dir = d
                    cur = j
                    found = True
                    break
        if not found:
            break
        if cur == start and not first:
            break
        first = False
        contour.append(cur)
        if len(contour) > limit:
            break
    return [(i % w, i // w) for i in contour]


def _avg_color(rgb_img, pix, w):
    rw, rh, data, bpl = _rgb_bytes(rgb_img)
    if not pix:
        return 0x808080
    step = max(1, len(pix) // 256)
    r = g = b = 0
    n = 0
    for i in pix[::step]:
        x, y = i % w, i // w
        if x >= rw or y >= rh:
            continue
        off = y * bpl + x * 4
        b += data[off]
        g += data[off + 1]
        r += data[off + 2]
        n += 1
    if not n:
        return 0x808080
    return ((r // n) << 16) | ((g // n) << 8) | (b // n)


# ------------------------------------------------------------------ API
def trace_image(path, limiar: int = 128, inverter: bool = False,
                suavizar: float = 2.0, min_area: int = 40):
    """Traça as formas escuras da imagem.

    Retorna (largura_px, altura_px, formas) onde cada forma é
    ``{"points_px": [(x, y), ...], "rgb": 0xRRGGBB}``.
    """
    gray, rgb = _load_images(path)
    w, h, g = _plane(gray)
    mask = bytearray(w * h)
    for i, v in enumerate(g):
        mask[i] = 1 if ((v < limiar) != bool(inverter)) else 0

    label = bytearray(w * h)
    comps = []
    nxt = 1
    for start in range(w * h):
        if mask[start] and not label[start]:
            label[start] = nxt
            pix = [start]
            stack = [start]
            while stack:
                i = stack.pop()
                x, y = i % w, i // w
                for j in ((i - 1 if x > 0 else -1),
                          (i + 1 if x + 1 < w else -1),
                          (i - w if y > 0 else -1),
                          (i + w if y + 1 < h else -1)):
                    if 0 <= j < w * h and mask[j] and not label[j]:
                        label[j] = nxt
                        pix.append(j)
                        stack.append(j)
            comps.append(pix)
            nxt += 1

    formas = []
    for pix in comps:
        if len(pix) < max(4, int(min_area)):
            continue
        cont = _trace_boundary(pix, w, h)
        if len(cont) < 3:
            continue
        pts = simplify(cont, max(0.5, float(suavizar)))
        if len(pts) < 3:
            continue
        formas.append({"points_px": pts, "rgb": _avg_color(rgb, pix, w)})
    # maior primeiro (a principal costura antes das pequenas)
    formas.sort(key=lambda f: -len(f["points_px"]))
    return w, h, formas


def shapes_to_design(formas, largura_mm: float, cx: float = 0.0,
                     cy: float = 0.0):
    """Escala as formas (px) para o desenho (unidades 10 = 1 mm), centradas."""
    if not formas:
        return []
    pts_all = [p for f in formas for p in f["points_px"]]
    xs = [p[0] for p in pts_all]
    ys = [p[1] for p in pts_all]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w_px = max(max_x - min_x, 1.0)
    escala = (float(largura_mm) * 10.0) / w_px
    mid_x, mid_y = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0
    saida = []
    for f in formas:
        pts = [((x - mid_x) * escala + float(cx),
                (y - mid_y) * escala + float(cy))
               for x, y in f["points_px"]]
        saida.append({"points": pts, "rgb": int(f["rgb"]) & 0xFFFFFF})
    return saida
