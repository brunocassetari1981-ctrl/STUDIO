"""Ponto de entrada da aplicação."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from . import APP_NAME, __version__
from .main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(APP_NAME)

    win = MainWindow()
    win.resize(1280, 820)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
