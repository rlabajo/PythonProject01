"""
src/ui/widgets/cards.py
-----------------------
Custom card widgets built on top of the dark theme defined in
src.ui.themes.theme.

Widgets provided:
  - BaseCard            — Foundation card; rounded surface with optional border.
  - TitledCard          — Card with a header (title + optional subtitle + icon).
  - StatCard            — Single KPI / metric display (value + label + trend).
  - ActionCard          — Card with a footer action button row.
  - SelectableCard      — Toggleable card that highlights on selection.
  - HorizontalCard      — Side-by-side icon/image column + content column.
  - StatusCard          — Card with a coloured left-edge status accent strip.
"""

from __future__ import annotations

from PySide6.QtCore    import Qt, Signal, QSize, QRect, QPoint
from PySide6.QtGui     import (QColor, QPainter, QPainterPath, QPen,
                                QFont, QFontMetrics, QMouseEvent,
                                QEnterEvent)
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QSizePolicy, QLayout,
                                QGraphicsDropShadowEffect)

from src.ui.themes.theme import Palette


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────��──────────────────────────────────────────

def _roboto(size_pt: int = 10, bold: bool = False) -> QFont:
    f = QFont("Roboto", size_pt)
    f.setBold(bold)
    f.setStyleHint(QFont.StyleHint.SansSerif)
    return f


def _glow(parent: QWidget, radius: int = 0) -> QGraphicsDropShadowEffect:
    fx = QGraphicsDropShadowEffect(parent)
    fx.setBlurRadius(radius)
    fx.setOffset(0, 2)
    fx.setColor(QColor(0, 0, 0, 120))
    return fx


def _label(
    text: str,
    size_pt: int = 10,
    bold: bool = False,
    color: str = Palette.TEXT_PRIMARY,
    wrap: bool = False,
) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(_roboto(size_pt, bold))
    lbl.setStyleSheet(
        f"color: {color}; background: transparent; border: none;"
    )
    lbl.setWordWrap(wrap)
    return lbl


# ─────────────────────────────────────────────────────────────────────────────
# 1. BaseCard
# ─────────────────────────────────────────────────────────────────────────────

class BaseCard(QWidget):
    """
    Foundation card widget.

    Renders a rounded-rectangle surface via paintEvent so the shadow effect
    composites correctly (QSS background + box-shadow do not work well with
    QGraphicsDropShadowEffect — painting manually avoids that conflict).

    Parameters
    ----------
    border : bool
        Show a 1.5 px border using Palette.BORDER. Default True.
    hover_highlight : bool
        Slightly lighten the surface on mouse hover. Default False.
    padding : int
        Inner content padding in pixels. Default 16.
    radius : int
        Corner radius in pixels. Default 10.
    parent : QWidget | None

    Content
    -------
    Add your own widgets to `.content_layout` (a QVBoxLayout) or replace
    the layout entirely on subclasses.

    Example::

        card = BaseCard()
        card.content_layout.addWidget(QLabel("Hello from a card"))
    """

    _BG_DEFAULT   = Palette.ELEVATED
    _BG_HOVER     = "#202020"
    _RADIUS       = 10
    _SHADOW_IDLE  = 18
    _SHADOW_HOVER = 28

    def __init__(
        self,
        border:          bool = True,
        hover_highlight: bool = False,
        padding:         int  = 16,
        radius:          int  = _RADIUS,
        parent:          QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._border          = border
        self._hover_highlight = hover_highlight
        self._padding         = padding
        self._radius          = radius
        self._hovered         = False

        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Drop shadow
        self._shadow = _glow(self, self._SHADOW_IDLE)
        self.setGraphicsEffect(self._shadow)

        # Content layout — subclasses and users add widgets here
        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(
            padding, padding, padding, padding
        )
        self.content_layout.setSpacing(8)

    # ── Paint ─────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QColor(self._BG_HOVER if self._hovered and self._hover_highlight
                    else self._BG_DEFAULT)

        path = QPainterPath()
        path.addRoundedRect(
            1.0, 1.0,
            self.width() - 2.0,
            self.height() - 2.0,
            self._radius, self._radius,
        )

        # Fill
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawPath(path)

        # Border
        if self._border:
            pen = QPen(QColor(Palette.BORDER))
            pen.setWidthF(1.5)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

        painter.end()

    # ── Hover ─────────────────────────────────────────────────────────

    def enterEvent(self, event: QEnterEvent) -> None:  # noqa: N802
        self._hovered = True
        self._shadow.setBlurRadius(self._SHADOW_HOVER)
        if self._hover_highlight:
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hovered = False
        self._shadow.setBlurRadius(self._SHADOW_IDLE)
        if self._hover_highlight:
            self.update()
        super().leaveEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
# 2. TitledCard
# ─────────────────────────────────────────────────────────────────────────────

class TitledCard(BaseCard):
    """
    Card with a structured header: optional icon glyph, title, and subtitle.
    A 1 px divider separates the header from the body content area.

    Add body widgets to `.body_layout`.

    Example::

        card = TitledCard(
            title    = "Recent Activity",
            subtitle = "Last 30 days",
            icon     = "📊",
        )
        card.body_layout.addWidget(my_table)
    """

    def __init__(
        self,
        title:    str  = "",
        subtitle: str  = "",
        icon:     str  = "",
        parent:   QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)

        # ── Header row ───────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(10)
        header.setContentsMargins(0, 0, 0, 0)

        if icon:
            icon_lbl = _label(icon, size_pt=14, color=Palette.PRIMARY)
            icon_lbl.setFixedWidth(24)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            header.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.setContentsMargins(0, 0, 0, 0)

        self._title_lbl = _label(title, size_pt=11, bold=True)
        title_col.addWidget(self._title_lbl)

        if subtitle:
            self._sub_lbl = _label(subtitle, size_pt=9,
                                   color=Palette.TEXT_SECONDARY)
            title_col.addWidget(self._sub_lbl)

        header.addLayout(title_col)
        header.addStretch()

        # ── Divider ───────────────────────────────────────────────────
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet(
            f"background-color: {Palette.BORDER}; border: none;"
        )

        # ── Body layout — callers add content here ────────────────────
        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(8)
        self.body_layout.setContentsMargins(0, 0, 0, 0)

        self.content_layout.addLayout(header)
        self.content_layout.addWidget(divider)
        self.content_layout.addLayout(self.body_layout)

    # ── Public API ────────────────────────────────────────────────────

    def set_title(self, text: str) -> None:
        self._title_lbl.setText(text)

    def set_subtitle(self, text: str) -> None:
        if hasattr(self, "_sub_lbl"):
            self._sub_lbl.setText(text)


# ─────────────────────────────────────────────────────────────────────────────
# 3. StatCard
# ─────────────────────────────────────────────────────────────────────────────

_TREND_UP   = "▲"
_TREND_DOWN = "▼"
_TREND_FLAT = "●"


class StatCard(BaseCard):
    """
    Single KPI / metric card.

    Displays:
      - An optional leading icon
      - A large primary value
      - A descriptive label beneath
      - An optional trend indicator (up / down / flat) with delta text

    Example::

        card = StatCard(
            label     = "Total Revenue",
            value     = "$48,295",
            icon      = "💰",
            trend     = "up",
            delta     = "+12.4% vs last month",
        )
    """

    _TREND_COLORS = {
        "up":   Palette.SUCCESS,
        "down": Palette.ERROR,
        "flat": Palette.TEXT_SECONDARY,
    }
    _TREND_GLYPHS = {
        "up":   _TREND_UP,
        "down": _TREND_DOWN,
        "flat": _TREND_FLAT,
    }

    def __init__(
        self,
        label:  str  = "",
        value:  str  = "—",
        icon:   str  = "",
        trend:  str  = "",   # "up" | "down" | "flat" | ""
        delta:  str  = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(hover_highlight=True, parent=parent)

        # ── Top row: icon + label ─────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        top_row.setContentsMargins(0, 0, 0, 0)

        if icon:
            top_row.addWidget(_label(icon, size_pt=13, color=Palette.PRIMARY))

        self._label_lbl = _label(
            label, size_pt=9, color=Palette.TEXT_SECONDARY
        )
        top_row.addWidget(self._label_lbl)
        top_row.addStretch()

        # ── Value ─────────────────────────────────────────────────────
        self._value_lbl = _label(value, size_pt=22, bold=True)

        # ── Trend row ─────────────────────────────────────────────────
        self._trend_lbl = QLabel("")
        self._trend_lbl.setFont(_roboto(8))
        self._trend_lbl.setStyleSheet(
            "background: transparent; border: none;"
        )
        self._trend_lbl.setWordWrap(False)

        self.content_layout.addLayout(top_row)
        self.content_layout.addWidget(self._value_lbl)
        if trend or delta:
            self.content_layout.addWidget(self._trend_lbl)
            self._set_trend(trend, delta)

    # ------------------------------------------------------------------
    def _set_trend(self, trend: str, delta: str) -> None:
        color = self._TREND_COLORS.get(trend, Palette.TEXT_SECONDARY)
        glyph = self._TREND_GLYPHS.get(trend, "")
        self._trend_lbl.setText(f"{glyph}  {delta}".strip())
        self._trend_lbl.setStyleSheet(
            f"color: {color}; background: transparent; border: none;"
        )

    # ── Public API ────────────────────────────────────────────────────

    def set_value(self, value: str) -> None:
        self._value_lbl.setText(value)

    def set_label(self, label: str) -> None:
        self._label_lbl.setText(label)

    def set_trend(self, trend: str, delta: str = "") -> None:
        self._set_trend(trend, delta)


# ─────────────────────────────���───────────────────────────────────────────────
# 4. ActionCard
# ─────────────────────────────────────────────────────────────────────────────

class ActionCard(BaseCard):
    """
    Card with a footer action row.

    Pass any QWidget instances (typically QPushButtons) as `actions`.
    They are laid out right-aligned in the footer, separated from the
    body by a 1 px divider.

    Add body content to `.body_layout`.

    Example::

        from PySide6.QtWidgets import QPushButton

        cancel = QPushButton("Cancel")
        confirm = QPushButton("Confirm")

        card = ActionCard(
            title   = "Delete Project",
            actions = [cancel, confirm],
        )
        card.body_layout.addWidget(
            QLabel("This action cannot be undone.")
        )
    """

    def __init__(
        self,
        title:   str          = "",
        actions: list[QWidget] | None = None,
        parent:  QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)

        # ── Title ─────────────────────────────────────────────────────
        if title:
            self.content_layout.addWidget(
                _label(title, size_pt=11, bold=True)
            )

        # ── Body ──────────────────────────────────────────────────────
        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(8)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.addLayout(self.body_layout)

        # ── Divider ───────────────────────────────────────────────────
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet(
            f"background-color: {Palette.BORDER}; border: none;"
        )
        self.content_layout.addWidget(divider)

        # ── Footer action row ─────────────────────────────────────────
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 4, 0, 0)
        footer.setSpacing(8)
        footer.addStretch()

        for widget in (actions or []):
            footer.addWidget(widget)

        self.content_layout.addLayout(footer)


# ─────────────────────────────────────────────────────────────────────────────
# 5. SelectableCard
# ─────────────────────────────────────────────────────────────────────────────

class SelectableCard(BaseCard):
    """
    A toggleable card that highlights with a blue border and tinted background
    when selected. Clicking it toggles the selected state.

    Emits `toggled(bool)` on state change.

    Add content to `.content_layout` as normal.

    Example::

        card = SelectableCard()
        card.content_layout.addWidget(QLabel("Option A"))
        card.toggled.connect(lambda on: print("Selected:", on))

        # Set programmatically:
        card.set_selected(True)
    """

    toggled: Signal = Signal(bool)

    _BG_SELECTED      = "#0D1F3C"   # dark blue tint
    _BORDER_SELECTED  = Palette.PRIMARY
    _BORDER_DEFAULT   = Palette.BORDER

    def __init__(
        self,
        selected: bool = False,
        parent:   QWidget | None = None,
    ) -> None:
        super().__init__(border=True, hover_highlight=True, parent=parent)
        self._selected = selected
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ── Paint ─────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._selected:
            bg     = QColor(self._BG_SELECTED)
            border = QColor(self._BORDER_SELECTED)
            pen_w  = 2.0
        elif self._hovered:
            bg     = QColor(self._BG_HOVER)
            border = QColor(Palette.BORDER_MUTED)
            pen_w  = 1.5
        else:
            bg     = QColor(self._BG_DEFAULT)
            border = QColor(self._BORDER_DEFAULT)
            pen_w  = 1.5

        path = QPainterPath()
        path.addRoundedRect(
            1.0, 1.0,
            self.width() - 2.0, self.height() - 2.0,
            self._radius, self._radius,
        )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawPath(path)

        pen = QPen(border)
        pen.setWidthF(pen_w)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        painter.end()

    # ── Interaction ───────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected(not self._selected)
        super().mousePressEvent(event)

    # ── Public API ────────────────────────────────────────────────────

    def set_selected(self, selected: bool) -> None:
        if selected != self._selected:
            self._selected = selected
            self.update()
            self.toggled.emit(self._selected)

    def is_selected(self) -> bool:
        return self._selected


# ─────────────────────────────────────────────────────────────────────────────
# 6. HorizontalCard
# ─────────────────────────────────────────────────────────────────────────────

class HorizontalCard(BaseCard):
    """
    Two-column card: a fixed-width left panel and an expanding right panel.

    The left panel (`left_layout`) is typically used for a large icon,
    avatar, colour swatch, or thumbnail. The right panel (`right_layout`)
    holds the main textual content.

    Parameters
    ----------
    left_width : int
        Fixed pixel width of the left panel. Default 64.
    left_bg : str
        Background colour of the left panel. Defaults to a slightly
        lighter surface so it reads as a distinct zone.

    Example::

        card = HorizontalCard(left_width=56, left_bg=Palette.PRIMARY)

        icon = QLabel("🗂")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.left_layout.addWidget(icon)

        card.right_layout.addWidget(HeadingLabel("Project Alpha", level=3))
        card.right_layout.addWidget(SubtitleLabel("12 open tasks · Updated 2h ago"))
    """

    def __init__(
        self,
        left_width: int = 64,
        left_bg:    str = Palette.SURFACE,
        parent:     QWidget | None = None,
    ) -> None:
        # Bypass BaseCard's default VBox — we build our own HBox root
        super().__init__(border=True, hover_highlight=True, parent=parent)
        self._left_bg    = left_bg
        self._left_width = left_width

        # Clear the default VBox padding; we replace it entirely
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # ── Left panel ────────────────────────────────────────────────
        self._left_panel = QWidget(self)
        self._left_panel.setFixedWidth(left_width)
        self._left_panel.setStyleSheet(
            f"background: transparent; border: none;"
        )
        self.left_layout = QVBoxLayout(self._left_panel)
        self.left_layout.setContentsMargins(8, 16, 8, 16)
        self.left_layout.setSpacing(6)
        self.left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── Right panel ───────────────────────────────────────────────
        right_panel = QWidget(self)
        right_panel.setStyleSheet("background: transparent; border: none;")
        self.right_layout = QVBoxLayout(right_panel)
        self.right_layout.setContentsMargins(14, 14, 14, 14)
        self.right_layout.setSpacing(6)
        self.right_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        # ── Root row ──────────────────────────────────────────────────
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self._left_panel)
        row.addWidget(right_panel, 1)

        self.content_layout.addLayout(row)

    # ── Paint: override to paint left-panel background separately ─────

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = self._radius
        w = self.width()
        h = self.height()
        lw = self._left_width

        # ── Full card background ──────────────────────────────────────
        card_path = QPainterPath()
        card_path.addRoundedRect(1.0, 1.0, w - 2.0, h - 2.0, r, r)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self._BG_DEFAULT))
        painter.drawPath(card_path)

        # ── Left panel tint (clipped to left portion + left corners) ──
        left_path = QPainterPath()
        # Full rounded rect for the left portion, then clip to card
        full_left = QPainterPath()
        full_left.addRoundedRect(1.0, 1.0, lw - 1.0, h - 2.0, r, r)
        # Square off the right side of the left panel
        square_right = QPainterPath()
        square_right.addRect(lw - r, 1.0, r, h - 2.0)
        left_path = full_left.united(square_right)
        # Clip to the overall card path
        left_path = left_path.intersected(card_path)

        painter.setBrush(QColor(self._left_bg))
        painter.drawPath(left_path)

        # ── Border ────────────────────────────────────────────────────
        if self._border:
            pen = QPen(QColor(Palette.BORDER))
            pen.setWidthF(1.5)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(card_path)

        painter.end()


# ─────────────────────────────────────────────────────────────────────────────
# 7. StatusCard
# ─────────────────────────────────────────────────────────────────────────────

class StatusCard(BaseCard):
    """
    Card with a coloured accent strip along the left edge, communicating
    a status at a glance (success, warning, error, info).

    Add body content to `.content_layout` as normal.

    Parameters
    ----------
    status : str
        One of "success", "warning", "error", "info". Default "info".
    title : str
        Optional bold heading rendered at the top of the card.
    message : str
        Optional body text beneath the title.

    Example::

        card = StatusCard(
            status  = "error",
            title   = "Deployment Failed",
            message = "Build step exited with code 1. Check logs for details.",
        )
    """

    _STATUS_COLORS: dict[str, str] = {
        "success": Palette.SUCCESS,
        "warning": Palette.WARNING,
        "error":   Palette.ERROR,
        "info":    Palette.PRIMARY,
    }
    _STRIP_WIDTH = 4   # px

    def __init__(
        self,
        status:  str = "info",
        title:   str = "",
        message: str = "",
        parent:  QWidget | None = None,
    ) -> None:
        super().__init__(border=True, hover_highlight=False, parent=parent)
        self._status = status if status in self._STATUS_COLORS else "info"

        # Indent content to make room for the strip
        self.content_layout.setContentsMargins(
            self._STRIP_WIDTH + 16, 14, 16, 14
        )

        if title:
            color = self._STATUS_COLORS[self._status]
            self.content_layout.addWidget(
                _label(title, size_pt=11, bold=True, color=color)
            )
        if message:
            self.content_layout.addWidget(
                _label(message, size_pt=10, color=Palette.TEXT_SECONDARY,
                       wrap=True)
            )

    # ── Public API ───��────────────────────────────────────────────────

    def set_status(self, status: str) -> None:
        self._status = status if status in self._STATUS_COLORS else "info"
        self.update()

    # ── Paint: draw strip over the standard card background ───────────

    def paintEvent(self, event) -> None:  # noqa: N802
        # Draw the base card first
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color  = QColor(self._STATUS_COLORS[self._status])
        r      = self._radius
        sw     = self._STRIP_WIDTH
        h      = self.height()

        # Strip path: rounded on the left side only, matching the card radius
        strip = QPainterPath()
        strip.addRoundedRect(1.0, 1.0, sw + r, h - 2.0, r, r)

        # Square off the right side of the strip
        square = QPainterPath()
        square.addRect(1.0 + r, 1.0, sw, h - 2.0)
        strip = strip.united(square)

        # Clip strip to card bounds
        card_path = QPainterPath()
        card_path.addRoundedRect(1.0, 1.0, self.width() - 2.0, h - 2.0, r, r)
        strip = strip.intersected(card_path)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPath(strip)

        painter.end()