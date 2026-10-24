"""Accounts manager page."""
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

from ..account_service import AccountService
from ..client import ClientManager
from ..db import Database
from .login_dialog import LoginDialog, TwoFaDialog


class AddAccountDialog(QDialog):
    def __init__(self, proxies: list, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Telegram account")
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.api_id_input = QLineEdit()
        self.api_hash_input = QLineEdit()
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("optional proxy id")

        form.addRow("Name:", self.name_input)
        form.addRow("Phone:", self.phone_input)
        form.addRow("API ID:", self.api_id_input)
        form.addRow("API Hash:", self.api_hash_input)
        form.addRow("Proxy ID:", self.proxy_input)
        layout.addLayout(form)

        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        layout.addWidget(box)

    def data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "phone": self.phone_input.text().strip() or None,
            "api_id": self.api_id_input.text().strip() or None,
            "api_hash": self.api_hash_input.text().strip() or None,
            "proxy_id": int(self.proxy_input.text()) if self.proxy_input.text().strip().isdigit() else None,
        }


class AccountsPage(QWidget):
    def __init__(self, db: Database, cm: ClientManager, accounts: AccountService) -> None:
        super().__init__()
        self.db = db
        self.cm = cm
        self.accounts = accounts
        self._pending_account_id: int | None = None

        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("Add account")
        self.btn_add.setObjectName("primary")
        self.btn_connect = QPushButton("Connect")
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_edit = QPushButton("Edit")
        self.btn_delete = QPushButton("Delete")
        self.btn_check = QPushButton("Check status")
        for b in (self.btn_add, self.btn_connect, self.btn_disconnect, self.btn_edit, self.btn_delete, self.btn_check):
            toolbar.addWidget(b)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "Phone", "Status", "Proxy", "Last check", "Error"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTriggers.NoEditTriggers)
        layout.addWidget(self.table)

        self.btn_add.clicked.connect(self._add)
        self.btn_connect.clicked.connect(self._connect)
        self.btn_disconnect.clicked.connect(self._disconnect)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_check.clicked.connect(self._check)

        # authorization flow
        self.cm.authorization_required.connect(self._on_authorization_required)
        self.cm.twofa_required.connect(self._on_twofa_required)

        self.refresh()

    def _selected_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def refresh(self) -> None:
        accounts = self.db.get_accounts()
        self.table.setRowCount(len(accounts))
        for r, a in enumerate(accounts):
            vals = [
                str(a["id"]),
                a["name"],
                a["phone"] or "",
                a["status"],
                str(a["proxy_id"]) if a["proxy_id"] else "",
                a["last_check"] or "",
                a["error_message"] or "",
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()

    def on_show(self) -> None:
        self.refresh()

    def _add(self) -> None:
        proxies = self.db.get_proxies()
        dlg = AddAccountDialog(proxies, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.data()
        if not data["name"] or not data["api_id"] or not data["api_hash"]:
            QMessageBox.warning(self, "Missing fields", "Name, API ID and API Hash are required.")
            return
        import re
        m = re.search(r"\d+", data["phone"] or "")
        phone = m.group(0) if m else data["phone"]
        session_file = None
        aid = self.accounts.add_account(
            name=data["name"],
            phone=phone,
            api_id=data["api_id"],
            api_hash=data["api_hash"],
            session_file=session_file,
            proxy_id=data["proxy_id"],
        )
        self.db.add_event("account_added", message=f"Account {data['name']} added", account_id=aid)
        self.refresh()

    def _connect(self) -> None:
        aid = self._selected_id()
        if aid is None:
            return
        self.accounts.connect_account(aid)

    def _disconnect(self) -> None:
        aid = self._selected_id()
        if aid is None:
            return
        self.accounts.disconnect_account(aid)

    def _edit(self) -> None:
        aid = self._selected_id()
        if aid is None:
            return
        acc = self.db.get_account(aid)
        if not acc:
            return
        dlg = AddAccountDialog([], self)
        dlg.name_input.setText(acc["name"] or "")
        dlg.phone_input.setText(acc["phone"] or "")
        dlg.api_id_input.setText(acc["api_id"] or "")
        dlg.api_hash_input.setText(acc["api_hash"] or "")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.data()
        self.accounts.update_account(
            aid,
            name=data["name"],
            phone=data["phone"],
            api_id=data["api_id"],
            api_hash=data["api_hash"],
            proxy_id=data["proxy_id"],
        )
        self.db.add_event("account_edited", message=f"Account {aid} updated", account_id=aid)
        self.refresh()

    def _delete(self) -> None:
        aid = self._selected_id()
        if aid is None:
            return
        confirm = QMessageBox.question(
            self, "Delete account", "Remove this account and its session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.accounts.delete_account(aid)
        self.refresh()

    def _check(self) -> None:
        aid = self._selected_id()
        if aid is None:
            return
        self.accounts.check_connection(aid)

    def _on_authorization_required(self, account_id: int, phone: str) -> None:
        if account_id != self._selected_id():
            # still record; open dialog anyway for the pending account
            pass
        self._pending_account_id = account_id
        dlg = LoginDialog(phone or "", self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        code = dlg.get_code()
        if code:
            self.cm.submit_code(account_id, code)

    def _on_twofa_required(self, account_id: int) -> None:
        if self._pending_account_id is not None and account_id != self._pending_account_id:
            return
        dlg = TwoFaDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        pw = dlg.get_password()
        if pw:
            self.cm.submit_password(account_id, pw)
