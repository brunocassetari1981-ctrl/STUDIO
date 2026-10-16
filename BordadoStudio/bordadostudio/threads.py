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
    # ---- catálogos de linhas (aproximações visuais próprias) ----
    "Madeira Classic": [
        ThreadColor("Branco", 0xF8F8F8, "1000", "Madeira"),
        ThreadColor("Marfim", 0xF3EAD8, "1001", "Madeira"),
        ThreadColor("Preto", 0x141414, "1082", "Madeira"),
        ThreadColor("Cinza", 0x9A9A9A, "1083", "Madeira"),
        ThreadColor("Prata", 0xC5C7C9, "1011", "Madeira"),
        ThreadColor("Ouro", 0xC9A227, "1025", "Madeira"),
        ThreadColor("Amarelo Claro", 0xFFE24A, "1114", "Madeira"),
        ThreadColor("Amarelo", 0xF5C518, "1133", "Madeira"),
        ThreadColor("Ocre", 0xE0A310, "1024", "Madeira"),
        ThreadColor("Laranja Claro", 0xFF9E45, "1164", "Madeira"),
        ThreadColor("Laranja", 0xEE7203, "1147", "Madeira"),
        ThreadColor("Vermelho Claro", 0xF4574B, "1182", "Madeira"),
        ThreadColor("Vermelho", 0xD63027, "1146", "Madeira"),
        ThreadColor("Vermelho Escuro", 0x9E1B1B, "1237", "Madeira"),
        ThreadColor("Rosa Claro", 0xF9A8C0, "1116", "Madeira"),
        ThreadColor("Rosa", 0xE75480, "1117", "Madeira"),
        ThreadColor("Magenta", 0xC2185B, "1310", "Madeira"),
        ThreadColor("Roxo", 0x7B3FA0, "1240", "Madeira"),
        ThreadColor("Lilás", 0xB39DDB, "1241", "Madeira"),
        ThreadColor("Azul Royal", 0x2743A3, "1134", "Madeira"),
        ThreadColor("Azul", 0x2E6FD9, "1050", "Madeira"),
        ThreadColor("Azul Claro", 0x6EC1E4, "1173", "Madeira"),
        ThreadColor("Turquesa", 0x00A8A8, "1168", "Madeira"),
        ThreadColor("Verde Claro", 0x6FCE53, "1167", "Madeira"),
        ThreadColor("Verde", 0x2E9E3F, "1049", "Madeira"),
        ThreadColor("Verde Escuro", 0x1B5E2A, "1250", "Madeira"),
        ThreadColor("Verde Musgo", 0x6B7A2E, "1251", "Madeira"),
        ThreadColor("Bege", 0xE6C9A3, "1042", "Madeira"),
        ThreadColor("Areia", 0xD9B38C, "1043", "Madeira"),
        ThreadColor("Marrom Claro", 0xB07A4F, "1230", "Madeira"),
        ThreadColor("Marrom", 0x8B5A2B, "1055", "Madeira"),
        ThreadColor("Marrom Escuro", 0x5D3A1A, "1232", "Madeira"),
        ThreadColor("Salmão", 0xFA8072, "1166", "Madeira"),
        ThreadColor("Pêssego", 0xFFCBA4, "1017", "Madeira"),
        ThreadColor("Vinho", 0x7B2233, "1238", "Madeira"),
        ThreadColor("Petróleo", 0x0F5257, "1272", "Madeira"),
    ],
    "Anchor": [
        ThreadColor("Branco", 0xF8F8F8, "1", "Anchor"),
        ThreadColor("Creme", 0xF5EBD5, "2", "Anchor"),
        ThreadColor("Preto", 0x171717, "3", "Anchor"),
        ThreadColor("Cinza", 0x8E8E8E, "39", "Anchor"),
        ThreadColor("Prata", 0xC0C3C7, "37", "Anchor"),
        ThreadColor("Ouro", 0xD4AF37, "315", "Anchor"),
        ThreadColor("Amarelo", 0xF2C230, "290", "Anchor"),
        ThreadColor("Ouro Antigo", 0xC8952B, "891", "Anchor"),
        ThreadColor("Laranja", 0xEE7203, "304", "Anchor"),
        ThreadColor("Coral", 0xF4685A, "346", "Anchor"),
        ThreadColor("Vermelho", 0xD62828, "334", "Anchor"),
        ThreadColor("Vermelho Escuro", 0x922B21, "341", "Anchor"),
        ThreadColor("Rosa", 0xF2789F, "58", "Anchor"),
        ThreadColor("Rosa Claro", 0xF9B7C8, "55", "Anchor"),
        ThreadColor("Magenta", 0xC2185B, "51", "Anchor"),
        ThreadColor("Roxo", 0x7B3FA0, "87", "Anchor"),
        ThreadColor("Lilás", 0xA98BD1, "89", "Anchor"),
        ThreadColor("Azul Royal", 0x2743A3, "142", "Anchor"),
        ThreadColor("Azul", 0x2E6FD9, "145", "Anchor"),
        ThreadColor("Azul Claro", 0x74B9E8, "139", "Anchor"),
        ThreadColor("Turquesa", 0x1FA8A0, "1087", "Anchor"),
        ThreadColor("Verde Claro", 0x7BC950, "225", "Anchor"),
        ThreadColor("Verde", 0x2E9E3F, "227", "Anchor"),
        ThreadColor("Verde Escuro", 0x1B5E2A, "230", "Anchor"),
        ThreadColor("Verde Oliva", 0x6E7B2D, "255", "Anchor"),
        ThreadColor("Bege", 0xE6C9A3, "358", "Anchor"),
        ThreadColor("Pêssego", 0xFFCBA4, "351", "Anchor"),
        ThreadColor("Marrom Claro", 0xB07A4F, "353", "Anchor"),
        ThreadColor("Marrom", 0x8B5A2B, "356", "Anchor"),
        ThreadColor("Marrom Escuro", 0x5D3A1A, "379", "Anchor"),
        ThreadColor("Vinho", 0x81263B, "46", "Anchor"),
        ThreadColor("Petróleo", 0x0F5257, "1084", "Anchor"),
    ],
    "Isacord": [
        ThreadColor("Branco", 0xF9F9F9, "5500", "Isacord"),
        ThreadColor("Marfim", 0xF1E7D3, "5501", "Isacord"),
        ThreadColor("Preto", 0x121212, "5000", "Isacord"),
        ThreadColor("Cinza Claro", 0xBFC1C3, "5820", "Isacord"),
        ThreadColor("Cinza", 0x8A8D8F, "5822", "Isacord"),
        ThreadColor("Prata", 0xC7CACC, "5860", "Isacord"),
        ThreadColor("Ouro", 0xC9A227, "5850", "Isacord"),
        ThreadColor("Amarelo", 0xF2C230, "5115", "Isacord"),
        ThreadColor("Amarelo Claro", 0xFFE24A, "5110", "Isacord"),
        ThreadColor("Laranja", 0xEE7203, "5240", "Isacord"),
        ThreadColor("Laranja Claro", 0xFF9E45, "5235", "Isacord"),
        ThreadColor("Vermelho", 0xD63027, "5320", "Isacord"),
        ThreadColor("Vermelho Escuro", 0x9E1B1B, "5340", "Isacord"),
        ThreadColor("Rosa", 0xE75480, "5170", "Isacord"),
        ThreadColor("Rosa Claro", 0xF9A8C0, "5165", "Isacord"),
        ThreadColor("Magenta", 0xC2185B, "5185", "Isacord"),
        ThreadColor("Vinho", 0x7B2233, "5360", "Isacord"),
        ThreadColor("Roxo", 0x7B3FA0, "5520", "Isacord"),
        ThreadColor("Lilás", 0xB39DDB, "5515", "Isacord"),
        ThreadColor("Azul Royal", 0x2743A3, "5670", "Isacord"),
        ThreadColor("Azul", 0x2E6FD9, "5665", "Isacord"),
        ThreadColor("Azul Claro", 0x6EC1E4, "5660", "Isacord"),
        ThreadColor("Turquesa", 0x00A8A8, "5770", "Isacord"),
        ThreadColor("Verde Claro", 0x6FCE53, "5715", "Isacord"),
        ThreadColor("Verde", 0x2E9E3F, "5720", "Isacord"),
        ThreadColor("Verde Escuro", 0x1B5E2A, "5740", "Isacord"),
        ThreadColor("Verde Musgo", 0x6B7A2E, "5755", "Isacord"),
        ThreadColor("Bege", 0xE6C9A3, "5425", "Isacord"),
        ThreadColor("Areia", 0xD9B38C, "5420", "Isacord"),
        ThreadColor("Marrom Claro", 0xB07A4F, "5410", "Isacord"),
        ThreadColor("Marrom", 0x8B5A2B, "5405", "Isacord"),
        ThreadColor("Marrom Escuro", 0x5D3A1A, "5400", "Isacord"),
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
