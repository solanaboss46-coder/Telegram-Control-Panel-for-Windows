"""Modern dark QSS theme for the application."""
DARK_STYLESHEET = """
QMainWindow {
    background: #0f1115;
    color: #e8eaf2;
}
QWidget {
    background: #0f1115;
    color: #e8eaf2;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}
QLabel {
    color: #e8eaf2;
    background: transparent;
}
#sidebar {
    background: #0a0b10;
    border-right: 1px solid #1f2229;
}
#sidebarTitle {
    color: #7c9aff;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding-bottom: 12px;
    border-bottom: 1px solid #1f2229;
    margin-bottom: 12px;
}
QListWidget#nav {
    background: transparent;
    border: none;
    outline: none;
    padding: 4px;
}
QListWidget::item {
    background: transparent;
    color: #a9b1c6;
    padding: 10px 12px;
    border-radius: 8px;
    margin: 2px 4px;
    font-size: 13px;
}
QListWidget::item:selected {
    background: #1c212c;
    color: #7c9aff;
    border-left: 3px solid #7c9aff;
}
QListWidget::item:hover:!selected {
    background: #14171e;
    color: #c7ccd9;
}
#statusLabel {
    color: #8a93a8;
    font-size: 11px;
    padding: 4px 10px;
    background: #0a0b10;
    border-radius: 4px;
}
QStatusBar {
    background: #0a0b10;
    color: #8a93a8;
    border-top: 1px solid #1f2229;
}

QFrame#statCard {
    background: #14171e;
    border: 1px solid #232833;
    border-radius: 12px;
}
#cardTitle {
    color: #8a93a8;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
#cardValue {
    color: #e8eaf2;
    font-size: 24px;
    font-weight: 800;
    margin-top: 4px;
}

QTableWidget {
    background: #14171e;
    border: 1px solid #232833;
    border-radius: 10px;
    gridline-color: #1f2229;
    selection-background-color: #1c212c;
    selection-color: #7c9aff;
    outline: none;
}
QTableWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #1f2229;
}
QTableWidget::item:selected {
    background: #1c212c;
    color: #7c9aff;
}
QHeaderView::section {
    background: #0a0b10;
    color: #8a93a8;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #232833;
    border-right: 1px solid #232833;
}
QHeaderView::section:last {
    border-right: none;
}

QPushButton {
    background: #1c212c;
    color: #e8eaf2;
    border: 1px solid #2a303c;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton:hover {
    background: #232833;
    border-color: #3a4250;
}
QPushButton:pressed {
    background: #14171e;
}
QPushButton:checked {
    background: #1c212c;
    border-color: #7c9aff;
    color: #7c9aff;
}
QPushButton#primary {
    background: #7c9aff;
    color: #0b0d12;
    border: none;
}
QPushButton#primary:hover {
    background: #92abff;
}
QPushButton#primary:pressed {
    background: #6a86e8;
}
QPushButton#danger {
    background: #4a1f1f;
    color: #ffadad;
    border: 1px solid #6b2a2a;
}
QPushButton#danger:hover {
    background: #5b2525;
}

QLineEdit, QTextEdit, QListWidget {
    background: #0a0b10;
    border: 1px solid #232833;
    border-radius: 8px;
    padding: 8px 12px;
    color: #e8eaf2;
    selection-background-color: #7c9aff;
    selection-color: #0b0d12;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #7c9aff;
}
QTextEdit {
    padding: 10px 12px;
}

QSplitter::handle {
    background: #232833;
    width: 4px;
}

QDialog {
    background: #0f1115;
}
QDialog QLabel {
    color: #e8eaf2;
}
QDialogButtonBox QPushButton {
    min-width: 90px;
}

QScrollBar:vertical {
    background: #0a0b10;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #3a4250;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #505a68;
}
QScrollBar:horizontal {
    background: #0a0b10;
    height: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #3a4250;
    border-radius: 5px;
    min-width: 24px;
}
"""
