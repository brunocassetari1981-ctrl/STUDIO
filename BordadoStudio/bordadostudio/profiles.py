"""Predefinições (perfis) de costura do BordadoStudio.

Salvas em ~/.bordadostudio/profiles.json — sem servidor, sem login.
"""

from __future__ import annotations

import json
import os

DEFAULT_PROFILES: dict[str, dict] = {
    "Padrão": {
        "stitch_type": "fill", "stitch_length": 25.0, "spacing": 18.0,
        "angle": 0.0, "width": 40.0, "density": 8.0, "edge_underlay": True,
    },
    "Linha fina": {
        "stitch_type": "run", "stitch_length": 18.0, "spacing": 18.0,
        "angle": 0.0, "width": 20.0, "density": 8.0, "edge_underlay": False,
    },
    "Satin largo": {
        "stitch_type": "satin", "stitch_length": 25.0, "spacing": 10.0,
        "angle": 0.0, "width": 60.0, "density": 6.0, "edge_underlay": True,
    },
    "Textura densa": {
        "stitch_type": "fill", "stitch_length": 20.0, "spacing": 12.0,
        "angle": 45.0, "width": 40.0, "density": 8.0, "edge_underlay": True,
    },
    "Contorno leve": {
        "stitch_type": "run2", "stitch_length": 25.0, "spacing": 18.0,
        "angle": 0.0, "width": 30.0, "density": 8.0, "edge_underlay": False,
    },
}


class ProfileStore:
    """Conjunto nomeado de parâmetros de costura."""

    def __init__(self, path: str | None = None):
        self.path = path or os.path.join(
            os.path.expanduser("~"), ".bordadostudio", "profiles.json")
        self.profiles: dict[str, dict] = {}
        self.load()

    def load(self):
        self.profiles = {k: dict(v) for k, v in DEFAULT_PROFILES.items()}
        try:
            with open(self.path, encoding="utf-8") as f:
                dados = json.load(f)
            for nome, params in dados.items():
                if isinstance(params, dict):
                    self.profiles[nome] = dict(params)
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, ensure_ascii=False, indent=1)
        except OSError:
            pass

    def names(self) -> list[str]:
        return sorted(self.profiles)

    def get(self, name: str) -> dict | None:
        p = self.profiles.get(name)
        return dict(p) if p else None

    def set(self, name: str, params: dict):
        self.profiles[name] = dict(params)
        self.save()

    def remove(self, name: str):
        if name in self.profiles:
            del self.profiles[name]
            self.save()
