"""Inbox page: dialogs and messages per account."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..account_service import AccountService
from ..client import ClientManager
from ..db import Database
from ..inbox_service import InboxService


class InboxPage(QWidget):
    def __init__(self, db: Database, cm: ClientManager, inbox: InboxService, accounts: AccountService) -> None:
        super().__init__()
        self.db = db
        self.cm = cm
        self.inbox = inbox
        self.accounts = accounts

        self.account_id: int | None = None
        self.all_accounts = False
        self.chat_id: int | None = None
        self.dialogs: list = []
        self.messages: list = []

        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Account:"))
        self.account_combo = QLabel("—")
        toolbar.addWidget(self.account_combo)
        self.btn_all = QPushButton("All accounts")
        self.btn_all.setCheckable(True)
        self.btn_all.clicked.connect(self._toggle_all)
        toolbar.addWidget(self.btn_all)
        toolbar.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search dialogs / messages")
        self.search_input.textChanged.connect(self._filter)
        toolbar.addWidget(self.search_input)
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self._refresh_dialogs)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        splitter = QSplitter()

        # Dialogs list
        self.dialogs_list = QListWidget()
        self.dialogs_list.itemClicked.connect(self._on_dialog_clicked)
        splitter.addWidget(self.dialogs_list)

        # Messages
        msgs_panel = QWidget()
        msgs_layout = QVBoxLayout(msgs_panel)
        msgs_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_list = QListWidget()
        msgs_layout.addWidget(self.messages_list)

        send_panel = QHBoxLayout()
        self.msg_input = QTextEdit()
        self.msg_input.setFixedHeight(60)
        self.msg_input.setPlaceholderText("Message...")
        self.btn_send = QPushButton("Send")
        self.btn_send.setObjectName("primary")
        self.btn_send.clicked.connect(self._send)
        send_panel.addWidget(self.msg_input)
        send_panel.addWidget(self.btn_send)
        msgs_layout.addLayout(send_panel)
        splitter.addWidget(msgs_panel)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

    def _toggle_all(self) -> None:
        self.all_accounts = self.btn_all.isChecked()
        if self.all_accounts:
            self.account_id = None
            self.account_combo.setText("All accounts")
        self.dialogs_list.clear()
        self.messages_list.clear()
        self.chat_id = None

    def _refresh_dialogs(self) -> None:
        if self.all_accounts:
            for a in self.db.get_accounts():
                if a["status"] == "connected":
                    self.cm.load_dialogs(a["id"], limit=30)
        elif self.account_id is not None:
            self.cm.load_dialogs(self.account_id, limit=50)

    def handle_dialogs(self, account_id: int, dialogs: list) -> None:
        self.dialogs_list.clear()
        for d in dialogs:
            label = f"{d['title']} ({d['unread_count']} unread)" if d["unread_count"] else d["title"]
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, {"account_id": account_id, "chat_id": d["chat_id"], "title": d["title"]})
            self.dialogs_list.addItem(item)

    def _on_dialog_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        self.account_id = data["account_id"]
        self.chat_id = data["chat_id"]
        self.account_combo.setText(f"Account {data['account_id']} — {data['title']}")
        self.btn_all.setChecked(False)
        self.all_accounts = False
        self.cm.load_messages(self.account_id, self.chat_id, limit=100)

    def handle_message(self, account_id: int, message: dict) -> None:
        if message.get("__batch__"):
            if self.chat_id == message.get("chat_id") and (
                self.all_accounts or account_id == self.account_id
            ):
                self.messages_list.clear()
                for m in message["messages"]:
                    self._append_message(m)
            return
        if self.chat_id is not None and (
            (self.all_accounts and message.get("chat_id") == self.chat_id)
            or (not self.all_accounts and account_id == self.account_id and message.get("chat_id") == self.chat_id)
        ):
            self._append_message(message)

    def _append_message(self, m: dict) -> None:
        date = m.get("date", "")[:16]
        text = (m.get("text") or "").replace("\n", " ")
        prefix = ">>" if m.get("out") else "<<"
        item = QListWidgetItem(f"[{date}] {prefix} {m.get('sender_name','?')}: {text}")
        if not m.get("out") and m.get("unread"):
            item.setBackground(Qt.GlobalColor.yellow)
        self.messages_list.addItem(item)
        self.messages_list.scrollToBottom()

    def _filter(self, text: str) -> None:
        text = text.lower()
        for i in range(self.messages_list.count()):
            item = self.messages_list.item(i)
            item.setHidden(text not in item.text().lower())

    def _send(self) -> None:
        text = self.msg_input.toPlainText().strip()
        if not text or self.chat_id is None or self.account_id is None:
            return
        self.inbox.send_message(self.account_id, self.chat_id, text)
        self.msg_input.clear()
