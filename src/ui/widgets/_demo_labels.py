"""
Run this file directly to preview all custom labels:
    python -m src.ui.widgets._demo_labels
"""

import sys
from PySide6.QtCore    import Qt
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                                QHBoxLayout, QFrame)

from src.ui.themes.theme import apply_dark_theme, Palette
from src.ui.widgets.labels import (
    HeadingLabel, SubtitleLabel, CaptionLabel,
    BadgeLabel, TagLabel,
    IconLabel, StatusLabel,
    LinkLabel, ElidedLabel, SectionDividerLabel,
)


def _rule() -> SectionDividerLabel:
    return SectionDividerLabel()


def main() -> None:
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    scroll_content = QWidget()
    root = QVBoxLayout(scroll_content)
    root.setSpacing(14)
    root.setContentsMargins(36, 36, 36, 36)

    # ── Headings ─────────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("HEADINGS"))
    for level in range(1, 5):
        root.addWidget(HeadingLabel(f"Heading Level {level}", level=level))

    # ── Subtitle & Caption ───────────────────────────────────────────────
    root.addWidget(_rule())
    root.addWidget(SectionDividerLabel("SUBTITLE & CAPTION"))
    root.addWidget(SubtitleLabel("Last synced 2 minutes ago · 3 active sessions"))
    root.addWidget(CaptionLabel("* All fields are required unless marked optional."))

    # ── Badges ───────────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("BADGES"))
    badge_row = QHBoxLayout()
    badge_row.setSpacing(8)
    for variant, text in [
        ("primary", "Primary"),
        ("success", "Active"),
        ("warning", "Pending"),
        ("error",   "Failed"),
        ("muted",   "Archived"),
    ]:
        badge_row.addWidget(BadgeLabel(text, variant=variant))
    badge_row.addStretch()
    root.addLayout(badge_row)

    # ── Tags ─────────────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("TAGS"))
    tag_row = QHBoxLayout()
    tag_row.setSpacing(8)
    for color, text in [
        (Palette.PRIMARY,  "Python"),
        (Palette.SUCCESS,  "Passing"),
        (Palette.WARNING,  "In Review"),
        (Palette.ERROR,    "Blocked"),
        (Palette.TEXT_SECONDARY, "Draft"),
    ]:
        tag_row.addWidget(TagLabel(text, color=color))
    tag_row.addStretch()
    root.addLayout(tag_row)

    # ── Icon Labels ──────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("ICON LABELS"))
    root.addWidget(IconLabel("📁", "Documents",           icon_color=Palette.PRIMARY))
    root.addWidget(IconLabel("✔",  "Changes saved",       icon_color=Palette.SUCCESS))
    root.addWidget(IconLabel("⚠",  "Unsaved changes",     icon_color=Palette.WARNING))
    root.addWidget(IconLabel("✖",  "Connection lost",     icon_color=Palette.ERROR))

    # ── Status Labels ────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("STATUS LABELS"))
    root.addWidget(StatusLabel("All systems operational",  variant="success"))
    root.addWidget(StatusLabel("Elevated error rate",      variant="warning"))
    root.addWidget(StatusLabel("Service unavailable",      variant="error"))
    root.addWidget(StatusLabel("Sync in progress…",        variant="info"))
    root.addWidget(StatusLabel("Monitoring paused",        variant="muted"))

    # ── Link Labels ──────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("LINK LABELS"))
    lnk = LinkLabel("Forgot password?")
    lnk.clicked.connect(lambda: print("Link clicked"))
    root.addWidget(lnk)

    # ── Elided Labels ────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("ELIDED LABELS (resize window to see)"))
    elided = ElidedLabel(
        "src/modules/data_pipeline/processors/transform/normalize_records.py"
    )
    elided.setFixedWidth(300)
    root.addWidget(elided)

    # ── Section Dividers ─────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("SECTION DIVIDERS"))
    root.addWidget(SectionDividerLabel("Left-aligned title"))
    root.addWidget(SectionDividerLabel("Centred title", align="center"))
    root.addWidget(SectionDividerLabel())   # no text — plain rule

    root.addStretch()

    # ── Window ───────────────────────────────────────────────────────────
    from PySide6.QtWidgets import QScrollArea
    scroll = QScrollArea()
    scroll.setWidget(scroll_content)
    scroll.setWidgetResizable(True)
    scroll.setWindowTitle("Custom Labels — Demo")
    scroll.resize(560, 740)
    scroll.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()