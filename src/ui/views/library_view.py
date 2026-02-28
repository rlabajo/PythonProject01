"""
src/ui/views/library_view.py
-----------------------------
Scrollable grid view that shows all books in the library.

Views provided:
  - LibraryView   — Responsive grid of BookCardWidgets with empty state.
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore    import Qt, Signal, QSize
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QScrollArea, QLabel, QSizePolicy,
                                QFrame, QGridLayout, QSpacerItem)
from PySide6.QtGui     import QFont

from src.ui.themes.theme         import Palette
from src.ui.widgets.book_card    import BookCardWidget
from src.ui.widgets.labels       import HeadingLabel, SubtitleLabel
from src.models.book             import Book


# ── Empty-state placeholder ───────────────────────────────────────────────────

class _EmptyState(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 80, 40, 40)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        icon = QLabel("📚")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFont(QFont("Segoe UI Emoji", 48))
        icon.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(icon)

        heading = HeadingLabel("Your library is empty", level=3)
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(heading)

        sub = SubtitleLabel('Press \u201cAdd Book\u201d to start building your collection.')
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        lay.addWidget(sub)


# ── Library grid ──────────────────────────────────────────────────────────────

_CARD_W    = 160   # must match BookCardWidget._CARD_W
_COL_GAP   = 20
_ROW_GAP   = 20
_MARGIN    = 24


class LibraryView(QWidget):
    """
    Scrollable responsive grid of book cards.

    Signals
    -------
    bookClicked(book_id: str)   Forwarded from each BookCardWidget.
    """

    bookClicked: Signal = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        self._books: List[Book] = []
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {Palette.BASE};
                width: 6px; margin: 0; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {Palette.BORDER};
                border-radius: 3px; min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Palette.PRIMARY};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0; background: none;
            }}
        """)

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent; border: none;")
        self._scroll.setWidget(self._content)

        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(_MARGIN, _MARGIN, _MARGIN, _MARGIN)
        self._content_layout.setSpacing(0)

        # Empty state (shown when no books)
        self._empty_state = _EmptyState()
        self._content_layout.addWidget(self._empty_state)

        # Grid container (hidden when empty)
        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background: transparent; border: none;")
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setHorizontalSpacing(_COL_GAP)
        self._grid_layout.setVerticalSpacing(_ROW_GAP)
        self._content_layout.addWidget(self._grid_container)
        self._grid_container.hide()

        self._content_layout.addStretch()
        outer.addWidget(self._scroll, 1)

    # ── Public API ────────────────────────────────────────────────────────

    def set_books(self, books: List[Book]) -> None:
        """Replace the displayed books with the given list."""
        self._books = books
        self._rebuild_grid()

    def _rebuild_grid(self) -> None:
        # Clear existing cards
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._books:
            self._empty_state.show()
            self._grid_container.hide()
            return

        self._empty_state.hide()
        self._grid_container.show()

        # Calculate columns based on available width
        available = max(self._scroll.viewport().width() - 2 * _MARGIN, _CARD_W)
        cols = max(1, (available + _COL_GAP) // (_CARD_W + _COL_GAP))

        for idx, book in enumerate(self._books):
            row, col = divmod(idx, cols)
            card = BookCardWidget(book)
            card.clicked.connect(self.bookClicked)
            self._grid_layout.addWidget(card, row, col,
                                        Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Fill remaining columns in last row so cards left-align
        last_row_count = len(self._books) % cols
        if last_row_count:
            fill_cols = cols - last_row_count
            last_row = (len(self._books) - 1) // cols
            for c in range(last_row_count, cols):
                spacer = QWidget()
                spacer.setFixedWidth(_CARD_W)
                spacer.setStyleSheet("background: transparent; border: none;")
                self._grid_layout.addWidget(spacer, last_row, c)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._books:
            self._rebuild_grid()
