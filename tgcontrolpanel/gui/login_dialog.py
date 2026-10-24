"""Login / authorization dialog for Telegram code and 2FA."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class LoginDialog(QDialog):
    def __init__(self, phone: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Telegram authorization")
        self.setModal(True)
        self.code_result: str | None = None
        self.password_result: str | None = None

        layout = QVBoxLayout(self)

        self.info = QLabel(f"Enter the login code sent to {phone or 'your phone'}.")
        layout.addWidget(self.info)

        form = QFormLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Code")
        form.addRow("Code:", self.code_input)
        layout.addLayout(form)

        btns = QHBoxLayout()
        self.send_code_btn = QPushButton("Request code")
        self.send_code_btn.clicked.connect(self._request_code)
        btns.addWidget(self.send_code_btn)
        layout.addLayout(btns)

        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        layout.addWidget(box)

        self._mode = "code"

    def _request_code(self) -> None:
        self.code_result = self.code_input.text().strip() or None
        if not self.code_result:
            return
        self.accept()

    def get_code(self) -> str | None:
        return self.code_result


class TwoFaDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Two-step verification")
        self.setModal(True)
        self.password_result: str | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter your Telegram cloud password (2FA):"))
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.pw_input)

        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        layout.addWidget(box)

    def get_password(self) -> str | None:
        return self.pw_input.text().strip() or None
