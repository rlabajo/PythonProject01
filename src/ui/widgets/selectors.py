"""
src/ui/widgets/selectors.py
---------------------------
Fully custom-painted selector widgets.  Zero native QComboBox,
zero native QSpinBox — every pixel is drawn in paintEvent so there
is nothing for Qt's style engine to interfere with.

Widgets
-------
  BaseComboBox        — Dropdown selector, fully painted.
  BaseSpinBox         — Integer stepper, fully painted.
  BaseDoubleSpinBox   — Float stepper, fully painted.
  PrefixSpinBox       — Integer stepper with a leading unit label.
  SuffixSpinBox       — Integer stepper with a trailing unit label.
  StepDoubleSpinBox   — Float stepper with fine / coarse step.
  SearchableComboBox  — Combo with a live-filter search popup.
"""

from __future__ import annotations

import re
from typing import Any

from PySide6.QtCore    import (Qt, Signal, QRect, QPoint, QSize,
                                QPropertyAnimation, QEasingCurve,
                                Property, QTimer)
from PySide6.QtGui     import (QColor, QPainter, QPainterPath, QPen,
                                QFont, QFontMetrics, QMouseEvent,
                                QWheelEvent, QKeyEvent,
                                QFocusEvent)
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QSizePolicy, QApplication,
                                QListWidget, QListWidgetItem,
                                QLineEdit, QFrame, QScrollBar,
                                QGraphicsDropShadowEffect, QToolButton)

from src.ui.themes.theme import Palette


# ─────────────────────────────────────────────────────────────────────────────
# Shared constants & helpers
# ─────────────────────────────────────────────────────────────────────────────

_H      = 38          # widget height
_R      = 6           # corner radius
_FONT   = "Roboto"


def _f(pt: int = 10, bold: bool = False) -> QFont:
    font = QFont(_FONT, pt)
    font.setBold(bold)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    return font


def _color(hex_str: str, alpha: int = 255) -> QColor:
    c = QColor(hex_str)
    c.setAlpha(alpha)
    return c


def _draw_rounded_rect(
    p: QPainter,
    rect: QRect,
    radius: int,
    fill: QColor,
    border: QColor | None = None,
    border_width: float = 1.5,
) -> None:
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(fill)
    p.drawPath(path)
    if border:
        pen = QPen(border)
        pen.setWidthF(border_width)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)


def _draw_chevron(p: QPainter, cx: int, cy: int,
                  color: QColor, size: int = 8) -> None:
    """Down-pointing filled triangle centred at (cx, cy)."""
    h = size // 2
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    from PySide6.QtGui import QPolygon
    p.drawPolygon(QPolygon([
        QPoint(cx - size // 2, cy - h // 2),
        QPoint(cx + size // 2, cy - h // 2),
        QPoint(cx,             cy + h // 2),
    ]))


# ─────────────────────────────────────────────────────────────────────────────
# Dropdown popup  (shared by BaseComboBox and SearchableComboBox)
# ─────────────────────────────────────────────────────────────────────────────

class _DropdownPopup(QFrame):
    """
    Floating list popup.  Painted entirely without native QSS so the
    scrollbar and item highlight are consistent with the theme.
    """

    itemSelected: Signal = Signal(int, str)   # (index, text)

    _ITEM_H    = 34
    _PADDING   = 6
    _MAX_ITEMS = 8

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._items:   list[str] = []
        self._hovered: int       = -1

        self._list = QListWidget(self)
        self._list.setFont(_f(10))
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
                color: {Palette.TEXT_PRIMARY};
                font-family: '{_FONT}', sans-serif;
                font-size: 10pt;
            }}
            QListWidget::item {{
                height: {self._ITEM_H}px;
                padding: 0 12px;
                border-radius: 5px;
            }}
            QListWidget::item:hover {{
                background: rgba(41,121,255,0.14);
                color: {Palette.PRIMARY};
            }}
            QListWidget::item:selected {{
                background: {Palette.PRIMARY};
                color: {Palette.TEXT_ON_PRIMARY};
                font-weight: 600;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 5px; border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {Palette.BORDER};
                border-radius: 2px; min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Palette.PRIMARY};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(
            self._PADDING, self._PADDING,
            self._PADDING, self._PADDING,
        )
        lay.addWidget(self._list)

        # Shadow
        sh = QGraphicsDropShadowEffect(self)
        sh.setBlurRadius(24)
        sh.setOffset(0, 4)
        sh.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(sh)

        self._list.itemClicked.connect(
            lambda item: self._emit(self._list.row(item), item.text())
        )
        self.hide()

    # ── Paint background ──────────────────────────────────────────────

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        _draw_rounded_rect(
            p,
            self.rect().adjusted(1, 1, -1, -1),
            radius=8,
            fill=_color(Palette.ELEVATED),
            border=_color(Palette.BORDER),
            border_width=1.0,
        )
        p.end()

    # ── Public API ────────────────────────────────────────────────────

    def set_items(self, items: list[str]) -> None:
        self._items = items
        self._list.clear()
        for t in items:
            self._list.addItem(QListWidgetItem(t))

    def set_current(self, index: int) -> None:
        if 0 <= index < self._list.count():
            self._list.setCurrentRow(index)

    def open_below(self, anchor: QWidget,
                   width: int | None = None) -> None:
        n    = min(self._list.count(), self._MAX_ITEMS)
        h    = n * self._ITEM_H + self._PADDING * 2 + 2
        w    = width or anchor.width()
        gp   = anchor.mapToGlobal(QPoint(0, anchor.height() + 2))
        self.setFixedSize(w, h)
        self.move(gp)
        self.show()
        self.raise_()

    def _emit(self, idx: int, text: str) -> None:
        self.itemSelected.emit(idx, text)
        self.hide()


# ─────────────────────────────────────────────────────────────────────────────
# 1. BaseComboBox  — fully painted, no QComboBox
# ─────────────────────────────────────────────────────────────────────────────

class BaseComboBox(QWidget):
    """
    Fully painted dropdown selector.

    No QComboBox, no native subcontrols, no style-engine interference.
    Everything is drawn in paintEvent.

    Signals
    -------
    currentIndexChanged(int)
    currentTextChanged(str)

    Usage::

        cb = BaseComboBox()
        cb.addItems(["Option A", "Option B", "Option C"])
        cb.currentTextChanged.connect(my_slot)
    """

    currentIndexChanged: Signal = Signal(int)
    currentTextChanged:  Signal = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items:   list[str] = []
        self._index:   int       = -1
        self._hovered: bool      = False
        self._open:    bool      = False

        self.setFixedHeight(_H)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

        self._popup = _DropdownPopup()
        self._popup.itemSelected.connect(self._on_pick)

    # ── Paint ─────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        enabled = self.isEnabled()
        focused = self.hasFocus() or self._open

        # Background
        if not enabled:
            bg = _color(Palette.BASE)
        elif self._open:
            bg = _color(Palette.ELEVATED)
        elif self._hovered:
            bg = _color(Palette.ELEVATED)
        else:
            bg = _color(Palette.SURFACE)

        border = (
            _color(Palette.TEXT_DISABLED) if not enabled
            else _color(Palette.PRIMARY)  if focused
            else _color(Palette.BORDER_MUTED) if self._hovered
            else _color(Palette.BORDER)
        )

        _draw_rounded_rect(
            p,
            self.rect().adjusted(1, 1, -1, -1),
            _R, bg, border, 1.5,
        )

        # Text
        text = (self._items[self._index]
                if 0 <= self._index < len(self._items)
                else "")
        if text:
            p.setFont(_f(10))
            p.setPen(
                _color(Palette.TEXT_DISABLED) if not enabled
                else _color(Palette.TEXT_PRIMARY)
            )
            text_rect = QRect(
                12, 0,
                self.width() - 44, self.height(),
            )
            p.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignVCenter
                | Qt.AlignmentFlag.AlignLeft,
                text,
            )

        # Chevron
        chevron_color = (
            _color(Palette.TEXT_DISABLED) if not enabled
            else _color(Palette.PRIMARY)  if focused
            else _color(Palette.TEXT_SECONDARY)
        )
        cx = self.width() - 18
        cy = self.height() // 2
        _draw_chevron(p, cx, cy, chevron_color, size=8)

        p.end()

    # ── Mouse / keyboard events ───────────────────────────────────────

    def mousePressEvent(self, _e: QMouseEvent) -> None:  # noqa: N802
        if not self.isEnabled():
            return
        if self._popup.isVisible():
            self._popup.hide()
            self._open = False
        else:
            self._open_popup()
        self.update()

    def enterEvent(self, _e) -> None:      # noqa: N802
        self._hovered = True;  self.update()

    def leaveEvent(self, _e) -> None:      # noqa: N802
        self._hovered = False; self.update()

    def focusInEvent(self, _e: QFocusEvent) -> None:   # noqa: N802
        self.update()

    def focusOutEvent(self, _e: QFocusEvent) -> None:  # noqa: N802
        self.update()

    def keyPressEvent(self, e: QKeyEvent) -> None:     # noqa: N802
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Space):
            self._open_popup()
        elif e.key() == Qt.Key.Key_Up:
            self._set_index(max(0, self._index - 1))
        elif e.key() == Qt.Key.Key_Down:
            self._set_index(min(len(self._items) - 1,
                                self._index + 1))
        elif e.key() == Qt.Key.Key_Escape:
            self._popup.hide(); self._open = False; self.update()
        else:
            super().keyPressEvent(e)

    def wheelEvent(self, e: QWheelEvent) -> None:
        if self.hasFocus() and self._items:
            delta = -1 if e.angleDelta().y() > 0 else 1
            self._set_index(
                max(0, min(len(self._items) - 1,
                           self._index + delta))
            )
        else:
            e.ignore()

    # ── Internal ──────────────────────────────────────────────────────

    def _open_popup(self) -> None:
        self._popup.set_items(self._items)
        self._popup.set_current(self._index)
        self._popup.open_below(self)
        self._open = True
        self.update()

    def _on_pick(self, idx: int, text: str) -> None:
        self._open = False
        self._set_index(idx)
        self.update()

    def _set_index(self, idx: int) -> None:
        if idx == self._index:
            return
        self._index = idx
        self.update()
        self.currentIndexChanged.emit(idx)
        if 0 <= idx < len(self._items):
            self.currentTextChanged.emit(self._items[idx])

    # ── Public API ────────────────────────────────────────────────────

    def addItem(self, text: str) -> None:
        self._items.append(text)
        if self._index == -1:
            self._index = 0
        self.update()

    def addItems(self, texts: list[str]) -> None:
        for t in texts:
            self.addItem(t)

    def currentText(self) -> str:
        if 0 <= self._index < len(self._items):
            return self._items[self._index]
        return ""

    def currentIndex(self) -> int:
        return self._index

    def setCurrentIndex(self, idx: int) -> None:
        self._set_index(idx)

    def setCurrentText(self, text: str) -> None:
        try:
            self._set_index(self._items.index(text))
        except ValueError:
            pass

    def count(self) -> int:
        return len(self._items)

    def itemText(self, idx: int) -> str:
        return self._items[idx] if 0 <= idx < len(self._items) else ""

    def clear(self) -> None:
        self._items.clear()
        self._index = -1
        self.update()

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self.update()


# ─────────────────��───────────────────────────────────────────────────────────
# SearchableComboBox
# ─────────────────────────────────────────────────────────────────────────────

class SearchableComboBox(BaseComboBox):
    """
    Combo box with a live-filter search field in the dropdown.

    Usage::

        scb = SearchableComboBox()
        scb.addItems(["Albania", "Algeria", …])
        scb.currentTextChanged.connect(my_slot)
    """

    def _open_popup(self) -> None:
        """Override: show a popup that has a search field."""
        self._search_popup = _SearchPopup(self._items, self)
        self._search_popup.itemSelected.connect(self._on_pick)
        self._search_popup.open_below(self)
        self._open = True
        self.update()


class _SearchPopup(QFrame):
    """Popup with an embedded search QLineEdit above the list."""

    itemSelected: Signal = Signal(int, str)

    _ITEM_H  = 34
    _PAD     = 6
    _MAX_VIS = 7

    def __init__(self, items: list[str],
                 parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._all_items = items

        # Search field
        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Search…")
        self._search.setFont(_f(10))
        self._search.setFixedHeight(32)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: {Palette.SURFACE};
                color: {Palette.TEXT_PRIMARY};
                border: 1.5px solid {Palette.BORDER};
                border-radius: 5px;
                padding: 0 8px;
                font-family: '{_FONT}', sans-serif;
                font-size: 10pt;
            }}
            QLineEdit:focus {{ border-color: {Palette.PRIMARY}; }}
        """)
        self._search.setClearButtonEnabled(True)

        # List
        self._list = QListWidget(self)
        self._list.setFont(_f(10))
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._list.setStyleSheet(f"""
            QListWidget {{
                background: transparent; border: none;
                outline: none; color: {Palette.TEXT_PRIMARY};
                font-family: '{_FONT}', sans-serif; font-size: 10pt;
            }}
            QListWidget::item {{
                height: {self._ITEM_H}px;
                padding: 0 12px; border-radius: 5px;
            }}
            QListWidget::item:hover {{
                background: rgba(41,121,255,0.14);
                color: {Palette.PRIMARY};
            }}
            QListWidget::item:selected {{
                background: {Palette.PRIMARY};
                color: {Palette.TEXT_ON_PRIMARY};
                font-weight: 600;
            }}
            QScrollBar:vertical {{
                background: transparent; width: 5px; border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {Palette.BORDER}; border-radius: 2px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Palette.PRIMARY};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(self._PAD, self._PAD,
                               self._PAD, self._PAD)
        lay.setSpacing(4)
        lay.addWidget(self._search)
        lay.addWidget(self._list)

        sh = QGraphicsDropShadowEffect(self)
        sh.setBlurRadius(24); sh.setOffset(0, 4)
        sh.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(sh)

        self._fill(items)
        self._search.textChanged.connect(self._filter)
        self._list.itemClicked.connect(
            lambda item: self._pick(item.text())
        )

    def _fill(self, items: list[str]) -> None:
        self._list.clear()
        for t in items:
            self._list.addItem(QListWidgetItem(t))

    def _filter(self, q: str) -> None:
        pat = re.compile(re.escape(q), re.IGNORECASE)
        self._fill([t for t in self._all_items if pat.search(t)])

    def _pick(self, text: str) -> None:
        try:
            idx = self._all_items.index(text)
        except ValueError:
            idx = -1
        self.itemSelected.emit(idx, text)
        self.hide()

    def open_below(self, anchor: QWidget,
                   width: int | None = None) -> None:
        n   = min(self._list.count(), self._MAX_VIS)
        h   = 32 + 4 + n * self._ITEM_H + self._PAD * 2 + 4
        w   = width or anchor.width()
        gp  = anchor.mapToGlobal(QPoint(0, anchor.height() + 2))
        self.setFixedSize(w, h)
        self.move(gp)
        self.show()
        self.raise_()
        self._search.setFocus()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        _draw_rounded_rect(
            p,
            self.rect().adjusted(1, 1, -1, -1),
            8,
            _color(Palette.ELEVATED),
            _color(Palette.BORDER),
            1.0,
        )
        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# _SpinWidget  —  shared painted base for all spin boxes
# ─────────────────────────────────────────────────────────────────────────────

class _SpinWidget(QWidget):
    """
    Fully painted spin box base.

    Layout:  [−]  [     value field     ]  [+]

    The ENTIRE widget is one QWidget whose sizeHint is exactly
    (_H + 2) px tall.  There are NO child widgets — buttons and the
    value area are hit-tested in mousePressEvent and painted directly.
    This means no layout clipping can ever occur.
    """

    _BTN_W = 36   # width of each ± button

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(_H)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.IBeamCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

        self._editing   = False
        self._edit_text = ""
        self._hov_dec   = False
        self._hov_inc   = False
        self._hov_field = False

        # Auto-repeat
        self._repeat_timer = QTimer(self)
        self._repeat_timer.timeout.connect(self._on_repeat)
        self._repeat_which: str = ""
        self._repeat_delay = True

    # ── Geometry helpers ──────────────────────────────────────────────

    def _dec_rect(self) -> QRect:
        return QRect(0, 0, self._BTN_W, self.height())

    def _inc_rect(self) -> QRect:
        return QRect(self.width() - self._BTN_W, 0,
                     self._BTN_W, self.height())

    def _field_rect(self) -> QRect:
        return QRect(self._BTN_W + 4, 0,
                     self.width() - self._BTN_W * 2 - 8,
                     self.height())

    # ── To be implemented by subclasses ──────────────────────────────

    def _display_text(self) -> str:
        raise NotImplementedError

    def _step_up(self) -> None:
        raise NotImplementedError

    def _step_down(self) -> None:
        raise NotImplementedError

    def _commit_edit(self, text: str) -> None:
        raise NotImplementedError

    # ── Paint ─────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        enabled = self.isEnabled()
        focused = self.hasFocus()

        # ── Field background ──────────────────────────────────────────
        field_bg = (
            _color(Palette.BASE)     if not enabled
            else _color(Palette.ELEVATED) if focused or self._editing
            else _color(Palette.SURFACE)
        )
        field_border = (
            _color(Palette.TEXT_DISABLED) if not enabled
            else _color(Palette.PRIMARY)  if focused or self._editing
            else _color(Palette.BORDER_MUTED) if self._hov_field
            else _color(Palette.BORDER)
        )
        _draw_rounded_rect(p, self.rect().adjusted(1, 1, -1, -1),
                           _R, field_bg, field_border, 1.5)

        # ── Dec button ────────────────────────────────────────────────
        dec_r = self._dec_rect().adjusted(1, 1, -1, -1)
        dec_bg = (
            _color(Palette.SURFACE)      if not enabled
            else _color(Palette.PRIMARY_PRESSED) if self._hov_dec and self._repeat_which == "dec"
            else _color(Palette.PRIMARY) if self._hov_dec
            else _color(Palette.ELEVATED)
        )
        dec_border = (
            _color(Palette.BORDER) if not enabled
            else _color(Palette.PRIMARY) if self._hov_dec
            else _color(Palette.BORDER)
        )
        _draw_rounded_rect(p, dec_r, _R, dec_bg, dec_border, 1.5)

        # Dec symbol
        p.setFont(_f(14, bold=True))
        p.setPen(
            _color(Palette.TEXT_DISABLED) if not enabled
            else _color(Palette.TEXT_ON_PRIMARY) if self._hov_dec
            else _color(Palette.TEXT_SECONDARY)
        )
        p.drawText(dec_r, Qt.AlignmentFlag.AlignCenter, "−")

        # ── Inc button ────────────────────────────────────────────────
        inc_r = self._inc_rect().adjusted(1, 1, -1, -1)
        inc_bg = (
            _color(Palette.SURFACE)      if not enabled
            else _color(Palette.PRIMARY_PRESSED) if self._hov_inc and self._repeat_which == "inc"
            else _color(Palette.PRIMARY) if self._hov_inc
            else _color(Palette.ELEVATED)
        )
        inc_border = (
            _color(Palette.BORDER) if not enabled
            else _color(Palette.PRIMARY) if self._hov_inc
            else _color(Palette.BORDER)
        )
        _draw_rounded_rect(p, inc_r, _R, inc_bg, inc_border, 1.5)

        p.setFont(_f(14, bold=True))
        p.setPen(
            _color(Palette.TEXT_DISABLED) if not enabled
            else _color(Palette.TEXT_ON_PRIMARY) if self._hov_inc
            else _color(Palette.TEXT_SECONDARY)
        )
        p.drawText(inc_r, Qt.AlignmentFlag.AlignCenter, "+")

        # ── Value text ────────────────────────────────────────────────
        display = (self._edit_text + "|"
                   if self._editing
                   else self._display_text())
        p.setFont(_f(10))
        p.setPen(
            _color(Palette.TEXT_DISABLED) if not enabled
            else _color(Palette.TEXT_PRIMARY)
        )
        p.drawText(
            self._field_rect(),
            Qt.AlignmentFlag.AlignCenter,
            display,
        )

        p.end()

    # ── Mouse events ──────────────────────────────────────────────────

    def mousePressEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        if not self.isEnabled():
            return
        self.setFocus()
        pos = e.position().toPoint()

        if self._dec_rect().contains(pos):
            self._end_edit()
            self._step_down()
            self._hov_dec = True
            self._repeat_which = "dec"
            self._repeat_delay = True
            self._repeat_timer.start(400)

        elif self._inc_rect().contains(pos):
            self._end_edit()
            self._step_up()
            self._hov_inc = True
            self._repeat_which = "inc"
            self._repeat_delay = True
            self._repeat_timer.start(400)

        elif self._field_rect().contains(pos):
            if not self._editing:
                self._editing   = True
                self._edit_text = self._display_text()

        self.update()

    def mouseReleaseEvent(self, _e: QMouseEvent) -> None:  # noqa: N802
        self._repeat_timer.stop()
        self._repeat_which = ""
        self.update()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        pos = e.position().toPoint()
        self._hov_dec   = self._dec_rect().contains(pos)
        self._hov_inc   = self._inc_rect().contains(pos)
        self._hov_field = self._field_rect().contains(pos)
        self.update()

    def leaveEvent(self, _e) -> None:      # noqa: N802
        self._hov_dec = self._hov_inc = self._hov_field = False
        self.update()

    def wheelEvent(self, e: QWheelEvent) -> None:
        if self.hasFocus():
            if e.angleDelta().y() > 0:
                self._step_up()
            else:
                self._step_down()
        else:
            e.ignore()

    # ── Keyboard events ───────────────────────────────────────────────

    def keyPressEvent(self, e: QKeyEvent) -> None:  # noqa: N802
        key = e.key()
        if self._editing:
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._commit_edit(self._edit_text)
                self._end_edit()
            elif key == Qt.Key.Key_Escape:
                self._end_edit()
            elif key == Qt.Key.Key_Backspace:
                self._edit_text = self._edit_text[:-1]
            else:
                char = e.text()
                if char in "0123456789.-+":
                    self._edit_text += char
            self.update()
        else:
            if key == Qt.Key.Key_Up:
                self._step_up()
            elif key == Qt.Key.Key_Down:
                self._step_down()
            else:
                super().keyPressEvent(e)

    def focusOutEvent(self, e: QFocusEvent) -> None:  # noqa: N802
        if self._editing:
            self._commit_edit(self._edit_text)
            self._end_edit()
        super().focusOutEvent(e)
        self.update()

    # ── Auto-repeat ───────────────────────────────────────────────────

    def _on_repeat(self) -> None:
        if self._repeat_delay:
            self._repeat_delay = False
            self._repeat_timer.setInterval(80)
        if self._repeat_which == "dec":
            self._step_down()
        elif self._repeat_which == "inc":
            self._step_up()

    # ── Edit helpers ──────────────────────────────────────────────────

    def _end_edit(self) -> None:
        self._editing   = False
        self._edit_text = ""
        self.update()


# ─────────────────────────────────────────────────────────────────────────────
# 3. BaseSpinBox  (integer)
# ─────────────────────────────────────────────────────────────────────────────

class BaseSpinBox(_SpinWidget):
    """
    Fully painted integer spin box.

    Usage::

        s = BaseSpinBox(minimum=0, maximum=100, value=10, step=1)
        s.valueChanged.connect(lambda v: print(v))
    """

    valueChanged: Signal = Signal(int)

    def __init__(self, minimum: int = 0, maximum: int = 100,
                 value: int = 0, step: int = 1,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._min   = minimum
        self._max   = maximum
        self._step  = step
        self._value = max(minimum, min(maximum, value))

    def _display_text(self) -> str:
        return str(self._value)

    def _clamp(self, v: int) -> int:
        return max(self._min, min(self._max, v))

    def _apply(self, v: int) -> None:
        c = self._clamp(v)
        if c != self._value:
            self._value = c
            self.update()
            self.valueChanged.emit(c)

    def _step_up(self) -> None:
        self._apply(self._value + self._step)

    def _step_down(self) -> None:
        self._apply(self._value - self._step)

    def _commit_edit(self, text: str) -> None:
        try:
            self._apply(int(text))
        except ValueError:
            pass

    # ── Public API ────────────────────────────────────────────────────

    def value(self) -> int:
        return self._value

    def setValue(self, v: int) -> None:
        self._apply(v)

    def setMinimum(self, v: int) -> None:
        self._min = v; self._apply(self._value)

    def setMaximum(self, v: int) -> None:
        self._max = v; self._apply(self._value)

    def setRange(self, lo: int, hi: int) -> None:
        self._min = lo; self._max = hi; self._apply(self._value)

    def setSingleStep(self, s: int) -> None:
        self._step = s


# ─────────────────────────────────────────────────────────────────────────────
# 4. PrefixSpinBox
# ─────────────────────────────────────────────────────────────────────────────

class PrefixSpinBox(BaseSpinBox):
    """Integer spin box with a leading prefix label (e.g. "$")."""

    def __init__(self, prefix: str = "", minimum: int = 0,
                 maximum: int = 100, value: int = 0, step: int = 1,
                 parent: QWidget | None = None) -> None:
        self._prefix = prefix
        super().__init__(minimum, maximum, value, step, parent)

    def _display_text(self) -> str:
        return f"{self._prefix}{self._value}"

    def _commit_edit(self, text: str) -> None:
        try:
            self._apply(int(text.lstrip(self._prefix).strip()))
        except ValueError:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# 5. SuffixSpinBox
# ─────────────────────────────────────────────────────────────────────────────

class SuffixSpinBox(BaseSpinBox):
    """Integer spin box with a trailing suffix label (e.g. " px")."""

    def __init__(self, suffix: str = "", minimum: int = 0,
                 maximum: int = 100, value: int = 0, step: int = 1,
                 parent: QWidget | None = None) -> None:
        self._suffix = suffix
        super().__init__(minimum, maximum, value, step, parent)

    def _display_text(self) -> str:
        return f"{self._value}{self._suffix}"

    def _commit_edit(self, text: str) -> None:
        try:
            self._apply(int(text.rstrip(self._suffix.strip()).strip()))
        except ValueError:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# 6. BaseDoubleSpinBox  (float)
# ─────────────────────────────────────────────────────────────────────────────

class BaseDoubleSpinBox(_SpinWidget):
    """
    Fully painted float spin box.

    Usage::

        s = BaseDoubleSpinBox(minimum=0.0, maximum=1.0,
                               value=0.5, step=0.1, decimals=2)
        s.valueChanged.connect(lambda v: print(f"{v:.2f}"))
    """

    valueChanged: Signal = Signal(float)

    def __init__(self, minimum: float = 0.0, maximum: float = 100.0,
                 value: float = 0.0, step: float = 1.0,
                 decimals: int = 2,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._min      = minimum
        self._max      = maximum
        self._step     = step
        self._decimals = decimals
        self._value    = max(minimum, min(maximum, value))

    def _display_text(self) -> str:
        return f"{self._value:.{self._decimals}f}"

    def _clamp(self, v: float) -> float:
        return max(self._min, min(self._max, v))

    def _apply(self, v: float) -> None:
        c = round(self._clamp(v), self._decimals)
        if c != self._value:
            self._value = c
            self.update()
            self.valueChanged.emit(c)

    def _step_up(self) -> None:
        self._apply(self._value + self._step)

    def _step_down(self) -> None:
        self._apply(self._value - self._step)

    def _commit_edit(self, text: str) -> None:
        try:
            self._apply(float(text))
        except ValueError:
            pass

    # ── Public API ────────────────────────────────────────────────────

    def value(self) -> float:
        return self._value

    def setValue(self, v: float) -> None:
        self._apply(v)

    def setMinimum(self, v: float) -> None:
        self._min = v; self._apply(self._value)

    def setMaximum(self, v: float) -> None:
        self._max = v; self._apply(self._value)

    def setRange(self, lo: float, hi: float) -> None:
        self._min = lo; self._max = hi; self._apply(self._value)

    def setSingleStep(self, s: float) -> None:
        self._step = s

    def setDecimals(self, d: int) -> None:
        self._decimals = d; self.update()


# ─────────────────────────────────────────────────────────────────────────────
# 7. StepDoubleSpinBox
# ─────────────────────────────────────────────────────────────────────────────

class StepDoubleSpinBox(BaseDoubleSpinBox):
    """Float spin box with fine/coarse step (hold Ctrl) and suffix."""

    def __init__(self, minimum: float = 0.0, maximum: float = 100.0,
                 value: float = 0.0, step: float = 0.1,
                 coarse_step: float = 1.0, decimals: int = 2,
                 suffix: str = "",
                 parent: QWidget | None = None) -> None:
        self._coarse = coarse_step
        self._suffix = suffix
        super().__init__(minimum, maximum, value, step,
                         decimals, parent)

    def _display_text(self) -> str:
        return f"{self._value:.{self._decimals}f}{self._suffix}"

    def _commit_edit(self, text: str) -> None:
        try:
            self._apply(float(
                text.rstrip(self._suffix).strip()
            ))
        except ValueError:
            pass

    def _active_step(self) -> float:
        mods = QApplication.keyboardModifiers()
        return (self._coarse
                if mods & Qt.KeyboardModifier.ControlModifier
                else self._step)

    def _step_up(self) -> None:
        self._apply(self._value + self._active_step())

    def _step_down(self) -> None:
        self._apply(self._value - self._active_step())

    def wheelEvent(self, e: QWheelEvent) -> None:
        if self.hasFocus():
            if e.angleDelta().y() > 0:
                self._step_up()
            else:
                self._step_down()
        else:
            e.ignore()