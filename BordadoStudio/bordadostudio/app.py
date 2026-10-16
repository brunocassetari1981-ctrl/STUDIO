"""Ponto de entrada da aplicação."""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, Signal
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

    # primeira execução portátil (sem instalação) também avisa o desenvolvedor
    if not controle.existe_id():
        controle.install_id()
        controle.notificar_instalacao(__version__, evento="primeira_execucao")

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
    controle.checar_bloqueio_async(
        lambda bloqueado, motivo: sinal.pronto.emit(bloqueado, motivo))

    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
