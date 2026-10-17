"""Ponto de entrada da aplicação."""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication, QMessageBox

from . import APP_NAME, __version__, controle
from .main_window import MainWindow


class _SinalBloqueio(QObject):
    """Encaminha o resultado do bloqueio para a thread da interface."""
    pronto = Signal(bool, str)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(APP_NAME)

    win = MainWindow()
    win.resize(1280, 820)

    # aviso ao desenvolvedor em TODA abertura (celular + e-mail),
    # em segundo plano — nunca atrasa ou trava o programa
    primeiro = not controle.existe_id()
    controle.install_id()
    controle.notificar_instalacao(
        __version__, evento="primeira_execucao" if primeiro else "abertura")

    # bloqueio remoto (consulta rápida em segundo plano; se não houver
    # internet, o programa abre normalmente — falha aberta)
    sinal = _SinalBloqueio()

    def _ao_bloquear(bloqueado: bool, motivo: str):
        if not bloqueado:
            return
        QMessageBox.critical(
            None, f"{APP_NAME} — bloqueado",
            f"{motivo}\n\n"
            "Este programa foi bloqueado pelo desenvolvedor.\n"
            "Se você acha que é um engano, contate o suporte.")
        win.close()
        app.quit()

    sinal.pronto.connect(_ao_bloquear)

    def _checar():
        controle.checar_bloqueio_async(
            lambda bloqueado, motivo: sinal.pronto.emit(bloqueado, motivo))

    _checar()

    # reavalia de tempos em tempos: o comando do celular (ntfy) passa
    # a valer mesmo com o programa já aberto (a cada 10 minutos)
    timer = QTimer(app)
    timer.setInterval(10 * 60 * 1000)
    timer.timeout.connect(_checar)
    timer.start()

    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
