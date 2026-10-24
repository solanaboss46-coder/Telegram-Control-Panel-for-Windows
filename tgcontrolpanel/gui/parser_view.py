"""Participant parser page."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..account_service import AccountService
from ..client import ClientManager
from ..db import Database
from ..parser_service import ParserService


class ParserPage(QWidget):
    def __init__(self, db: Database, cm: ClientManager, parser: ParserService, accounts: AccountService) -> None:
        super().__init__()
        self.db = db
        self.cm = cm
        self.parser = parser
        self.accounts = accounts
        self.participants: list = []

        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Account:"))
        self.account_combo = QLabel("—")
        toolbar.addWidget(self.account_combo)
        toolbar.addWidget(QLabel("Chat link / ID:"))
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("https://t.me/... or chat ID")
        toolbar.addWidget(self.chat_input)
        self.btn_load = QPushButton("Load participants")
        self.btn_load.setObjectName("primary")
        self.btn_load.clicked.connect(self._load)
        toolbar.addWidget(self.btn_load)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self.parser.stop)
        toolbar.addWidget(self.btn_stop)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.progress = QLabel("")
        layout.addWidget(self.progress)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Name", "Phone", "Bot", "Account"])
        self.table.setEditTriggers(QAbstractItemView.EditTriggers.NoEditTriggers)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        self.btn_search = QLineEdit()
        self.btn_search.setPlaceholderText("Search results")
        self.btn_search.textChanged.connect(self._filter)
        btns.addWidget(self.btn_search)
        self.btn_export = QPushButton("Export CSV")
        self.btn_export.clicked.connect(self._export)
        btns.addWidget(self.btn_export)
        btns.addStretch()
        layout.addLayout(btns)

        self.cm.participants_loaded.connect(self._on_participants)

    def _selected_account_id(self) -> int | None:
        accounts = self.db.get_accounts()
        connected = [a for a in accounts if a["status"] == "connected"]
        if not connected:
            return None
        return connected[0]["id"]

    def _load(self) -> None:
        chat = self.chat_input.text().strip()
        if not chat:
            QMessageBox.warning(self, "Missing", "Enter a chat link or ID.")
            return
        aid = self._selected_account_id()
        if aid is None:
            QMessageBox.warning(self, "No account", "No connected account available.")
            return
        self.account_combo.setText(f"Account {aid}")
        self.progress.setText("Loading participants...")
        self.table.setRowCount(0)
        self.participants = []
        peer: int | str = int(chat) if chat.lstrip("-").isdigit() else chat
        self.cm.load_participants(aid, peer)

    def _on_participants(self, participants: list) -> None:
        self.participants = participants
        self.progress.setText(f"Loaded {len(participants)} participants")
        self._refresh_table()

    def _refresh_table(self) -> None:
        self.table.setRowCount(len(self.participants))
        for r, p in enumerate(self.participants):
            vals = [str(p.get("id", "")), p.get("username", ""), p.get("name", ""), p.get("phone", ""), str(p.get("bot", "")), ""]
            for c, v in enumerate(vals):
                self.table.setItem(r, c, QTableWidgetItem(v))
        self.table.resizeColumnsToContents()

    def _filter(self, text: str) -> None:
        text = text.lower()
        for r in range(self.table.rowCount()):
            hidden = True
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item and text in item.text().lower():
                    hidden = False
                    break
            self.table.setRowHidden(r, hidden)

    def _export(self) -> None:
        if not self.participants:
            QMessageBox.information(self, "Export", "No participants to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "participants.csv", "CSV (*.csv)")
        if not path:
            return
        self.parser.export_csv(self.participants, path)
        self.db.add_event("export", message=f"Exported {len(self.participants)} participants to {path}")
        QMessageBox.information(self, "Export", f"Exported to {path}")
