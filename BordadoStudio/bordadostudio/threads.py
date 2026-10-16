"""Paletas de linha de bordado.

Os valores hexadecimais são aproximações visuais para uso no editor.
O usuário pode definir cores personalizadas e mapear o próprio catálogo.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ThreadColor:
    name: str
    hex_color: int
    code: str = ""
    brand: str = ""

    def to_dict(self):
        return {
            "name": self.name,
            "hex_color": self.hex_color,
            "code": self.code,
            "brand": self.brand,
        }

    @staticmethod
    def from_dict(d):
        return ThreadColor(
            name=d.get("name", ""),
            hex_color=int(d.get("hex_color", 0x808080)),
            code=d.get("code", ""),
            brand=d.get("brand", ""),
        )


# Paletas nomeadas em português
PALETTES: dict[str, list[ThreadColor]] = {
    "Essenciais": [
        ThreadColor("Branco", 0xF7F7F7, "1", "BordadoStudio"),
        ThreadColor("Preto", 0x1A1A1A, "2", "BordadoStudio"),
        ThreadColor("Cinza Claro", 0xBFBFBF, "3", "BordadoStudio"),
        ThreadColor("Cinza Escuro", 0x5E5E5E, "4", "BordadoStudio"),
        ThreadColor("Vermelho", 0xD62828, "5", "BordadoStudio"),
        ThreadColor("Vermelho Escuro", 0x8B1A1A, "6", "BordadoStudio"),
        ThreadColor("Rosa", 0xF2789F, "7", "BordadoStudio"),
        ThreadColor("Laranja", 0xF26A1B, "8", "BordadoStudio"),
        ThreadColor("Amarelo", 0xF2C230, "9", "BordadoStudio"),
        ThreadColor("Verde Claro", 0x7BC950, "10", "BordadoStudio"),
        ThreadColor("Verde", 0x2E9E3F, "11", "BordadoStudio"),
        ThreadColor("Verde Escuro", 0x1B5E2A, "12", "BordadoStudio"),
        ThreadColor("Azul Claro", 0x5DB7F2, "13", "BordadoStudio"),
        ThreadColor("Azul", 0x1F5FC4, "14", "BordadoStudio"),
        ThreadColor("Azul Escuro", 0x12315E, "15", "BordadoStudio"),
        ThreadColor("Roxo", 0x7B3FA0, "16", "BordadoStudio"),
        ThreadColor("Marrom", 0x8B5A2B, "17", "BordadoStudio"),
        ThreadColor("Bege", 0xE6C9A3, "18", "BordadoStudio"),
    ],
    "Tons de Pele": [
        ThreadColor("Pele Muito Clara", 0xFBE0D0, "P1", "BordadoStudio"),
        ThreadColor("Pele Clara", 0xF3C7A9, "P2", "BordadoStudio"),
        ThreadColor("Pele Média", 0xE0A87E, "P3", "BordadoStudio"),
        ThreadColor("Pele Escura", 0xB07A52, "P4", "BordadoStudio"),
        ThreadColor("Pele Muito Escura", 0x7A4E32, "P5", "BordadoStudio"),
        ThreadColor("Sombra Pele Clara", 0xD99C77, "P6", "BordadoStudio"),
        ThreadColor("Sombra Pele Escura", 0x8D5A3B, "P7", "BordadoStudio"),
        ThreadColor("Rosado", 0xF2A6A0, "P8", "BordadoStudio"),
    ],
    "Natureza": [
        ThreadColor("Folha Clara", 0x9CCC65, "N1", "BordadoStudio"),
        ThreadColor("Folha", 0x558B2F, "N2", "BordadoStudio"),
        ThreadColor("Folha Escura", 0x33691E, "N3", "BordadoStudio"),
        ThreadColor("Grama", 0x7CB342, "N4", "BordadoStudio"),
        ThreadColor("Céu", 0x81D4FA, "N5", "BordadoStudio"),
        ThreadColor("Água", 0x0288D1, "N6", "BordadoStudio"),
        ThreadColor("Areia", 0xF0D9A8, "N7", "BordadoStudio"),
        ThreadColor("Terra", 0x795548, "N8", "BordadoStudio"),
        ThreadColor("Madeira Clara", 0xC8A165, "N9", "BordadoStudio"),
        ThreadColor("Madeira Escura", 0x6D4C41, "N10", "BordadoStudio"),
        ThreadColor("Pedra", 0x9E9E9E, "N11", "BordadoStudio"),
        ThreadColor("Flor Amarela", 0xFFCA28, "N12", "BordadoStudio"),
        ThreadColor("Flor Rosa", 0xEC407A, "N13", "BordadoStudio"),
        ThreadColor("Flor Vermelha", 0xE53935, "N14", "BordadoStudio"),
        ThreadColor("Flor Lilás", 0xAB47BC, "N15", "BordadoStudio"),
        ThreadColor("Flor Laranja", 0xFF7043, "N16", "BordadoStudio"),
    ],
    "Metálicas e Especiais": [
        ThreadColor("Ouro", 0xD4AF37, "M1", "BordadoStudio"),
        ThreadColor("Prata", 0xC0C0C0, "M2", "BordadoStudio"),
        ThreadColor("Bronze", 0xA97142, "M3", "BordadoStudio"),
        ThreadColor("Cobre", 0xB87333, "M4", "BordadoStudio"),
        ThreadColor("Perolado", 0xEDE7DC, "M5", "BordadoStudio"),
        ThreadColor("Neon Rosa", 0xFF4FC3, "M6", "BordadoStudio"),
        ThreadColor("Neon Verde", 0x76FF03, "M7", "BordadoStudio"),
        ThreadColor("Neon Laranja", 0xFF6D00, "M8", "BordadoStudio"),
    ],
}

DEFAULT_PALETTE = "Essenciais"


def palette_names():
    return list(PALETTES.keys())


def colors_of(palette: str):
    return PALETTES.get(palette, PALETTES[DEFAULT_PALETTE])


def find_color(hex_color: int, name: str = ""):
    """Procura uma cor em todas as paletas; senão cria uma personalizada."""
    for colors in PALETTES.values():
        for c in colors:
            if c.hex_color == (hex_color & 0xFFFFFF):
                return ThreadColor(c.name, c.hex_color, c.code, c.brand)
    return ThreadColor(name or "Personalizada", hex_color & 0xFFFFFF, "", "Personalizada")
