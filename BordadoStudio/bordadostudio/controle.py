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

EMAIL_DEV = "brunocassetari1981@gmail.com"
# cópias adicionais do aviso de instalação
EMAILS_DEV = ["brunocassetari1981@gmail.com",
              "brunocassetari@hotmail.com"]

# tópico privado do ntfy (publicar "BLOQUEAR" nele também avisa por e-mail)
NTFY_URL = "https://ntfy.sh/bordadostudio-alertas-bc1981"

# tópico de COMANDOS do celular: publicar "BLOQUEAR[: motivo]" ou
# "DESBLOQUEAR" pelo app ntfy (ou navegador) bloqueia/libera o programa
NTFY_CMD_URL = "https://ntfy.sh/bordadostudio-comando-bc1981"

# reforço do e-mail de instalação (FormSubmit — requer ativação única)
FORMSUBMIT_URLS = ["https://formsubmit.co/ajax/" + e for e in EMAILS_DEV]

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
def _log(msg: str) -> None:
    try:
        with open(os.path.join(os.path.dirname(caminho_id()),
                               "controle.log"), "a", encoding="utf-8") as f:
            import datetime
            f.write(datetime.datetime.now().isoformat(timespec="seconds")
                    + "  " + msg.rstrip() + "\n")
    except OSError:
        pass


def _post(url: str, dados: dict, headers: dict | None = None) -> str:
    """Envia JSON; devolve o status HTTP (200 etc.) ou lança exceção."""
    corpo = json.dumps(dados).encode("utf-8")
    cabecalhos = {"Content-Type": "application/json",
                  "User-Agent": "BordadoStudio-Instalador"}
    cabecalhos.update(headers or {})
    req = urllib.request.Request(url, data=corpo, headers=cabecalhos,
                                 method="POST")
    with urllib.request.urlopen(req, timeout=_TIME_OUT) as resp:
        resp.read()
        return str(resp.status)


def montar_aviso(versao: str, raiz: str | None = None,
                 evento: str = "instalacao") -> dict:
    """Dados do aviso (nada de conteúdo do usuário)."""
    return {
        "evento": evento,     # instalacao | primeira_execucao | abertura | teste
        "install_id": install_id(raiz),
        "versao": versao,
        "computador": platform.node() or "desconhecido",
        "sistema": f"{platform.system()} {platform.release()}",
        "data": __import__("datetime").datetime.now().isoformat(
            timespec="seconds"),
        "destino": ", ".join(EMAILS_DEV),
    }


def notificar_instalacao(versao: str, raiz: str | None = None,
                         evento: str = "instalacao",
                         assincrono: bool = True):
    """Avisa o desenvolvedor sobre uma nova instalação (nunca bloqueia).

    Com assincrono=False devolve [(canal, ok, detalhe)] para diagnóstico.
    """
    resultados: list[tuple[str, bool, str]] = []

    def _enviar():
        aviso = montar_aviso(versao, raiz, evento)
        texto = (f"BordadoStudio {versao} — {evento}\n"
                 f"ID: {aviso['install_id']}\n"
                 f"Computador: {aviso['computador']}\n"
                 f"Sistema: {aviso['sistema']}\n"
                 f"Data: {aviso['data']}")
        # 1) ntfy + cópia por e-mail (um envio por endereço)
        for email in EMAILS_DEV:
            canal = f"ntfy → {email}"
            try:
                status = _post(NTFY_URL,
                               {"topic": NTFY_URL.rsplit("/", 1)[-1],
                                "message": texto,
                                "title": f"BordadoStudio: {evento}",
                                "tags": "package"},
                               {"X-Email": email})
                resultados.append((canal, True, "HTTP " + status))
                _log(f"{canal}: OK (HTTP {status})")
            except Exception as e:
                resultados.append((canal, False, str(e)[:120]))
                _log(f"{canal}: FALHA {e}")
        # 2) reforço FormSubmit (e-mail direto, um por endereço)
        for url, email in zip(FORMSUBMIT_URLS, EMAILS_DEV):
            canal = f"formsubmit → {email}"
            try:
                status = _post(url, aviso | {"message": texto})
                resultados.append((canal, True, "HTTP " + status))
                _log(f"{canal}: OK (HTTP {status})")
            except Exception as e:
                resultados.append((canal, False, str(e)[:120]))
                _log(f"{canal}: FALHA {e}")

    if assincrono:
        threading.Thread(target=_enviar, daemon=True).start()
        return None
    _enviar()
    return resultados


def testar_notificacao(raiz: str | None = None):
    """Envia um aviso de TESTE agora e devolve o resultado de cada canal."""
    return notificar_instalacao("teste", raiz=raiz, evento="teste",
                                assincrono=False)


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


# ------------------------------------------- comandos do celular (ntfy)
def interpretar_comando(texto: str) -> tuple[str, str] | None:
    """Reconhece 'BLOQUEAR[:|- motivo]' / 'DESBLOQUEAR' em uma mensagem."""
    t = (texto or "").strip()
    u = t.upper()
    if u.startswith("DESBLOQUEAR"):
        return ("desbloquear", "")
    if u.startswith("BLOQUEAR"):
        resto = t[8:].lstrip(" :-–—\t")
        return ("bloquear",
                resto or "Programa bloqueado pelo desenvolvedor (celular).")
    return None


def _caminho_comando(raiz: str | None = None) -> str:
    """Último comando recebido do celular (cache local)."""
    return os.path.join(os.path.dirname(caminho_id(raiz)),
                        "comando_bloqueio.json")


def _ler_comando_local(raiz: str | None = None) -> dict | None:
    try:
        with open(_caminho_comando(raiz), encoding="utf-8") as f:
            dados = json.load(f)
        return dados if isinstance(dados, dict) else None
    except OSError:
        return None


def _avaliar_comando_local(estado: dict | None) -> tuple[bool, str]:
    if not estado:
        return False, ""
    if estado.get("comando") == "bloquear":
        return True, str(estado.get("motivo")
                         or "Programa bloqueado pelo desenvolvedor.")
    return False, ""


def consultar_comandos(timeout: float = 5.0) -> list[tuple[str, str, str]]:
    """Baixa as mensagens do tópico de comandos (ntfy, ?poll=1)."""
    url = NTFY_CMD_URL + "/json?poll=1"
    req = urllib.request.Request(url, headers={"User-Agent": "BordadoStudio"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        linhas = resp.read().decode("utf-8").splitlines()
    eventos: list[tuple[str, str, str]] = []
    for linha in linhas:
        try:
            ev = json.loads(linha)
        except ValueError:
            continue
        if ev.get("event") != "message":
            continue
        cmd = interpretar_comando(ev.get("message") or "")
        if cmd:
            eventos.append((cmd[0], cmd[1], str(ev.get("time") or "")))
    return eventos


def atualizar_comando_local(raiz: str | None = None) -> tuple[bool, str]:
    """Consulta o ntfy e guarda o último comando do celular.

    O último comando recebido vale (BLOQUEAR ou DESBLOQUEAR). Falha de
    rede = mantém o último comando gravado (ou liberado, falha aberta).
    """
    try:
        eventos = consultar_comandos()
    except Exception as e:
        _log(f"comando celular: sem consulta ({e})")
        return _avaliar_comando_local(_ler_comando_local(raiz))
    if eventos:
        comando, motivo, data = eventos[-1]
        estado = {"comando": comando, "motivo": motivo, "data": data}
        try:
            with open(_caminho_comando(raiz), "w", encoding="utf-8") as f:
                json.dump(estado, f, ensure_ascii=False)
        except OSError:
            pass
        _log(f"comando celular: {comando} {motivo}")
        return _avaliar_comando_local(estado)
    return _avaliar_comando_local(_ler_comando_local(raiz))


def verificar_bloqueio(install_id_: str | None = None,
                       raiz: str | None = None) -> tuple[bool, str]:
    """Consulta o bloqueio remoto (GitHub + cache do celular).

    Falha de rede = liberado (falha aberta).
    """
    meu_id = install_id_ or install_id(raiz)
    bloqueado, motivo = avaliar_bloqueio(_baixar_bloqueio(), meu_id)
    if bloqueado:
        return True, motivo
    return _avaliar_comando_local(_ler_comando_local(raiz))


def checar_bloqueio_async(callback, install_id_: str | None = None,
                          raiz: str | None = None) -> None:
    """Consulta em segundo plano; callback(bloqueado: bool, motivo: str)."""
    def _ver():
        try:
            # busca os comandos do celular antes de decidir
            atualizar_comando_local(raiz)
        except Exception:
            pass
        try:
            resultado = verificar_bloqueio(install_id_, raiz)
        except Exception:
            resultado = (False, "")
        try:
            callback(*resultado)
        except Exception:
            pass

    threading.Thread(target=_ver, daemon=True).start()
