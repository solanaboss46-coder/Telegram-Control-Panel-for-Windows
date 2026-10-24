"""Message sender page."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..account_service import AccountService
from ..client import ClientManager
from ..db import Database
from ..sender_service import SenderService


class SenderPage(QWidget):
    def __init__(self, db: Database, cm: ClientManager, sender: SenderService, accounts: AccountService) -> None:
        super().__init__()
        self.db = db
        self.cm = cm
        self.sender = sender
        self.accounts = accounts

        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Account:"))
        self.account_combo = QLabel("—")
        toolbar.addWidget(self.account_combo)
        toolbar.addWidget(QLabel("Recipients (IDs, comma separated):"))
        self.recipients_input = QLineEdit()
        self.recipients_input.setPlaceholderText("123456, @username")
        toolbar.addWidget(self.recipients_input)
        toolbar.addWidget(QLabel("Interval (s):"))
        self.interval_input = QLineEdit("1")
        self.interval_input.setFixedWidth(50)
        toolbar.addWidget(self.interval_input)
        layout.addLayout(toolbar)

        layout.addWidget(QLabel("Message text:"))
        self.text_input = QTextEdit()
        self.text_input.setFixedHeight(140)
        layout.addWidget(self.text_input)

        btns = QHBoxLayout()
        self.btn_preview = QPushButton("Preview")
        self.btn_preview.clicked.connect(self._preview)
        self.btn_start = QPushButton("Start")
        self.btn_start.setObjectName("primary")
        self.btn_start.clicked.connect(self._start)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("danger")
        self.btn_stop.clicked.connect(self._stop)
        self.btn_stop.setEnabled(False)
        for b in (self.btn_preview, self.btn_start, self.btn_stop):
            btns.addWidget(b)
        btns.addStretch()
        layout.addLayout(btns)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels(["Recipient", "Text", "Status", "Detail", "Account"])
        self.log_table.setEditTriggers(QAbstractItemView.EditTriggers.NoEditTriggers)
        layout.addWidget(self.log_table)

    def _selected_account_id(self) -> int | None:
        accounts = self.db.get_accounts()
        connected = [a for a in accounts if a["status"] == "connected"]
        if not connected:
            return None
        return connected[0]["id"]

    def _preview(self) -> None:
        text = self.text_input.toPlainText().strip()
        aid = self._selected_account_id()
        if aid is None or not text:
            return
        recipients = self._parse_recipients()
        self.sender.send_batch(aid, recipients[:1], text, 0, preview_only=True)
        self.account_combo.setText(f"Account {aid}")

    def _start(self) -> None:
        text = self.text_input.toPlainText().strip()
        aid = self._selected_account_id()
        if aid is None or not text:
            return
        recipients = self._parse_recipients()
        if not recipients:
            return
        interval = float(self.interval_input.text() or "1")
        self.sender.send_batch(aid, recipients, text, interval, preview_only=False)
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.account_combo.setText(f"Account {aid}")
        self.db.add_event("send_batch", message=f"Started sending to {len(recipients)} recipients", account_id=aid)

    def _stop(self) -> None:
        self.sender.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _parse_recipients(self) -> list[int]:
        raw = self.recipients_input.text()
        out = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                out.append(int(part))
            except ValueError:
                # username not directly supported as int; skip non-numeric
                continue
        return out
