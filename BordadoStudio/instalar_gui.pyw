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

PASSOS = 5


def venv_curto():
    """Ambiente virtual em caminho curto.

    Evita o limite de 260 caracteres do Windows: pastas profundas
    (ex.: Desktop\\...\\Nova pasta\\...) fazem o pip falhar com
    "OSError: No such file or directory" / dica de Long Path ao
    descompactar as dependências.
    """
    base = (os.environ.get("LOCALAPPDATA") or os.environ.get("TMPDIR")
            or os.environ.get("TEMP"))
    if base:
        return os.path.join(base, "BordadoStudio", ".venv")
    return os.path.join(RAIZ, ".venv")


VENV = venv_curto()


def venv_python():
    if os.name == "nt":
        return os.path.join(VENV, "Scripts", "python.exe")
    return os.path.join(VENV, "bin", "python")


def venv_pythonw():
    if os.name == "nt":
        return os.path.join(VENV, "Scripts", "pythonw.exe")
    return venv_python()


def _tem_python(venv):
    if os.name == "nt":
        return os.path.exists(os.path.join(venv, "Scripts", "python.exe"))
    return os.path.exists(os.path.join(venv, "bin", "python"))


def habilitar_long_paths():
    """Melhor esforço: liga o suporte a caminhos longos do Windows."""
    if os.name != "nt":
        return
    try:
        subprocess.run(
            ["reg", "add",
             r"HKLM\SYSTEM\CurrentControlSet\Control\FileSystem",
             "/v", "LongPathsEnabled", "/t", "REG_DWORD", "/d", "1", "/f"],
            capture_output=True, **criar_env_oculto())
    except Exception:
        pass


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
    global VENV
    try:
        open(LOG, "w", encoding="utf-8").write(
            "Instalacao BordadoStudio\nPython: " + sys.executable + "\n")

        # controle do desenvolvedor: bloqueio remoto + aviso de instalação
        sys.path.insert(0, RAIZ)
        try:
            from bordadostudio import controle
            from bordadostudio import __version__ as VERSAO
        except Exception:
            controle, VERSAO = None, "desconhecida"

        if controle is not None:
            fila.put((0, "Consultando o controle do desenvolvedor..."))
            bloqueado, motivo = controle.verificar_bloqueio(raiz=RAIZ)
            if bloqueado:
                log("BLOQUEADO: " + motivo)
                fila.put(("bloqueado", motivo))
                return

        fila.put((1, "Procurando o Python..."))
        py = sys.executable
        if not py or not os.path.exists(py):
            raise RuntimeError("Python nao encontrado.")
        log("usando " + py)

        fila.put((2, "Criando o ambiente virtual..."))
        # caminho curto primeiro: pastas profundas estouram o limite
        # de 260 caracteres do Windows durante a instalacao do pip.
        # Nunca reutiliza um .venv antigo da pasta do programa antes de
        # tentar o caminho curto (pode ter ficado de uma instalacao que
        # falhou justamente por caminho longo).
        candidatos = [venv_curto(), os.path.join(RAIZ, ".venv")]
        escolhido = None
        if _tem_python(candidatos[0]):
            escolhido = candidatos[0]
            log("reusando ambiente virtual em " + escolhido)
        else:
            for cand in candidatos:
                log("criando ambiente virtual em " + cand)
                if rodar([py, "-m", "venv", cand]) and _tem_python(cand):
                    escolhido = cand
                    break
        if escolhido is None:
            raise RuntimeError(
                "Falha ao criar o ambiente virtual.\n"
                "Tente mover a pasta do programa para um caminho\n"
                "mais curto (ex.: C:\\BordadoStudio) e reinstalar.")
        VENV = escolhido
        log("ambiente virtual: " + VENV)

        fila.put((3, "Instalando componentes (pode levar alguns minutos)..."))
        habilitar_long_paths()
        vpy = venv_python()
        rodar([vpy, "-m", "pip", "install", "--upgrade", "pip"])
        if not rodar([vpy, "-m", "pip", "install", "-r", "requirements.txt"]):
            raise RuntimeError(
                "Falha ao instalar os componentes.\n"
                "Verifique a conexao com a internet.")

        fila.put((4, "Criando o atalho na area de trabalho..."))
        vpyw = venv_pythonw()
        atalho = os.path.join(RAIZ, "Abrir BordadoStudio.bat")
        with open(atalho, "w", encoding="utf-8") as f:
            f.write(
                "@echo off\r\n"
                "cd /d \"%~dp0\"\r\n"
                "set \"PYW=" + vpyw + "\"\r\n"
                "if not exist \"%PYW%\" "
                "set \"PYW=%~dp0.venv\\Scripts\\pythonw.exe\"\r\n"
                "if not exist \"%PYW%\" goto :naoinstalado\r\n"
                "start \"\" \"%PYW%\" main.py\r\n"
                "exit /b 0\r\n"
                ":naoinstalado\r\n"
                "echo Ambiente nao encontrado. Execute o instalador "
                "novamente.\r\n"
                "pause\r\n")
        try:
            resultado = criar_atalho_area_trabalho()
            log("atalho da area de trabalho: " + resultado)
        except Exception as e:
            log("atalho da area de trabalho: FALHA " + str(e))

        fila.put((PASSOS, "Instalado com sucesso!"))
        # avisa o desenvolvedor (nunca atrasa a instalação)
        if controle is not None:
            try:
                controle.notificar_instalacao(VERSAO, raiz=RAIZ,
                                              evento="instalacao")
            except Exception:
                pass
    except Exception as e:  # mostra o erro na janela
        log(traceback.format_exc())
        fila.put(("erro", str(e)))


def criar_atalho_area_trabalho():
    """Cria o atalho 'BordadoStudio' na Área de Trabalho (Windows)."""
    if os.name != "nt":
        return "ignorado (não Windows)"
    # primeiro o pythonw do ambiente (onde as dependências foram instaladas)
    py = venv_pythonw()
    if not os.path.exists(py):
        py = sys.executable
        if os.path.basename(py).lower() == "python.exe":
            alt = os.path.join(os.path.dirname(py), "pythonw.exe")
            if os.path.exists(alt):
                py = alt
    icone = os.path.join(RAIZ, "icone", "BordadoStudio.ico")
    main_py = os.path.join(RAIZ, "main.py")
    ps = (
        "$d=[Environment]::GetFolderPath('Desktop');"
        "$ws=New-Object -ComObject WScript.Shell;"
        "$s=$ws.CreateShortcut((Join-Path $d 'BordadoStudio.lnk'));"
        f"$s.TargetPath='{py}';"
        f"$s.Arguments='\"{main_py}\"';"
        f"$s.WorkingDirectory='{RAIZ}';"
        f"$s.IconLocation='{icone},0';"
        "$s.Description='BordadoStudio - Estudio de bordado';"
        "$s.Save()"
    )
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-Command", ps],
        capture_output=True, text=True, **criar_env_oculto())
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "falha no powershell")
                           .strip()[:200])
    return "criado"


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
                if etapa == "bloqueado":
                    self.titulo.config(text="Instalacao bloqueada",
                                       fg="#b02020")
                    self.status.config(
                        text=msg or "Programa bloqueado pelo desenvolvedor.",
                        fg="#b02020", wraplength=360, justify="left")
                    self.btn_log.pack(side="left")
                    return
                self.barra["value"] = etapa
                self.status.config(text=msg)
                if etapa == PASSOS:
                    self.titulo.config(text="Instalacao concluida!",
                                       fg="#1f7a2e")
                    self.status.config(
                        text="Pronto! Use o icone \"BordadoStudio\" na "
                             "Area de Trabalho ou o botao acima.")
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
