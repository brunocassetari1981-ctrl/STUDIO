# -*- coding: utf-8 -*-
"""Instalador gráfico do BordadoStudio (roda sem console, via pythonw).

Mostra apenas uma caixinha "Instalando BordadoStudio..." com barra de
progresso. Usa somente a biblioteca padrão do Python (tkinter).
"""

import os
import queue
import subprocess
import sys
import threading
import traceback

RAIZ = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(RAIZ, "instalar.log")
VENV = os.path.join(RAIZ, ".venv")

PASSOS = 5


def venv_python():
    if os.name == "nt":
        return os.path.join(VENV, "Scripts", "python.exe")
    return os.path.join(VENV, "bin", "python")


def criar_env_oculto():
    """Flags para não abrir janelas de console nos subprocessos."""
    if os.name == "nt":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        return {"startupinfo": si,
                "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {}


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg.rstrip() + "\n")


def rodar(cmd, **kw):
    log("$ " + " ".join(cmd))
    env = criar_env_oculto()
    env.update(kw)
    r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True, **env)
    if r.stdout:
        log(r.stdout)
    if r.stderr:
        log(r.stderr)
    return r.returncode == 0


def passos_instalacao(fila):
    """Executa a instalação, avisando o progresso pela fila."""
    try:
        open(LOG, "w", encoding="utf-8").write(
            "Instalacao BordadoStudio\nPython: " + sys.executable + "\n")

        fila.put((1, "Procurando o Python..."))
        py = sys.executable
        if not py or not os.path.exists(py):
            raise RuntimeError("Python nao encontrado.")
        log("usando " + py)

        fila.put((2, "Criando o ambiente virtual..."))
        if not os.path.exists(venv_python()):
            if not rodar([py, "-m", "venv", ".venv"]):
                raise RuntimeError("Falha ao criar o ambiente virtual.")

        fila.put((3, "Instalando componentes (pode levar alguns minutos)..."))
        vpy = venv_python()
        rodar([vpy, "-m", "pip", "install", "--upgrade", "pip"])
        if not rodar([vpy, "-m", "pip", "install", "-r", "requirements.txt"]):
            raise RuntimeError(
                "Falha ao instalar os componentes.\n"
                "Verifique a conexao com a internet.")

        fila.put((4, "Criando o atalho de inicializacao..."))
        atalho = os.path.join(RAIZ, "Abrir BordadoStudio.bat")
        with open(atalho, "w", encoding="utf-8") as f:
            f.write(
                "@echo off\r\n"
                "cd /d \"%~dp0\"\r\n"
                "if not exist \".venv\\Scripts\\pythonw.exe\" goto :naoinstalado\r\n"
                "start \"\" \".venv\\Scripts\\pythonw.exe\" main.py\r\n"
                "exit /b 0\r\n"
                ":naoinstalado\r\n"
                "echo Execute o instalar.bat primeiro.\r\n"
                "pause\r\n")

        fila.put((PASSOS, "Instalado com sucesso!"))
    except Exception as e:  # mostra o erro na janela
        log(traceback.format_exc())
        fila.put(("erro", str(e)))


class Instalador:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk
        self.root = root
        root.title("BordadoStudio — Instalador")
        root.resizable(False, False)
        root.configure(padx=18, pady=14)
        root.attributes("-topmost", True)

        self.titulo = tk.Label(
            root, text="Instalando BordadoStudio...",
            font=("Segoe UI", 13, "bold"))
        self.titulo.pack(anchor="w")
        tk.Label(
            root, text="Sem login, sem ativacao — pode deixar a janela aberta.",
            fg="#666").pack(anchor="w", pady=(0, 10))

        self.status = tk.Label(root, text="Preparando...", anchor="w")
        self.status.pack(fill="x")

        self.barra = ttk.Progressbar(root, maximum=PASSOS, length=360)
        self.barra.pack(fill="x", pady=(6, 12))

        linha = tk.Frame(root)
        linha.pack(fill="x")
        self.btn_abrir = tk.Button(
            linha, text="Abrir BordadoStudio", state="disabled",
            command=self.abrir)
        self.btn_log = tk.Button(linha, text="Ver log", command=self.ver_log)
        self.btn_fechar = tk.Button(linha, text="Fechar", command=root.destroy)
        self.btn_fechar.pack(side="right")

        self.fila = queue.Queue()
        threading.Thread(target=passos_instalacao,
                         args=(self.fila,), daemon=True).start()
        root.after(120, self.atualizar)

    def atualizar(self):
        import tkinter as tk
        try:
            while True:
                etapa, msg = self.fila.get_nowait()
                if etapa == "erro":
                    self.titulo.config(text="Falha na instalacao",
                                       fg="#b02020")
                    self.status.config(text=msg, fg="#b02020",
                                       wraplength=360, justify="left")
                    self.btn_log.pack(side="left")
                    return
                self.barra["value"] = etapa
                self.status.config(text=msg)
                if etapa == PASSOS:
                    self.titulo.config(text="Instalacao concluida!",
                                       fg="#1f7a2e")
                    self.status.config(
                        text="Para usar, clique em \"Abrir BordadoStudio\" "
                             "ou no atalho criado na pasta.")
                    self.btn_abrir.config(state="normal")
                    self.btn_abrir.pack(side="left", padx=(0, 6))
                    self.btn_log.pack(side="left")
                    self.root.attributes("-topmost", False)
                    return
        except queue.Empty:
            pass
        self.root.after(120, self.atualizar)

    def abrir(self):
        vpy = venv_python()
        if os.path.exists(vpy):
            kwargs = criar_env_oculto()
            subprocess.Popen([vpy, "main.py"], cwd=RAIZ, **kwargs)
        self.root.destroy()

    def ver_log(self):
        if os.path.exists(LOG):
            if os.name == "nt":
                os.startfile(LOG)  # noqa: S606
            else:
                subprocess.Popen(["xdg-open", LOG])


def main():
    try:
        import tkinter  # noqa: F401
    except Exception:
        # sem tkinter: instala direto, no modo texto (sem janela bonita)
        fila = queue.Queue()
        passos_instalacao(fila)
        while not fila.empty():
            print(fila.get())
        return
    from tkinter import Tk
    root = Tk()
    try:
        root.iconbitmap(default="")  # ícone padrão do sistema
    except Exception:
        pass
    Instalador(root)
    root.mainloop()


if __name__ == "__main__":
    main()
