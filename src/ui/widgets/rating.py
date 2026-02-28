"""
src/ui/widgets/rating.py
-------------------------
Interactive star rating widget.

Widgets provided:
  - RatingWidget   — Clickable ★ rating (1–5), hover preview, half-star support.
"""

from __future__ import annotations

from PySide6.QtCore    import Qt, Signal, QSize, QRect
from PySide6.QtGui     import (QColor, QPainter, QFont,
                                QMouseEvent, QEnterEvent)
from PySide6.QtWidgets import QWidget, QSizePolicy

from src.ui.themes.theme import Palette


class RatingWidget(QWidget):
    """
    Interactive star rating widget.

    Parameters
    ----------
    max_stars  : int   Total number of stars. Default 5.
    half_stars : bool  Allow half-star increments. Default True.
    star_size  : int   Size of each star glyph in pt. Default 20.
    read_only  : bool  Disable interaction. Default False.

    Signals
    -------
    ratingChanged(float)   Emitted on click. Value is 0.0–max_stars.

    Usage::

        r = RatingWidget()
        r.set_rating(3.5)
        r.ratingChanged.connect(lambda v: print(f"Rated: {v}"))
    """

    ratingChanged: Signal = Signal(float)

    _FILLED  = "★"
    _HALF    = "⯨"
    _EMPTY   = "☆"
    _GAP     = 4

    def __init__(
        self,
        max_stars:  int  = 5,
        half_stars: bool = True,
        star_size:  int  = 20,
        read_only:  bool = False,
        parent:     QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._max       = max_stars
        self._half      = half_stars
        self._size      = star_size
        self._read_only = read_only
        self._rating    = 0.0
        self._hover     = -1.0     # hovered rating (–1 = none)

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        if not read_only:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ── Size ──────────────────────────────────────────────────────────

    def sizeHint(self) -> QSize:
        w = self._max * (self._size + self._GAP) - self._GAP
        return QSize(w, self._size + 4)

    # ── Public API ────────────────────────────────────���───────────────

    def rating(self) -> float:
        return self._rating

    def set_rating(self, value: float) -> None:
        self._rating = max(0.0, min(float(self._max), value))
        self.update()

    def set_read_only(self, ro: bool) -> None:
        self._read_only = ro
        self.setCursor(
            Qt.CursorShape.ArrowCursor if ro
            else Qt.CursorShape.PointingHandCursor
        )
        self.update()

    # ── Paint ─────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        display = self._hover if self._hover >= 0 else self._rating
        font    = QFont("Roboto", self._size)
        p.setFont(font)

        cell_w = self._size + self._GAP

        for i in range(self._max):
            x = i * cell_w
            r = QRect(x, 0, self._size, self._size + 4)

            filled = display - i
            if filled >= 1.0:
                glyph = self._FILLED
                color = QColor(Palette.WARNING)     # gold
            elif filled >= 0.5 and self._half:
                glyph = self._HALF
                color = QColor(Palette.WARNING)
            else:
                glyph = self._EMPTY
                color = QColor(Palette.TEXT_SECONDARY)

            p.setPen(color)
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, glyph)

        p.end()

    # ── Mouse ─────────────────────────────────────────────────────────

    def _rating_from_x(self, x: int) -> float:
        cell_w = self._size + self._GAP
        star   = x / cell_w
        if self._half:
            return round(star * 2) / 2
        return float(round(star))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._read_only:
            return
        self._hover = max(0.5 if self._half else 1.0,
                          self._rating_from_x(int(event.position().x())))
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._read_only or event.button() != Qt.MouseButton.LeftButton:
            return
        new_rating = self._rating_from_x(int(event.position().x()))
        # Clicking the same value toggles to 0
        if new_rating == self._rating:
            new_rating = 0.0
        self._rating = new_rating
        self._hover  = -1.0
        self.update()
        self.ratingChanged.emit(self._rating)

    def leaveEvent(self, _event) -> None:  # noqa: N802
        self._hover = -1.0
        self.update()