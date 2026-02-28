"""
src/ui/widgets/line_edits.py
----------------------------
Custom QLineEdit widgets built on top of the dark theme defined in
src.ui.themes.theme.

Widgets provided:
  - BaseLineEdit        — Foundation widget; all others inherit from this.
  - PrimaryLineEdit     — Standard input with blue-accented focus ring.
  - SearchLineEdit      — Input with a leading search icon and clear button.
  - PasswordLineEdit    — Secure input with a show/hide toggle button.
  - LabeledLineEdit     — Floating-label input (label animates on focus/fill).
  - StatusLineEdit      — Inline validation with success / warning / error states.
"""

from __future__ import annotations

from PySide6.QtCore import (QEasingCurve, QPoint, QPropertyAnimation, QSize, Qt)
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QPainter)
from PySide6.QtWidgets import (QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
                               QLineEdit, QSizePolicy, QToolButton, QVBoxLayout,
                               QWidget)

from src.ui.themes.theme import Palette


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_icon_button(symbol: str, tooltip: str, parent: QWidget) -> QToolButton:
    """Create a small, transparent icon-only QToolButton with a text glyph."""
    btn = QToolButton(parent)
    btn.setText(symbol)
    btn.setToolTip(tooltip)
    btn.setFixedSize(QSize(28, 28))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    btn.setStyleSheet(f"""
        QToolButton {{
            background: transparent;
            border: none;
            color: {Palette.TEXT_SECONDARY};
            font-size: 14px;
        }}
        QToolButton:hover {{
            color: {Palette.PRIMARY};
        }}
    """)
    return btn


# ─────────────────────────────────────────────────────────────────────────────
# 1. BaseLineEdit
# ─────────────────────────────────────────────────────────────────────────────

class BaseLineEdit(QLineEdit):
    """
    Foundation for all custom line edits.

    Inherits the global stylesheet from theme.py and adds:
      - Consistent height & border-radius
      - Focus glow effect via QGraphicsDropShadowEffect
    """

    _BORDER_RADIUS = 6
    _HEIGHT = 38
    _PADDING_H = 12

    def __init__(self, placeholder: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(self._HEIGHT)
        self.setFont(QFont("Roboto", 10))

        # Focus glow effect
        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setBlurRadius(0)
        self._glow.setOffset(0, 0)
        self._glow.setColor(QColor(Palette.PRIMARY))
        self.setGraphicsEffect(self._glow)

        # Animation for glow on focus
        self._glow_anim = QPropertyAnimation(self._glow, b"blurRadius", self)
        self._glow_anim.setDuration(180)
        self._glow_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._apply_base_style()

    # ------------------------------------------------------------------
    def _apply_base_style(self) -> None:
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Palette.SURFACE};
                color: {Palette.TEXT_PRIMARY};
                border: 1.5px solid {Palette.BORDER};
                border-radius: {self._BORDER_RADIUS}px;
                padding: 0px {self._PADDING_H}px;
                font-family: "Roboto", "Segoe UI", Arial, sans-serif;
                font-size: 10pt;
                selection-background-color: {Palette.SELECTION_BG};
                selection-color: {Palette.SELECTION_FG};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {Palette.PRIMARY};
                background-color: {Palette.ELEVATED};
            }}
            QLineEdit:hover:!focus {{
                border: 1.5px solid {Palette.BORDER_MUTED};
            }}
            QLineEdit:disabled {{
                background-color: {Palette.BASE};
                color: {Palette.TEXT_DISABLED};
                border-color: {Palette.BORDER};
            }}
        """)

    # ------------------------------------------------------------------
    def focusInEvent(self, event) -> None:  # noqa: N802
        super().focusInEvent(event)
        self._glow_anim.stop()
        self._glow_anim.setStartValue(self._glow.blurRadius())
        self._glow_anim.setEndValue(10)
        self._glow_anim.start()

    def focusOutEvent(self, event) -> None:  # noqa: N802
        super().focusOutEvent(event)
        self._glow_anim.stop()
        self._glow_anim.setStartValue(self._glow.blurRadius())
        self._glow_anim.setEndValue(0)
        self._glow_anim.start()


# ─────────────────────────────────────────────────────────────────────────────
# 2. PrimaryLineEdit
# ─────────────────────────────────────────────────────────────────────────────

class PrimaryLineEdit(BaseLineEdit):
    """
    Standard single-line input with an optional leading label/icon string
    rendered inside the left padding.

    Example::

        edit = PrimaryLineEdit(placeholder="Email address", leading_text="@")
    """

    def __init__(
            self,
            placeholder: str = "",
            leading_text: str = "",
            parent: QWidget | None = None,
    ) -> None:
        super().__init__(placeholder, parent)
        self._leading_text = leading_text

        if leading_text:
            fm = QFontMetrics(self.font())
            w = fm.horizontalAdvance(leading_text) + 24
            self.setTextMargins(w, 0, 0, 0)

    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if not self._leading_text:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        font = QFont("Roboto", 10)
        painter.setFont(font)
        painter.setPen(QColor(Palette.TEXT_SECONDARY))

        fm = QFontMetrics(font)
        text_height = fm.height()
        y = (self.height() - text_height) // 2 + fm.ascent()
        painter.drawText(QPoint(10, y), self._leading_text)
        painter.end()


# ─────────────────────────────────────────────────────────────────────────────
# 3. SearchLineEdit
# ──────────────────────────────────────────────────────────────────────────���──

class SearchLineEdit(BaseLineEdit):
    """
    Search-oriented input with:
      - A leading 🔍 icon (Unicode, no asset required)
      - A ✕ clear button that appears only when there is text
      - Keyboard shortcut: Escape clears and de-focuses

    Example::

        search = SearchLineEdit(placeholder="Search…")
        search.textChanged.connect(my_filter_fn)
    """

    def __init__(self, placeholder: str = "Search…",
                 parent: QWidget | None = None) -> None:
        super().__init__(placeholder, parent)

        # Reserve left space for search icon
        self.setTextMargins(30, 0, 32, 0)

        # Clear button (hidden until text is entered)
        self._clear_btn = _make_icon_button("✕", "Clear", self)
        self._clear_btn.hide()
        self._clear_btn.clicked.connect(self.clear)
        self._clear_btn.clicked.connect(self.clearFocus)

        self.textChanged.connect(self._on_text_changed)

    # ------------------------------------------------------------------
    def _on_text_changed(self, text: str) -> None:
        self._clear_btn.setVisible(bool(text))
        self._position_clear_btn()

    def _position_clear_btn(self) -> None:
        btn_size = self._clear_btn.size()
        x = self.width() - btn_size.width() - 4
        y = (self.height() - btn_size.height()) // 2
        self._clear_btn.move(x, y)

    # ------------------------------------------------------------------
    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._position_clear_btn()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.clear()
            self.clearFocus()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        font = QFont("Roboto", 12)
        painter.setFont(font)
        color = (
            QColor(Palette.PRIMARY)
            if self.hasFocus()
            else QColor(Palette.TEXT_SECONDARY)
        )
        painter.setPen(color)

        fm = QFontMetrics(font)
        y = (self.height() - fm.height()) // 2 + fm.ascent()
        painter.drawText(QPoint(8, y), "🔍")
        painter.end()


# ���────────────────────────────────────────────────────────────────────────────
# 4. PasswordLineEdit
# ─────────────────────────────────────────────────────────────────────────────

class PasswordLineEdit(BaseLineEdit):
    """
    Password input with a show/hide toggle button on the right.

    The toggle cycles between QLineEdit.Password and QLineEdit.Normal echo modes.

    Example::

        pwd = PasswordLineEdit(placeholder="Password")
    """

    _EYE_OPEN = "👁"
    _EYE_CLOSED = "🚫"

    def __init__(self, placeholder: str = "Password",
                 parent: QWidget | None = None) -> None:
        super().__init__(placeholder, parent)
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setTextMargins(0, 0, 34, 0)

        self._toggle_btn = _make_icon_button(self._EYE_OPEN, "Show password", self)
        self._toggle_btn.clicked.connect(self._toggle_visibility)

        self._position_toggle_btn()

    # ------------------------------------------------------------------
    def _toggle_visibility(self) -> None:
        if self.echoMode() == QLineEdit.EchoMode.Password:
            self.setEchoMode(QLineEdit.EchoMode.Normal)
            self._toggle_btn.setToolTip("Hide password")
            self._toggle_btn.setText(self._EYE_CLOSED)
        else:
            self.setEchoMode(QLineEdit.EchoMode.Password)
            self._toggle_btn.setToolTip("Show password")
            self._toggle_btn.setText(self._EYE_OPEN)

    def _position_toggle_btn(self) -> None:
        btn_size = self._toggle_btn.size()
        x = self.width() - btn_size.width() - 4
        y = (self.height() - btn_size.height()) // 2
        self._toggle_btn.move(x, y)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._position_toggle_btn()


# ─────────────────────────────────────────────────────────────────────────────
# 5. LabeledLineEdit  ← FIXED
# ─────────────────────────────────────────────────────────────────────────────

class LabeledLineEdit(QWidget):
    """
    A compound widget that wraps a BaseLineEdit with a floating label.

    The label animates from inside the field (resting/placeholder position)
    to straddling the top border when focused or filled — exactly like a
    Material Design outlined text field. A matching background chip is drawn
    behind the label text so it cleanly occludes the border beneath it.

    Access the inner field via `.field`.

    Example::

        widget = LabeledLineEdit(label="Full Name")
        layout.addWidget(widget)
        value = widget.field.text()
    """

    # Extra top margin so the floated label has room to live above the field
    _TOP_MARGIN = 10  # px of space reserved above the field for the floated label
    _LABEL_IDLE_SIZE = 10  # pt — matches body text
    _LABEL_FLOAT_SIZE = 8  # pt — smaller when floated
    _LABEL_LEFT_OFFSET = 10  # px — horizontal indent of the label (aligns with text)
    _LABEL_BG_PAD_H = 4  # px — horizontal padding of the background chip
    _ANIM_DURATION = 160  # ms

    def __init__(
            self,
            label: str = "",
            placeholder: str = "",
            parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._label_text = label
        self._floated = False

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # ── Field ────────────────────────────────────────────────────────
        self.field = BaseLineEdit(placeholder, self)

        # ── Root layout: top margin + field ─────────────────────────────
        root = QVBoxLayout(self)
        root.setContentsMargins(0, self._TOP_MARGIN, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.field)

        # ── Floating label (child of self, not the field) ────────────────
        # Being a direct child of the container lets it overlap the field's
        # top border freely.
        self._label = QLabel(label, self)
        self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._label.setFont(QFont("Roboto", self._LABEL_IDLE_SIZE))
        self._label.adjustSize()
        # Start: visually inside the field (idle position)
        self._label.move(self._LABEL_LEFT_OFFSET, self._idle_y())
        # Ensure it renders on top of the field's border
        self._label.raise_()
        self._set_label_idle_style()

        # ── Animations ───────────────────────────────────────────────────
        self._pos_anim = QPropertyAnimation(self._label, b"pos", self)
        self._pos_anim.setDuration(self._ANIM_DURATION)
        self._pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # ── Wire up field events ─────────────────────────────────────────
        self.field.focusInEvent = self._on_focus_in  # type: ignore[method-assign]
        self.field.focusOutEvent = self._on_focus_out  # type: ignore[method-assign]
        self.field.textChanged.connect(self._on_text_changed)

    # ── Geometry helpers ─────────────────────────────────────────────────

    def _field_top(self) -> int:
        """Absolute Y of the field's top edge within this widget."""
        return self._TOP_MARGIN

    def _idle_y(self) -> int:
        """
        Y position so the label sits vertically centred inside the field
        (placeholder position).
        """
        field_h = self.field.minimumHeight()
        lbl_h = self._label.sizeHint().height()
        return self._field_top() + (field_h - lbl_h) // 2

    def _float_y(self) -> int:
        """
        Y position so the label straddles the field's top border:
        centred on that border line.
        """
        lbl_h = self._label.sizeHint().height()
        # field_top is the border line; centre the label on it
        return self._field_top() - lbl_h // 2

    # ── Style helpers ────────────────────────────────────────────────────

    def _set_label_idle_style(self) -> None:
        """Label looks like placeholder text — no visible background."""
        self._label.setFont(QFont("Roboto", self._LABEL_IDLE_SIZE))
        self._label.setStyleSheet(
            f"color: {Palette.TEXT_SECONDARY};"
            "background: transparent;"
            "border: none;"
            "padding: 0px;"
        )
        self._label.adjustSize()

    def _set_label_float_style(self, focused: bool) -> None:
        """
        Label shrinks, turns blue when focused (grey when filled but blurred),
        and gets a solid background chip so it covers the border beneath it.

        The background colour matches what the field's background will be:
          - focused  → Palette.ELEVATED  (field's :focus background)
          - filled   → Palette.SURFACE   (field's normal background)
        """
        color = Palette.PRIMARY if focused else Palette.TEXT_SECONDARY
        bg = Palette.ELEVATED if focused else Palette.SURFACE
        pad = self._LABEL_BG_PAD_H
        self._label.setFont(QFont("Roboto", self._LABEL_FLOAT_SIZE))
        self._label.setStyleSheet(
            f"color: {color};"
            f"background-color: {bg};"
            "border: none;"
            f"padding: 0px {pad}px;"
            "border-radius: 2px;"
        )
        self._label.adjustSize()

    # ── Float / sink ─────────────────────────────────────────────────────

    def _float_label(self, focused: bool) -> None:
        if self._floated and focused:
            # Already floated — just update the colour/bg for focus state
            self._set_label_float_style(focused=True)
            return
        if self._floated:
            return

        self._floated = True
        self._set_label_float_style(focused=focused)

        target_y = self._float_y()
        self._pos_anim.stop()
        self._pos_anim.setStartValue(self._label.pos())
        # Keep X at the same left indent plus chip padding compensation
        target_x = self._LABEL_LEFT_OFFSET - self._LABEL_BG_PAD_H
        self._pos_anim.setEndValue(QPoint(target_x, target_y))
        self._pos_anim.start()

    def _sink_label(self) -> None:
        if not self._floated:
            return
        self._floated = False
        self._set_label_idle_style()

        self._pos_anim.stop()
        self._pos_anim.setStartValue(self._label.pos())
        self._pos_anim.setEndValue(QPoint(self._LABEL_LEFT_OFFSET, self._idle_y()))
        self._pos_anim.start()

    # ── Event hooks ──────────────────────────────────────────────────────

    def _on_focus_in(self, event) -> None:
        QLineEdit.focusInEvent(self.field, event)
        self._float_label(focused=True)
        if self._floated:
            # Refresh colour to PRIMARY when re-focused while already floated
            self._set_label_float_style(focused=True)

    def _on_focus_out(self, event) -> None:
        QLineEdit.focusOutEvent(self.field, event)
        if self.field.text():
            # Stay floated but switch to unfocused colour + surface background
            self._set_label_float_style(focused=False)
        else:
            self._sink_label()

    def _on_text_changed(self, text: str) -> None:
        if text and not self._floated:
            self._float_label(focused=self.field.hasFocus())

    # ── Resize ───────────────────────────────────────────────────────────

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        # Re-sync idle position if not yet floated
        if not self._floated:
            self._label.move(self._LABEL_LEFT_OFFSET, self._idle_y())
        self._label.raise_()


# ─────────────────────────────────────────────────────────────────────────────
# 6. StatusLineEdit
# ─────────────────────────────────────────────────────────────────────────────

class _Status:
    NONE = "none"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


_STATUS_COLORS: dict[str, str] = {
    _Status.NONE: Palette.BORDER,
    _Status.SUCCESS: Palette.SUCCESS,
    _Status.WARNING: Palette.WARNING,
    _Status.ERROR: Palette.ERROR,
}

_STATUS_ICONS: dict[str, str] = {
    _Status.NONE: "",
    _Status.SUCCESS: "✔",
    _Status.WARNING: "⚠",
    _Status.ERROR: "✖",
}


class StatusLineEdit(QWidget):
    """
    A line edit with inline validation feedback.

    Call the helper methods to set state:
      - `set_success(message)`
      - `set_warning(message)`
      - `set_error(message)`
      - `set_normal()`

    Access the inner field via `.field`.

    Example::

        email_input = StatusLineEdit(placeholder="Email address")
        email_input.set_error("Invalid email format")
        email_input.set_success("Looks good!")
        email_input.set_normal()
    """

    def __init__(
            self,
            placeholder: str = "",
            parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._status = _Status.NONE

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # ── Field ────────────────────────────────────────────────────
        self.field = BaseLineEdit(placeholder, self)

        # ── Status row: icon + message ───────────────────────────────
        self._icon_label = QLabel("", self)
        self._icon_label.setFixedWidth(18)
        self._icon_label.setFont(QFont("Roboto", 10))
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._msg_label = QLabel("", self)
        self._msg_label.setFont(QFont("Roboto", 8))
        self._msg_label.setStyleSheet(
            f"color: {Palette.TEXT_SECONDARY}; background: transparent; border: none;"
        )

        status_row = QHBoxLayout()
        status_row.setContentsMargins(4, 2, 0, 0)
        status_row.setSpacing(4)
        status_row.addWidget(self._icon_label)
        status_row.addWidget(self._msg_label)
        status_row.addStretch()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.field)
        root.addLayout(status_row)

    # ------------------------------------------------------------------
    def _apply_status(self, status: str, message: str) -> None:
        self._status = status
        color = _STATUS_COLORS[status]
        icon = _STATUS_ICONS[status]

        self.field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Palette.SURFACE};
                color: {Palette.TEXT_PRIMARY};
                border: 1.5px solid {color};
                border-radius: {BaseLineEdit._BORDER_RADIUS}px;
                padding: 0px {BaseLineEdit._PADDING_H}px;
                font-family: "Roboto", "Segoe UI", Arial, sans-serif;
                font-size: 10pt;
                selection-background-color: {Palette.SELECTION_BG};
                selection-color: {Palette.SELECTION_FG};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {color};
                background-color: {Palette.ELEVATED};
            }}
        """)

        self._icon_label.setText(icon)
        self._icon_label.setStyleSheet(
            f"color: {color}; background: transparent; border: none;"
        )
        self._msg_label.setText(message)
        self._msg_label.setStyleSheet(
            f"color: {color}; background: transparent; border: none; font-size: 8pt;"
        )

    # ── Public API ───────────────────────────────────────────────────
    def set_normal(self) -> None:
        """Reset to default state with no message."""
        self._apply_status(_Status.NONE, "")
        self.field._apply_base_style()

    def set_success(self, message: str = "Looks good!") -> None:
        self._apply_status(_Status.SUCCESS, message)

    def set_warning(self, message: str = "Double-check this field.") -> None:
        self._apply_status(_Status.WARNING, message)

    def set_error(self, message: str = "This field has an error.") -> None:
        self._apply_status(_Status.ERROR, message)

    @property
    def text(self) -> str:
        return self.field.text()
