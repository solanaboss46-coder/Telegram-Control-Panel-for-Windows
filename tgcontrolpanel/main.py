"""Application entry point."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from tgcontrolpanel.config import APP_DISPLAY_NAME, SESSIONS_DIR
from tgcontrolpanel.gui.main_window import MainWindow


def main() -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_DISPLAY_NAME)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
