"""Settings page."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..db import Database


class SettingsPage(QWidget):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.api_id_input = QLineEdit()
        self.api_hash_input = QLineEdit()
        self.poll_input = QLineEdit("5")
        form.addRow("Default API ID:", self.api_id_input)
        form.addRow("Default API Hash:", self.api_hash_input)
        form.addRow("Inbox poll interval (s):", self.poll_input)
        layout.addLayout(form)

        self.btn_save = QPushButton("Save settings")
        self.btn_save.clicked.connect(self._save)
        layout.addWidget(self.btn_save)
        layout.addStretch()

        self._load()

    def _load(self) -> None:
        self.api_id_input.setText(str(self.db.get_setting("api_id", "")))
        self.api_hash_input.setText(str(self.db.get_setting("api_hash", "")))
        self.poll_input.setText(str(self.db.get_setting("poll_interval", "5")))

    def _save(self) -> None:
        self.db.set_setting("api_id", self.api_id_input.text().strip())
        self.db.set_setting("api_hash", self.api_hash_input.text().strip())
        try:
            self.db.set_setting("poll_interval", int(self.poll_input.text()))
        except ValueError:
            self.db.set_setting("poll_interval", 5)
        self._load()
