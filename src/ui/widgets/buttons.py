"""
src/ui/widgets/buttons.py
-------------------------
Custom button widgets built on top of the dark theme defined in
src.ui.themes.theme.

Widgets provided:
  - BaseButton          — Foundation; all others inherit from this.
  - PrimaryButton       — Solid filled blue CTA button.
  - SecondaryButton     — Outlined blue button.
  - GhostButton         — Transparent, text-only button.
  - DangerButton        — Solid red destructive-action button.
  - IconButton          — Square icon-only button (no label).
  - IconTextButton      — Leading icon glyph + label.
  - ToggleButton        — Stateful on/off button, emits toggled(bool).
  - SegmentedButton     — Mutually exclusive inline button group.
  - LoadingButton       — Any button variant with a built-in spinner state.
  - FloatingActionButton— Circular FAB with drop shadow.
"""

from __future__ import annotations

import math

from PySide6.QtCore    import (Qt, Signal, QSize, QRect,
                                QPropertyAnimation, QEasingCurve,
                                Property, QTimer)
from PySide6.QtGui     import (QColor, QPainter, QPainterPath, QPen,
                                QFont, QFontMetrics, QMouseEvent,
                                QEnterEvent)
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QSizePolicy,
                                QButtonGroup, QAbstractButton,
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


# ─────────────────────────────────────────────────────────────────────────────
# 1. BaseButton
# ─────────────────────────────────────────────────────────────────────────────

class BaseButton(QAbstractButton):
    """
    Foundation button painted entirely via paintEvent.

    FIX — glow / shadow ownership
    ──────────────────────────────
    The previous version stored the QGraphicsDropShadowEffect as self._glow
    and used a QPropertyAnimation whose target was that C++ object.
    Qt takes ownership of any object passed to setGraphicsEffect(), so when
    the widget was repainted, reparented, or a second effect was set, Qt
    deleted the C++ peer while Python (and the animation) still held a
    dangling reference → RuntimeError.

    Solution: the glow intensity is tracked as a pure-Python float property
    (_glow_value).  A QPropertyAnimation drives that float.  In paintEvent
    we call setGraphicsEffect() with a *fresh* effect built from the current
    float — but ONLY when the value has actually changed, and we immediately
    clear our Python reference afterwards so we never own the object Qt just
    took.  This keeps the animation target (self) alive for the full widget
    lifetime and removes all dangling C++ pointer risk.
    """

    # ���─ Appearance tokens ─────────────────────────────────────────────
    _bg_idle      = Palette.PRIMARY
    _bg_hover     = Palette.PRIMARY_HOVER
    _bg_pressed   = Palette.PRIMARY_PRESSED
    _bg_disabled  = Palette.ELEVATED

    _fg_idle      = Palette.TEXT_ON_PRIMARY
    _fg_disabled  = Palette.TEXT_DISABLED

    _border_color = "transparent"
    _border_width = 0.0

    _radius       = 6
    _glow_color   = Palette.PRIMARY
    _glow_radius  = 14

    _HEIGHT       = 36
    _H_PADDING    = 20
    _FONT_SIZE    = 10
    _FONT_BOLD    = True

    def __init__(self, label: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setText(label)
        self.setFont(_roboto(self._FONT_SIZE, self._FONT_BOLD))
        self.setFixedHeight(self._HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._hovered  = False
        self._pressed  = False

        # ── Ripple ──────���─────────────────────────────────────────────
        self._ripple_x       = 0.0
        self._ripple_y       = 0.0
        self._ripple_radius  = 0.0
        self._ripple_opacity = 0.0

        self._ripple_anim = QPropertyAnimation(self, b"_ripple_r", self)
        self._ripple_anim.setDuration(380)
        self._ripple_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._ripple_fade = QPropertyAnimation(self, b"_ripple_op", self)
        self._ripple_fade.setDuration(380)
        self._ripple_fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        # ── Glow — pure Python float, NOT a C++ object ────────────────
        # The animation targets self (always alive), never the effect.
        self._glow_value: float = 0.0

        self._glow_anim = QPropertyAnimation(self, b"_glow_v", self)
        self._glow_anim.setDuration(160)
        self._glow_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._glow_anim.valueChanged.connect(self._on_glow_changed)

    # ── Glow Qt property (targets self — always safe) ─────────────────

    def _get_glow_v(self) -> float:
        return self._glow_value

    def _set_glow_v(self, v: float) -> None:
        self._glow_value = v
        # Apply a fresh effect each frame only if glow is meaningful
        self._apply_glow_effect(v)

    _glow_v = Property(float, _get_glow_v, _set_glow_v)

    def _on_glow_changed(self, _value) -> None:
        """Slot connected to valueChanged for explicit repaints."""
        self.update()

    def _apply_glow_effect(self, radius: float) -> None:
        """
        Build and install a shadow effect with the given blur radius.
        We deliberately do NOT store the returned object — Qt owns it
        from the moment setGraphicsEffect() is called.
        """
        if radius <= 0.5:
            # Clear the effect entirely when glow fades to zero
            self.setGraphicsEffect(None)
            return
        fx = QGraphicsDropShadowEffect()
        fx.setBlurRadius(radius)
        fx.setOffset(0, 0)
        fx.setColor(QColor(self._glow_color))
        self.setGraphicsEffect(fx)
        # Do NOT keep a reference — fx is now owned by Qt

    # ── Ripple Qt properties ──────────────────────────────────────────

    def _get_ripple_r(self) -> float:
        return self._ripple_radius

    def _set_ripple_r(self, r: float) -> None:
        self._ripple_radius = r
        self.update()

    _ripple_r = Property(float, _get_ripple_r, _set_ripple_r)

    def _get_ripple_op(self) -> float:
        return self._ripple_opacity

    def _set_ripple_op(self, op: float) -> None:
        self._ripple_opacity = op
        self.update()

    _ripple_op = Property(float, _get_ripple_op, _set_ripple_op)

    # ── Size hint ─────────────────────────────────────────────────────

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        w  = fm.horizontalAdvance(self.text()) + self._H_PADDING * 2
        return QSize(max(w, 80), self._HEIGHT)

    # ── Paint ─────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = self.width(), self.height()

        # Background
        if not self.isEnabled():
            bg = QColor(self._bg_disabled)
        elif self._pressed:
            bg = QColor(self._bg_pressed)
        elif self._hovered:
            bg = QColor(self._bg_hover)
        else:
            bg = QColor(self._bg_idle)

        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, self._radius, self._radius)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawPath(path)

        # Border
        if self._border_width > 0:
            pen = QPen(QColor(self._border_color))
            pen.setWidthF(self._border_width)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)

        # Ripple
        if self._ripple_radius > 0 and self._ripple_opacity > 0:
            p.setClipPath(path)
            ripple_color = QColor(255, 255, 255,
                                  int(self._ripple_opacity * 255))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(ripple_color)
            p.drawEllipse(
                int(self._ripple_x - self._ripple_radius),
                int(self._ripple_y - self._ripple_radius),
                int(self._ripple_radius * 2),
                int(self._ripple_radius * 2),
            )
            p.setClipping(False)

        # Focus ring
        if self.hasFocus() and self.isEnabled():
            focus_pen = QPen(QColor(Palette.PRIMARY))
            focus_pen.setWidthF(2.0)
            p.setPen(focus_pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            focus_path = QPainterPath()
            focus_path.addRoundedRect(
                1.5, 1.5, w - 3, h - 3,
                self._radius, self._radius,
            )
            p.drawPath(focus_path)

        # Label
        fg = QColor(self._fg_disabled if not self.isEnabled()
                    else self._fg_idle)
        p.setPen(fg)
        p.setFont(self.font())
        p.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter,
                   self.text())
        p.end()

    # ── Events ────────────────────────────────────────────────────────

    def enterEvent(self, event: QEnterEvent) -> None:  # noqa: N802
        self._hovered = True
        self._animate_glow(self._glow_radius)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hovered = False
        self._animate_glow(0)
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self._start_ripple(event.position().x(), event.position().y())
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def focusInEvent(self, event) -> None:  # noqa: N802
        self._animate_glow(self._glow_radius)
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:  # noqa: N802
        if not self._hovered:
            self._animate_glow(0)
        self.update()
        super().focusOutEvent(event)

    # ── Ripple helpers ────────────────────────────────────────────────

    def _start_ripple(self, x: float, y: float) -> None:
        self._ripple_x = x
        self._ripple_y = y
        max_r = math.hypot(max(x, self.width() - x),
                           max(y, self.height() - y))

        self._ripple_anim.stop()
        self._ripple_anim.setStartValue(0.0)
        self._ripple_anim.setEndValue(max_r)
        self._ripple_anim.start()

        self._ripple_fade.stop()
        self._ripple_fade.setStartValue(0.22)
        self._ripple_fade.setEndValue(0.0)
        self._ripple_fade.start()

    # ── Glow helpers ─────────────────────────────────���────────────────

    def _animate_glow(self, target: float) -> None:
        self._glow_anim.stop()
        self._glow_anim.setStartValue(self._glow_value)
        self._glow_anim.setEndValue(float(target))
        self._glow_anim.start()


# ─────────────────────────────────────────────────────────────────────────────
# 2. PrimaryButton
# ─────────────────────────────────────────────────────────────────────────────

class PrimaryButton(BaseButton):
    """
    Solid filled blue call-to-action button.

    Usage::

        btn = PrimaryButton("Save Changes")
        btn.clicked.connect(on_save)
    """

    _bg_idle     = Palette.PRIMARY
    _bg_hover    = Palette.PRIMARY_HOVER
    _bg_pressed  = Palette.PRIMARY_PRESSED
    _bg_disabled = Palette.ELEVATED
    _fg_idle     = Palette.TEXT_ON_PRIMARY
    _fg_disabled = Palette.TEXT_DISABLED
    _glow_color  = Palette.PRIMARY


# ─────────────────────────────────────────────────────────────────────────────
# 3. SecondaryButton
# ─────────────────────────────────────────────────────────────────────────────

class SecondaryButton(BaseButton):
    """
    Outlined blue button for secondary actions.

    Usage::

        btn = SecondaryButton("Cancel")
        btn.clicked.connect(on_cancel)
    """

    _bg_idle      = "transparent"
    _bg_hover     = "rgba(41,121,255,0.10)"
    _bg_pressed   = "rgba(41,121,255,0.18)"
    _bg_disabled  = "transparent"
    _fg_idle      = Palette.PRIMARY
    _fg_disabled  = Palette.TEXT_DISABLED
    _border_color = Palette.PRIMARY
    _border_width = 1.5
    _glow_color   = Palette.PRIMARY

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, self._radius, self._radius)

        # Background
        if not self.isEnabled():
            bg = QColor(0, 0, 0, 0)
        elif self._pressed:
            bg = QColor(41, 121, 255, 46)
        elif self._hovered:
            bg = QColor(41, 121, 255, 26)
        else:
            bg = QColor(0, 0, 0, 0)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawPath(path)

        # Border
        border_color = (
            QColor(Palette.TEXT_DISABLED)
            if not self.isEnabled()
            else QColor(Palette.PRIMARY_HOVER
                        if self._hovered else Palette.PRIMARY)
        )
        pen = QPen(border_color)
        pen.setWidthF(1.5)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        # Ripple
        if self._ripple_radius > 0 and self._ripple_opacity > 0:
            p.setClipPath(path)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(41, 121, 255,
                               int(self._ripple_opacity * 180)))
            p.drawEllipse(
                int(self._ripple_x - self._ripple_radius),
                int(self._ripple_y - self._ripple_radius),
                int(self._ripple_radius * 2),
                int(self._ripple_radius * 2),
            )
            p.setClipping(False)

        # Focus ring
        if self.hasFocus() and self.isEnabled():
            fp = QPen(QColor(Palette.PRIMARY))
            fp.setWidthF(2.0)
            p.setPen(fp)
            p.setBrush(Qt.BrushStyle.NoBrush)
            fr = QPainterPath()
            fr.addRoundedRect(1.5, 1.5, w - 3, h - 3,
                              self._radius, self._radius)
            p.drawPath(fr)

        # Text
        fg = (QColor(Palette.TEXT_DISABLED) if not self.isEnabled()
              else QColor(Palette.PRIMARY_HOVER
                          if self._hovered else Palette.PRIMARY))
        p.setPen(fg)
        p.setFont(self.font())
        p.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter,
                   self.text())
        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# 4. GhostButton
# ─────────────────────────────────────────────────────────────────────────────

class GhostButton(BaseButton):
    """
    Transparent text-only button for low-emphasis actions.

    Usage::

        btn = GhostButton("Learn More")
        btn.clicked.connect(open_docs)
    """

    _bg_idle     = "transparent"
    _bg_hover    = Palette.ELEVATED
    _bg_pressed  = Palette.BORDER
    _bg_disabled = "transparent"
    _fg_idle     = Palette.TEXT_PRIMARY
    _fg_disabled = Palette.TEXT_DISABLED
    _glow_color  = Palette.PRIMARY
    _glow_radius = 8


# ─────────────────────────────────────────────────────────────────────────────
# 5. DangerButton
# ─────────────────────────────────────────────────────────────────────────────

class DangerButton(BaseButton):
    """
    Solid red button for destructive / irreversible actions.

    Usage::

        btn = DangerButton("Delete Account")
        btn.clicked.connect(on_delete)
    """

    _bg_idle     = Palette.ERROR
    _bg_hover    = "#E53935"
    _bg_pressed  = "#B71C1C"
    _bg_disabled = Palette.ELEVATED
    _fg_idle     = "#FFFFFF"
    _fg_disabled = Palette.TEXT_DISABLED
    _glow_color  = Palette.ERROR


# ─────────────────────────────────────────────────────────────────────────────
# 6. IconButton
# ─────────────────────────────────────────────────────────────────────────────

class IconButton(BaseButton):
    """
    Square icon-only button. Pass any Unicode glyph or emoji as `icon`.

    Sizes: "sm" (28 px), "md" (36 px, default), "lg" (44 px).

    Usage::

        btn = IconButton("✕", tooltip="Close",   size="sm")
        btn = IconButton("⚙", tooltip="Settings")
        btn = IconButton("＋", tooltip="Add",    size="lg")
    """

    _SIZES       = {"sm": 28, "md": 36, "lg": 44}
    _bg_idle     = "transparent"
    _bg_hover    = Palette.ELEVATED
    _bg_pressed  = Palette.BORDER
    _bg_disabled = "transparent"
    _fg_idle     = Palette.TEXT_SECONDARY
    _fg_disabled = Palette.TEXT_DISABLED
    _glow_color  = Palette.PRIMARY
    _glow_radius = 8
    _FONT_BOLD   = False

    def __init__(
        self,
        icon:    str,
        tooltip: str = "",
        size:    str = "md",
        parent:  QWidget | None = None,
    ) -> None:
        px = self._SIZES.get(size, 36)
        self._HEIGHT    = px
        self._H_PADDING = 0
        super().__init__(icon, parent)
        self.setFixedSize(QSize(px, px))
        self.setToolTip(tooltip)
        self.setFont(_roboto(13))

    def sizeHint(self) -> QSize:
        return QSize(self._HEIGHT, self._HEIGHT)


# ─────────────────────────────────────────────────────────────────────────────
# 7. IconTextButton
# ─────────────────────────────────────────────────────────────────────────────

class IconTextButton(BaseButton):
    """
    Button with a leading icon glyph and a text label.

    Usage::

        btn = IconTextButton(icon="📁", label="Open File")
        btn = IconTextButton(icon="＋", label="New Project",
                             icon_color=Palette.PRIMARY)
    """

    _GAP = 8

    def __init__(
        self,
        icon:       str,
        label:      str = "",
        icon_color: str = Palette.TEXT_ON_PRIMARY,
        parent:     QWidget | None = None,
    ) -> None:
        super().__init__(label, parent)
        self._icon       = icon
        self._icon_color = icon_color
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def sizeHint(self) -> QSize:
        fm     = QFontMetrics(self.font())
        icon_w = fm.horizontalAdvance(self._icon)
        text_w = fm.horizontalAdvance(self.text())
        gap    = self._GAP if self.text() else 0
        total  = self._H_PADDING + icon_w + gap + text_w + self._H_PADDING
        return QSize(max(total, 80), self._HEIGHT)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, self._radius, self._radius)

        if not self.isEnabled():
            bg = QColor(self._bg_disabled)
        elif self._pressed:
            bg = QColor(self._bg_pressed)
        elif self._hovered:
            bg = QColor(self._bg_hover)
        else:
            bg = QColor(self._bg_idle)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawPath(path)

        if self._ripple_radius > 0 and self._ripple_opacity > 0:
            p.setClipPath(path)
            p.setBrush(QColor(255, 255, 255,
                               int(self._ripple_opacity * 255)))
            p.drawEllipse(
                int(self._ripple_x - self._ripple_radius),
                int(self._ripple_y - self._ripple_radius),
                int(self._ripple_radius * 2),
                int(self._ripple_radius * 2),
            )
            p.setClipping(False)

        if self.hasFocus() and self.isEnabled():
            fp = QPen(QColor(Palette.PRIMARY))
            fp.setWidthF(2.0)
            p.setPen(fp)
            p.setBrush(Qt.BrushStyle.NoBrush)
            fr = QPainterPath()
            fr.addRoundedRect(1.5, 1.5, w - 3, h - 3,
                              self._radius, self._radius)
            p.drawPath(fr)

        fg = QColor(self._fg_disabled if not self.isEnabled()
                    else self._fg_idle)
        fm = QFontMetrics(self.font())

        icon_w = fm.horizontalAdvance(self._icon)
        text_w = fm.horizontalAdvance(self.text())
        gap    = self._GAP if self.text() else 0
        total  = icon_w + gap + text_w
        x      = (w - total) // 2
        y      = (h - fm.height()) // 2 + fm.ascent()

        p.setFont(self.font())
        icon_color = (QColor(self._fg_disabled)
                      if not self.isEnabled()
                      else QColor(self._icon_color))
        p.setPen(icon_color)
        p.drawText(x, y, self._icon)

        if self.text():
            p.setPen(fg)
            p.drawText(x + icon_w + gap, y, self.text())

        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# 8. ToggleButton
# ─────────────────────────────────────────────────────────────────────────────

class ToggleButton(BaseButton):
    """
    Stateful on/off button. Emits `toggled(bool)` on state change.

    Usage::

        btn = ToggleButton("Dark Mode", on_label="Dark Mode ✔")
        btn.toggled.connect(lambda on: apply_theme(on))
    """

    toggled: Signal = Signal(bool)

    def __init__(
        self,
        label:    str,
        on_label: str | None = None,
        active:   bool = False,
        parent:   QWidget | None = None,
    ) -> None:
        super().__init__(label, parent)
        self._on_label  = on_label or label
        self._off_label = label
        self._active    = active
        self.setCheckable(True)
        self.setChecked(active)
        self._sync_style()
        self.clicked.connect(self._on_click)

    def _on_click(self) -> None:
        self._active = not self._active
        self.setChecked(self._active)
        self._sync_style()
        self.setText(self._on_label if self._active else self._off_label)
        self.toggled.emit(self._active)
        self.update()

    def _sync_style(self) -> None:
        if self._active:
            self._bg_idle      = Palette.PRIMARY
            self._bg_hover     = Palette.PRIMARY_HOVER
            self._bg_pressed   = Palette.PRIMARY_PRESSED
            self._fg_idle      = Palette.TEXT_ON_PRIMARY
            self._border_width = 0.0
        else:
            self._bg_idle      = "transparent"
            self._bg_hover     = "rgba(41,121,255,0.10)"
            self._bg_pressed   = "rgba(41,121,255,0.18)"
            self._fg_idle      = Palette.PRIMARY
            self._border_color = Palette.PRIMARY
            self._border_width = 1.5

    def is_active(self) -> bool:
        return self._active

    def set_active(self, active: bool) -> None:
        if active != self._active:
            self._on_click()


# ─────────────────────────────────────────────────────────────────────────────
# 9. SegmentedButton
# ─────────────────────────────────────────────────────────────────────────────

class _Segment(QAbstractButton):
    """Single segment inside a SegmentedButton."""

    _HEIGHT = 36

    def __init__(
        self,
        label:    str,
        position: str,
        parent:   QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setText(label)
        self.setCheckable(True)
        self.setFont(_roboto(10, bold=False))
        self.setFixedHeight(self._HEIGHT)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._position = position
        self._hovered  = False

    def enterEvent(self, _e: QEnterEvent) -> None:  # noqa: N802
        self._hovered = True
        self.update()

    def leaveEvent(self, _e) -> None:  # noqa: N802
        self._hovered = False
        self.update()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        return QSize(fm.horizontalAdvance(self.text()) + 32, self._HEIGHT)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h    = self.width(), self.height()
        r       = 6
        checked = self.isChecked()

        path = QPainterPath()
        if self._position == "left":
            path.addRoundedRect(0, 0, w + r, h, r, r)
            path.addRect(w, 0, r, h)
        elif self._position == "right":
            path.addRoundedRect(-r, 0, w + r, h, r, r)
            path.addRect(-r, 0, r, h)
        elif self._position == "only":
            path.addRoundedRect(0, 0, w, h, r, r)
        else:
            path.addRect(0, 0, w, h)

        if checked:
            bg = QColor(Palette.PRIMARY)
        elif self._hovered:
            bg = QColor(Palette.ELEVATED)
        else:
            bg = QColor("transparent")

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.setClipPath(path)
        p.drawPath(path)
        p.setClipping(False)

        p.setPen(QColor(
            Palette.TEXT_ON_PRIMARY if checked
            else (Palette.TEXT_PRIMARY if self._hovered
                  else Palette.TEXT_SECONDARY)
        ))
        p.setFont(self.font())
        if checked:
            f = self.font()
            f.setBold(True)
            p.setFont(f)
        p.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter,
                   self.text())
        p.end()


class SegmentedButton(QWidget):
    """
    Mutually exclusive inline button group inside a single pill container.

    Usage::

        seg = SegmentedButton()
        seg.add_segment("Day")
        seg.add_segment("Week")
        seg.add_segment("Month")
        seg.currentChanged.connect(lambda i, l: print(i, l))
        seg.set_current_index(1)
    """

    currentChanged: Signal = Signal(int, str)

    _RADIUS = 6

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._group    = QButtonGroup(self)
        self._group.setExclusive(True)
        self._segments: list[_Segment] = []

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(36)

        self._group.buttonToggled.connect(self._on_toggle)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(0.75, 0.75, self.width() - 1.5,
                            self.height() - 1.5,
                            self._RADIUS, self._RADIUS)
        pen = QPen(QColor(Palette.BORDER))
        pen.setWidthF(1.5)
        p.setPen(pen)
        p.setBrush(QColor(Palette.SURFACE))
        p.drawPath(path)

        pen.setColor(QColor(Palette.BORDER))
        pen.setWidthF(1.0)
        p.setPen(pen)
        x = 0
        for seg in self._segments[:-1]:
            x += seg.width()
            p.drawLine(x, 4, x, self.height() - 4)

        p.end()

    def add_segment(self, label: str) -> int:
        idx = len(self._segments)
        seg = _Segment(label, "only", self)
        self._group.addButton(seg, idx)
        self._layout.addWidget(seg)
        self._segments.append(seg)
        self._recompute_positions()

        if idx == 0:
            seg.setChecked(True)

        return idx

    def _recompute_positions(self) -> None:
        n = len(self._segments)
        for i, seg in enumerate(self._segments):
            if n == 1:
                seg._position = "only"
            elif i == 0:
                seg._position = "left"
            elif i == n - 1:
                seg._position = "right"
            else:
                seg._position = "middle"
            seg.update()

    def set_current_index(self, index: int) -> None:
        btn = self._group.button(index)
        if btn:
            btn.setChecked(True)

    def current_index(self) -> int:
        return self._group.checkedId()

    def _on_toggle(self, btn: QAbstractButton, checked: bool) -> None:
        if checked:
            idx = self._group.id(btn)
            self.currentChanged.emit(idx, btn.text())


# ─────────────────────────────────────────────────────────────────────────────
# 10. LoadingButton
# ───────────────��─────────────────────────────────────────────────────────────

class LoadingButton(BaseButton):
    """
    Any button variant with a built-in spinner state.

    Usage::

        btn = LoadingButton("Submit", variant="primary")
        btn.clicked.connect(on_submit)
        btn.set_loading(True)   # shows spinner
        btn.set_loading(False)  # restores label
    """

    def __init__(
        self,
        label:   str,
        variant: str = "primary",
        parent:  QWidget | None = None,
    ) -> None:
        super().__init__(label, parent)
        self._original_label = label
        self._loading        = False
        self._spinner_angle  = 0.0

        _map = {
            "primary":   PrimaryButton,
            "secondary": SecondaryButton,
            "ghost":     GhostButton,
            "danger":    DangerButton,
        }
        base = _map.get(variant, PrimaryButton)
        for attr in ("_bg_idle", "_bg_hover", "_bg_pressed", "_bg_disabled",
                     "_fg_idle", "_fg_disabled", "_border_color",
                     "_border_width", "_glow_color"):
            setattr(self, attr, getattr(base, attr))

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick_spinner)

    def set_loading(self, loading: bool) -> None:
        self._loading = loading
        self.setEnabled(not loading)
        if loading:
            self.setText("")
            self._spinner_angle = 0.0
            self._timer.start()
        else:
            self._timer.stop()
            self.setText(self._original_label)
        self.update()

    def is_loading(self) -> bool:
        return self._loading

    def _tick_spinner(self) -> None:
        self._spinner_angle = (self._spinner_angle + 6) % 360
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        if not self._loading:
            super().paintEvent(_event)
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, self._radius, self._radius)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self._bg_disabled))
        p.drawPath(path)

        size = min(w, h) - 16
        x    = (w - size) // 2
        y    = (h - size) // 2
        pen  = QPen(QColor(Palette.PRIMARY))
        pen.setWidthF(2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(
            x, y, size, size,
            int(-self._spinner_angle * 16),
            int(270 * 16),
        )
        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# 11. FloatingActionButton
# ─────────────────────────────────────────────────────────────────────────────

class FloatingActionButton(BaseButton):
    """
    Circular floating action button with a prominent drop shadow.

    FIX — shadow ownership
    ──────────────────────
    The previous version called setGraphicsEffect() a second time inside
    __init__ (after BaseButton.__init__ had already set one), which caused
    Qt to immediately delete the first effect while the glow animation still
    held a pointer to it.

    Now FloatingActionButton does NOT call setGraphicsEffect() at all.
    Instead it overrides _apply_glow_effect() to blend both the glow colour
    AND the resting shadow offset into a single effect, installed through the
    same safe "no stored reference" path that BaseButton uses.

    Usage::

        fab = FloatingActionButton("＋", tooltip="Create new item")
        fab.clicked.connect(on_create)
    """

    _SIZES       = {"md": 48, "lg": 56}
    _bg_idle     = Palette.PRIMARY
    _bg_hover    = Palette.PRIMARY_HOVER
    _bg_pressed  = Palette.PRIMARY_PRESSED
    _bg_disabled = Palette.ELEVATED
    _fg_idle     = Palette.TEXT_ON_PRIMARY
    _fg_disabled = Palette.TEXT_DISABLED
    _glow_color  = Palette.PRIMARY
    _glow_radius = 20
    _FONT_BOLD   = False

    # Resting shadow parameters (no glow active)
    _SHADOW_IDLE_BLUR   = 20
    _SHADOW_IDLE_OFFSET = 4
    _SHADOW_HOVER_BLUR  = 28
    _SHADOW_HOVER_OFFSET = 6

    def __init__(
        self,
        icon:    str = "＋",
        tooltip: str = "",
        size:    str = "md",
        parent:  QWidget | None = None,
    ) -> None:
        px = self._SIZES.get(size, 48)
        self._HEIGHT    = px
        self._H_PADDING = 0
        self._radius    = px // 2
        # BaseButton.__init__ sets up the glow animation machinery.
        # It does NOT call setGraphicsEffect() directly — that happens
        # lazily via _apply_glow_effect() when the animation first runs.
        super().__init__(icon, parent)
        self.setFixedSize(QSize(px, px))
        self.setToolTip(tooltip)
        self.setFont(_roboto(18))
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Install the resting shadow immediately through the safe path
        self._apply_glow_effect(0.0)

    # ------------------------------------------------------------------
    def sizeHint(self) -> QSize:
        return QSize(self._HEIGHT, self._HEIGHT)

    def _apply_glow_effect(self, radius: float) -> None:
        """
        Override: merge resting shadow + optional glow into one effect.
        No reference is stored — Qt takes ownership immediately.
        """
        if self._hovered:
            blur   = max(float(self._SHADOW_HOVER_BLUR), radius)
            offset = self._SHADOW_HOVER_OFFSET
        else:
            blur   = max(float(self._SHADOW_IDLE_BLUR), radius)
            offset = self._SHADOW_IDLE_OFFSET

        fx = QGraphicsDropShadowEffect()
        fx.setBlurRadius(blur)
        fx.setOffset(0, offset)
        fx.setColor(QColor(0, 0, 0, 140) if radius <= 0.5
                    else QColor(self._glow_color))
        self.setGraphicsEffect(fx)
        # No self._anything = fx  ← intentional

    def enterEvent(self, event: QEnterEvent) -> None:  # noqa: N802
        self._hovered = True
        self._animate_glow(self._glow_radius)
        self.update()
        # Skip BaseButton.enterEvent to avoid double glow call
        super(BaseButton, self).enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hovered = False
        self._animate_glow(0)
        self.update()
        super(BaseButton, self).leaveEvent(event)