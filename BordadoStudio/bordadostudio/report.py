"""Relatório de produção: pontos, linha, tempo e custo — lógica pura (testável)."""

from __future__ import annotations

import math
from datetime import datetime

from . import stitcher

DEFAULT_SPEED = 500.0        # pontos por minuto
THREAD_WASTE = 1.12          # margem de linha (agulha/bobina + cortes)
COLOR_CHANGE_MINUTES = 0.25  # tempo médio de troca de cor (min)


def object_length_mm(cmds):
    """Comprimento costurado (mm) de uma lista de comandos (1 unidade = 0,1 mm)."""
    total = 0.0
    prev = None
    for x, y, c in cmds:
        if c == stitcher.STITCH and prev is not None:
            total += math.hypot(x - prev[0], y - prev[1])
        prev = (x, y)
    return total / 10.0


def build_report(doc, speed: float = DEFAULT_SPEED,
                 hourly_rate: float = 0.0, per_color: float = 0.0):
    """Monta os dados do relatório para o documento."""
    objects = [o for o in doc.objects if o.visible and o.stitches]
    total_stitches = sum(o.stitch_count() for o in objects)
    total_len = sum(object_length_mm(o.stitches) for o in objects)
    color_changes = max(0, len(objects) - 1)

    speed = max(1.0, float(speed))
    minutes = total_stitches / speed + color_changes * COLOR_CHANGE_MINUTES
    hours = minutes / 60.0

    cost = hours * max(0.0, float(hourly_rate)) \
        + color_changes * max(0.0, float(per_color))

    b = doc.bounds()
    width_mm = (b[2] - b[0]) / 10.0
    height_mm = (b[3] - b[1]) / 10.0

    per_object = [
        {
            "name": o.name,
            "stitches": o.stitch_count(),
            "length_mm": object_length_mm(o.stitches),
            "color": o.thread.name,
        }
        for o in objects
    ]

    return {
        "title": doc.title,
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "objects": len(objects),
        "colors": len({id(o.thread) if o.thread.code else o.thread.hex_color
                       for o in objects}) or (1 if objects else 0),
        "color_changes": color_changes,
        "stitches": total_stitches,
        "length_mm": total_len,
        "thread_m": total_len / 1000.0 * THREAD_WASTE,
        "width_mm": width_mm,
        "height_mm": height_mm,
        "speed": speed,
        "minutes": minutes,
        "hourly_rate": hourly_rate,
        "per_color": per_color,
        "cost": cost,
        "per_object": per_object,
    }


def _fmt_time(minutes: float) -> str:
    if minutes < 1:
        return f"{minutes * 60:.0f} segundos"
    if minutes < 60:
        return f"{minutes:.1f} minutos"
    h = int(minutes // 60)
    m = int(round(minutes % 60))
    return f"{h}h{m:02d}min"


def format_report(data: dict) -> str:
    """Formata o relatório em texto (português)."""
    lines = [
        "=" * 52,
        "   RELATÓRIO DE PRODUÇÃO — BordadoStudio",
        "=" * 52,
        f"Desenho:  {data['title']}",
        f"Data:     {data['date']}",
        "",
        "PRODUÇÃO",
        f"  Objetos:           {data['objects']}",
        f"  Cores:             {data['colors']} "
        f"({data['color_changes']} trocas)",
        f"  Pontos totais:     {data['stitches']:,}".replace(",", "."),
        f"  Área:              {data['width_mm']:.1f} x "
        f"{data['height_mm']:.1f} mm",
        f"  Linha estimada:    {data['thread_m']:.2f} m",
        "",
        "TEMPO",
        f"  Velocidade:        {data['speed']:.0f} pontos/min",
        f"  Tempo de costura:  {_fmt_time(data['minutes'])}",
        "",
    ]
    if data["hourly_rate"] > 0 or data["per_color"] > 0:
        lines += [
            "CUSTO ESTIMADO",
            f"  Valor da hora:     R$ {data['hourly_rate']:.2f}".replace(".", ","),
            f"  Por troca de cor:  R$ {data['per_color']:.2f}".replace(".", ","),
            f"  >>> TOTAL:         R$ {data['cost']:.2f}".replace(".", ","),
            "",
        ]
    if data["per_object"]:
        lines += ["POR OBJETO (ordem de costura):"]
        for i, o in enumerate(data["per_object"], 1):
            lines.append(
                f"  {i:2}. {o['name'][:26]:26} {o['stitches']:6} pts  "
                f"{o['length_mm']:7.0f} mm  [{o['color']}]")
        lines.append("")
    lines.append("=" * 52)
    return "\n".join(lines)
