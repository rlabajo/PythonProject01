"""
src/ui/widgets/labels.py
------------------------
Custom QLabel widgets built on top of the dark theme defined in
src.ui.themes.theme.

Widgets provided:
  - BaseLabel          — Foundation; all others inherit from this.
  - HeadingLabel       — Section / page headings (H1 → H4 scale).
  - SubtitleLabel      — Muted secondary line beneath a heading.
  - CaptionLabel       — Small helper / annotation text.
  - BadgeLabel         — Pill-shaped inline badge (status colours).
  - TagLabel           — Outlined chip / tag (e.g. category pills).
  - IconLabel          — Leading Unicode glyph + text on one line.
  - StatusLabel        — Inline status line: success / warning / error / info.
  - LinkLabel          — Clickable hyperlink-style label.
  - ElidedLabel        — Single-line label that elides with "…" on overflow.
  - SectionDividerLabel— Full-width rule with centred or left-aligned title.
"""

from __future__ import annotations

from PySide6.QtCore    import Qt, Signal, QRect, QSize
from PySide6.QtGui     import (QFont, QColor, QPainter, QPen,
                                QFontMetrics, QCursor, QMouseEvent)
from PySide6.QtWidgets import QLabel, QWidget, QSizePolicy

from src.ui.themes.theme import Palette


# ─────────────────────────────────────────────────────────────────────────────
# Typography scale  (Roboto)
# ─────────────────────────────────────────────────────────────────────────────
class _Scale:
    H1       = (22, True )   # (pt, bold)
    H2       = (18, True )
    H3       = (14, True )
    H4       = (12, True )
    SUBTITLE = (10, False)
    BODY     = (10, False)
    CAPTION  =  (8, False)


def _font(size_pt: int, bold: bool = False, italic: bool = False) -> QFont:
    f = QFont("Roboto", size_pt)
    f.setBold(bold)
    f.setItalic(italic)
    f.setStyleHint(QFont.StyleHint.SansSerif)
    return f


# ─────────────────────────────────────────────────────────────────────────────
# 1. BaseLabel
# ─────────────────────────────────────────────────────────────────────────────

class BaseLabel(QLabel):
    """
    Transparent, theme-aware QLabel foundation.
    Sets Roboto body font and primary text colour.
    All other labels inherit from this.
    """

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setFont(_font(*_Scale.BODY))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(
            f"color: {Palette.TEXT_PRIMARY};"
            "background: transparent;"
            "border: none;"
        )
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)


# ─────────────────────────────────────────────────────────────────────────────
# 2. HeadingLabel
# ─────────────────────────────────────────────────────────────────────────────

class HeadingLabel(BaseLabel):
    """
    Page / section heading on a 4-level scale.

    Usage::

        HeadingLabel("Dashboard",  level=1)   # largest
        HeadingLabel("Overview",   level=2)
        HeadingLabel("Details",    level=3)
        HeadingLabel("Sub-section",level=4)   # smallest heading
    """

    _SCALES = {
        1: _Scale.H1,
        2: _Scale.H2,
        3: _Scale.H3,
        4: _Scale.H4,
    }
    # Letter-spacing (em approximation via stylesheet) per level
    _TRACKING = {1: "−0.5px", 2: "0px", 3: "0px", 4: "0.2px"}

    def __init__(
        self,
        text: str = "",
        level: int = 1,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        level = max(1, min(4, level))
        size, bold = self._SCALES[level]
        self.setFont(_font(size, bold=bold))
        self.setStyleSheet(
            f"color: {Palette.TEXT_PRIMARY};"
            "background: transparent;"
            "border: none;"
        )
        self.setWordWrap(True)


# ────────────────────────────────────────────────────────��────────────────────
# 3. SubtitleLabel
# ─────────────────────────────────────────────────────────────────────────────

class SubtitleLabel(BaseLabel):
    """
    Muted secondary line, typically placed directly below a HeadingLabel.

    Usage::

        SubtitleLabel("Last updated 5 minutes ago")
    """

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setFont(_font(*_Scale.SUBTITLE))
        self.setStyleSheet(
            f"color: {Palette.TEXT_SECONDARY};"
            "background: transparent;"
            "border: none;"
        )
        self.setWordWrap(True)


# ─────────────────────────────────────────────────────────────────────────────
# 4. CaptionLabel
# ─────────────────────────────────────────────────────────────────────────────

class CaptionLabel(BaseLabel):
    """
    Very small helper text — field annotations, footnotes, timestamps.

    Usage::

        CaptionLabel("* Required field")
    """

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setFont(_font(*_Scale.CAPTION))
        self.setStyleSheet(
            f"color: {Palette.TEXT_SECONDARY};"
            "background: transparent;"
            "border: none;"
        )
        self.setWordWrap(True)


# ─────────────────────────────────────────────────────────────────────────────
# 5. BadgeLabel
# ─────────────────────────────────────────────────────────────────────────────

class BadgeLabel(QLabel):
    """
    Solid pill-shaped badge for statuses, counts, or short keywords.

    Colour variants map to semantic meaning:

    +-----------+----------------------------------+
    | variant   | use-case                         |
    +===========+==================================+
    | "primary" | highlighted / active (blue)      |
    | "success" | completed / online / approved    |
    | "warning" | pending / degraded               |
    | "error"   | failed / offline / critical      |
    | "muted"   | neutral / archived / disabled    |
    +-----------+----------------------------------+

    Usage::

        BadgeLabel("Active",  variant="success")
        BadgeLabel("7",       variant="error")
        BadgeLabel("Beta",    variant="primary")
    """

    _BG: dict[str, str] = {
        "primary": Palette.PRIMARY,
        "success": Palette.SUCCESS,
        "warning": Palette.WARNING,
        "error":   Palette.ERROR,
        "muted":   Palette.ELEVATED,
    }
    _FG: dict[str, str] = {
        "primary": Palette.TEXT_ON_PRIMARY,
        "success": "#0A0A0A",
        "warning": "#0A0A0A",
        "error":   "#FFFFFF",
        "muted":   Palette.TEXT_SECONDARY,
    }

    def __init__(
        self,
        text: str = "",
        variant: str = "primary",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._variant = variant if variant in self._BG else "primary"
        self.setFont(_font(8, bold=True))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._refresh_style()

    # ------------------------------------------------------------------
    def set_variant(self, variant: str) -> None:
        """Change colour variant at runtime."""
        self._variant = variant if variant in self._BG else "primary"
        self._refresh_style()

    def _refresh_style(self) -> None:
        bg = self._BG[self._variant]
        fg = self._FG[self._variant]
        self.setStyleSheet(
            f"color: {fg};"
            f"background-color: {bg};"
            "border: none;"
            "border-radius: 9px;"
            "padding: 2px 8px;"
            "font-family: 'Roboto', 'Segoe UI', Arial, sans-serif;"
            "font-size: 8pt;"
            "font-weight: 700;"
            "letter-spacing: 0.3px;"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 6. TagLabel
# ─────────────────────────────────────────────────────────────────────────────

class TagLabel(QLabel):
    """
    Outlined chip / tag — same pill shape as BadgeLabel but uses a border
    instead of a filled background.  Great for categories, filters, keywords.

    Usage::

        TagLabel("Python")
        TagLabel("In Review", color=Palette.WARNING)
    """

    def __init__(
        self,
        text: str = "",
        color: str = Palette.PRIMARY,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._color = color
        self.setFont(_font(8))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._refresh_style()

    # ------------------------------------------------------------------
    def set_color(self, color: str) -> None:
        self._color = color
        self._refresh_style()

    def _refresh_style(self) -> None:
        self.setStyleSheet(
            f"color: {self._color};"
            "background-color: transparent;"
            f"border: 1.5px solid {self._color};"
            "border-radius: 9px;"
            "padding: 2px 8px;"
            "font-family: 'Roboto', 'Segoe UI', Arial, sans-serif;"
            "font-size: 8pt;"
            "letter-spacing: 0.2px;"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 7. IconLabel
# ─────────────────────────────────────────────────────────────────────────────

class IconLabel(BaseLabel):
    """
    A single-line label with a leading icon glyph (Unicode / emoji).
    The icon and text are vertically aligned and share a consistent gap.

    Usage::

        IconLabel("📁", "Documents")
        IconLabel("✔", "Saved successfully", icon_color=Palette.SUCCESS)
    """

    _GAP = 6   # px between icon and text

    def __init__(
        self,
        icon: str = "",
        text: str = "",
        icon_color: str = Palette.PRIMARY,
        parent: QWidget | None = None,
    ) -> None:
        # Store separately; render via paintEvent for precise alignment
        super().__init__("", parent)
        self._icon       = icon
        self._body_text  = text
        self._icon_color = icon_color
        self.setFont(_font(*_Scale.BODY))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(24)

    # ------------------------------------------------------------------
    def set_icon(self, icon: str) -> None:
        self._icon = icon
        self.update()

    def set_text(self, text: str) -> None:  # type: ignore[override]
        self._body_text = text
        self.update()

    def set_icon_color(self, color: str) -> None:
        self._icon_color = color
        self.update()

    # ------------------------------------------------------------------
    def sizeHint(self) -> QSize:
        fm   = QFontMetrics(self.font())
        icon_w = fm.horizontalAdvance(self._icon) if self._icon else 0
        text_w = fm.horizontalAdvance(self._body_text)
        gap    = self._GAP if self._icon and self._body_text else 0
        return QSize(icon_w + gap + text_w + 4, max(fm.height() + 4, 24))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        fm = QFontMetrics(self.font())
        y  = (self.height() - fm.height()) // 2 + fm.ascent()
        x  = 0

        # Icon
        if self._icon:
            painter.setPen(QColor(self._icon_color))
            painter.setFont(self.font())
            painter.drawText(x, y, self._icon)
            x += fm.horizontalAdvance(self._icon) + self._GAP

        # Body text
        if self._body_text:
            painter.setPen(QColor(Palette.TEXT_PRIMARY))
            painter.drawText(x, y, self._body_text)

        painter.end()


# ─────────────────────────────────────────────────────────────────────────────
# 8. StatusLabel
# ─────────────────────────────────────────────────────────────────────────────

class StatusLabel(BaseLabel):
    """
    Inline status message with a coloured leading dot indicator.

    Variants: "success", "warning", "error", "info", "muted"

    Usage::

        lbl = StatusLabel("All systems operational", variant="success")
        lbl.set_status("Degraded performance", variant="warning")
    """

    _COLORS: dict[str, str] = {
        "success": Palette.SUCCESS,
        "warning": Palette.WARNING,
        "error":   Palette.ERROR,
        "info":    Palette.PRIMARY,
        "muted":   Palette.TEXT_SECONDARY,
    }
    _DOT_SIZE  = 8    # px diameter of the indicator dot
    _DOT_GAP   = 8    # px between dot and text

    def __init__(
        self,
        text: str = "",
        variant: str = "info",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("", parent)   # text drawn manually
        self._body_text = text
        self._variant   = variant if variant in self._COLORS else "info"
        self.setFont(_font(*_Scale.BODY))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(22)

    # ------------------------------------------------------------------
    def set_status(self, text: str, variant: str | None = None) -> None:
        """Update text and optionally change the variant."""
        self._body_text = text
        if variant is not None:
            self._variant = variant if variant in self._COLORS else self._variant
        self.update()

    # ------------------------------------------------------------------
    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        w  = self._DOT_SIZE + self._DOT_GAP + fm.horizontalAdvance(self._body_text) + 4
        h  = max(fm.height() + 4, 22)
        return QSize(w, h)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        color = QColor(self._COLORS[self._variant])
        fm    = QFontMetrics(self.font())
        cy    = self.height() // 2

        # Dot
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(
            0, cy - self._DOT_SIZE // 2,
            self._DOT_SIZE, self._DOT_SIZE,
        )

        # Text
        x = self._DOT_SIZE + self._DOT_GAP
        y = (self.height() - fm.height()) // 2 + fm.ascent()
        painter.setPen(color)
        painter.setFont(self.font())
        painter.drawText(x, y, self._body_text)

        painter.end()


# ─────────────────────────────────────────────────────────────────────────────
# 9. LinkLabel
# ─────────────────────────────────────────────────────────────────────────────

class LinkLabel(BaseLabel):
    """
    A clickable label styled as a hyperlink.
    Emits `clicked` when pressed. Does NOT open a browser unless you connect
    the signal to `QDesktopServices.openUrl`.

    Usage::

        lnk = LinkLabel("Forgot password?")
        lnk.clicked.connect(lambda: handle_forgot_password())

        # Open a URL:
        lnk.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://example.com"))
        )
    """

    clicked: Signal = Signal()

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._hovered = False
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._refresh_style()

    # ------------------------------------------------------------------
    def _refresh_style(self) -> None:
        color = Palette.PRIMARY_HOVER if self._hovered else Palette.PRIMARY
        decoration = "underline" if self._hovered else "none"
        self.setStyleSheet(
            f"color: {color};"
            "background: transparent;"
            "border: none;"
            f"text-decoration: {decoration};"
            "font-family: 'Roboto', 'Segoe UI', Arial, sans-serif;"
            "font-size: 10pt;"
        )

    # ------------------------------------------------------------------
    def enterEvent(self, event) -> None:  # noqa: N802
        self._hovered = True
        self._refresh_style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hovered = False
        self._refresh_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
# 10. ElidedLabel
# ─────────────────────────────────────────────────────────────────────────────

class ElidedLabel(BaseLabel):
    """
    Single-line label that automatically elides overflowing text with "…".

    Elide mode options (Qt.TextElideMode):
      - ElideRight  (default) — "Long text that over…"
      - ElideLeft             — "…g text that overflows"
      - ElideMiddle           — "Long text…overflows"

    The full text is always available in the tooltip.

    Usage::

        lbl = ElidedLabel("Very long path/to/some/file/that/may/not/fit.py")
        lbl.setFixedWidth(200)
    """

    def __init__(
        self,
        text: str = "",
        elide_mode: Qt.TextElideMode = Qt.TextElideMode.ElideRight,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._full_text  = text
        self._elide_mode = elide_mode
        self.setToolTip(text)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    # ------------------------------------------------------------------
    def setText(self, text: str) -> None:  # type: ignore[override]
        self._full_text = text
        self.setToolTip(text)
        self.update()

    def text(self) -> str:  # type: ignore[override]
        return self._full_text

    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setFont(self.font())
        painter.setPen(QColor(Palette.TEXT_PRIMARY))

        fm      = QFontMetrics(self.font())
        elided  = fm.elidedText(self._full_text, self._elide_mode, self.width())
        y       = (self.height() - fm.height()) // 2 + fm.ascent()
        painter.drawText(0, y, elided)
        painter.end()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        return QSize(super().sizeHint().width(), fm.height() + 4)


# ─────────────────────────────────────────────────────────────────────────────
# 11. SectionDividerLabel
# ─────────────────────────────────────────────────────────────────────────────

class SectionDividerLabel(QWidget):
    """
    A full-width horizontal rule with an inline section title.
    Visually separates content regions without consuming too much vertical space.

    Alignment options: "left" (default) or "center"

    Usage::

        SectionDividerLabel("Account Settings")
        SectionDividerLabel("Advanced", align="center")
        SectionDividerLabel()   # rule only, no text
    """

    _RULE_COLOR    = Palette.BORDER
    _RULE_HEIGHT   = 1    # px
    _TEXT_GAP      = 10   # px between text and rule segments
    _VERTICAL_PAD  = 10   # px above and below the widget

    def __init__(
        self,
        text: str = "",
        align: str = "left",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._text  = text
        self._align = align if align in ("left", "center") else "left"
        self.setFont(_font(8, bold=False))
        self.setMinimumHeight(self._VERTICAL_PAD * 2 + 14)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w   = self.width()
        cy  = self.height() // 2   # vertical centre line

        pen = QPen(QColor(self._RULE_COLOR))
        pen.setWidth(self._RULE_HEIGHT)
        painter.setPen(pen)

        if not self._text:
            # Plain rule spanning full width
            painter.drawLine(0, cy, w, cy)
        else:
            fm        = QFontMetrics(self.font())
            text_w    = fm.horizontalAdvance(self._text)
            text_h    = fm.height()
            text_y    = cy - text_h // 2

            if self._align == "center":
                text_x    = (w - text_w) // 2
                left_end  = text_x - self._TEXT_GAP
                right_start = text_x + text_w + self._TEXT_GAP

                # Left segment
                if left_end > 0:
                    painter.drawLine(0, cy, left_end, cy)
                # Right segment
                if right_start < w:
                    painter.drawLine(right_start, cy, w, cy)

            else:   # left-aligned
                right_start = text_w + self._TEXT_GAP * 2
                if right_start < w:
                    painter.drawLine(right_start, cy, w, cy)
                text_x = 0

            # Text
            painter.setPen(QColor(Palette.TEXT_SECONDARY))
            painter.setFont(self.font())
            painter.drawText(
                text_x,
                text_y + fm.ascent(),
                self._text,
            )

        painter.end()