"""Event log page."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..db import Database


class LogPage(QWidget):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter events...")
        self.filter_input.textChanged.connect(self._filter)
        toolbar.addWidget(self.filter_input)
        self.btn_clear = QPushButton("Clear log")
        self.btn_clear.clicked.connect(self._clear)
        toolbar.addWidget(self.btn_clear)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Time", "Account", "Type", "Message", ""])
        self.table.setEditTriggers(QAbstractItemView.EditTriggers.NoEditTriggers)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self) -> None:
        events = self.db.get_events(limit=300)
        self.table.setRowCount(len(events))
        for r, e in enumerate(events):
            vals = [e["timestamp"][:16], str(e["account_id"] or ""), e["type"], e["message"], ""]
            for c, v in enumerate(vals):
                self.table.setItem(r, c, QTableWidgetItem(v))
        self.table.resizeColumnsToContents()

    def on_show(self) -> None:
        self.refresh()

    def _filter(self, text: str) -> None:
        text = text.lower()
        for r in range(self.table.rowCount()):
            hidden = True
            for c in range(self.table.columnCount() - 1):
                item = self.table.item(r, c)
                if item and text in item.text().lower():
                    hidden = False
                    break
            self.table.setRowHidden(r, hidden)

    def _clear(self) -> None:
        self.db.clear_events()
        self.refresh()
