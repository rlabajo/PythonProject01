"""
src/ui/widgets/book_card.py
----------------------------
Card widget that displays a single book in the library grid.

Widgets provided:
  - BookCardWidget   — Clickable card showing cover, title, author, status.
"""

from __future__ import annotations

from PySide6.QtCore    import Qt, Signal, QSize
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QSizePolicy)
from PySide6.QtGui     import QFont, QColor, QPainter, QPainterPath

from src.ui.themes.theme      import Palette
from src.ui.widgets.book_cover import BookCoverWidget
from src.ui.widgets.rating    import RatingWidget
from src.models.book          import Book


# ── Status badge colours ──────────────────────────────────────────────────────
_STATUS_COLORS: dict[str, str] = {
    "Unread":                   Palette.TEXT_SECONDARY,
    "Currently Reading":        Palette.PRIMARY,
    "Finished":                 Palette.SUCCESS,
    "Did Not Finish (DNF)":     Palette.ERROR,
    "On Hold":                  Palette.WARNING,
    "Wishlist":                 "#9C27B0",
}


def _status_color(status: str) -> str:
    return _STATUS_COLORS.get(status, Palette.TEXT_SECONDARY)


class BookCardWidget(QWidget):
    """
    Compact card for the library grid.

    Signals
    -------
    clicked(book_id: str)   Emitted when the card is pressed.
    """

    clicked: Signal = Signal(str)

    _CARD_W = 160
    _COVER_H = 220

    def __init__(self, book: Book, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._book_id = book.book_id
        self._hovered = False
        self.setFixedWidth(self._CARD_W)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui(book)

    def _build_ui(self, book: Book) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 8)
        lay.setSpacing(6)

        # Cover
        self._cover = BookCoverWidget(width=self._CARD_W, height=self._COVER_H,
                                      radius=8)
        if book.cover_path:
            self._cover.set_pixmap_from_path(book.cover_path)
        else:
            self._cover.set_placeholder(book.title, book.genre)
        lay.addWidget(self._cover)

        # Title
        title_lbl = QLabel(book.title or "Untitled")
        title_lbl.setWordWrap(True)
        title_lbl.setMaximumWidth(self._CARD_W)
        title_font = QFont("Roboto", 9)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        title_lbl.setStyleSheet(
            f"color: {Palette.TEXT_PRIMARY}; background: transparent; border: none;"
        )
        lay.addWidget(title_lbl)

        # Author
        author_lbl = QLabel(book.authors or "")
        author_lbl.setMaximumWidth(self._CARD_W)
        author_font = QFont("Roboto", 8)
        author_lbl.setFont(author_font)
        author_lbl.setStyleSheet(
            f"color: {Palette.TEXT_SECONDARY}; background: transparent; border: none;"
        )
        lay.addWidget(author_lbl)

        # Status badge
        color = _status_color(book.reading_status)
        status_lbl = QLabel(book.reading_status)
        status_font = QFont("Roboto", 7)
        status_font.setBold(True)
        status_lbl.setFont(status_font)
        status_lbl.setStyleSheet(
            f"color: {color}; background: transparent; border: none;"
        )
        lay.addWidget(status_lbl)

        # Rating (read-only, compact)
        if book.rating > 0:
            self._rating = RatingWidget(max_stars=5, half_stars=True,
                                        star_size=12, read_only=True)
            self._rating.set_rating(book.rating)
            lay.addWidget(self._rating)

    # ── Events ────────────────────────────────────────────────────────────

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._book_id)
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        if self._hovered:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(
                0, 0, self.width() - 1, self.height() - 1, 8, 8
            )
            painter.fillPath(path, QColor(Palette.PRIMARY + "18"))
            painter.end()
        super().paintEvent(event)
