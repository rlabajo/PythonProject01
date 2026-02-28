"""
Run this file directly to preview all custom line edits:
    python -m src.ui.widgets._demo
"""

import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel

from src.ui.themes.theme import apply_dark_theme
from src.ui.widgets.line_edits import (
    PrimaryLineEdit,
    SearchLineEdit,
    PasswordLineEdit,
    LabeledLineEdit,
    StatusLineEdit,
)


def main() -> None:
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    window = QWidget()
    window.setWindowTitle("Custom Line Edits — Demo")
    window.setMinimumWidth(420)

    layout = QVBoxLayout(window)
    layout.setSpacing(20)
    layout.setContentsMargins(32, 32, 32, 32)

    def section(title: str) -> QLabel:
        lbl = QLabel(title)
        lbl.setStyleSheet("color: #9E9E9E; font-size: 8.5pt; letter-spacing: 1px;")
        return lbl

    # 1. PrimaryLineEdit
    layout.addWidget(section("PRIMARY — with leading text"))
    layout.addWidget(PrimaryLineEdit(placeholder="Email address", leading_text="@"))

    # 2. SearchLineEdit
    layout.addWidget(section("SEARCH — with clear button"))
    layout.addWidget(SearchLineEdit(placeholder="Search…"))

    # 3. PasswordLineEdit
    layout.addWidget(section("PASSWORD — with show/hide toggle"))
    layout.addWidget(PasswordLineEdit(placeholder="Password"))

    # 4. LabeledLineEdit
    layout.addWidget(section("LABELED — floating label"))
    layout.addWidget(LabeledLineEdit(label="Full Name"))

    # 5. StatusLineEdit — each state
    layout.addWidget(section("STATUS — success / warning / error"))

    success_edit = StatusLineEdit(placeholder="Email")
    success_edit.set_success("Email is available!")
    layout.addWidget(success_edit)

    warning_edit = StatusLineEdit(placeholder="Username")
    warning_edit.set_warning("Username already taken, try another.")
    layout.addWidget(warning_edit)

    error_edit = StatusLineEdit(placeholder="Password")
    error_edit.set_error("Password must be at least 8 characters.")
    layout.addWidget(error_edit)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()