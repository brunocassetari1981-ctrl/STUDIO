#!/usr/bin/env python3
"""Gera stubs .so para o Qt rodar offscreen em ambientes sem GPU/X11 (sandbox).

Ferramenta de DESENVOLVIMENTO — não faz parte do programa final.
Para cada biblioteca de sistema ausente, cria um .so com o SONAME certo
e, quando o Qt referencia símbolos versionados (ex.: dbus), gera
definições dummy com os .symver correspondentes.

Uso:
    python3 tests/dev_gen_stubs.py [destino]     (padrão: /home/user/glstub/out)

Depois: exportar LD_LIBRARY_PATH=<destino> e QT_QPA_PLATFORM=offscreen.
"""

import os
import re
import subprocess
import sys

BASE_STUBS = {
    "libGL.so.1": ["libGL.so.1", "libGL.so"],
    "libEGL.so.1": ["libEGL.so.1", "libEGL.so"],
    "libxkbcommon.so.0": ["libxkbcommon.so.0", "libxkbcommon.so"],
    "libdbus-1.so.3": ["libdbus-1.so.3", "libdbus-1.so"],
}

VERSION_OWNER = [
    (re.compile(r"^LIBDBUS"), "libdbus-1.so.3"),
    (re.compile(r"^(V_|XKBCOMMON)"), "libxkbcommon.so.0"),
    (re.compile(r"^EGL"), "libEGL.so.1"),
    (re.compile(r"^(GLX|GL_|GL$|OPENGL)"), "libGL.so.1"),
]

UNVERSIONED_OWNERS = [
    (re.compile(r"^egl"), "libEGL.so.1"),
    (re.compile(r"^glX"), "libGL.so.1"),
    (re.compile(r"^gl[A-Z_]"), "libGL.so.1"),
]

VENV_PY = "/home/user/STUDIO/.venv"


def qt_libs():
    root = os.path.join(VENV_PY, "lib")
    out = []
    for dirpath, _dirs, files in os.walk(root):
        if "PySide6" not in dirpath:
            continue
        for name in files:
            if name.endswith(".so") or ".so." in name:
                out.append(os.path.join(dirpath, name))
    return out


def undefined_refs(lib):
    """[(symbol, version)] referenciados e não definidos em lib ('' = sem versão)."""
    out = []
    try:
        txt = subprocess.check_output(
            ["objdump", "-T", lib], stderr=subprocess.DEVNULL, text=True)
    except Exception:
        return out
    for line in txt.splitlines():
        if "*UND*" not in line:
            continue
        rest = line.split("*UND*", 1)[1].strip()
        tokens = rest.split()
        if not tokens:
            continue
        tokens = tokens[1:]  # remove o endereço
        if not tokens:
            continue
        if len(tokens) == 1:
            version, sym = "", tokens[0]
        else:
            version, sym = tokens[0].strip("()"), tokens[1]
        if version in ("*ABS*", ".hidden") or sym.startswith("_"):
            continue
        if re.match(r"^(GLIBC|CXXABI|GCC|Qt_|QT_|OPENSSL)", version):
            continue
        out.append((sym, version))
    return out


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "/home/user/glstub/out"
    os.makedirs(out_dir, exist_ok=True)

    by_owner: dict[str, dict[str, set[str]]] = {}
    for lib in qt_libs():
        for sym, ver in undefined_refs(lib):
            owner = None
            if ver == "":
                for rx, o in UNVERSIONED_OWNERS:
                    if rx.match(sym):
                        owner = o
                        break
            else:
                for rx, o in VERSION_OWNER:
                    if rx.match(ver):
                        owner = o
                        break
            if owner is None:
                continue
            by_owner.setdefault(owner, {}).setdefault(ver, set()).add(sym)

    for soname, aliases in BASE_STUBS.items():
        c_path = os.path.join(out_dir, soname + ".c")
        map_path = os.path.join(out_dir, soname + ".map")
        versions = by_owner.get(soname, {})
        with open(c_path, "w") as f:
            f.write("void __stub_marker(void) {}\n")
            for ver, syms in sorted(versions.items()):
                if ver == "":
                    for sym in sorted(syms):
                        f.write(f"void {sym}(void) {{}}\n")
                    continue
                for i, sym in enumerate(sorted(syms)):
                    alias = f"{sym}__{i}"
                    f.write(f"void {alias}(void) {{}}\n")
                    f.write(f"asm(\".symver {alias}, {sym}@{ver}\");\n")
        with open(map_path, "w") as f:
            any_ver = False
            for ver, syms in sorted(versions.items()):
                if ver == "":
                    continue
                any_ver = True
                f.write(f"{ver} {{\n  global:\n")
                for sym in sorted(syms):
                    f.write(f"    {sym};\n")
                f.write("};\n")
            if versions.get("", set()) or not any_ver:
                f.write("STUB { global: *; };\n")
        for alias in aliases:
            subprocess.check_call(
                ["gcc", "-shared", "-fPIC",
                 "-Wl,-soname," + alias,
                 "-Wl,--version-script," + map_path,
                 "-o", os.path.join(out_dir, alias), c_path])
        total = sum(len(v) for v in versions.values())
        print(f"{soname}: {total} símbolos -> {aliases}")
    print("stubs em", out_dir)


if __name__ == "__main__":
    main()
