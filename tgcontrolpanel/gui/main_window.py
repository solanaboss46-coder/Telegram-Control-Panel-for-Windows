"""Main window: shell with sidebar navigation and stacked pages."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..account_service import AccountService
from ..client import ClientManager
from ..config import APP_DISPLAY_NAME
from ..db import Database
from ..inbox_service import InboxService
from ..parser_service import ParserService
from ..proxy_service import ProxyService
from ..sender_service import SenderService
from .accounts_view import AccountsPage
from .dashboard import DashboardPage
from .inbox_view import InboxPage
from .log_view import LogPage
from .parser_view import ParserPage
from .proxies_view import ProxiesPage
from .sender_view import SenderPage
from .settings_view import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.resize(1200, 800)

        # Core services
        self.db = Database()
        self.cm = ClientManager(self.db)
        self.accounts = AccountService(self.db, self.cm)
        self.proxies = ProxyService(self.db, self.cm)
        self.inbox = InboxService(self.db, self.cm)
        self.parser = ParserService(self.db, self.cm)
        self.sender = SenderService(self.db, self.cm)

        self._build_ui()
        self._wire_signals()

        self.cm.start()

        # Periodic dashboard refresh
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_dashboard)
        self._refresh_timer.start(5000)

        self._refresh_dashboard()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(210)
        sidebar.setObjectName("sidebar")
        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(8, 16, 8, 16)
        s_layout.setSpacing(4)

        title = QLabel(APP_DISPLAY_NAME)
        title.setObjectName("sidebarTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s_layout.addWidget(title)

        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setCurrentRow(0)
        pages = [
            ("Dashboard", "dashboard"),
            ("Accounts", "accounts"),
            ("Proxies", "proxies"),
            ("Inbox", "inbox"),
            ("Parser", "parser"),
            ("Sender", "sender"),
            ("Events", "events"),
            ("Settings", "settings"),
        ]
        for label, key in pages:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.nav.addItem(item)
        s_layout.addWidget(self.nav)
        s_layout.addStretch()

        # Status bar summary
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        self.statusBar().addWidget(self.status_label)

        # Pages
        self.stack = QStackedWidget()
        self.pages: dict[str, QWidget] = {}
        for label, key in pages:
            page = self._create_page(key)
            self.stack.addWidget(page)
            self.pages[key] = page

        layout.addWidget(sidebar)
        layout.addWidget(self.stack)

        self.nav.currentRowChanged.connect(self._on_nav_changed)

    def _create_page(self, key: str) -> QWidget:
        if key == "dashboard":
            return DashboardPage(self.db, self.cm, self.accounts, self.proxies, self.inbox)
        if key == "accounts":
            return AccountsPage(self.db, self.cm, self.accounts)
        if key == "proxies":
            return ProxiesPage(self.db, self.cm, self.proxies)
        if key == "inbox":
            return InboxPage(self.db, self.cm, self.inbox, self.accounts)
        if key == "parser":
            return ParserPage(self.db, self.cm, self.parser, self.accounts)
        if key == "sender":
            return SenderPage(self.db, self.cm, self.sender, self.accounts)
        if key == "events":
            return LogPage(self.db)
        if key == "settings":
            return SettingsPage(self.db)
        return QWidget()

    def _on_nav_changed(self, row: int) -> None:
        item = self.nav.item(row)
        if not item:
            return
        key = item.data(Qt.ItemDataRole.UserRole)
        page = self.pages.get(key)
        if page and hasattr(page, "on_show"):
            page.on_show()
        self.stack.setCurrentWidget(page)

    def _wire_signals(self) -> None:
        cm = self.cm
        cm.connected.connect(self._on_connected)
        cm.disconnected.connect(self._on_disconnected)
        cm.error.connect(self._on_error)
        cm.new_message.connect(self._on_new_message)
        cm.dialogs_loaded.connect(self._on_dialogs_loaded)
        cm.participants_loaded.connect(self._on_participants_loaded)
        cm.operation_log.connect(self._on_operation_log)

    # ---------------- signal handlers ----------------
    def _on_connected(self, account_id: int, name: str) -> None:
        self.accounts.db.set_account_status(account_id, "connected")
        self.status_label.showMessage(f"Connected: {name}", 3000)
        self._refresh_dashboard()

    def _on_disconnected(self, account_id: int) -> None:
        self.accounts.db.set_account_status(account_id, "disconnected")
        self._refresh_dashboard()

    def _on_error(self, account_id: int, message: str) -> None:
        self.status_label.showMessage(f"Error: {message}", 5000)
        self.accounts.db.add_event("error", message=message, account_id=account_id)
        self._refresh_dashboard()

    def _on_new_message(self, account_id: int, message: dict) -> None:
        inbox_page = self.pages.get("inbox")
        if inbox_page and hasattr(inbox_page, "handle_message"):
            inbox_page.handle_message(account_id, message)
        self._refresh_dashboard()

    def _on_dialogs_loaded(self, account_id: int, dialogs: list) -> None:
        inbox_page = self.pages.get("inbox")
        if inbox_page and hasattr(inbox_page, "handle_dialogs"):
            inbox_page.handle_dialogs(account_id, dialogs)

    def _on_participants_loaded(self, account_id: int, participants: list) -> None:
        parser_page = self.pages.get("parser")
        if parser_page and hasattr(parser_page, "handle_participants"):
            parser_page.handle_participants(participants)

    def _on_operation_log(self, text: str) -> None:
        self.db.add_event("system", message=text)

    def _refresh_dashboard(self) -> None:
        page = self.pages.get("dashboard")
        if page and hasattr(page, "refresh"):
            page.refresh()

    def closeEvent(self, event) -> None:
        self.sender.stop()
        self.parser.stop()
        self.cm.stop()
        self.db.close()
        super().closeEvent(event)
