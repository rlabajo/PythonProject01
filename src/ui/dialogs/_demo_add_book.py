"""
Run this file directly to open the Add Book dialog immediately:
    python -m src.ui.dialogs._demo_add_book
        or
    python src/ui/dialogs/_demo_add_book.py
"""

import sys
from PySide6.QtWidgets import QApplication
from src.ui.themes.theme import apply_dark_theme
from src.ui.dialogs.add_book_dialog import AddBookDialog


def main() -> None:
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    dlg = AddBookDialog()
    dlg.setWindowFlag(dlg.windowFlags()
                      | __import__("PySide6.QtCore", fromlist=["Qt"])
                      .Qt.WindowType.Window)

    accepted = dlg.exec()

    if accepted:
        data = dlg.collect_data()
        print("\n── Collected Data ──────────────────────")
        for k, v in data.items():
            print(f"  {k:<22} {v!r}")
        print("────────────────────────────────────────\n")
    else:
        print("\nDialog cancelled.\n")

    sys.exit(0)


if __name__ == "__main__":
    main()