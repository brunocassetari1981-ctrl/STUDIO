"""Geração de pontos de bordado a partir de geometria.

Todas as funções recebem coordenadas em unidades de bordado
(1 unidade = 0,1 mm) e retornam listas de comandos (x, y, comando).

Comandos (mesmos valores da especificação de bordado):
    STITCH = 0  -> ponto de costura
    JUMP   = 1  -> pulo de agulha
    TRIM   = 2  -> corte de linha
"""

from __future__ import annotations

import math

STITCH = 0
JUMP = 1
TRIM = 2

# Parâmetros padrão (em unidades de 0,1 mm)
DEFAULT_STITCH_LENGTH = 25.0      # 2,5 mm entre pontos
DEFAULT_FILL_SPACING = 18.0       # 1,8 mm entre linhas de preenchimento
DEFAULT_SATIN_WIDTH = 40.0        # 4 mm de largura do satin
DEFAULT_SATIN_DENSITY = 8.0       # passo do zig-zag
DEFAULT_EDGE_MARGIN = 2.0


def _dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def resample_polyline(points, step: float):
    """Reamostra uma polilinha em passos máximos de `step`."""
    if not points:
        return []
    if len(points) == 1 or step <= 0:
        return [tuple(map(float, points[0]))]
    out = [tuple(map(float, points[0]))]
    for i in range(1, len(points)):
        x0, y0 = out[-1] if False else points[i - 1]
        x1, y1 = points[i]
        d = math.hypot(x1 - x0, y1 - y0)
        if d == 0:
            continue
        n = max(1, int(round(d / step)))
        for k in range(1, n + 1):
            t = k / n
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    return out


def close_polygon(points):
    """Garante que o polígono esteja fechado."""
    if len(points) < 2:
        return [tuple(map(float, p)) for p in points]
    pts = [tuple(map(float, p)) for p in points]
    if _dist(pts[0], pts[-1]) > 1e-6:
        pts.append(pts[0])
    return pts


def running_stitch(points, stitch_length: float = DEFAULT_STITCH_LENGTH):
    """Pontos de linha simples (run stitch) ao longo da polilinha."""
    if len(points) < 2:
        return []
    step = max(1.0, float(stitch_length))
    dense = resample_polyline(points, step)
    return [(x, y, STITCH) for x, y in dense]


def _polygon_scanline_rows(polygon, spacing: float):
    """Interseções da linha de varredura com o polígono (regra par-ímpar)."""
    if len(polygon) < 3:
        return []
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    min_y, max_y = min(ys), max(ys)
    spacing = max(2.0, float(spacing))
    rows = []
    y = min_y + spacing * 0.5
    while y <= max_y:
        inter = []
        n = len(polygon)
        for i in range(n):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % n]
            if y1 == y2:
                continue
            ymin, ymax = (y1, y2) if y1 < y2 else (y2, y1)
            if y < ymin or y >= ymax:
                continue
            t = (y - y1) / (y2 - y1)
            inter.append(x1 + t * (x2 - x1))
        inter.sort()
        for i in range(0, len(inter) - 1, 2):
            if inter[i + 1] - inter[i] > 0.5:
                rows.append((y, inter[i], inter[i + 1]))
        y += spacing
    return rows


def fill_stitch(polygon, spacing: float = DEFAULT_FILL_SPACING,
                angle_deg: float = 0.0,
                stitch_length: float = DEFAULT_STITCH_LENGTH,
                edge_underlay: bool = True):
    """Preenchimento tatami (fill) com linhas paralelas dentro do polígono."""
    if len(polygon) < 3:
        return []
    spacing = max(2.0, float(spacing))
    step = max(1.0, float(stitch_length))
    ang = math.radians(float(angle_deg))
    ca, sa = math.cos(-ang), math.sin(-ang)

    def rot(p):
        x, y = p
        return (x * ca - y * sa, x * sa + y * ca)

    def unrot(p):
        x, y = p
        return (x * ca + y * sa, -x * sa + y * ca)

    poly = [rot((float(x), float(y))) for x, y in polygon]
    rows = _polygon_scanline_rows(poly, spacing)

    cmds = []
    if edge_underlay:
        edge = close_polygon(polygon)
        edge_pts = resample_polyline(edge, max(step * 1.5, 20.0))
        if len(edge_pts) >= 2:
            cmds.extend((x, y, STITCH) for x, y in edge_pts)

    prev_end = None
    for idx, (y, x1, x2) in enumerate(rows):
        length = x2 - x1
        n = max(1, int(round(length / step)))
        if idx % 2 == 0:
            xs = [x1 + (length) * k / n for k in range(n + 1)]
        else:
            xs = [x2 - (length) * k / n for k in range(n + 1)]
        pts = [(x, y) for x in xs]
        if prev_end is not None and _dist(prev_end, pts[0]) > spacing * 1.8:
            cmds.append((pts[0][0], pts[0][1], JUMP))
        for x, yy in pts:
            ux, uy = unrot((x, yy))
            cmds.append((ux, uy, STITCH))
        prev_end = pts[-1]
    return cmds


def satin_stitch(centerline, width: float = DEFAULT_SATIN_WIDTH,
                 density: float = DEFAULT_SATIN_DENSITY,
                 edge_underlay: bool = True):
    """Bordado satin: zig-zag entre duas margens de uma coluna."""
    if len(centerline) < 2:
        return []
    width = max(2.0, float(width))
    density = max(2.0, float(density))
    pts = resample_polyline(centerline, density)
    if len(pts) < 2:
        return []

    left, right = [], []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        if i == 0:
            tx, ty = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            tx, ty = x - pts[-2][0], y - pts[-2][1]
        else:
            tx, ty = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        norm = math.hypot(tx, ty)
        if norm < 1e-9:
            nx, ny = 0.0, 0.0
        else:
            nx, ny = -ty / norm, tx / norm
        half = width / 2.0
        left.append((x + nx * half, y + ny * half))
        right.append((x - nx * half, y - ny * half))

    cmds = []
    if edge_underlay:
        for x, y in left:
            cmds.append((x, y, STITCH))
        for x, y in reversed(right):
            cmds.append((x, y, STITCH))
        cmds.append((left[0][0], left[0][1], JUMP))

    for i in range(n):
        side = left if i % 2 == 0 else right
        x, y = side[i]
        cmds.append((x, y, STITCH))
    return cmds


def rect_points(x: float, y: float, w: float, h: float):
    """Retângulo como 4 cantos (polígono aberto; o fechamento é automático)."""
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def ellipse_points(cx: float, cy: float, rx: float, ry: float, segments: int = 48):
    """Elipse aproximada por polígono regular."""
    segments = max(8, int(segments))
    pts = []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


# ---------------------------------------------------------- formas prontas
def heart_points(cx: float, cy: float, rx: float, ry: float, segments: int = 64):
    """Coração (parâmetro clássico de 16 sin³t / 13 cos t − …)."""
    segments = max(24, int(segments))
    pts = []
    for i in range(segments):
        t = 2.0 * math.pi * i / segments
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x / 17.0 * rx, cy - y / 17.0 * ry))
    return pts


def star_points(cx: float, cy: float, rx: float, ry: float, points: int = 5,
                inner: float = 0.45):
    """Estrela de N pontas (intercalando raio externo e interno)."""
    points = max(3, int(points))
    inner = min(0.9, max(0.1, float(inner)))
    pts = []
    for i in range(points * 2):
        a = -math.pi / 2 + math.pi * i / points
        k = 1.0 if i % 2 == 0 else inner
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return pts


def diamond_points(cx: float, cy: float, rx: float, ry: float):
    """Losango (rombo)."""
    return [(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]


def triangle_points(cx: float, cy: float, rx: float, ry: float):
    """Triângulo equilátero apontando para cima."""
    pts = []
    for i in range(3):
        a = -math.pi / 2 + 2.0 * math.pi * i / 3
        pts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
    return pts


def hexagon_points(cx: float, cy: float, rx: float, ry: float):
    """Hexágono regular."""
    pts = []
    for i in range(6):
        a = -math.pi / 2 + 2.0 * math.pi * i / 6
        pts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
    return pts


def cross_points(cx: float, cy: float, rx: float, ry: float, thick: float = 0.33):
    """Cruz grega (sinal de +) como polígono de 12 cantos."""
    t = min(0.45, max(0.15, float(thick)))
    ax, ay = rx, ry                      # meia-extensão total
    bx, by = rx * t, ry * t              # meia-espessura dos braços
    return [
        (cx - ax, cy - by), (cx - bx, cy - by), (cx - bx, cy - ay),
        (cx + bx, cy - ay), (cx + bx, cy - by), (cx + ax, cy - by),
        (cx + ax, cy + by), (cx + bx, cy + by), (cx + bx, cy + ay),
        (cx - bx, cy + ay), (cx - bx, cy + by), (cx - ax, cy + by),
    ]


def compile_shape(shape: str, points, params: dict):
    """Compila uma forma do editor em lista de comandos de costura."""
    stitch_type = params.get("stitch_type", "fill")
    stitch_length = float(params.get("stitch_length", DEFAULT_STITCH_LENGTH))
    spacing = float(params.get("spacing", DEFAULT_FILL_SPACING))
    width = float(params.get("width", DEFAULT_SATIN_WIDTH))

    if shape == "text":
        return _compile_text(points, params)

    if stitch_type == "applique" and len(points) >= 3:
        poly = close_polygon(points)
        cmds = [(poly[0][0], poly[0][1], JUMP)]
        # 1) linha de posicionamento + 2) fixação
        cmds.extend(running_stitch(poly, stitch_length))
        cmds.append((poly[0][0], poly[0][1], JUMP))
        cmds.extend(running_stitch(poly, stitch_length))
        cmds.append((poly[0][0], poly[0][1], JUMP))
        # 3) borda em zigue-zague (blanket)
        cmds.extend(satin_stitch(poly, width=max(20.0, width * 0.5),
                                 density=max(6.0, width * 0.15),
                                 edge_underlay=False))
        return cmds

    if shape == "satin":
        return satin_stitch(
            points,
            width=width,
            density=float(params.get("density", DEFAULT_SATIN_DENSITY)),
            edge_underlay=bool(params.get("edge_underlay", True)),
        )

    closed = params.get("closed", True) and len(points) >= 3
    path = close_polygon(points) if closed else points

    if stitch_type == "satin":
        # borda satinada ao longo do contorno da forma
        return satin_stitch(
            path,
            width=width,
            density=float(params.get("density", DEFAULT_SATIN_DENSITY)),
            edge_underlay=bool(params.get("edge_underlay", True)),
        )

    if stitch_type == "run":
        return running_stitch(path, stitch_length)

    if stitch_type == "cross":
        return cross_stitch(close_polygon(points) if len(points) >= 3 else points,
                            cell=spacing)

    if stitch_type == "chain":
        return chain_stitch(path, link=spacing * 1.4, width=width * 0.55)

    if stitch_type == "backstitch":
        return backstitch(path, step=spacing)

    if stitch_type == "stem":
        return stem_stitch(path, step=spacing * 0.6, width=width * 0.4)

    if stitch_type == "sequin":
        return motif_fill(close_polygon(points) if len(points) >= 3 else points,
                          motif="sequin", size=width, spacing=spacing * 1.6)

    if stitch_type == "motif_cross":
        return motif_fill(close_polygon(points) if len(points) >= 3 else points,
                          motif="cross", size=width * 0.7, spacing=spacing * 1.6)

    if stitch_type == "motif_star":
        return motif_fill(close_polygon(points) if len(points) >= 3 else points,
                          motif="star", size=width * 0.8, spacing=spacing * 1.6)

    # ---- contornos novos (v1.6) ----
    if stitch_type == "run2":
        return double_run(path, stitch_length)

    if stitch_type == "zigzag":
        return zigzag_stitch(path, spacing=spacing, width=width)

    if stitch_type == "scallop":
        return scallop_stitch(path, spacing=spacing, stitch_length=stitch_length)

    if stitch_type == "spring":
        return spring_stitch(path, spacing=spacing, width=width)

    if stitch_type == "motif_run":
        return motif_run(path, spacing=spacing, stitch_length=stitch_length)

    # ---- enchimentos novos (v1.6) ----
    if stitch_type == "fill_contour" and len(points) >= 3:
        return fill_contour(close_polygon(points), spacing=spacing,
                            stitch_length=stitch_length)

    if stitch_type == "fill_radial" and len(points) >= 3:
        return fill_radial(close_polygon(points), spacing=spacing,
                           stitch_length=stitch_length)

    if stitch_type == "fill_mesh" and len(points) >= 3:
        return fill_mesh(close_polygon(points), spacing=spacing,
                         stitch_length=stitch_length)

    if stitch_type == "fill_spiral" and len(points) >= 3:
        return fill_spiral(close_polygon(points), spacing=spacing,
                           stitch_length=stitch_length)

    if stitch_type == "fill_brick" and len(points) >= 3:
        return fill_brick(close_polygon(points), spacing=spacing,
                          stitch_length=stitch_length)

    if shape == "freehand":
        return running_stitch(points, stitch_length)

    poly = close_polygon(points) if len(points) >= 3 else points
    return fill_stitch(
        poly,
        spacing=spacing,
        angle_deg=float(params.get("angle", 0.0)),
        stitch_length=stitch_length,
        edge_underlay=bool(params.get("edge_underlay", True)),
    )


def translate_cmds(cmds, dx: float, dy: float):
    """Desloca todos os comandos."""
    return [(x + dx, y + dy, c) for x, y, c in cmds]


# ============================================================
#  Texto bordado (usa o alfabeto do módulo lettering)
# ============================================================

def _compile_text(points, params: dict):
    """Compila um objeto de texto em pontos de costura."""
    from . import lettering

    text = params.get("text", "")
    if not text.strip():
        return []
    size = float(params.get("size", lettering.DEFAULT_SIZE))
    tracking = float(params.get("spacing", lettering.DEFAULT_TRACKING))
    strokes, w, h = lettering.text_strokes(text, size, tracking)
    if not strokes:
        return []

    # transformações do bloco de texto
    cx, cy = w / 2.0, h / 2.0
    if params.get("flip_h"):
        strokes = [[(2 * cx - x, y) for x, y in s] for s in strokes]
    if params.get("flip_v"):
        strokes = [[(x, 2 * cy - y) for x, y in s] for s in strokes]
    for _ in range(int(params.get("rotation", 0)) // 90 % 4):
        strokes = [[(cx + (y - cy), cy - (x - cx)) for x, y in s]
                   for s in strokes]

    # ancora no ponto de origem (canto superior esquerdo do bloco)
    x0, y0 = points[0] if points else (0.0, 0.0)
    all_x = [x for s in strokes for x, y in s]
    all_y = [y for s in strokes for x, y in s]
    min_x, min_y = min(all_x), min(all_y)
    strokes = [[(x - min_x + x0, y - min_y + y0) for x, y in s] for s in strokes]

    stitch_type = params.get("stitch_type", "run")
    stitch_length = float(params.get("stitch_length", DEFAULT_STITCH_LENGTH))
    width = float(params.get("width", 25.0))

    cmds = []
    first = True
    for stroke in strokes:
        if not first:
            cmds.append((stroke[0][0], stroke[0][1], JUMP))
        first = False
        if stitch_type == "satin":
            cmds.extend(satin_stitch(stroke, width=width,
                                     density=max(5.0, width * 0.22),
                                     edge_underlay=False))
        elif stitch_type == "stem":
            cmds.extend(stem_stitch(stroke, step=max(8.0, stitch_length * 0.5),
                                    width=max(8.0, width * 0.5)))
        elif stitch_type == "chain":
            cmds.extend(chain_stitch(stroke, link=max(14.0, stitch_length),
                                     width=max(10.0, width * 0.6)))
        elif stitch_type == "backstitch":
            cmds.extend(backstitch(stroke, step=stitch_length))
        else:
            cmds.extend(running_stitch(stroke, stitch_length))
    return cmds


def bounds_of(cmds):
    """Limites (min_x, min_y, max_x, max_y) dos pontos."""
    xs = [c[0] for c in cmds]
    ys = [c[1] for c in cmds]
    if not xs:
        return (0, 0, 0, 0)
    return (min(xs), min(ys), max(xs), max(ys))


def stitch_count(cmds):
    """Quantidade de pontos de costura reais (STITCH)."""
    return sum(1 for c in cmds if c[2] == STITCH)


# ============================================================
#  Efeitos especiais: ponto cruz, bordado à mão, lantejoulas
# ============================================================

def point_in_polygon(x, y, polygon):
    """Teste ponto no polígono (regra par-ímpar)."""
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                inside = not inside
    return inside


def _normals(pts):
    """Normais unitárias em cada ponto de uma polilinha."""
    out = []
    n = len(pts)
    for i in range(n):
        if i == 0:
            tx, ty = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
        elif i == n - 1:
            tx, ty = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
        else:
            tx, ty = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        d = math.hypot(tx, ty)
        if d < 1e-9:
            out.append((0.0, 0.0))
        else:
            out.append((-ty / d, tx / d))
    return out


def cross_stitch(polygon, cell: float = 26.0):
    """Ponto cruz: células com X dentro do polígono."""
    if len(polygon) < 3:
        return []
    cell = max(10.0, float(cell))
    half = cell * 0.32
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    cmds = []
    prev = None
    y = min_y + cell * 0.5
    row_idx = 0
    while y <= max_y:
        row = []
        x = min_x + cell * 0.5
        while x <= max_x:
            if point_in_polygon(x, y, polygon):
                row.append(x)
            x += cell
        if row_idx % 2 == 1:
            row.reverse()
        for x in row:
            if prev is not None and math.hypot(x - prev[0], y - prev[1]) > cell * 1.6:
                cmds.append((x, y, JUMP))
            cmds.append((x - half, y - half, STITCH))
            cmds.append((x + half, y + half, STITCH))
            cmds.append((x - half, y + half, STITCH))
            cmds.append((x + half, y - half, STITCH))
            prev = (x, y)
        y += cell
        row_idx += 1
    return cmds


def chain_stitch(centerline, link: float = 30.0, width: float = 22.0):
    """Cadeia (chain stitch) — laços alternados, visual de bordado à mão."""
    if len(centerline) < 2:
        return []
    link = max(10.0, float(link))
    width = max(4.0, float(width))
    pts = resample_polyline(centerline, link)
    cmds = []
    side = 1.0
    arc_steps = 8
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        dx, dy = x1 - x0, y1 - y0
        d = math.hypot(dx, dy)
        if d < 1e-9:
            continue
        ux, uy = dx / d, dy / d
        nx, ny = -uy * side, ux * side
        for s in range(arc_steps + 1):
            th = math.pi * (1.0 - s / arc_steps)   # pi -> 0
            px = mx + ux * (d / 2.0) * math.cos(th) + nx * (width / 2.0) * math.sin(th)
            py = my + uy * (d / 2.0) * math.cos(th) + ny * (width / 2.0) * math.sin(th)
            cmds.append((px, py, STITCH))
        side = -side
    return cmds


def backstitch(points, step: float = 24.0):
    """Ponto atrás (backstitch) — segmentos sobrepostos como costura manual."""
    if len(points) < 2:
        return []
    step = max(8.0, float(step))
    pts = resample_polyline(points, step)
    cmds = []
    i = 0
    while i < len(pts) - 1:
        j = min(i + 2, len(pts) - 1)
        cmds.append((pts[i][0], pts[i][1], JUMP))
        cmds.append((pts[i][0], pts[i][1], STITCH))
        cmds.append((pts[j][0], pts[j][1], STITCH))
        i += 1
    return cmds


def stem_stitch(centerline, step: float = 14.0, width: float = 16.0):
    """Ponto haste (stem stitch) — trança inclinada ao longo do caminho."""
    if len(centerline) < 2:
        return []
    step = max(5.0, float(step))
    width = max(3.0, float(width))
    pts = resample_polyline(centerline, step)
    normals = _normals(pts)
    cmds = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        nx, ny = normals[i]
        mx, my = normals[i + 1]
        cmds.append((x0 - nx * width / 2.0, y0 - ny * width / 2.0, STITCH))
        cmds.append((x1 + mx * width / 2.0, y1 + my * width / 2.0, STITCH))
    return cmds


def _sequin_motif(x, y, size):
    """Uma lantejoula: contorno circular + ponto central de fixação."""
    r = max(6.0, size / 2.0)
    cmds = []
    n = 14
    for k in range(n + 1):
        a = 2.0 * math.pi * k / n
        cmds.append((x + r * math.cos(a), y + r * math.sin(a), STITCH))
    cmds.append((x, y, JUMP))
    cmds.append((x, y, STITCH))
    return cmds


def _motif_cross(x, y, size):
    h = size / 2.0
    return [
        (x - h, y - h, STITCH), (x + h, y + h, STITCH),
        (x - h, y + h, STITCH), (x + h, y - h, STITCH),
    ]


def _motif_star(x, y, size):
    cmds = []
    r_out, r_in = size / 2.0, size / 5.0
    for k in range(11):
        a = -math.pi / 2 + 2.0 * math.pi * k / 10
        r = r_out if k % 2 == 0 else r_in
        cmds.append((x + r * math.cos(a), y + r * math.sin(a), STITCH))
    return cmds


_MOTIFS = {
    "sequin": _sequin_motif,
    "cross": _motif_cross,
    "star": _motif_star,
}


def motif_fill(polygon, motif: str = "sequin", size: float = 28.0,
               spacing: float = 36.0):
    """Preenchimento com motivo repetido (lantejoula, cruz, estrela)."""
    if len(polygon) < 3:
        return []
    maker = _MOTIFS.get(motif, _sequin_motif)
    size = max(10.0, float(size))
    spacing = max(size * 1.1, float(spacing))
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    cmds = []
    first = True
    y = min_y + spacing * 0.5
    row_idx = 0
    while y <= max_y:
        row = []
        x = min_x + spacing * 0.5
        while x <= max_x:
            if point_in_polygon(x, y, polygon):
                row.append(x)
            x += spacing
        if row_idx % 2 == 1:
            row.reverse()
        for x in row:
            if not first:
                cmds.append((x, y, JUMP))
            cmds.extend(maker(x, y, size))
            first = False
        y += spacing
        row_idx += 1
    return cmds


# ============================================================
# v1.6 — catálogo de contornos e enchimentos
# ============================================================

def double_run(points, stitch_length: float = DEFAULT_STITCH_LENGTH):
    """Ponto duplo (Holbein): vai e volta sobre a mesma linha."""
    fwd = running_stitch(points, stitch_length)
    if len(fwd) < 2:
        return fwd
    back = [(x, y, STITCH) for x, y, _c in reversed(fwd)]
    return fwd + back


def zigzag_stitch(points, spacing: float = DEFAULT_FILL_SPACING,
                  width: float = DEFAULT_SATIN_WIDTH):
    """Ondulado (zigzag) ao longo do contorno."""
    if len(points) < 2:
        return []
    amp = max(4.0, float(width) * 0.35)
    step = max(6.0, float(spacing))
    dense = resample_polyline(points, step / 2.0)
    if len(dense) < 2:
        return []
    normals = _normals(dense)
    cmds = []
    for i, ((x, y), (nx, ny)) in enumerate(zip(dense, normals)):
        side = 1.0 if i % 2 == 0 else -1.0
        cmds.append((x + nx * amp * side, y + ny * amp * side, STITCH))
    return cmds


def scallop_stitch(points, spacing: float = DEFAULT_FILL_SPACING,
                   stitch_length: float = DEFAULT_STITCH_LENGTH):
    """Bico (scallop): arcos entre pontos consecutivos do contorno."""
    if len(points) < 2:
        return []
    step = max(1.0, float(stitch_length))
    cmds = []
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        d = _dist((x0, y0), (x1, y1))
        if d < 1e-6:
            continue
        # arco semicircular para o lado externo
        mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        ux, uy = (x1 - x0) / d, (y1 - y0) / d
        r = d / 2.0
        n = max(6, int(math.pi * r / step))
        for k in range(n + 1):
            a = math.pi * k / n
            # ponto do arco (base + altura senoidal)
            px = mx - ux * r * math.cos(a)
            py = my - uy * r * math.sin(a) * 0.0 + (-uy) * 0.0
            # rotaciona (ux,uy) 90° para a normal esquerda
            nxv, nyv = -uy, ux
            px = (x0 + x1) / 2.0 + ux * (-r * math.cos(a))
            py = (y0 + y1) / 2.0 + uy * (-r * math.cos(a))
            px += nxv * (r * math.sin(a))
            py += nyv * (r * math.sin(a))
            cmds.append((px, py, STITCH))
        cmds.append((x1, y1, STITCH))
    return cmds


def spring_stitch(points, spacing: float = DEFAULT_FILL_SPACING,
                  width: float = DEFAULT_SATIN_WIDTH):
    """Mola (coil): pequenas voltas ao longo do contorno."""
    if len(points) < 2:
        return []
    loop_w = max(12.0, float(width) * 0.7)
    step = max(20.0, float(spacing) * 1.4)
    dense = resample_polyline(points, step)
    if len(dense) < 2:
        return []
    normals = _normals(dense)
    cmds = []
    for (x, y), (nx, ny) in zip(dense, normals):
        # volta completa de 8 pontos ao redor do ponto
        for k in range(9):
            a = 2.0 * math.pi * k / 8.0
            px = x + nx * loop_w * 0.5 * math.cos(a) + (-ny) * loop_w * 0.32 * math.sin(a)
            py = y + ny * loop_w * 0.5 * math.cos(a) + nx * loop_w * 0.32 * math.sin(a)
            cmds.append((px, py, STITCH))
    return cmds


def motif_run(points, spacing: float = DEFAULT_FILL_SPACING,
              stitch_length: float = DEFAULT_STITCH_LENGTH,
              motif: str = "circle"):
    """Ponto motivo: motivos repetidos ao longo do contorno."""
    if len(points) < 2:
        return []
    step = max(24.0, float(spacing) * 1.8)
    dense = resample_polyline(close_polygon(points)
                              if len(points) >= 3 else points, step)
    cmds = []
    first = True
    r = max(6.0, float(spitch) if False else float(spacing) * 0.35)
    for x, y in dense:
        if not first:
            cmds.append((x, y, JUMP))
        # pequeno círculo (motivo)
        n = 8
        for k in range(n + 1):
            a = 2.0 * math.pi * k / n
            cmds.append((x + r * math.cos(a), y + r * math.sin(a), STITCH))
        first = False
    return cmds


# ---------------------------------------------------------- enchimentos novos

def _centroid(polygon):
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _rows_rotated(polygon, spacing: float, angle_deg: float):
    """Linhas de varredura rotacionadas; devolve ((x1,y1),(x2,y2)) no espaço original."""
    ang = math.radians(float(angle_deg))
    ca, sa = math.cos(-ang), math.sin(-ang)

    def rot(p):
        x, y = p
        return (x * ca - y * sa, x * sa + y * ca)

    def unrot(p):
        x, y = p
        return (x * ca + y * sa, -x * sa + y * ca)

    poly = [rot((float(x), float(y))) for x, y in polygon]
    out = []
    for y, x1, x2 in _polygon_scanline_rows(poly, spacing):
        out.append((unrot((x1, y)), unrot((x2, y))))
    return out


def fill_contour(polygon, spacing: float = DEFAULT_FILL_SPACING,
                 stitch_length: float = DEFAULT_STITCH_LENGTH):
    """Contorno concêntrico: anéis encolhendo em direção ao centro."""
    if len(polygon) < 3:
        return []
    step = max(1.0, float(stitch_length))
    gap = max(3.0, float(spacing))
    cx, cy = _centroid(polygon)
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    rmax = max(math.hypot(x - cx, y - cy) for x, y in polygon) or 1.0
    cmds = []
    r = rmax
    first = True
    while r > gap:
        k = r / rmax
        ring = [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in polygon]
        pts = resample_polyline(close_polygon(ring), step)
        if len(pts) >= 2:
            if not first:
                cmds.append((pts[0][0], pts[0][1], JUMP))
            cmds.extend((x, y, STITCH) for x, y in pts)
            first = False
        r -= gap
    return cmds


def fill_radial(polygon, spacing: float = DEFAULT_FILL_SPACING,
                stitch_length: float = DEFAULT_STITCH_LENGTH):
    """Radial: raios do centro até a borda (efeito leque/sol)."""
    if len(polygon) < 3:
        return []
    step = max(1.0, float(stitch_length))
    gap = max(3.0, float(spacing))
    cx, cy = _centroid(polygon)
    edge = resample_polyline(close_polygon(polygon), gap)
    cmds = []
    first = True
    for x, y in edge:
        if not first:
            cmds.append((cx, cy, JUMP))
        d = math.hypot(x - cx, y - cy)
        n = max(1, int(round(d / step)))
        for k in range(n + 1):
            t = k / n
            cmds.append((cx + (x - cx) * t, cy + (y - cy) * t, STITCH))
        first = False
    return cmds


def fill_mesh(polygon, spacing: float = DEFAULT_FILL_SPACING,
              stitch_length: float = DEFAULT_STITCH_LENGTH):
    """Rede (malha): dois cruzamentos de linhas simples."""
    if len(polygon) < 3:
        return []
    step = max(1.0, float(stitch_length))
    gap = max(8.0, float(spacing) * 1.6)
    cmds = []
    first = True
    for ang in (0.0, 90.0):
        for (x1, y1), (x2, y2) in _rows_rotated(polygon, gap, ang):
            n = max(1, int(round(_dist((x1, y1), (x2, y2)) / step)))
            pts = [(x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n)
                   for k in range(n + 1)]
            if not first:
                cmds.append((pts[0][0], pts[0][1], JUMP))
            cmds.extend((x, y, STITCH) for x, y in pts)
            first = False
    return cmds


def fill_spiral(polygon, spacing: float = DEFAULT_FILL_SPACING,
                stitch_length: float = DEFAULT_STITCH_LENGTH):
    """Espiral: arquimediana partindo do centro, cortada no polígono."""
    if len(polygon) < 3:
        return []
    step = max(1.0, float(stitch_length))
    gap = max(3.0, float(spacing))
    cx, cy = _centroid(polygon)
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    rmax = max(math.hypot(x - cx, y - cy) for x, y in polygon) or 1.0
    cmds = []
    running = False
    r = 0.0
    a = 0.0
    while r < rmax * 1.2:
        r += gap / (2.0 * math.pi) * 0.55
        a += 0.55
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        inside = point_in_polygon(x, y, polygon)
        if inside:
            cmds.append((x, y, STITCH))
            running = True
        elif running:
            running = False
    return cmds


def fill_brick(polygon, spacing: float = DEFAULT_FILL_SPACING,
               stitch_length: float = DEFAULT_STITCH_LENGTH):
    """Tijolinho: fileiras de traços curtos deslocados (padrão alvenaria)."""
    if len(polygon) < 3:
        return []
    step = max(1.0, float(stitch_length))
    gap = max(6.0, float(spacing))
    brick = gap * 2.4
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    cmds = []
    first = True
    row = 0
    y = min_y + gap * 0.5
    while y <= max_y:
        offset = (brick / 2.0) if row % 2 else 0.0
        x = min_x + offset
        while x <= max_x:
            x2 = min(x + brick * 0.82, max_x)
            mid = ((x + x2) / 2.0, y)
            if point_in_polygon(mid[0], mid[1], polygon):
                n = max(1, int(round((x2 - x) / step)))
                pts = [(x + (x2 - x) * k / n, y) for k in range(n + 1)]
                if not first:
                    cmds.append((pts[0][0], pts[0][1], JUMP))
                cmds.extend((px, py, STITCH) for px, py in pts)
                first = False
            x += brick
        y += gap
        row += 1
    return cmds
