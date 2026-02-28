"""
Run this file directly to preview all custom card widgets:
    python -m src.ui.widgets._demo_cards
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from src.ui.themes.theme import Palette, apply_dark_theme
from src.ui.widgets.cards import (ActionCard, BaseCard, HorizontalCard, SelectableCard,
                                  StatCard, StatusCard, TitledCard)
from src.ui.widgets.labels import (CaptionLabel, HeadingLabel, SectionDividerLabel,
                                   SubtitleLabel)


def main() -> None:
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    content = QWidget()
    root = QVBoxLayout(content)
    root.setSpacing(14)
    root.setContentsMargins(36, 36, 36, 36)

    # ── BaseCard ──────────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("BASE CARD"))
    base = BaseCard()
    base.content_layout.addWidget(HeadingLabel("Base Card", level=3))
    base.content_layout.addWidget(
        SubtitleLabel("Drop content into .content_layout freely.")
    )
    root.addWidget(base)

    # ── TitledCard ────────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("TITLED CARD"))
    titled = TitledCard(
        title    = "Recent Activity",
        subtitle = "Last 30 days",
        icon     = "📊",
    )
    for line in ["Deployed v2.4.1", "Merged PR #118", "Closed 4 issues"]:
        row = QLabel(f"  •  {line}")
        row.setStyleSheet(
            f"color: {Palette.TEXT_PRIMARY}; background: transparent; border: none;"
        )
        titled.body_layout.addWidget(row)
    root.addWidget(titled)

    # ── StatCards ─────────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("STAT CARDS"))
    stat_row = QHBoxLayout()
    stat_row.setSpacing(12)
    stat_row.addWidget(StatCard(
        label="Total Revenue", value="$48,295",
        icon="💰", trend="up", delta="+12.4% vs last month",
    ))
    stat_row.addWidget(StatCard(
        label="Active Users", value="3,842",
        icon="👥", trend="up", delta="+5.1% this week",
    ))
    stat_row.addWidget(StatCard(
        label="Error Rate", value="0.42%",
        icon="⚠", trend="down", delta="−0.08% vs yesterday",
    ))
    root.addLayout(stat_row)

    # ── ActionCard ────────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("ACTION CARD"))
    cancel_btn  = QPushButton("Cancel")
    cancel_btn.setProperty("secondary", True)
    confirm_btn = QPushButton("Delete")

    action_card = ActionCard(
        title   = "Delete Project",
        actions = [cancel_btn, confirm_btn],
    )
    action_card.body_layout.addWidget(
        SubtitleLabel(
            "Are you sure you want to delete this project? "
            "This action is permanent and cannot be undone."
        )
    )
    root.addWidget(action_card)

    # ── SelectableCards ───────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("SELECTABLE CARDS"))
    sel_row = QHBoxLayout()
    sel_row.setSpacing(12)
    for plan, price, note in [
        ("Starter",    "$0 / mo",   "Up to 3 projects"),
        ("Pro",        "$12 / mo",  "Unlimited projects"),
        ("Enterprise", "$49 / mo",  "SSO + priority support"),
    ]:
        card = SelectableCard()
        card.content_layout.addWidget(_plan_label(plan, price, note))
        card.toggled.connect(
            lambda on, p=plan: print(f"SelectableCard '{p}' → {on}")
        )
        sel_row.addWidget(card)
    root.addLayout(sel_row)
    root.addWidget(CaptionLabel("Click a card to select / deselect it."))

    # ── HorizontalCard ────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("HORIZONTAL CARD"))
    hcard = HorizontalCard(left_width=64, left_bg="#0D1F3C")
    icon_lbl = QLabel("🗂")
    icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_lbl.setStyleSheet("font-size: 26px; background: transparent; border: none;")
    hcard.left_layout.addWidget(icon_lbl)
    hcard.right_layout.addWidget(HeadingLabel("Project Alpha", level=3))
    hcard.right_layout.addWidget(
        SubtitleLabel("12 open tasks · Updated 2 hours ago")
    )
    root.addWidget(hcard)

    # ── StatusCards ───────────────────────────────────────────────────────
    root.addWidget(SectionDividerLabel("STATUS CARDS"))
    for status, title, msg in [
        ("success", "Deployment Successful",
         "Version 2.4.1 is live across all regions."),
        ("warning", "High Memory Usage",
         "Node pool utilisation at 87%. Consider scaling up."),
        ("error",   "Deployment Failed",
         "Build step exited with code 1. Check the logs for details."),
        ("info",    "Scheduled Maintenance",
         "Downtime window: Saturday 02:00–04:00 UTC."),
    ]:
        root.addWidget(StatusCard(status=status, title=title, message=msg))

    root.addStretch()

    # ── Window ────────────────────────────────────────────────────────────
    scroll = QScrollArea()
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    scroll.setWindowTitle("Custom Cards — Demo")
    scroll.resize(680, 800)
    scroll.show()

    sys.exit(app.exec())


def _plan_label(plan: str, price: str, note: str) -> QWidget:
    """Helper: vertical stack of plan name, price, note for SelectableCard."""
    container = QWidget()
    container.setStyleSheet("background: transparent; border: none;")
    lay = QVBoxLayout(container)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(4)
    for text, size, bold, color in [
        (plan,  11, True,  Palette.TEXT_PRIMARY),
        (price, 13, True,  Palette.PRIMARY),
        (note,   8, False, Palette.TEXT_SECONDARY),
    ]:
        lbl = QLabel(text)
        lbl.setFont(QFont("Roboto", size))
        f = lbl.font()
        f.setBold(bold)
        lbl.setFont(f)
        lbl.setStyleSheet(
            f"color: {color}; background: transparent; border: none;"
        )
        lay.addWidget(lbl)
    return container


if __name__ == "__main__":
    main()