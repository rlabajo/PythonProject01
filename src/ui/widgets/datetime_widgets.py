"""
src/ui/widgets/datetime_widgets.py
-----------------------------------
Custom date and time widgets built on top of the dark theme defined in
src.ui.themes.theme.

Widgets provided:
  - TimePicker          — HH:MM (optionally HH:MM:SS) scroll-drum picker.
  - DatePicker          — Single-date calendar picker with month navigation.
  - DateRangePicker     — Two-date (start → end) range selector.
  - DateTimeWidget      — Combined date + time input in one compact row.
  - CountdownTimer      — Live visual countdown to a target datetime.
  - StopwatchWidget     — Start / pause / lap / reset stopwatch.
  - TimelineWidget      — Read-only vertical list of timestamped events.
"""

from __future__ import annotations

import calendar
from datetime  import datetime, date, time, timedelta
from typing    import NamedTuple

from PySide6.QtCore    import (Qt, Signal, QTimer, QDate, QTime,
                                QPropertyAnimation, QEasingCurve,
                                QRect, QPoint, QSize, Property)
from PySide6.QtGui     import (QColor, QPainter, QPainterPath, QPen,
                                QFont, QFontMetrics, QMouseEvent,
                                QWheelEvent)
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QSizePolicy, QToolButton,
                                QScrollArea, QFrame, QGridLayout,
                                QGraphicsDropShadowEffect)

from src.ui.themes.theme import Palette


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _roboto(size_pt: int = 10, bold: bool = False) -> QFont:
    f = QFont("Roboto", size_pt)
    f.setBold(bold)
    f.setStyleHint(QFont.StyleHint.SansSerif)
    return f


def _label(text: str, size_pt: int = 10, bold: bool = False,
           color: str = Palette.TEXT_PRIMARY,
           align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft
           ) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(_roboto(size_pt, bold))
    lbl.setAlignment(align)
    lbl.setStyleSheet(
        f"color: {color}; background: transparent; border: none;"
    )
    return lbl


def _icon_btn(symbol: str, tooltip: str,
              parent: QWidget | None = None) -> QToolButton:
    btn = QToolButton(parent)
    btn.setText(symbol)
    btn.setToolTip(tooltip)
    btn.setFixedSize(QSize(30, 30))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    btn.setStyleSheet(f"""
        QToolButton {{
            background: transparent;
            border: none;
            color: {Palette.TEXT_SECONDARY};
            font-size: 13px;
        }}
        QToolButton:hover  {{ color: {Palette.PRIMARY}; }}
        QToolButton:pressed {{ color: {Palette.PRIMARY_PRESSED}; }}
    """)
    return btn


def _card_frame(parent: QWidget | None = None) -> QFrame:
    """Rounded surface matching BaseCard aesthetics."""
    f = QFrame(parent)
    f.setStyleSheet(f"""
        QFrame {{
            background-color: {Palette.ELEVATED};
            border: 1.5px solid {Palette.BORDER};
            border-radius: 10px;
        }}
    """)
    shadow = QGraphicsDropShadowEffect(f)
    shadow.setBlurRadius(18)
    shadow.setOffset(0, 2)
    shadow.setColor(QColor(0, 0, 0, 110))
    f.setGraphicsEffect(shadow)
    return f


_MONTH_NAMES = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December",
]
_DAY_ABBRS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


# ─────────────────────────────────────────────────────────────────────────────
# 1. TimePicker
# ─────────────────────────────────────────────────────────────────────────────

class _DrumColumn(QWidget):
    """
    Scrollable drum-column for a single time unit (hours, minutes, seconds).
    Scroll-wheel or click the ▲/▼ arrows to change the value.
    """

    valueChanged: Signal = Signal(int)

    _ITEM_H  = 36
    _VISIBLE = 5           # odd number so selection is centred
    _COL_W   = 56

    def __init__(self, max_val: int, zero_pad: bool = True,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._max      = max_val
        self._pad      = zero_pad
        self._value    = 0
        self._drag_y   : int | None = None

        self.setFixedSize(self._COL_W,
                          self._ITEM_H * self._VISIBLE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # ── Public API ────────────────────────────────────────────────────

    def value(self) -> int:
        return self._value

    def set_value(self, v: int) -> None:
        v = v % (self._max + 1)
        if v != self._value:
            self._value = v
            self.update()
            self.valueChanged.emit(v)

    # ── Paint ─────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = self.width()
        h = self.height()
        mid_y = h // 2

        # Selection highlight strip
        sel_rect = QRect(0, mid_y - self._ITEM_H // 2,
                         w, self._ITEM_H)
        sel_path = QPainterPath()
        sel_path.addRoundedRect(sel_rect, 6, 6)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(Palette.PRIMARY) if self.hasFocus()
                   else QColor(Palette.BORDER))
        p.drawPath(sel_path)

        # Items
        half = self._VISIBLE // 2
        for offset in range(-half, half + 1):
            val  = (self._value + offset) % (self._max + 1)
            text = f"{val:02d}" if self._pad else str(val)
            y    = mid_y + offset * self._ITEM_H

            distance = abs(offset) / half
            alpha    = int(255 * (1.0 - distance * 0.65))
            size_pt  = 14 if offset == 0 else max(8, 12 - abs(offset) * 2)
            bold     = offset == 0

            font = _roboto(size_pt, bold)
            p.setFont(font)

            if offset == 0:
                color = QColor(Palette.TEXT_ON_PRIMARY
                               if self.hasFocus()
                               else Palette.TEXT_PRIMARY)
            else:
                color = QColor(Palette.TEXT_SECONDARY)
                color.setAlpha(alpha)

            p.setPen(color)
            fm = QFontMetrics(font)
            tx = (w - fm.horizontalAdvance(text)) // 2
            ty = y + fm.ascent() - fm.height() // 2
            p.drawText(tx, ty, text)

        # Top / bottom fade gradients
        for top in (True, False):
            grad_rect = QRect(0, 0 if top else h - self._ITEM_H,
                              w, self._ITEM_H)
            grad = QPainterPath()
            grad.addRect(grad_rect)
            fade = QColor(Palette.ELEVATED)
            fade.setAlpha(200 if top else 200)
            p.fillPath(grad, fade)

        p.end()

    # ── Input events ──────────────────────────────────────────────────

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = -1 if event.angleDelta().y() > 0 else 1
        self.set_value(self._value + delta)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_y = int(event.position().y())
        self.setFocus()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_y is not None:
            dy    = int(event.position().y()) - self._drag_y
            steps = -dy // self._ITEM_H
            if steps != 0:
                self.set_value(self._value + steps)
                self._drag_y = int(event.position().y())

    def mouseReleaseEvent(self, _event: QMouseEvent) -> None:  # noqa: N802
        self._drag_y = None

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Up:
            self.set_value(self._value - 1)
        elif event.key() == Qt.Key.Key_Down:
            self.set_value(self._value + 1)
        else:
            super().keyPressEvent(event)

    def focusInEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().focusOutEvent(event)


class TimePicker(QWidget):
    """
    Scroll-drum time picker.

    Parameters
    ----------
    show_seconds : bool
        Include a seconds drum. Default False.
    initial : datetime.time | None
        Starting time. Defaults to midnight.

    Signals
    -------
    timeChanged(datetime.time)

    Usage::

        picker = TimePicker(show_seconds=True)
        picker.timeChanged.connect(lambda t: print(t.strftime("%H:%M:%S")))
        current = picker.time()
    """

    timeChanged: Signal = Signal(object)   # datetime.time

    def __init__(
        self,
        show_seconds: bool = False,
        initial:      time | None = None,
        parent:       QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        t = initial or time(0, 0, 0)

        self._hour_drum = _DrumColumn(23)
        self._min_drum  = _DrumColumn(59)
        self._sec_drum  = _DrumColumn(59) if show_seconds else None

        self._hour_drum.set_value(t.hour)
        self._min_drum.set_value(t.minute)
        if self._sec_drum:
            self._sec_drum.set_value(t.second)

        # ── Layout ────────────────────────────────────────────────────
        card = _card_frame(self)
        row  = QHBoxLayout(card)
        row.setContentsMargins(16, 12, 16, 12)
        row.setSpacing(4)

        row.addWidget(self._hour_drum)
        row.addWidget(_label(":", 20, bold=True,
                             color=Palette.TEXT_SECONDARY,
                             align=Qt.AlignmentFlag.AlignCenter))
        row.addWidget(self._min_drum)

        if self._sec_drum:
            row.addWidget(_label(":", 20, bold=True,
                                 color=Palette.TEXT_SECONDARY,
                                 align=Qt.AlignmentFlag.AlignCenter))
            row.addWidget(self._sec_drum)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # ── Signals ───────────────────────────────────────────────────
        self._hour_drum.valueChanged.connect(self._emit)
        self._min_drum.valueChanged.connect(self._emit)
        if self._sec_drum:
            self._sec_drum.valueChanged.connect(self._emit)

    # ------------------------------------------------------------------
    def _emit(self) -> None:
        self.timeChanged.emit(self.time())

    def time(self) -> time:
        s = self._sec_drum.value() if self._sec_drum else 0
        return time(self._hour_drum.value(), self._min_drum.value(), s)

    def set_time(self, t: time) -> None:
        self._hour_drum.set_value(t.hour)
        self._min_drum.set_value(t.minute)
        if self._sec_drum:
            self._sec_drum.set_value(t.second)


# ─────────────────────────────────────────────────────────────────────────────
# 2. DatePicker
# ─────────────────────────────────────────────────────────────────────────────

class DatePicker(QWidget):
    """
    Monthly calendar grid for picking a single date.

    Parameters
    ----------
    initial : datetime.date | None
        Pre-selected date. Defaults to today.
    min_date / max_date : datetime.date | None
        Optional bounds; out-of-range days are greyed and unclickable.

    Signals
    -------
    dateChanged(datetime.date)

    Usage::

        picker = DatePicker()
        picker.dateChanged.connect(lambda d: print(d.isoformat()))
        selected = picker.date()
    """

    dateChanged: Signal = Signal(object)   # datetime.date

    _CELL_W = 38
    _CELL_H = 34
    _RADIUS = 6

    def __init__(
        self,
        initial:  date | None = None,
        min_date: date | None = None,
        max_date: date | None = None,
        parent:   QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._selected  = initial or date.today()
        self._viewing   = date(self._selected.year, self._selected.month, 1)
        self._min_date  = min_date
        self._max_date  = max_date
        self._hovered:  date | None = None

        self._build_ui()
        self._refresh()
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    # ── Build ─────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        card = _card_frame(self)

        # Header
        self._prev_btn = _icon_btn("‹", "Previous month")
        self._next_btn = _icon_btn("›", "Next month")
        self._month_lbl = _label("", 11, bold=True,
                                 align=Qt.AlignmentFlag.AlignCenter)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(self._prev_btn)
        header.addWidget(self._month_lbl, 1)
        header.addWidget(self._next_btn)

        # Day-of-week row
        dow_row = QHBoxLayout()
        dow_row.setContentsMargins(0, 0, 0, 4)
        dow_row.setSpacing(0)
        for abbr in _DAY_ABBRS:
            lbl = _label(abbr, 8, color=Palette.TEXT_SECONDARY,
                         align=Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedWidth(self._CELL_W)
            dow_row.addWidget(lbl)

        # Date grid
        self._grid = QGridLayout()
        self._grid.setSpacing(2)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._day_buttons: dict[int, QToolButton] = {}

        for row in range(6):
            for col in range(7):
                btn = QToolButton()
                btn.setFixedSize(self._CELL_W, self._CELL_H)
                btn.setFont(_roboto(10))
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(
                    lambda _, r=row, c=col: self._on_cell_click(r, c)
                )
                self._grid.addWidget(btn, row, col)
                self._day_buttons[row * 7 + col] = btn

        root_lay = QVBoxLayout(card)
        root_lay.setContentsMargins(14, 14, 14, 14)
        root_lay.setSpacing(6)
        root_lay.addLayout(header)
        root_lay.addLayout(dow_row)
        root_lay.addLayout(self._grid)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)

        self._prev_btn.clicked.connect(self._go_prev)
        self._next_btn.clicked.connect(self._go_next)

    # ── Refresh grid ──────────────────────────────────────────────────

    def _refresh(self) -> None:
        y, m = self._viewing.year, self._viewing.month
        self._month_lbl.setText(
            f"{_MONTH_NAMES[m - 1]}  {y}"
        )

        # calendar.monthcalendar returns weeks as lists of day numbers
        # (0 = day not in this month)
        weeks = calendar.monthcalendar(y, m)
        # Pad to 6 rows so the grid height stays constant
        while len(weeks) < 6:
            weeks.append([0] * 7)

        today = date.today()

        for row in range(6):
            for col in range(7):
                btn = self._day_buttons[row * 7 + col]
                day = weeks[row][col] if row < len(weeks) else 0

                if day == 0:
                    btn.setText("")
                    btn.setEnabled(False)
                    btn.setStyleSheet(
                        "background: transparent; border: none;"
                    )
                    continue

                d = date(y, m, day)
                out_of_range = (
                    (self._min_date and d < self._min_date) or
                    (self._max_date and d > self._max_date)
                )

                btn.setText(str(day))
                btn.setEnabled(not out_of_range)
                btn.setStyleSheet(
                    self._cell_style(d, today, out_of_range)
                )

    def _cell_style(self, d: date, today: date,
                    disabled: bool) -> str:
        r = self._RADIUS
        if d == self._selected:
            return (f"background: {Palette.PRIMARY}; color: {Palette.TEXT_ON_PRIMARY};"
                    f"border: none; border-radius: {r}px; font-weight: 700;")
        if d == today:
            return (f"background: transparent; color: {Palette.PRIMARY};"
                    f"border: 1.5px solid {Palette.PRIMARY};"
                    f"border-radius: {r}px; font-weight: 600;")
        if disabled:
            return (f"background: transparent; color: {Palette.TEXT_DISABLED};"
                    "border: none;")
        return (f"background: transparent; color: {Palette.TEXT_PRIMARY};"
                f"border: none; border-radius: {r}px;"
                "} QToolButton:hover { background: rgba(41,121,255,0.15);"
                f"color: {Palette.PRIMARY}; border-radius: {r}px;")

    # ── Navigation ────────────────────────────────────────────────────

    def _go_prev(self) -> None:
        y, m = self._viewing.year, self._viewing.month
        m -= 1
        if m == 0:
            m, y = 12, y - 1
        self._viewing = date(y, m, 1)
        self._refresh()

    def _go_next(self) -> None:
        y, m = self._viewing.year, self._viewing.month
        m += 1
        if m == 13:
            m, y = 1, y + 1
        self._viewing = date(y, m, 1)
        self._refresh()

    # ── Clicks ────────────────────────────────────────────────────────

    def _on_cell_click(self, row: int, col: int) -> None:
        btn = self._day_buttons[row * 7 + col]
        if not btn.text():
            return
        y, m = self._viewing.year, self._viewing.month
        self._selected = date(y, m, int(btn.text()))
        self._refresh()
        self.dateChanged.emit(self._selected)

    # ── Public API ────────────────────────────────────────────────────

    def date(self) -> date:
        return self._selected

    def set_date(self, d: date) -> None:
        self._selected = d
        self._viewing  = date(d.year, d.month, 1)
        self._refresh()

    def set_range(self, min_date: date | None,
                  max_date: date | None) -> None:
        self._min_date = min_date
        self._max_date = max_date
        self._refresh()


# ─────────────────────────────────────────────────────────────────────────────
# 3. DateRangePicker
# ─────────────────────────────────────────────────────────────────────────────

class DateRangePicker(QWidget):
    """
    Two-month side-by-side calendar for selecting a date range.

    Click once to set the start date; click again to set the end date.
    Days inside the range are tinted blue; the two endpoints are fully
    highlighted.

    Signals
    -------
    rangeChanged(start: datetime.date, end: datetime.date)
        Emitted only when both start and end are confirmed.

    Usage::

        rp = DateRangePicker()
        rp.rangeChanged.connect(
            lambda s, e: print(s.isoformat(), "→", e.isoformat())
        )
        start, end = rp.range()
    """

    rangeChanged: Signal = Signal(object, object)

    _CELL_W = 34
    _CELL_H = 30
    _RADIUS = 5

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        today           = date.today()
        self._start:    date | None = None
        self._end:      date | None = None
        self._hovered:  date | None = None
        self._pending:  date | None = None   # first click, waiting for second

        # Two month views
        self._left_view  = date(today.year, today.month, 1)
        self._right_view = self._next_month(self._left_view)

        self._build_ui()
        self._refresh()
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    # ── Helpers ──────────────────────────────────────���────────────────

    @staticmethod
    def _next_month(d: date) -> date:
        m, y = d.month + 1, d.year
        if m == 13:
            m, y = 1, y + 1
        return date(y, m, 1)

    @staticmethod
    def _prev_month(d: date) -> date:
        m, y = d.month - 1, d.year
        if m == 0:
            m, y = 12, y - 1
        return date(y, m, 1)

    # ── Build ─────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        card = _card_frame(self)

        self._prev_btn  = _icon_btn("‹", "Previous")
        self._next_btn  = _icon_btn("›", "Next")
        self._left_lbl  = _label("", 11, bold=True,
                                 align=Qt.AlignmentFlag.AlignCenter)
        self._right_lbl = _label("", 11, bold=True,
                                 align=Qt.AlignmentFlag.AlignCenter)

        nav = QHBoxLayout()
        nav.setContentsMargins(0, 0, 0, 0)
        nav.addWidget(self._prev_btn)
        nav.addWidget(self._left_lbl,  1)
        nav.addWidget(self._right_lbl, 1)
        nav.addWidget(self._next_btn)

        self._left_grid  = self._make_grid("L")
        self._right_grid = self._make_grid("R")

        grids = QHBoxLayout()
        grids.setSpacing(16)
        grids.setContentsMargins(0, 0, 0, 0)
        grids.addLayout(self._left_grid)
        grids.addLayout(self._right_grid)

        root = QVBoxLayout(card)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(8)
        root.addLayout(nav)
        root.addLayout(grids)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)

        self._prev_btn.clicked.connect(self._go_prev)
        self._next_btn.clicked.connect(self._go_next)

    def _make_grid(self, side: str) -> QGridLayout:
        """Build a 7×6 grid of QToolButtons, stored in _cells_L / _cells_R."""
        layout = QGridLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)

        # Day headers
        for col, abbr in enumerate(_DAY_ABBRS):
            lbl = _label(abbr, 8, color=Palette.TEXT_SECONDARY,
                         align=Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedWidth(self._CELL_W)
            layout.addWidget(lbl, 0, col)

        cells: dict[int, QToolButton] = {}
        for row in range(6):
            for col in range(7):
                btn = QToolButton()
                btn.setFixedSize(self._CELL_W, self._CELL_H)
                btn.setFont(_roboto(9))
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(
                    lambda _, s=side, r=row,
                    c=col: self._on_click(s, r, c)
                )
                # hover tracking
                btn.installEventFilter(self)
                layout.addWidget(btn, row + 1, col)
                cells[row * 7 + col] = btn

        setattr(self, f"_cells_{side}", cells)
        return layout

    # ── Event filter for hover tracking ──────────────────────────────

    def eventFilter(self, obj, event) -> bool:
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Type.HoverEnter:
            for side in ("L", "R"):
                cells = getattr(self, f"_cells_{side}")
                view  = (self._left_view if side == "L"
                         else self._right_view)
                for idx, btn in cells.items():
                    if btn is obj and btn.text():
                        row, col = idx // 7, idx % 7
                        weeks = calendar.monthcalendar(
                            view.year, view.month)
                        if row < len(weeks):
                            day = weeks[row][col]
                            if day:
                                self._hovered = date(
                                    view.year, view.month, day)
                                self._refresh()
                                return False
        if event.type() == QEvent.Type.HoverLeave:
            self._hovered = None
            self._refresh()
        return False

    # ── Refresh ───────────────────────────────────────────────────────

    def _refresh(self) -> None:
        for side, view, lbl in (
            ("L", self._left_view,  self._left_lbl),
            ("R", self._right_view, self._right_lbl),
        ):
            lbl.setText(
                f"{_MONTH_NAMES[view.month - 1]} {view.year}"
            )
            self._fill_grid(side, view)

    def _fill_grid(self, side: str, view: date) -> None:
        cells  = getattr(self, f"_cells_{side}")
        today  = date.today()
        weeks  = calendar.monthcalendar(view.year, view.month)
        while len(weeks) < 6:
            weeks.append([0] * 7)

        # Effective range for in-range tinting
        range_start = self._pending or self._start
        range_end   = (
            self._hovered if self._pending and self._hovered
            else self._end
        )
        if range_start and range_end and range_start > range_end:
            range_start, range_end = range_end, range_start

        for row in range(6):
            for col in range(7):
                btn = cells[row * 7 + col]
                day = weeks[row][col] if row < len(weeks) else 0

                if day == 0:
                    btn.setText("")
                    btn.setEnabled(False)
                    btn.setStyleSheet(
                        "background: transparent; border: none;"
                    )
                    continue

                d = date(view.year, view.month, day)
                btn.setText(str(day))
                btn.setEnabled(True)
                btn.setStyleSheet(self._range_cell_style(
                    d, today, range_start, range_end
                ))

    def _range_cell_style(
        self,
        d: date,
        today: date,
        rs: date | None,
        re: date | None,
    ) -> str:
        r = self._RADIUS
        is_start  = d == rs
        is_end    = d == re
        in_range  = rs and re and rs < d < re

        if is_start or is_end:
            return (f"background: {Palette.PRIMARY};"
                    f"color: {Palette.TEXT_ON_PRIMARY};"
                    f"border: none; border-radius: {r}px; font-weight: 700;")
        if in_range:
            return (f"background: rgba(41,121,255,0.18);"
                    f"color: {Palette.PRIMARY};"
                    "border: none; border-radius: 0px;")
        if d == today:
            return (f"background: transparent; color: {Palette.PRIMARY};"
                    f"border: 1.5px solid {Palette.PRIMARY};"
                    f"border-radius: {r}px; font-weight: 600;")
        return (f"background: transparent; color: {Palette.TEXT_PRIMARY};"
                f"border: none; border-radius: {r}px;"
                "} QToolButton:hover { background: rgba(41,121,255,0.12);"
                f"border-radius: {r}px;")

    # ── Navigation ────────────────────────────────────────────────────

    def _go_prev(self) -> None:
        self._left_view  = self._prev_month(self._left_view)
        self._right_view = self._next_month(self._left_view)
        self._refresh()

    def _go_next(self) -> None:
        self._left_view  = self._next_month(self._left_view)
        self._right_view = self._next_month(self._left_view)
        self._refresh()

    # ── Click logic ───────────────────────────────────────────────────

    def _on_click(self, side: str, row: int, col: int) -> None:
        cells = getattr(self, f"_cells_{side}")
        btn   = cells[row * 7 + col]
        if not btn.text():
            return
        view = self._left_view if side == "L" else self._right_view
        d    = date(view.year, view.month, int(btn.text()))

        if self._pending is None:
            # First click — set pending start
            self._pending = d
            self._start   = d
            self._end     = None
        else:
            # Second click — confirm range
            if d < self._pending:
                self._start, self._end = d, self._pending
            else:
                self._start, self._end = self._pending, d
            self._pending = None
            self.rangeChanged.emit(self._start, self._end)

        self._refresh()

    # ── Public API ────────────────────────────────────────────────────

    def range(self) -> tuple[date | None, date | None]:
        return self._start, self._end

    def set_range(self, start: date, end: date) -> None:
        self._start   = start
        self._end     = end
        self._pending = None
        self._refresh()


# ─────────────────────────────────────────────────────────────────────────────
# 4. DateTimeWidget
# ─────────────────────────────────────────────────────────────────────────────

class DateTimeWidget(QWidget):
    """
    Compact inline date + time selector in a single row.
    Clicking the date chip opens a floating DatePicker popup.
    Clicking the time chip opens a floating TimePicker popup.

    Signals
    -------
    dateTimeChanged(datetime.datetime)

    Usage::

        dt = DateTimeWidget()
        dt.dateTimeChanged.connect(lambda v: print(v.isoformat()))
        current = dt.datetime()
    """

    dateTimeChanged: Signal = Signal(object)   # datetime.datetime

    def __init__(
        self,
        initial:      datetime | None = None,
        show_seconds: bool = False,
        parent:       QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        dt = initial or datetime.now().replace(microsecond=0)
        self._date         = dt.date()
        self._time         = dt.time().replace(microsecond=0)
        self._show_seconds = show_seconds

        self._date_btn = QToolButton()
        self._time_btn = QToolButton()

        for btn in (self._date_btn, self._time_btn):
            btn.setFont(_roboto(10))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(36)
            btn.setStyleSheet(f"""
                QToolButton {{
                    background: {Palette.SURFACE};
                    color: {Palette.TEXT_PRIMARY};
                    border: 1.5px solid {Palette.BORDER};
                    border-radius: 6px;
                    padding: 0px 12px;
                    font-family: "Roboto", sans-serif;
                    font-size: 10pt;
                }}
                QToolButton:hover {{
                    border-color: {Palette.PRIMARY};
                    color: {Palette.PRIMARY};
                    background: {Palette.ELEVATED};
                }}
            """)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(self._date_btn)
        row.addWidget(_label("  at  ", 9,
                             color=Palette.TEXT_SECONDARY))
        row.addWidget(self._time_btn)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Popups
        self._date_popup = self._make_popup(DatePicker(self._date))
        self._time_popup = self._make_popup(
            TimePicker(show_seconds, self._time)
        )

        self._date_picker: DatePicker = \
            self._date_popup.findChild(DatePicker)
        self._time_picker: TimePicker = \
            self._time_popup.findChild(TimePicker)

        self._date_picker.dateChanged.connect(self._on_date)
        self._time_picker.timeChanged.connect(self._on_time)

        self._date_btn.clicked.connect(
            lambda: self._toggle_popup(self._date_popup, self._date_btn)
        )
        self._time_btn.clicked.connect(
            lambda: self._toggle_popup(self._time_popup, self._time_btn)
        )

        self._update_labels()

    # ── Popup factory ─────────────────────────────────────────────────

    def _make_popup(self, inner: QWidget) -> QFrame:
        popup = QFrame(
            self.window(),
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint,
        )
        popup.setStyleSheet(f"""
            QFrame {{
                background: {Palette.ELEVATED};
                border: 1px solid {Palette.BORDER};
                border-radius: 10px;
            }}
        """)
        lay = QVBoxLayout(popup)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.addWidget(inner)

        shadow = QGraphicsDropShadowEffect(popup)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 150))
        popup.setGraphicsEffect(shadow)
        popup.hide()
        return popup

    def _toggle_popup(self, popup: QFrame, anchor: QToolButton) -> None:
        if popup.isVisible():
            popup.hide()
            return
        popup.setParent(
            self.window(),
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint,
        )
        popup.adjustSize()
        gp = anchor.mapToGlobal(QPoint(0, anchor.height() + 4))
        popup.move(gp)
        popup.show()

    # ── Handlers ─────────────────────────────────────────────────────

    def _on_date(self, d: date) -> None:
        self._date = d
        self._update_labels()
        self.dateTimeChanged.emit(self.datetime())

    def _on_time(self, t: time) -> None:
        self._time = t
        self._update_labels()
        self.dateTimeChanged.emit(self.datetime())

    def _update_labels(self) -> None:
        self._date_btn.setText(
            self._date.strftime("  📅  %d %b %Y  ")
        )
        fmt = "%H:%M:%S" if self._show_seconds else "%H:%M"
        self._time_btn.setText(
            f"  🕐  {self._time.strftime(fmt)}  "
        )

    # ── Public API ────────────────────────────────────────────────────

    def datetime(self) -> datetime:
        return datetime.combine(self._date, self._time)

    def set_datetime(self, dt: datetime) -> None:
        self._date = dt.date()
        self._time = dt.time().replace(microsecond=0)
        self._date_picker.set_date(self._date)
        self._time_picker.set_time(self._time)
        self._update_labels()


# ─────────────────────────────────────────────────────────────────────────────
# 5. CountdownTimer
# ─────────────────────────────────────────────────────────────────────────────

class CountdownTimer(QWidget):
    """
    Live countdown to a target datetime.

    Shows DD : HH : MM : SS remaining. Emits `finished` when it reaches
    zero; the display then shows "00 : 00 : 00 : 00".

    Usage::

        from datetime import datetime, timedelta
        target = datetime.now() + timedelta(hours=2, minutes=30)
        cd = CountdownTimer(target=target, label="Sale ends in")
        cd.finished.connect(lambda: print("Done!"))
    """

    finished: Signal = Signal()

    def __init__(
        self,
        target: datetime,
        label:  str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._target  = target
        self._done    = False

        card = _card_frame(self)

        self._label_lbl = _label(
            label, 9, color=Palette.TEXT_SECONDARY,
            align=Qt.AlignmentFlag.AlignCenter,
        )
        self._label_lbl.setVisible(bool(label))

        # Four digit pairs + three separators
        self._digits: list[QLabel] = []
        digit_row = QHBoxLayout()
        digit_row.setSpacing(4)
        digit_row.setContentsMargins(0, 0, 0, 0)

        for i, unit in enumerate(["DD", "HH", "MM", "SS"]):
            if i > 0:
                sep = _label(":", 20, bold=True,
                             color=Palette.PRIMARY,
                             align=Qt.AlignmentFlag.AlignCenter)
                sep.setFixedWidth(16)
                digit_row.addWidget(sep)

            block = QVBoxLayout()
            block.setSpacing(2)
            block.setContentsMargins(0, 0, 0, 0)

            val_lbl = _label("00", 28, bold=True,
                             color=Palette.TEXT_PRIMARY,
                             align=Qt.AlignmentFlag.AlignCenter)
            val_lbl.setFixedWidth(58)
            unit_lbl = _label(unit, 7,
                              color=Palette.TEXT_SECONDARY,
                              align=Qt.AlignmentFlag.AlignCenter)

            block.addWidget(val_lbl)
            block.addWidget(unit_lbl)
            digit_row.addLayout(block)
            self._digits.append(val_lbl)

        root = QVBoxLayout(card)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(6)
        if label:
            root.addWidget(self._label_lbl)
        root.addLayout(digit_row)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._tick()
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # ------------------------------------------------------------------
    def _tick(self) -> None:
        remaining = self._target - datetime.now()
        if remaining.total_seconds() <= 0:
            if not self._done:
                self._done = True
                self._set_digits(0, 0, 0, 0)
                self._timer.stop()
                self.finished.emit()
            return

        total_s = int(remaining.total_seconds())
        days    = total_s  // 86400
        hours   = (total_s % 86400) // 3600
        minutes = (total_s % 3600)  // 60
        seconds = total_s % 60
        self._set_digits(days, hours, minutes, seconds)

    def _set_digits(self, d: int, h: int, m: int, s: int) -> None:
        for lbl, val in zip(self._digits, (d, h, m, s)):
            lbl.setText(f"{val:02d}")

    # ── Public API ────────────────────────────────────────────────────

    def set_target(self, target: datetime) -> None:
        self._target = target
        self._done   = False
        if not self._timer.isActive():
            self._timer.start()
        self._tick()


# ─────────────────────────────────────────────────────────────────────────────
# 6. StopwatchWidget
# ─────────────────────────────────────────────────────────────────────────────

class _LapRow(NamedTuple):
    number:  int
    split:   timedelta
    elapsed: timedelta


class StopwatchWidget(QWidget):
    """
    Full-featured stopwatch with start / pause / lap / reset.

    The large display shows HH:MM:SS.cc (centiseconds).
    Laps are listed below in a scrollable list showing split and total times.

    Usage::

        sw = StopwatchWidget()
        sw.lapped.connect(lambda n, s, e: print(f"Lap {n}: {s}"))
    """

    lapped: Signal = Signal(int, object, object)  # (lap_no, split, elapsed)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._elapsed   = timedelta(0)
        self._lap_start = timedelta(0)
        self._last_tick : datetime | None = None
        self._running   = False
        self._laps:      list[_LapRow] = []

        card = _card_frame(self)

        # ── Main display ──────────────────────────────────────────────
        self._display = _label(
            "00:00:00.00", 32, bold=True,
            color=Palette.TEXT_PRIMARY,
            align=Qt.AlignmentFlag.AlignCenter,
        )
        self._display.setFixedHeight(56)

        # ── Buttons ───────────────────────────────────────────────────
        self._start_btn = QToolButton()
        self._lap_btn   = QToolButton()
        self._reset_btn = QToolButton()

        for btn, text, tip in (
            (self._start_btn, "▶  Start", "Start / Pause"),
            (self._lap_btn,   "⚑  Lap",   "Record lap"),
            (self._reset_btn, "↺  Reset",  "Reset"),
        ):
            btn.setText(text)
            btn.setToolTip(tip)
            btn.setFixedHeight(34)
            btn.setFont(_roboto(10, bold=True))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self._style_buttons()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addWidget(self._start_btn, 2)
        btn_row.addWidget(self._lap_btn,   1)
        btn_row.addWidget(self._reset_btn, 1)

        # ── Lap list ──────────────────────────────────────────────────
        self._lap_container = QWidget()
        self._lap_container.setStyleSheet(
            "background: transparent; border: none;"
        )
        self._lap_layout = QVBoxLayout(self._lap_container)
        self._lap_layout.setContentsMargins(0, 0, 0, 0)
        self._lap_layout.setSpacing(3)
        self._lap_layout.addStretch()

        lap_scroll = QScrollArea()
        lap_scroll.setWidgetResizable(True)
        lap_scroll.setFrameShape(QFrame.Shape.NoFrame)
        lap_scroll.setMaximumHeight(140)
        lap_scroll.setWidget(self._lap_container)
        lap_scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: {Palette.BASE}; width: 5px; border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {Palette.BORDER}; border-radius: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Palette.PRIMARY};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        root = QVBoxLayout(card)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)
        root.addWidget(self._display)
        root.addLayout(btn_row)
        root.addWidget(lap_scroll)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(320)

        # ── Timer ─────────────────────────────────────────────────────
        self._timer = QTimer(self)
        self._timer.setInterval(33)   # ~30 fps
        self._timer.timeout.connect(self._tick)

        # ── Connect ───────────────────────────────────────────────────
        self._start_btn.clicked.connect(self._toggle_start)
        self._lap_btn.clicked.connect(self._record_lap)
        self._reset_btn.clicked.connect(self._reset)

    # ── Style ─────────────────────────────────────────────────────────

    def _style_buttons(self) -> None:
        primary_style = f"""
            QToolButton {{
                background: {Palette.PRIMARY};
                color: {Palette.TEXT_ON_PRIMARY};
                border: none; border-radius: 6px; padding: 0px 10px;
            }}
            QToolButton:hover {{ background: {Palette.PRIMARY_HOVER}; }}
            QToolButton:pressed {{ background: {Palette.PRIMARY_PRESSED}; }}
        """
        ghost_style = f"""
            QToolButton {{
                background: {Palette.SURFACE};
                color: {Palette.TEXT_PRIMARY};
                border: 1.5px solid {Palette.BORDER};
                border-radius: 6px; padding: 0px 10px;
            }}
            QToolButton:hover {{
                border-color: {Palette.PRIMARY};
                color: {Palette.PRIMARY};
            }}
        """
        pause_style = f"""
            QToolButton {{
                background: {Palette.ELEVATED};
                color: {Palette.TEXT_PRIMARY};
                border: 1.5px solid {Palette.BORDER};
                border-radius: 6px; padding: 0px 10px;
            }}
            QToolButton:hover {{
                border-color: {Palette.PRIMARY};
                color: {Palette.PRIMARY};
            }}
        """
        self._start_btn.setStyleSheet(
            pause_style if self._running else primary_style
        )
        self._start_btn.setText(
            "⏸  Pause" if self._running else "▶  Start"
        )
        self._lap_btn.setStyleSheet(ghost_style)
        self._reset_btn.setStyleSheet(ghost_style)
        self._lap_btn.setEnabled(self._running or bool(self._laps))
        self._reset_btn.setEnabled(
            self._elapsed.total_seconds() > 0
        )

    # ── Tick ──────────────────────────────────────────────────────────

    def _tick(self) -> None:
        now = datetime.now()
        if self._last_tick:
            self._elapsed += now - self._last_tick
        self._last_tick = now
        self._update_display()

    def _update_display(self) -> None:
        total_cs = int(self._elapsed.total_seconds() * 100)
        cs  = total_cs  % 100
        s   = (total_cs // 100) % 60
        m   = (total_cs // 6000) % 60
        h   = total_cs  // 360000
        self._display.setText(f"{h:02d}:{m:02d}:{s:02d}.{cs:02d}")

    # ── Controls ──────────────────────────────────────────────────────

    def _toggle_start(self) -> None:
        self._running = not self._running
        if self._running:
            self._last_tick = datetime.now()
            self._timer.start()
        else:
            self._timer.stop()
            self._last_tick = None
        self._style_buttons()

    def _record_lap(self) -> None:
        if not self._running and self._elapsed.total_seconds() == 0:
            return
        split   = self._elapsed - self._lap_start
        lap_no  = len(self._laps) + 1
        row     = _LapRow(lap_no, split, self._elapsed)
        self._laps.append(row)
        self._lap_start = self._elapsed

        def _fmt(td: timedelta) -> str:
            total_cs = int(td.total_seconds() * 100)
            cs = total_cs % 100
            s  = (total_cs // 100) % 60
            m  = (total_cs // 6000) % 60
            return f"{m:02d}:{s:02d}.{cs:02d}"

        lap_lbl = _label(
            f"Lap {lap_no:>2}   split {_fmt(split)}   "
            f"total {_fmt(self._elapsed)}",
            9, color=Palette.TEXT_SECONDARY,
        )
        lap_lbl.setStyleSheet(
            f"color: {Palette.TEXT_SECONDARY};"
            "background: transparent; border: none; padding: 2px 0px;"
        )
        # Insert above the stretch
        self._lap_layout.insertWidget(
            self._lap_layout.count() - 1, lap_lbl
        )
        self.lapped.emit(lap_no, split, self._elapsed)

    def _reset(self) -> None:
        self._timer.stop()
        self._running   = False
        self._elapsed   = timedelta(0)
        self._lap_start = timedelta(0)
        self._last_tick = None
        self._laps.clear()
        self._update_display()
        self._style_buttons()

        # Clear lap widgets
        while self._lap_layout.count() > 1:
            item = self._lap_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ─────────────────────────────────────────────────────────────────────────────
# 7. TimelineWidget
# ─────────────────────────────────────────────────────────────────────────────

class TimelineEvent(NamedTuple):
    timestamp: datetime
    title:     str
    detail:    str = ""
    status:    str = "info"    # "info" | "success" | "warning" | "error"


class TimelineWidget(QWidget):
    """
    Read-only vertical list of timestamped events with a coloured dot
    status indicator and a connecting spine line.

    Usage::

        tl = TimelineWidget()
        tl.add_event(TimelineEvent(
            timestamp = datetime(2026, 2, 28, 14, 32),
            title     = "Deployment started",
            detail    = "v2.4.1 → production",
            status    = "info",
        ))
        tl.add_event(TimelineEvent(...))
    """

    _STATUS_COLORS: dict[str, str] = {
        "success": Palette.SUCCESS,
        "warning": Palette.WARNING,
        "error":   Palette.ERROR,
        "info":    Palette.PRIMARY,
    }
    _DOT_R    = 6
    _SPINE_X  = 16
    _ROW_GAP  = 6

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._events: list[TimelineEvent] = []

        card = _card_frame(self)
        self._inner_layout = QVBoxLayout(card)
        self._inner_layout.setContentsMargins(14, 14, 14, 14)
        self._inner_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidget(card)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: {Palette.BASE}; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {Palette.BORDER}; border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Palette.PRIMARY};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

    # ------------------------------------------------------------------
    def add_event(self, event: TimelineEvent) -> None:
        self._events.append(event)
        self._inner_layout.addWidget(self._build_row(event))

    def clear_events(self) -> None:
        self._events.clear()
        while self._inner_layout.count():
            item = self._inner_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── Row builder ───────────────────────────────────────────────────

    def _build_row(self, event: TimelineEvent) -> QWidget:
        color = self._STATUS_COLORS.get(event.status, Palette.PRIMARY)

        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        row.setMinimumHeight(56)

        lay = QHBoxLayout(row)
        lay.setContentsMargins(36, 6, 0, 6)
        lay.setSpacing(10)

        # Text block
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        title_lbl = _label(event.title, 10, bold=True)
        text_col.addWidget(title_lbl)

        if event.detail:
            detail_lbl = _label(event.detail, 9,
                                color=Palette.TEXT_SECONDARY)
            detail_lbl.setWordWrap(True)
            text_col.addWidget(detail_lbl)

        ts_lbl = _label(
            event.timestamp.strftime("%d %b %Y · %H:%M"),
            8, color=Palette.TEXT_DISABLED,
        )
        text_col.addWidget(ts_lbl)

        lay.addLayout(text_col, 1)

        # Custom dot + spine painted in paintEvent of a small widget
        dot_widget = _TimelineDot(color, row)
        dot_widget.setFixedSize(self._SPINE_X * 2 + 4, row.minimumHeight())
        dot_widget.move(0, 0)

        return row


class _TimelineDot(QWidget):
    """Paints the coloured dot and vertical spine for one timeline row."""

    _DOT_R   = 6
    _SPINE_X = 16

    def __init__(self, color: str, parent: QWidget) -> None:
        super().__init__(parent)
        self._color = color
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self._SPINE_X
        cy = self.height() // 2

        # Spine line (full height, behind dot)
        pen = QPen(QColor(Palette.BORDER))
        pen.setWidth(2)
        p.setPen(pen)
        p.drawLine(cx, 0, cx, self.height())

        # Dot
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self._color))
        p.drawEllipse(cx - self._DOT_R, cy - self._DOT_R,
                      self._DOT_R * 2, self._DOT_R * 2)

        # White inner circle
        p.setBrush(QColor(Palette.ELEVATED))
        inner = self._DOT_R - 3
        if inner > 0:
            p.drawEllipse(cx - inner, cy - inner,
                          inner * 2, inner * 2)
        p.end()