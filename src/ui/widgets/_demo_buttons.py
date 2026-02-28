"""
Run this file directly to preview all custom button widgets:
    python -m src.ui.widgets._demo_buttons
"""

import sys
from PySide6.QtCore    import Qt, QTimer
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                                QHBoxLayout, QScrollArea)

from src.ui.themes.theme import apply_dark_theme, Palette
from src.ui.widgets.labels import SectionDividerLabel, CaptionLabel
from src.ui.widgets.buttons import (
    PrimaryButton, SecondaryButton, GhostButton, DangerButton,
    IconButton, IconTextButton, ToggleButton, SegmentedButton,
    LoadingButton, FloatingActionButton,
)


def _row(*widgets, spacing: int = 10) -> QWidget:
    container = QWidget()
    container.setStyleSheet("background: transparent; border: none;")
    lay = QHBoxLayout(container)
    lay.setContentsMargins(0, 4, 0, 4)
    lay.setSpacing(spacing)
    for w in widgets:
        lay.addWidget(w)
    lay.addStretch()
    return container


def main() -> None:
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    content = QWidget()
    root = QVBoxLayout(content)
    root.setSpacing(12)
    root.setContentsMargins(36, 36, 36, 36)

    # ── Core variants ─────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("CORE VARIANTS"))
    root.addWidget(_row(
        PrimaryButton("Save Changes"),
        SecondaryButton("Cancel"),
        GhostButton("Learn More"),
        DangerButton("Delete"),
    ))

    # ── Disabled state ────────────────────────────��───────────────────────
    root.addWidget(SectionDividerLabel("DISABLED STATE"))
    disabled_row = []
    for cls, lbl in [(PrimaryButton, "Save Changes"),
                     (SecondaryButton, "Cancel"),
                     (GhostButton,     "Learn More"),
                     (DangerButton,    "Delete")]:
        b = cls(lbl)
        b.setEnabled(False)
        disabled_row.append(b)
    root.addWidget(_row(*disabled_row))

    # ── Icon buttons ──────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("ICON BUTTONS"))
    root.addWidget(_row(
        IconButton("✕", tooltip="Close",    size="sm"),
        IconButton("⚙", tooltip="Settings", size="md"),
        IconButton("＋", tooltip="Add",     size="lg"),
        IconButton("🔍", tooltip="Search",  size="md"),
    ))

    # ── Icon + text buttons ───────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("ICON + TEXT BUTTONS"))
    root.addWidget(_row(
        IconTextButton("📁", "Open File"),
        IconTextButton("＋", "New Project"),
        IconTextButton("🚀", "Deploy",   icon_color=Palette.SUCCESS),
        IconTextButton("🗑", "Remove",   icon_color=Palette.ERROR),
    ))

    # ── Toggle buttons ────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("TOGGLE BUTTONS"))
    tgl1 = ToggleButton("Notifications",  on_label="Notifications ✔")
    tgl2 = ToggleButton("Auto-save",      on_label="Auto-save ✔", active=True)
    tgl3 = ToggleButton("Dark Mode",      on_label="Dark Mode ✔")
    for t in (tgl1, tgl2, tgl3):
        t.toggled.connect(lambda on, lbl=t.text(): print(f"{lbl} → {on}"))
    root.addWidget(_row(tgl1, tgl2, tgl3))

    # ── Segmented buttons ─────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("SEGMENTED BUTTONS"))
    seg1 = SegmentedButton()
    for s in ("Day", "Week", "Month", "Year"):
        seg1.add_segment(s)
    seg1.set_current_index(1)
    seg1.currentChanged.connect(lambda i, l: print(f"Period → {l}"))

    seg2 = SegmentedButton()
    for s in ("List", "Grid", "Kanban"):
        seg2.add_segment(s)
    seg2.currentChanged.connect(lambda i, l: print(f"View → {l}"))

    root.addWidget(_row(seg1, seg2))

    # ── Loading buttons ───────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("LOADING BUTTONS"))

    def _make_loading_btn(label: str, variant: str) -> LoadingButton:
        btn = LoadingButton(label, variant=variant)

        def _on_click():
            btn.set_loading(True)
            QTimer.singleShot(2400, lambda: btn.set_loading(False))

        btn.clicked.connect(_on_click)
        return btn

    root.addWidget(_row(
        _make_loading_btn("Submit",    "primary"),
        _make_loading_btn("Verify",    "secondary"),
        _make_loading_btn("Refresh",   "ghost"),
        _make_loading_btn("Overwrite", "danger"),
    ))
    root.addWidget(CaptionLabel("Click any button above to trigger the spinner (auto-resets after 2.4 s)."))

    # ── FAB ───────────────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("FLOATING ACTION BUTTON"))
    root.addWidget(_row(
        FloatingActionButton("＋", tooltip="Create",    size="md"),
        FloatingActionButton("✎",  tooltip="Edit",      size="md"),
        FloatingActionButton("🚀", tooltip="Deploy",    size="lg"),
    ))

    root.addStretch()

    scroll = QScrollArea()
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    scroll.setWindowTitle("Custom Buttons — Demo")
    scroll.resize(700, 680)
    scroll.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()