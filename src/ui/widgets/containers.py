"""
src/ui/widgets/containers.py
----------------------------
Custom container widgets built on top of the dark theme defined in
src.ui.themes.theme.

Widgets provided:
  - BaseScrollArea      — Themed scroll area with styled thin scrollbars.
  - SidebarTabWidget    — Vertical icon+label sidebar navigation.
  - PillTabWidget       — Horizontal pill-shaped tab switcher.
  - UnderlineTabWidget  — Horizontal underline-style tab bar.
  - AccordionWidget     — Collapsible/expandable section container.
  - SplitterWidget      — Two-pane resizable splitter with themed handle.
  - StackedWidget       — QStackedWidget wrapper with animated slide/fade.
  - DrawerWidget        — Slide-in overlay panel from any screen edge.
"""

from __future__ import annotations

from PySide6.QtCore    import (Qt, Signal, QSize, QRect,
                                QPropertyAnimation, QEasingCurve,
                                QParallelAnimationGroup, Property,
                                QPoint)
from PySide6.QtGui     import (QColor, QPainter, QPainterPath, QPen,
                                QFont, QMouseEvent, QEnterEvent,
                                QResizeEvent)
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QScrollArea, QSizePolicy,
                                QSplitter, QStackedWidget, QToolButton,
                                QButtonGroup, QAbstractButton,
                                QGraphicsOpacityEffect, QFrame,
                                QScrollBar)

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
           color: str = Palette.TEXT_PRIMARY) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(_roboto(size_pt, bold))
    lbl.setStyleSheet(
        f"color: {color}; background: transparent; border: none;"
    )
    return lbl


_SCROLLBAR_QSS = f"""
    QScrollBar:vertical {{
        background: {Palette.BASE};
        width: 6px;
        margin: 0;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {Palette.BORDER};
        border-radius: 3px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {Palette.PRIMARY};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0; background: none;
    }}
    QScrollBar:horizontal {{
        background: {Palette.BASE};
        height: 6px;
        margin: 0;
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal {{
        background: {Palette.BORDER};
        border-radius: 3px;
        min-width: 24px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {Palette.PRIMARY};
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0; background: none;
    }}
"""


# ─────────────────────────────────────────────────────────────────────────────
# 1. BaseScrollArea
# ─────────────────────────────────────────────────────────────────────────────

class BaseScrollArea(QScrollArea):
    """
    Themed scroll area with minimal 6 px scrollbars that turn blue on hover.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {Palette.BASE};
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {Palette.BASE};
            }}
            {_SCROLLBAR_QSS}
        """)

    @classmethod
    def from_layout(cls, layout,
                    parent: QWidget | None = None) -> "BaseScrollArea":
        container = QWidget()
        container.setLayout(layout)
        instance  = cls(parent)
        instance.setWidget(container)
        return instance


# ─────────────────────────────────────────────��───────────────────────────────
# 2. SidebarTabWidget
# ─────────────────────────────────────────────────────────────────────────────

class _SidebarTab(QAbstractButton):
    _W = 200
    _H = 44

    def __init__(self, icon: str, label: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._icon  = icon
        self._label = label
        self.setCheckable(True)
        self.setFixedHeight(self._H)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self) -> QSize:
        return QSize(self._W, self._H)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        checked = self.isChecked()
        hovered = self.underMouse()

        if checked:
            bg = QColor(Palette.PRIMARY)
        elif hovered:
            bg = QColor(Palette.ELEVATED)
        else:
            bg = QColor("transparent")

        if checked or hovered:
            path = QPainterPath()
            path.addRoundedRect(4, 2, self.width() - 8,
                                self.height() - 4, 8, 8)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(bg)
            p.drawPath(path)

        p.setFont(QFont("Roboto", 13))
        p.setPen(QColor(Palette.TEXT_ON_PRIMARY if checked
                        else Palette.TEXT_SECONDARY))
        p.drawText(QRect(12, 0, 28, self.height()),
                   Qt.AlignmentFlag.AlignVCenter
                   | Qt.AlignmentFlag.AlignHCenter,
                   self._icon)

        text_font = QFont("Roboto", 10)
        text_font.setBold(checked)
        p.setFont(text_font)
        p.setPen(QColor(Palette.TEXT_ON_PRIMARY if checked
                        else Palette.TEXT_PRIMARY))
        p.drawText(
            QRect(48, 0, self.width() - 56, self.height()),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self._label,
        )
        p.end()


class SidebarTabWidget(QWidget):
    """Vertical sidebar navigation with icon + label tabs."""

    currentChanged: Signal = Signal(int)
    _SIDEBAR_WIDTH = 210

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._group  = QButtonGroup(self)
        self._group.setExclusive(True)
        self._pages: list[QWidget] = []

        self._sidebar = QWidget()
        self._sidebar.setFixedWidth(self._SIDEBAR_WIDTH)
        self._sidebar.setStyleSheet(
            f"background-color: {Palette.SURFACE}; border: none;"
        )
        self._sidebar_layout = QVBoxLayout(self._sidebar)
        self._sidebar_layout.setContentsMargins(8, 12, 8, 12)
        self._sidebar_layout.setSpacing(2)
        self._sidebar_layout.addStretch()

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(
            f"background-color: {Palette.BASE}; border: none;"
        )

        sep = QWidget()
        sep.setFixedWidth(1)
        sep.setStyleSheet(
            f"background-color: {Palette.BORDER}; border: none;"
        )

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._sidebar)
        root.addWidget(sep)
        root.addWidget(self._stack, 1)

        self._group.buttonToggled.connect(self._on_toggle)

    def add_tab(self, icon: str, label: str, page: QWidget) -> int:
        idx = len(self._pages)
        btn = _SidebarTab(icon, label)
        self._group.addButton(btn, idx)
        insert_pos = self._sidebar_layout.count() - 1
        self._sidebar_layout.insertWidget(insert_pos, btn)
        self._stack.addWidget(page)
        self._pages.append(page)
        if idx == 0:
            btn.setChecked(True)
        return idx

    def add_separator(self) -> None:
        rule = QWidget()
        rule.setFixedHeight(1)
        rule.setStyleSheet(
            f"background-color: {Palette.BORDER}; border: none;"
        )
        insert_pos = self._sidebar_layout.count() - 1
        self._sidebar_layout.insertWidget(insert_pos, rule)

    def set_current_index(self, index: int) -> None:
        btn = self._group.button(index)
        if btn:
            btn.setChecked(True)

    def current_index(self) -> int:
        return self._group.checkedId()

    def _on_toggle(self, btn: QAbstractButton, checked: bool) -> None:
        if checked:
            idx = self._group.id(btn)
            self._stack.setCurrentIndex(idx)
            self.currentChanged.emit(idx)


# ─────────────────────────────────────────────────────────────────────────────
# 3. PillTabWidget
# ─────────────────────────────────────────────────────────────────────────────

class PillTabWidget(QWidget):
    """Horizontal pill-shaped tab bar sitting above a page stack."""

    currentChanged: Signal = Signal(int)
    _BAR_HEIGHT  = 36
    _BAR_RADIUS  = 8
    _TAB_RADIUS  = 6
    _BAR_PADDING = 4

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._group  = QButtonGroup(self)
        self._group.setExclusive(True)
        self._labels: list[str] = []

        self._bar = QWidget()
        self._bar.setFixedHeight(self._BAR_HEIGHT)
        self._bar.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._bar_layout = QHBoxLayout(self._bar)
        self._bar_layout.setContentsMargins(
            self._BAR_PADDING, self._BAR_PADDING,
            self._BAR_PADDING, self._BAR_PADDING,
        )
        self._bar_layout.setSpacing(2)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(
            f"background-color: {Palette.BASE}; border: none;"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        root.addWidget(self._bar)
        root.addWidget(self._stack, 1)

        self._group.buttonToggled.connect(self._on_toggle)

    def add_tab(self, label: str, page: QWidget) -> int:
        idx = len(self._labels)
        self._labels.append(label)

        btn = QToolButton()
        btn.setText(label)
        btn.setCheckable(True)
        btn.setFont(_roboto(10))
        btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                color: {Palette.TEXT_SECONDARY};
                border: none;
                border-radius: {self._TAB_RADIUS}px;
                font-family: "Roboto", "Segoe UI", Arial, sans-serif;
                font-size: 10pt;
                padding: 0px 12px;
            }}
            QToolButton:hover {{
                color: {Palette.TEXT_PRIMARY};
                background: rgba(255,255,255,0.04);
            }}
            QToolButton:checked {{
                background: {Palette.PRIMARY};
                color: {Palette.TEXT_ON_PRIMARY};
                font-weight: 600;
            }}
        """)
        self._group.addButton(btn, idx)
        self._bar_layout.addWidget(btn)
        self._stack.addWidget(page)

        if idx == 0:
            btn.setChecked(True)
        return idx

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self._bar.geometry()
        path = QPainterPath()
        path.addRoundedRect(
            rect.x(), rect.y(),
            rect.width(), rect.height(),
            self._BAR_RADIUS, self._BAR_RADIUS,
        )
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(Palette.SURFACE))
        p.drawPath(path)
        p.end()

    def set_current_index(self, index: int) -> None:
        btn = self._group.button(index)
        if btn:
            btn.setChecked(True)

    def current_index(self) -> int:
        return self._group.checkedId()

    def _on_toggle(self, btn: QAbstractButton, checked: bool) -> None:
        if checked:
            idx = self._group.id(btn)
            self._stack.setCurrentIndex(idx)
            self.currentChanged.emit(idx)


# ─────────────────────────────────────────────────────────────────────────────
# 4. UnderlineTabWidget  ← FIXED
# ─────────────────────────────────────────────────────────────────────────────

class UnderlineTabWidget(QWidget):
    """
    Horizontal tab bar with a sliding 2 px blue underline indicator.

    FIX: The indicator is no longer synced in add_tab() (where button
    geometry is still zero because the widget hasn't been shown yet).
    Instead it is deferred to showEvent() so button positions are final.
    resizeEvent also re-syncs without animation so it stays accurate.
    """

    currentChanged: Signal = Signal(int)

    _BAR_HEIGHT  = 40
    _INDICATOR_H = 2

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._group   = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: list[QToolButton] = []

        self._bar = QWidget()
        self._bar.setFixedHeight(self._BAR_HEIGHT)
        self._bar.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._bar_layout = QHBoxLayout(self._bar)
        self._bar_layout.setContentsMargins(0, 0, 0, 0)
        self._bar_layout.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(
            f"background-color: {Palette.BASE}; border: none;"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._bar)
        root.addWidget(self._stack, 1)

        self._indicator_x     = 0.0
        self._indicator_w     = 0.0
        # Indicator is invisible until first showEvent
        self._ready           = False

        self._indicator_anim  = QPropertyAnimation(
            self, b"_indicator_pos", self
        )
        self._indicator_anim.setDuration(200)
        self._indicator_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._group.buttonToggled.connect(self._on_toggle)

    # ── Indicator animation property ─────────────────────────────────

    def _get_indicator_pos(self) -> float:
        return self._indicator_x

    def _set_indicator_pos(self, x: float) -> None:
        self._indicator_x = x
        self.update()

    _indicator_pos = Property(float, _get_indicator_pos,
                               _set_indicator_pos)

    # ── Tab management ────────────────────────────────────────────────

    def add_tab(self, label: str, page: QWidget) -> int:
        idx = len(self._buttons)

        btn = QToolButton()
        btn.setText(label)
        btn.setCheckable(True)
        btn.setFont(_roboto(10))
        btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                color: {Palette.TEXT_SECONDARY};
                border: none;
                padding: 0px 16px;
                font-family: "Roboto", "Segoe UI", Arial, sans-serif;
                font-size: 10pt;
            }}
            QToolButton:hover {{
                color: {Palette.TEXT_PRIMARY};
            }}
            QToolButton:checked {{
                color: {Palette.PRIMARY};
                font-weight: 600;
            }}
        """)
        self._group.addButton(btn, idx)
        self._bar_layout.addWidget(btn)
        self._buttons.append(btn)
        self._stack.addWidget(page)

        if idx == 0:
            btn.setChecked(True)
            # Do NOT sync indicator here — geometry is 0 until shown

        return idx

    # ── Sync indicator ────────────────────────────────────────────────

    def _sync_indicator(self, animate: bool = True) -> None:
        """
        Calculate the indicator position from the checked button's
        current geometry.  Only called after the widget is visible so
        button widths and positions are finalised.
        """
        if not self._buttons:
            return

        idx = self._group.checkedId()
        if idx < 0 or idx >= len(self._buttons):
            return

        btn    = self._buttons[idx]
        bar_x  = self._bar.x()
        target = float(bar_x + btn.x())
        w      = float(btn.width())

        # Guard: if the button hasn't been laid out yet, skip
        if w <= 0:
            return

        self._indicator_w = w

        if animate and self._ready:
            self._indicator_anim.stop()
            self._indicator_anim.setStartValue(self._indicator_x)
            self._indicator_anim.setEndValue(target)
            self._indicator_anim.start()
        else:
            self._indicator_x = target
            self.update()

    # ── Qt events ─────────────────────────────────────────────────────

    def showEvent(self, event) -> None:  # noqa: N802
        """
        FIX: defer initial indicator sync to here — this is the first
        point at which all button geometries are finalised.
        """
        super().showEvent(event)
        if not self._ready:
            self._ready = True
            self._sync_indicator(animate=False)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._sync_indicator(animate=False)

    def _on_toggle(self, btn: QAbstractButton, checked: bool) -> None:
        if checked:
            idx = self._group.id(btn)
            self._stack.setCurrentIndex(idx)
            self._sync_indicator(animate=True)
            self.currentChanged.emit(idx)

    # ── Paint ─────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:  # noqa: N802
        if not self._ready:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bar_bottom = self._bar.y() + self._bar.height()

        # Bottom border
        pen = QPen(QColor(Palette.BORDER))
        pen.setWidth(1)
        p.setPen(pen)
        p.drawLine(0, bar_bottom, self.width(), bar_bottom)

        # Sliding blue indicator
        if self._indicator_w > 0:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(Palette.PRIMARY))
            p.drawRoundedRect(
                int(self._indicator_x),
                bar_bottom - self._INDICATOR_H,
                int(self._indicator_w),
                self._INDICATOR_H,
                1, 1,
            )

        p.end()

    # ── Public API ────────────────────────────────────────────────────

    def set_current_index(self, index: int) -> None:
        btn = self._group.button(index)
        if btn:
            btn.setChecked(True)

    def current_index(self) -> int:
        return self._group.checkedId()


# ─────────────────────────────────────────────────────────────────────────────
# 5. AccordionWidget
# ─────────────────────────────────────────────────────────────────────────────

class _AccordionSection(QWidget):
    _HEADER_H = 40

    def __init__(self, title: str, content: QWidget,
                 expanded: bool = False,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._expanded = expanded
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        self._header = QWidget(self)
        self._header.setFixedHeight(self._HEADER_H)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._header.setStyleSheet(
            f"background-color: {Palette.SURFACE}; border-radius: 6px;"
        )

        header_row = QHBoxLayout(self._header)
        header_row.setContentsMargins(14, 0, 14, 0)
        header_row.setSpacing(10)

        self._title_lbl = _label(title, size_pt=10, bold=True)
        self._chevron   = _label(
            "▾" if expanded else "▸",
            size_pt=11, color=Palette.PRIMARY,
        )
        self._chevron.setFixedWidth(16)
        header_row.addWidget(self._chevron)
        header_row.addWidget(self._title_lbl, 1)

        self._content_wrapper = QWidget(self)
        self._content_wrapper.setStyleSheet(
            f"background-color: {Palette.BASE}; border: none;"
        )
        wrapper_layout = QVBoxLayout(self._content_wrapper)
        wrapper_layout.setContentsMargins(0, 4, 0, 4)
        wrapper_layout.setSpacing(0)
        wrapper_layout.addWidget(content)

        self._content_wrapper.setMaximumHeight(
            self._content_wrapper.sizeHint().height() if expanded else 0
        )

        self._anim = QPropertyAnimation(
            self._content_wrapper, b"maximumHeight", self
        )
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._header)
        root.addWidget(self._content_wrapper)

        self._header.mousePressEvent = (  # type: ignore[method-assign]
            lambda e: self.toggle()
        )

    def toggle(self) -> None:
        self.set_expanded(not self._expanded)

    def set_expanded(self, expanded: bool) -> None:
        if expanded == self._expanded:
            return
        self._expanded = expanded
        self._chevron.setText("▾" if expanded else "▸")
        full_h = self._content_wrapper.sizeHint().height()
        self._anim.stop()
        self._anim.setStartValue(self._content_wrapper.maximumHeight())
        self._anim.setEndValue(full_h if expanded else 0)
        self._anim.start()

    def is_expanded(self) -> bool:
        return self._expanded

    def enterEvent(self, _event: QEnterEvent) -> None:  # noqa: N802
        self._header.setStyleSheet(
            f"background-color: {Palette.ELEVATED}; border-radius: 6px;"
        )

    def leaveEvent(self, _event) -> None:  # noqa: N802
        self._header.setStyleSheet(
            f"background-color: {Palette.SURFACE}; border-radius: 6px;"
        )


class AccordionWidget(QWidget):
    """Vertical stack of collapsible sections."""

    sectionToggled: Signal = Signal(int, bool)

    def __init__(self, exclusive: bool = False,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._exclusive = exclusive
        self._sections: list[_AccordionSection] = []

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(4)
        self._root.addStretch()

    def add_section(self, title: str, content: QWidget,
                    expanded: bool = False) -> int:
        idx     = len(self._sections)
        section = _AccordionSection(title, content, expanded, self)

        def _toggle(s=section, i=idx):
            if self._exclusive and not s.is_expanded():
                for j, other in enumerate(self._sections):
                    if j != i and other.is_expanded():
                        other.set_expanded(False)
                        self.sectionToggled.emit(j, False)
            s.toggle()
            self.sectionToggled.emit(i, s.is_expanded())

        section._header.mousePressEvent = (  # type: ignore[method-assign]
            lambda e: _toggle()
        )
        self._root.insertWidget(self._root.count() - 1, section)
        self._sections.append(section)
        return idx

    def set_expanded(self, index: int, expanded: bool) -> None:
        if 0 <= index < len(self._sections):
            self._sections[index].set_expanded(expanded)

    def is_expanded(self, index: int) -> bool:
        if 0 <= index < len(self._sections):
            return self._sections[index].is_expanded()
        return False


# ───────────────────────────────────────��─────────────────────────────────────
# 6. SplitterWidget
# ─────────────────────────────────────────────────────────────────────────────

class SplitterWidget(QSplitter):
    """Two-pane resizable splitter with a themed handle."""

    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal,
                 parent: QWidget | None = None) -> None:
        super().__init__(orientation, parent)
        self.setHandleWidth(4)
        self.setChildrenCollapsible(False)
        self.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {Palette.BORDER};
            }}
            QSplitter::handle:hover {{
                background-color: {Palette.PRIMARY};
            }}
            QSplitter::handle:horizontal {{ width: 4px; }}
            QSplitter::handle:vertical   {{ height: 4px; }}
        """)

    def add_pane(self, widget: QWidget, stretch: int = 1) -> None:
        self.addWidget(widget)
        self.setStretchFactor(self.count() - 1, stretch)

    def set_sizes(self, sizes: list[int]) -> None:
        self.setSizes(sizes)


# ─────────────────────────────────────────────────────────────────────────────
# 7. StackedWidget
# ─────────────────────────────────────────────────────────────────────────────

class StackedWidget(QWidget):
    """Animated page switcher (fade / slide_left / slide_right / none)."""

    currentChanged: Signal = Signal(int)
    _DURATION = 280

    def __init__(self, transition: str = "fade",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._transition = transition
        self._pages:     list[QWidget] = []
        self._current:   int           = -1
        self._animating: bool          = False

        self._stack = QStackedWidget(self)
        self._stack.setStyleSheet(
            f"background-color: {Palette.BASE}; border: none;"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._stack)

    def add_page(self, page: QWidget) -> int:
        idx = self._stack.addWidget(page)
        self._pages.append(page)
        if self._current == -1:
            self._current = 0
            self._stack.setCurrentIndex(0)
        return idx

    def set_current_index(self, index: int,
                          transition: str | None = None) -> None:
        if index == self._current or self._animating:
            return
        mode = transition or self._transition
        prev, self._current = self._current, index

        if mode == "none" or prev < 0:
            self._stack.setCurrentIndex(index)
            self.currentChanged.emit(index)
            return

        old_page = self._stack.widget(prev)
        new_page = self._stack.widget(index)

        if mode == "fade":
            self._fade(old_page, new_page, index)
        elif mode in ("slide_left", "slide_right"):
            self._slide(old_page, new_page, index,
                        left=mode == "slide_left")
        else:
            self._stack.setCurrentIndex(index)
            self.currentChanged.emit(index)

    def current_index(self) -> int:
        return self._current

    def _fade(self, old: QWidget, new: QWidget, idx: int) -> None:
        self._animating = True
        self._stack.setCurrentIndex(idx)
        fx   = QGraphicsOpacityEffect(new)
        new.setGraphicsEffect(fx)
        anim = QPropertyAnimation(fx, b"opacity", self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(self._DURATION)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _done():
            new.setGraphicsEffect(None)
            self._animating = False
            self.currentChanged.emit(idx)

        anim.finished.connect(_done)
        anim.start()

    def _slide(self, old: QWidget, new: QWidget,
               idx: int, left: bool) -> None:
        self._animating = True
        w = self._stack.width()
        new.setParent(self._stack)
        new.show()
        new.raise_()
        start_x = w if left else -w
        new.move(start_x, 0)
        new.resize(old.size())

        grp     = QParallelAnimationGroup(self)
        anim_old = QPropertyAnimation(old, b"pos", self)
        anim_old.setStartValue(QPoint(0, 0))
        anim_old.setEndValue(QPoint(-start_x, 0))
        anim_old.setDuration(self._DURATION)
        anim_old.setEasingCurve(QEasingCurve.Type.OutCubic)

        anim_new = QPropertyAnimation(new, b"pos", self)
        anim_new.setStartValue(QPoint(start_x, 0))
        anim_new.setEndValue(QPoint(0, 0))
        anim_new.setDuration(self._DURATION)
        anim_new.setEasingCurve(QEasingCurve.Type.OutCubic)

        grp.addAnimation(anim_old)
        grp.addAnimation(anim_new)

        def _done():
            self._stack.setCurrentIndex(idx)
            old.move(0, 0)
            self._animating = False
            self.currentChanged.emit(idx)

        grp.finished.connect(_done)
        grp.start()


# ─���───────────────────────────────────────────────────────────────────────────
# 8. DrawerWidget
# ─────────────────────────────────────────────────────────────────────────────

class DrawerWidget(QWidget):
    """Slide-in overlay panel anchored to an edge of a parent widget."""

    opened: Signal = Signal()
    closed: Signal = Signal()

    _DURATION    = 260
    _SCRIM_COLOR = QColor(0, 0, 0, 140)

    def __init__(self, parent: QWidget, edge: str = "left",
                 size: int = 280) -> None:
        super().__init__(parent)
        self._edge    = edge
        self._size    = size
        self._is_open = False

        self.setGeometry(parent.rect())
        self.hide()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                          False)

        self._scrim = QWidget(self)
        self._scrim.setGeometry(self.rect())
        self._scrim.setStyleSheet("background: transparent;")
        self._scrim.mousePressEvent = lambda e: self.close()  # type: ignore[method-assign]

        self._panel = QWidget(self)
        self._panel.setStyleSheet(
            f"background-color: {Palette.SURFACE}; border: none;"
        )
        self._panel_layout = QVBoxLayout(self._panel)
        self._panel_layout.setContentsMargins(16, 16, 16, 16)
        self._panel_layout.setSpacing(8)

        self._set_panel_geometry(open_state=False)

        self._anim = QPropertyAnimation(self._panel, b"geometry", self)
        self._anim.setDuration(self._DURATION)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._scrim_fx   = QGraphicsOpacityEffect(self._scrim)
        self._scrim.setGraphicsEffect(self._scrim_fx)
        self._scrim_anim = QPropertyAnimation(
            self._scrim_fx, b"opacity", self
        )
        self._scrim_anim.setDuration(self._DURATION)
        self._panel.raise_()

    def layout(self) -> QVBoxLayout:  # type: ignore[override]
        return self._panel_layout

    def _closed_rect(self) -> QRect:
        pw, ph, s = self.width(), self.height(), self._size
        if self._edge == "left":   return QRect(-s, 0, s, ph)
        if self._edge == "right":  return QRect(pw, 0, s, ph)
        if self._edge == "top":    return QRect(0, -s, pw, s)
        return QRect(0, ph, pw, s)

    def _open_rect(self) -> QRect:
        pw, ph, s = self.width(), self.height(), self._size
        if self._edge == "left":   return QRect(0, 0, s, ph)
        if self._edge == "right":  return QRect(pw - s, 0, s, ph)
        if self._edge == "top":    return QRect(0, 0, pw, s)
        return QRect(0, ph - s, pw, s)

    def _set_panel_geometry(self, open_state: bool) -> None:
        self._panel.setGeometry(
            self._open_rect() if open_state else self._closed_rect()
        )

    def open(self) -> None:
        if self._is_open:
            return
        self._is_open = True
        self.setGeometry(self.parent().rect())  # type: ignore[union-attr]
        self._scrim.setGeometry(self.rect())
        self._set_panel_geometry(open_state=False)
        self.show()
        self.raise_()

        self._anim.stop()
        self._anim.setStartValue(self._panel.geometry())
        self._anim.setEndValue(self._open_rect())
        self._anim.start()

        self._scrim_anim.stop()
        self._scrim_anim.setStartValue(0.0)
        self._scrim_anim.setEndValue(1.0)
        self._scrim_anim.start()
        self.opened.emit()

    def close(self) -> None:  # type: ignore[override]
        if not self._is_open:
            return
        self._is_open = False

        self._anim.stop()
        self._anim.setStartValue(self._panel.geometry())
        self._anim.setEndValue(self._closed_rect())
        self._anim.finished.connect(self.hide)
        self._anim.start()

        self._scrim_anim.stop()
        self._scrim_anim.setStartValue(1.0)
        self._scrim_anim.setEndValue(0.0)
        self._scrim_anim.start()
        self.closed.emit()

    def is_open(self) -> bool:
        return self._is_open

    def paintEvent(self, _event) -> None:  # noqa: N802
        if not self._is_open:
            return
        p = QPainter(self._scrim)
        p.fillRect(self._scrim.rect(), self._SCRIM_COLOR)
        p.end()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._scrim.setGeometry(self.rect())
        if self._is_open:
            self._set_panel_geometry(open_state=True)