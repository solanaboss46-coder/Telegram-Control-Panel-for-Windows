"""Dashboard page."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class DashboardPage(QWidget):
    def __init__(self, db, cm, accounts, proxies, inbox) -> None:
        super().__init__()
        self.db = db
        self.cm = cm
        self.accounts = accounts
        self.proxies = proxies
        self.inbox = inbox

        layout = QVBoxLayout(self)

        # Stat cards
        stats = QGridLayout()
        self.card_total = self._card("Accounts", "0")
        self.card_connected = self._card("Connected", "0")
        self.card_errors = self._card("Errors", "0")
        self.card_proxy = self._card("Proxy", "—")
        self.card_messages = self._card("New messages", "0")
        for i, card in enumerate([self.card_total, self.card_connected, self.card_errors, self.card_proxy, self.card_messages]):
            stats.addWidget(card, 0, i)
        stats.setColumnStretch(5, 1)
        layout.addLayout(stats)

        # Recent events
        layout.addWidget(QLabel("Recent events"))
        self.events_list = QListWidget()
        layout.addWidget(self.events_list)

    def _card(self, title: str, value: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("statCard")
        frame.setFixedHeight(90)
        v = QVBoxLayout(frame)
        v.setContentsMargins(12, 10, 12, 10)
        t = QLabel(title)
        t.setObjectName("cardTitle")
        val = QLabel(value)
        val.setObjectName("cardValue")
        val.setProperty("cardKey", title)
        v.addWidget(t)
        v.addWidget(val)
        frame.value_label = val
        return frame

    def refresh(self) -> None:
        accounts = self.db.get_accounts()
        total = len(accounts)
        connected = sum(1 for a in accounts if a["status"] == "connected")
        errors = sum(1 for a in accounts if a["status"] == "error")
        auth_err = sum(1 for a in accounts if a["status"] == "authorization_required")

        self.card_total.value_label.setText(str(total))
        self.card_connected.value_label.setText(str(connected))
        self.card_errors.value_label.setText(str(errors + auth_err))

        proxies = self.db.get_proxies()
        proxy_status = proxies[0]["status"] if proxies else "—"
        self.card_proxy.value_label.setText(proxy_status.capitalize() if proxy_status != "—" else "—")

        # recent events count via db
        events = self.db.get_events(limit=10)
        self.events_list.clear()
        for ev in events:
            item = QListWidgetItem(f"{ev['timestamp'][:16]}  [{ev['type']}] {ev['message']}")
            self.events_list.addItem(item)

    def on_show(self) -> None:
        self.refresh()
