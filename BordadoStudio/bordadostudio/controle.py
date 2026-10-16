"""Controle do desenvolvedor: notificação de instalação e bloqueio remoto.

- A cada instalação é enviada uma notificação ao desenvolvedor
  (e-mail brunocassetari@hotmail.com) com o ID da instalação, computador,
  sistema e versão — sem nenhum dado de bordado.
- O desenvolvedor pode bloquear o programa editando o arquivo público
  https://github.com/brunocassetari1981-ctrl/BordadoStudio-Controle
  (bloqueio.json) — pelo celular ou navegador, de qualquer lugar.

Política de rede: o programa NUNCA exige internet para funcionar.
Se a consulta de bloqueio falhar (computador offline), o programa
continua normalmente (falha aberta). A notificação de instalação é
discreta e nunca atrasa ou interrompe a instalação.

Tudo aqui usa apenas a biblioteca padrão do Python.
"""

from __future__ import annotations

import base64
import json
import os
import platform
import threading
import urllib.request
import uuid

EMAIL_DEV = "brunocassetari@hotmail.com"

# tópico privado do ntfy (publicar "BLOQUEAR" nele também avisa por e-mail)
NTFY_URL = "https://ntfy.sh/bordadostudio-alertas-bc1981"

# reforço do e-mail de instalação (FormSubmit — requer ativação única)
FORMSUBMIT_URL = "https://formsubmit.co/ajax/" + EMAIL_DEV

# arquivo de bloqueio controlado pelo desenvolvedor (repositório público STUDIO)
_REPO = "brunocassetari1981-ctrl/STUDIO"
_CAMINHO = "BordadoStudio/controle/bloqueio.json"
_REFS = ("arena/866ffde9-studio", "main")
BLOQUEIO_RAW = (
    "https://raw.githubusercontent.com/{repo}/{ref}/" + _CAMINHO)
BLOQUEIO_API = (
    "https://api.github.com/repos/{repo}/contents/" + _CAMINHO + "?ref={ref}")

_TIME_OUT = 8.0


# ------------------------------------------------------------------ ID
def caminho_id(raiz: str | None = None) -> str:
    """Arquivo que guarda o ID desta instalação (na pasta do programa)."""
    base = raiz or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "instalacao_id")


def install_id(raiz: str | None = None, criar: bool = True) -> str:
    """ID único da instalação (criado na primeira vez)."""
    caminho = caminho_id(raiz)
    try:
        with open(caminho, encoding="utf-8") as f:
            texto = f.read().strip()
        if texto:
            return texto
    except OSError:
        pass
    if not criar:
        return ""
    novo = uuid.uuid4().hex[:12]
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(novo + "\n")
    except OSError:
        pass
    return novo


def existe_id(raiz: str | None = None) -> bool:
    try:
        with open(caminho_id(raiz), encoding="utf-8") as f:
            return bool(f.read().strip())
    except OSError:
        return False


# ------------------------------------------------------------- envio
def _post(url: str, dados: dict, headers: dict | None = None) -> bool:
    corpo = json.dumps(dados).encode("utf-8")
    cabecalhos = {"Content-Type": "application/json",
                  "User-Agent": "BordadoStudio-Instalador"}
    cabecalhos.update(headers or {})
    req = urllib.request.Request(url, data=corpo, headers=cabecalhos,
                                 method="POST")
    with urllib.request.urlopen(req, timeout=_TIME_OUT) as resp:
        resp.read()
    return True


def montar_aviso(versao: str, raiz: str | None = None,
                 evento: str = "instalacao") -> dict:
    """Dados do aviso (nada de conteúdo do usuário)."""
    return {
        "evento": evento,                      # instalacao | primeira_execucao
        "install_id": install_id(raiz),
        "versao": versao,
        "computador": platform.node() or "desconhecido",
        "sistema": f"{platform.system()} {platform.release()}",
        "data": __import__("datetime").datetime.now().isoformat(
            timespec="seconds"),
        "destino": EMAIL_DEV,
    }


def notificar_instalacao(versao: str, raiz: str | None = None,
                         evento: str = "instalacao",
                         assincrono: bool = True) -> None:
    """Avisa o desenvolvedor sobre uma nova instalação (nunca bloqueia)."""
    def _enviar():
        aviso = montar_aviso(versao, raiz, evento)
        texto = (f"BordadoStudio {versao} — {evento}\n"
                 f"ID: {aviso['install_id']}\n"
                 f"Computador: {aviso['computador']}\n"
                 f"Sistema: {aviso['sistema']}\n"
                 f"Data: {aviso['data']}")
        # 1) ntfy + cópia por e-mail (chega direto no Hotmail)
        try:
            _post(NTFY_URL, {"topic": NTFY_URL.rsplit("/", 1)[-1],
                             "message": texto,
                             "title": f"BordadoStudio: {evento}",
                             "tags": "package"},
                  {"X-Email": EMAIL_DEV})
        except Exception:
            pass
        # 2) reforço FormSubmit (e-mail direto)
        try:
            _post(FORMSUBMIT_URL, aviso | {"message": texto})
        except Exception:
            pass

    if assincrono:
        threading.Thread(target=_enviar, daemon=True).start()
    else:
        _enviar()


# ------------------------------------------------------------- bloqueio
def _baixar_bloqueio() -> dict | None:
    """Baixa o bloqueio.json (raw; se falhar, a API do GitHub)."""
    for ref in _REFS:
        for modelo in (BLOQUEIO_RAW, BLOQUEIO_API):
            url = modelo.format(repo=_REPO, ref=ref)
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "BordadoStudio",
                                  "Accept": "application/vnd.github+json"})
                with urllib.request.urlopen(req, timeout=_TIME_OUT) as resp:
                    dados = json.loads(resp.read().decode("utf-8"))
                if isinstance(dados, dict) and "content" in dados:
                    return json.loads(
                        base64.b64decode(dados["content"]).decode("utf-8"))
                return dados
            except Exception:
                continue
    return None


def avaliar_bloqueio(dados: dict | None, meu_id: str) -> tuple[bool, str]:
    """Decide se esta instalação está bloqueada (regra pura, testável)."""
    if not dados:
        return False, ""
    bloquear_ids = [str(i) for i in dados.get("bloquear_ids") or []]
    permitir_ids = [str(i) for i in dados.get("permitir_ids") or []]
    motivo = str(dados.get("motivo") or "Programa bloqueado pelo desenvolvedor.")
    if meu_id in permitir_ids:
        return False, ""
    if meu_id in bloquear_ids:
        return True, motivo
    if dados.get("bloquear"):
        return True, motivo
    return False, ""


def verificar_bloqueio(install_id_: str | None = None,
                       raiz: str | None = None) -> tuple[bool, str]:
    """Consulta o bloqueio remoto. Falha de rede = liberado (falha aberta)."""
    meu_id = install_id_ or install_id(raiz)
    return avaliar_bloqueio(_baixar_bloqueio(), meu_id)


def checar_bloqueio_async(callback, install_id_: str | None = None,
                          raiz: str | None = None) -> None:
    """Consulta em segundo plano; callback(bloqueado: bool, motivo: str)."""
    def _ver():
        try:
            resultado = verificar_bloqueio(install_id_, raiz)
        except Exception:
            resultado = (False, "")
        try:
            callback(*resultado)
        except Exception:
            pass

    threading.Thread(target=_ver, daemon=True).start()
