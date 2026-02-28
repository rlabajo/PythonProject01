"""
src/ui/main_window.py
---------------------
Main application window for the Book App.
"""

from __future__ import annotations

import os

from PySide6.QtCore    import Qt, QSize
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                                QHBoxLayout, QLabel, QLineEdit,
                                QSizePolicy, QStatusBar, QToolButton,
                                QFrame, QComboBox)
from PySide6.QtGui     import QFont, QAction

from src.ui.themes.theme          import Palette
from src.ui.widgets.buttons        import PrimaryButton, GhostButton, IconButton
from src.ui.widgets.labels         import HeadingLabel, SubtitleLabel
from src.ui.views.library_view     import LibraryView
from src.ui.dialogs.add_book_dialog import AddBookDialog
from src.models.book               import Book
from src.models.book_store         import BookStore


# ── Toolbar ───────────────────────────────────────────────────────────────────

class _Toolbar(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet(
            f"background-color: {Palette.ELEVATED}; border: none;"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(12)

        # App title
        title = QLabel("📚  Book Library")
        title_font = QFont("Roboto", 13)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(
            f"color: {Palette.TEXT_PRIMARY}; background: transparent; border: none;"
        )
        lay.addWidget(title)

        lay.addStretch()

        # Search bar
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search title, author or ISBN…")
        self.search_box.setFixedWidth(260)
        self.search_box.setFixedHeight(34)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background: {Palette.SURFACE};
                color: {Palette.TEXT_PRIMARY};
                border: 1.5px solid {Palette.BORDER};
                border-radius: 17px;
                padding: 0 14px;
                font-family: "Roboto", sans-serif;
                font-size: 10pt;
            }}
            QLineEdit:focus {{
                border-color: {Palette.PRIMARY};
            }}
        """)
        lay.addWidget(self.search_box)

        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "All Statuses",
            "Unread",
            "Currently Reading",
            "Finished",
            "Did Not Finish (DNF)",
            "On Hold",
            "Wishlist",
        ])
        self.status_filter.setFixedHeight(34)
        self.status_filter.setFixedWidth(180)
        self.status_filter.setStyleSheet(f"""
            QComboBox {{
                background: {Palette.SURFACE};
                color: {Palette.TEXT_PRIMARY};
                border: 1.5px solid {Palette.BORDER};
                border-radius: 6px;
                padding: 0 10px;
                font-family: "Roboto", sans-serif;
                font-size: 10pt;
            }}
            QComboBox:focus {{
                border-color: {Palette.PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background: {Palette.ELEVATED};
                color: {Palette.TEXT_PRIMARY};
                border: 1px solid {Palette.BORDER};
                selection-background-color: {Palette.PRIMARY};
            }}
        """)
        lay.addWidget(self.status_filter)

        # Add book button
        self.add_btn = PrimaryButton("+ Add Book")
        self.add_btn.setFixedHeight(34)
        lay.addWidget(self.add_btn)


# ── Stats bar ─────────────────────────────────────────────────────────────────

class _StatsBar(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setStyleSheet(
            f"background-color: {Palette.BASE}; border: none;"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(24)

        self._stats: list[QLabel] = []
        for _ in range(4):
            lbl = QLabel()
            lbl.setStyleSheet(
                f"color: {Palette.TEXT_SECONDARY}; "
                "font-family: 'Roboto', sans-serif; font-size: 9pt;"
                "background: transparent; border: none;"
            )
            self._stats.append(lbl)
            lay.addWidget(lbl)

        lay.addStretch()

    def update_stats(self, total: int, reading: int,
                     finished: int, unread: int) -> None:
        data = [
            (f"📚  {total}",   "Total"),
            (f"📖  {reading}", "Reading"),
            (f"✅  {finished}", "Finished"),
            (f"🔖  {unread}",  "Unread"),
        ]
        for lbl, (icon_count, label) in zip(self._stats, data):
            lbl.setText(f"{icon_count}  {label}")


# ── Divider ───────────────────────────────────────────────────────────────────

def _divider() -> QWidget:
    line = QWidget()
    line.setFixedHeight(1)
    line.setStyleSheet(
        f"background-color: {Palette.BORDER}; border: none;"
    )
    return line


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """
    Main application window for the Book App.

    Parameters
    ----------
    store : BookStore
        The shared book store.  If None, a new in-memory store is created.
    """

    def __init__(self, store: BookStore | None = None) -> None:
        super().__init__()
        self._store = store or BookStore()
        self.setWindowTitle("Book Library")
        self.setMinimumSize(QSize(900, 600))
        self.resize(QSize(1100, 720))
        self.setStyleSheet(
            f"QMainWindow {{ background-color: {Palette.BASE}; }}"
        )
        self._build_ui()
        self._connect_signals()
        self._refresh()

    # ── Build UI ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        central.setStyleSheet(
            f"background-color: {Palette.BASE}; border: none;"
        )
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._toolbar = _Toolbar()
        root.addWidget(self._toolbar)
        root.addWidget(_divider())

        self._stats_bar = _StatsBar()
        root.addWidget(self._stats_bar)
        root.addWidget(_divider())

        self._library_view = LibraryView()
        root.addWidget(self._library_view, 1)

    # ── Signals ───────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._toolbar.add_btn.clicked.connect(self._on_add_book)
        self._toolbar.search_box.textChanged.connect(self._on_filter_changed)
        self._toolbar.status_filter.currentIndexChanged.connect(
            self._on_filter_changed
        )
        self._library_view.bookClicked.connect(self._on_book_clicked)
        self._store.on_change(self._refresh)

    # ── Slots ─────────────────────────────────────────────────────────────

    def _on_add_book(self) -> None:
        dlg = AddBookDialog(self)
        if dlg.exec():
            data = dlg.collect_data()
            book = Book.from_dialog_data(data)
            self._store.add(book)

    def _on_filter_changed(self) -> None:
        self._refresh()

    def _on_book_clicked(self, book_id: str) -> None:
        # TODO: open detail/edit dialog
        pass

    # ── Refresh ───────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        query  = self._toolbar.search_box.text().strip()
        status = self._toolbar.status_filter.currentText()
        if status == "All Statuses":
            status = None  # type: ignore[assignment]

        books = self._store.filter(
            query=query or None,
            status=status,
        )
        self._library_view.set_books(books)

        all_books = self._store.all()
        self._stats_bar.update_stats(
            total   = len(all_books),
            reading = sum(1 for b in all_books
                          if b.reading_status == "Currently Reading"),
            finished= sum(1 for b in all_books
                          if b.reading_status == "Finished"),
            unread  = sum(1 for b in all_books
                          if b.reading_status == "Unread"),
        )
