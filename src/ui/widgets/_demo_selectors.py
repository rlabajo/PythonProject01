"""
Run this file directly to preview all custom selector widgets:
    python -m src.ui.widgets._demo_selectors
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
)

from src.ui.themes.theme import apply_dark_theme, Palette
from src.ui.widgets.labels import SectionDividerLabel, CaptionLabel
from src.ui.widgets.selectors import (
    BaseComboBox,
    SearchableComboBox,
    BaseSpinBox,
    PrefixSpinBox,
    SuffixSpinBox,
    BaseDoubleSpinBox,
    StepDoubleSpinBox,
)

COUNTRIES = [
    "Albania", "Algeria", "Argentina", "Australia", "Austria",
    "Belgium", "Brazil", "Canada", "Chile", "China",
    "Colombia", "Croatia", "Czech Republic", "Denmark", "Egypt",
    "Finland", "France", "Germany", "Greece", "Hungary",
    "India", "Indonesia", "Iran", "Iraq", "Ireland",
    "Israel", "Italy", "Japan", "Jordan", "Kenya",
    "Malaysia", "Mexico", "Morocco", "Netherlands", "New Zealand",
    "Nigeria", "Norway", "Pakistan", "Peru", "Philippines",
    "Poland", "Portugal", "Romania", "Russia", "Saudi Arabia",
    "South Africa", "South Korea", "Spain", "Sweden", "Switzerland",
    "Thailand", "Turkey", "Ukraine", "United Kingdom", "United States",
    "Vietnam",
]


def _row(*widgets: QWidget) -> QWidget:
    """
    Wrap a set of widgets in a horizontally laid-out container.

    Using an explicit QWidget container (instead of adding a bare QHBoxLayout
    directly to the root VBox) ensures the row has its own independent size
    hint and is never clipped by a parent fixedHeight constraint.
    """
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 4, 0, 4)   # 4 px top/bottom breathing room
    layout.setSpacing(12)
    for w in widgets:
        layout.addWidget(w)
    return container


def main() -> None:
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    # ── Scrollable content area ───────────────────────────────────────────
    content = QWidget()
    root = QVBoxLayout(content)
    root.setSpacing(10)
    root.setContentsMargins(36, 36, 36, 36)

    # ── ComboBox ──────────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("COMBO BOX"))
    cb = BaseComboBox()
    cb.addItems(["Design System", "Dark Mode", "Blue Accent", "Roboto Font"])
    cb.currentTextChanged.connect(lambda t: print(f"ComboBox → {t}"))
    root.addWidget(cb)

    # ── SearchableComboBox ────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("SEARCHABLE COMBO BOX"))
    scb = SearchableComboBox()
    scb.addItems(COUNTRIES)
    scb.currentTextChanged.connect(lambda t: print(f"Searchable → {t}"))
    root.addWidget(scb)
    root.addWidget(CaptionLabel("Click to open — type to filter the list."))

    # ── SpinBoxes ─────��───────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("SPIN BOXES"))
    root.addWidget(_row(
        BaseSpinBox(minimum=0, maximum=100, value=42, step=1),
        PrefixSpinBox(prefix="$", minimum=0, maximum=10_000, value=250, step=50),
        SuffixSpinBox(suffix=" px", minimum=0, maximum=64, value=8, step=1),
    ))
    root.addWidget(CaptionLabel("Left: plain · Middle: $ prefix · Right: px suffix"))

    # ── DoubleSpinBoxes ───────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("DOUBLE SPIN BOXES"))
    root.addWidget(_row(
        BaseDoubleSpinBox(minimum=0.0, maximum=1.0, value=0.5, step=0.05, decimals=2),
        StepDoubleSpinBox(minimum=0.1, maximum=10.0, value=1.0,
                          step=0.1, coarse_step=1.0, decimals=2, suffix="x"),
        StepDoubleSpinBox(minimum=-360.0, maximum=360.0, value=0.0,
                          step=0.5, coarse_step=45.0, decimals=1, suffix="°"),
    ))
    root.addWidget(CaptionLabel(
        "Left: 0.0–1.0 · Middle: zoom (Ctrl = ×1.0 step) · Right: angle (Ctrl = 45° step)"
    ))

    root.addStretch()

    # ── Scroll wrapper ────────────────────────────────────────────────────
    scroll = QScrollArea()
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    scroll.setWindowTitle("Custom Selectors — Demo")
    scroll.resize(560, 600)
    scroll.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()