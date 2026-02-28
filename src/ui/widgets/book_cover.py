"""
src/ui/widgets/book_cover.py
-----------------------------
Standalone book cover display widget.

Renders a cover image from a local path or URL.
When no image is available it paints a styled placeholder showing
the book's title initials and a genre-derived accent colour.

Widgets provided:
  - BookCoverWidget
"""

from __future__ import annotations

from PySide6.QtCore    import Qt, QSize, QRect, Signal, QThread, QObject
from PySide6.QtGui     import (QColor, QPainter, QPainterPath,
                                QPixmap, QFont, QFontMetrics,
                                QLinearGradient)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (QWidget, QSizePolicy, QVBoxLayout,
                                QLabel, QStackedWidget)
from PySide6.QtCore    import QUrl

from src.ui.themes.theme import Palette


# ── Genre → placeholder accent colour ─────────────────────────────────────────
_GENRE_COLORS: dict[str, str] = {
    "fiction":       "#1565C0",
    "non-fiction":   "#2E7D32",
    "science":       "#00838F",
    "history":       "#6D4C41",
    "biography":     "#4527A0",
    "fantasy":       "#6A1B9A",
    "mystery":       "#283593",
    "romance":       "#AD1457",
    "thriller":      "#BF360C",
    "horror":        "#212121",
    "children":      "#F57F17",
    "graphic novel": "#0277BD",
    "poetry":        "#558B2F",
    "other":         Palette.PRIMARY,
}

_DEFAULT_ACCENT = Palette.PRIMARY


def _genre_color(genre: str) -> str:
    return _GENRE_COLORS.get(genre.lower().strip(), _DEFAULT_ACCENT)


def _initials(title: str) -> str:
    """Up to two initials from the first two words of the title."""
    words = [w for w in title.split() if w]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][0].upper()
    return (words[0][0] + words[1][0]).upper()


# ─────────────────────────────────────────────────────────────────────────────
# BookCoverWidget
# ─────────────────────────────────────────────────────────────────────────────

class BookCoverWidget(QWidget):
    """
    Displays a book cover image with a rounded-rectangle clip.

    States
    ------
    - **Placeholder** (default): painted gradient + initials.
    - **Loaded**:    a QPixmap scaled to fit, aspect-ratio preserved.
    - **Loading**:   faint pulsing placeholder while a URL is fetched.

    Parameters
    ----------
    width : int     Widget (and image) display width.  Default 160.
    height : int    Widget (and image) display height. Default 220.
    radius : int    Corner radius. Default 10.

    Signals
    -------
    coverLoaded()   Emitted when a remote image finishes downloading.
    coverFailed()   Emitted when a remote image download fails.

    Usage::

        cover = BookCoverWidget()
        cover.set_placeholder("Dune", genre="Science Fiction")
        cover.set_pixmap_from_path("/path/to/cover.jpg")
        cover.set_pixmap_from_url("https://…/cover.jpg")
    """

    coverLoaded: Signal = Signal()
    coverFailed: Signal = Signal()

    def __init__(
        self,
        width:  int = 160,
        height: int = 220,
        radius: int = 10,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._w       = width
        self._h       = height
        self._radius  = radius
        self._pixmap: QPixmap | None = None
        self._title   = ""
        self._genre   = ""
        self._loading = False

        self.setFixedSize(QSize(width, height))
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        # Network manager for URL fetches (lazy init)
        self._nam: QNetworkAccessManager | None = None

    # ── Public API ────────────────────────────────────────────────────

    def set_placeholder(self, title: str = "", genre: str = "") -> None:
        """Show the painted placeholder (initials + gradient)."""
        self._title   = title
        self._genre   = genre
        self._pixmap  = None
        self._loading = False
        self.update()

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """Display a pre-loaded QPixmap."""
        self._pixmap  = pixmap
        self._loading = False
        self.update()

    def set_pixmap_from_path(self, path: str) -> None:
        """Load a cover from a local file path."""
        px = QPixmap(path)
        if px.isNull():
            self._pixmap  = None
            self._loading = False
        else:
            self._pixmap = px
        self.update()

    def set_pixmap_from_url(self, url: str) -> None:
        """
        Asynchronously download and display a cover from a URL.
        Emits coverLoaded / coverFailed when done.
        """
        self._loading = True
        self._pixmap  = None
        self.update()

        if self._nam is None:
            self._nam = QNetworkAccessManager(self)

        reply = self._nam.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda: self._on_reply(reply))

    def clear(self) -> None:
        """Reset to an empty placeholder."""
        self._pixmap  = None
        self._title   = ""
        self._genre   = ""
        self._loading = False
        self.update()

    def has_cover(self) -> bool:
        return self._pixmap is not None

    # ── Network reply ─────────────────────────────────────────────────

    def _on_reply(self, reply) -> None:
        from PySide6.QtNetwork import QNetworkReply
        self._loading = False
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            px   = QPixmap()
            if px.loadFromData(data):
                self._pixmap = px
                self.coverLoaded.emit()
            else:
                self.coverFailed.emit()
        else:
            self.coverFailed.emit()
        reply.deleteLater()
        self.update()

    # ── Paint ─────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        clip = QPainterPath()
        clip.addRoundedRect(0, 0, self._w, self._h,
                            self._radius, self._radius)
        p.setClipPath(clip)

        if self._pixmap and not self._pixmap.isNull():
            self._draw_image(p)
        elif self._loading:
            self._draw_loading(p)
        else:
            self._draw_placeholder(p)

        # Subtle inner border
        p.setClipping(False)
        pen_color = QColor(Palette.BORDER)
        pen_color.setAlpha(120)
        from PySide6.QtGui import QPen
        pen = QPen(pen_color)
        pen.setWidthF(1.5)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(clip)

        p.end()

    def _draw_image(self, p: QPainter) -> None:
        scaled = self._pixmap.scaled(  # type: ignore[union-attr]
            self._w, self._h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (scaled.width()  - self._w) // 2
        y = (scaled.height() - self._h) // 2
        p.drawPixmap(0, 0, scaled, x, y, self._w, self._h)

    def _draw_placeholder(self, p: QPainter) -> None:
        accent = QColor(_genre_color(self._genre))

        # Gradient background
        grad = QLinearGradient(0, 0, 0, self._h)
        dark = QColor(Palette.SURFACE)
        grad.setColorAt(0.0, dark.darker(115))
        grad.setColorAt(1.0, accent.darker(160))
        p.fillRect(0, 0, self._w, self._h, grad)

        # Accent strip at bottom
        strip_h = self._h // 5
        strip   = QLinearGradient(0, self._h - strip_h, 0, self._h)
        strip.setColorAt(0.0, QColor(0, 0, 0, 0))
        strip.setColorAt(1.0, accent)
        p.fillRect(0, self._h - strip_h, self._w, strip_h, strip)

        # Initials
        text = _initials(self._title) if self._title else "?"
        font = QFont("Roboto", 40, QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(QColor(255, 255, 255, 60))
        p.drawText(
            QRect(0, 0, self._w, self._h),
            Qt.AlignmentFlag.AlignCenter,
            text,
        )

        # Title at bottom (if short enough)
        if self._title:
            title_font = QFont("Roboto", 8, QFont.Weight.Bold)
            p.setFont(title_font)
            p.setPen(QColor(255, 255, 255, 200))
            title_rect = QRect(8, self._h - 40, self._w - 16, 36)
            p.drawText(
                title_rect,
                Qt.AlignmentFlag.AlignBottom
                | Qt.AlignmentFlag.AlignHCenter
                | Qt.TextFlag.TextWordWrap,
                self._title,
            )

    def _draw_loading(self, p: QPainter) -> None:
        p.fillRect(0, 0, self._w, self._h, QColor(Palette.SURFACE))
        font = QFont("Roboto", 9)
        p.setFont(font)
        p.setPen(QColor(Palette.TEXT_SECONDARY))
        p.drawText(
            QRect(0, 0, self._w, self._h),
            Qt.AlignmentFlag.AlignCenter,
            "Loading…",
        )