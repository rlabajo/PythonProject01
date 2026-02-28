"""
main.py
-------
Entry point for the Book Library application.

Usage:
    python main.py
"""

import sys
import os

from PySide6.QtWidgets import QApplication

from src.ui.themes.theme    import apply_dark_theme
from src.ui.main_window     import MainWindow
from src.models.book_store  import BookStore


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Book Library")
    apply_dark_theme(app)

    # Persist books in the user's home directory under .booklibrary/books.json
    data_dir = os.path.join(os.path.expanduser("~"), ".booklibrary")
    os.makedirs(data_dir, exist_ok=True)
    books_path = os.path.join(data_dir, "books.json")

    store = BookStore(path=books_path)
    window = MainWindow(store=store)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
