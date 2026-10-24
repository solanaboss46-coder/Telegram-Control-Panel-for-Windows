"""Proxies manager page."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..db import Database
from ..proxy_service import ProxyService


class AddProxyDialog(QDialog):
    TYPES = ("socks5", "socks4", "http", "mtproxy")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add proxy")
        self.setModal(True)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.type_input = QLineEdit("socks5")
        self.host_input = QLineEdit()
        self.port_input = QLineEdit("1080")
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Name:", self.name_input)
        form.addRow("Type:", self.type_input)
        form.addRow("Host:", self.host_input)
        form.addRow("Port:", self.port_input)
        form.addRow("Username:", self.user_input)
        form.addRow("Password:", self.pass_input)
        layout.addLayout(form)

        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        layout.addWidget(box)

    def data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "type": self.type_input.text().strip() or "socks5",
            "host": self.host_input.text().strip(),
            "port": int(self.port_input.text()) if self.port_input.text().strip().isdigit() else 0,
            "username": self.user_input.text().strip() or None,
            "password": self.pass_input.text().strip() or None,
        }


class ProxiesPage(QWidget):
    def __init__(self, db: Database, cm, proxies: ProxyService) -> None:
        super().__init__()
        self.db = db
        self.cm = cm
        self.proxies = proxies

        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("Add proxy")
        self.btn_edit = QPushButton("Edit")
        self.btn_delete = QPushButton("Delete")
        self.btn_test = QPushButton("Test connection")
        for b in (self.btn_add, self.btn_edit, self.btn_delete, self.btn_test):
            toolbar.addWidget(b)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "Type", "Host", "Port", "Username", "Status", "Error"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTriggers.NoEditTriggers)
        layout.addWidget(self.table)

        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_test.clicked.connect(self._test)

        self.refresh()

    def _selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def refresh(self) -> None:
        proxies = self.proxies.list_proxies()
        self.table.setRowCount(len(proxies))
        for r, p in enumerate(proxies):
            vals = [
                str(p["id"]),
                p["name"],
                p["type"],
                p["host"],
                str(p["port"]),
                p["username"] or "",
                p["status"],
                p["error_message"] or "",
            ]
            for c, v in enumerate(vals):
                self.table.setItem(r, c, QTableWidgetItem(v))
        self.table.resizeColumnsToContents()

    def on_show(self) -> None:
        self.refresh()

    def _add(self) -> None:
        dlg = AddProxyDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.data()
        if not data["name"] or not data["host"] or not data["port"]:
            QMessageBox.warning(self, "Missing fields", "Name, host and port are required.")
            return
        self.proxies.add_proxy(
            name=data["name"],
            type=data["type"],
            host=data["host"],
            port=data["port"],
            username=data["username"],
            password=data["password"],
        )
        self.db.add_event("proxy_added", message=f"Proxy {data['name']} added")
        self.refresh()

    def _edit(self) -> None:
        pid = self._selected_id()
        if pid is None:
            return
        p = self.db.get_proxy(pid)
        if not p:
            return
        dlg = AddProxyDialog(self)
        dlg.name_input.setText(p["name"] or "")
        dlg.type_input.setText(p["type"] or "")
        dlg.host_input.setText(p["host"] or "")
        dlg.port_input.setText(str(p["port"] or ""))
        dlg.user_input.setText(p["username"] or "")
        dlg.pass_input.setText(p.get("password") or "")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.data()
        self.proxies.update_proxy(
            pid,
            name=data["name"],
            type=data["type"],
            host=data["host"],
            port=data["port"],
            username=data["username"],
            password=data["password"],
        )
        self.db.add_event("proxy_edited", message=f"Proxy {pid} updated")
        self.refresh()

    def _delete(self) -> None:
        pid = self._selected_id()
        if pid is None:
            return
        confirm = QMessageBox.question(
            self, "Delete proxy", "Remove this proxy?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.proxies.delete_proxy(pid)
        self.db.add_event("proxy_deleted", message=f"Proxy {pid} removed")
        self.refresh()

    def _test(self) -> None:
        pid = self._selected_id()
        if pid is None:
            return
        self.proxies.check_proxy(pid)
        self.refresh()
