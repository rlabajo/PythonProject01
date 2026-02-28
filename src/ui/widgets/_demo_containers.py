"""
Run this file directly to preview all custom container widgets:
    python -m src.ui.widgets._demo_containers
"""

import sys
from PySide6.QtCore    import Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                                QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton)

from src.ui.themes.theme import apply_dark_theme, Palette
from src.ui.widgets.labels import (HeadingLabel, SubtitleLabel,
                                    CaptionLabel, SectionDividerLabel)
from src.ui.widgets.containers import (
    BaseScrollArea, SidebarTabWidget, PillTabWidget,
    UnderlineTabWidget, AccordionWidget, SplitterWidget,
    StackedWidget, DrawerWidget,
)


# ── Placeholder page factory ──────────────────────────────────────────────────

def _page(title: str, color: str = Palette.BASE) -> QWidget:
    w = QWidget()
    w.setStyleSheet(f"background-color: {color}; border: none;")
    lay = QVBoxLayout(w)
    lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl = HeadingLabel(title, level=2)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(lbl)
    return w


def _text_block(lines: int = 12) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background: transparent; border: none;")
    lay = QVBoxLayout(w)
    lay.setSpacing(6)
    for i in range(lines):
        lbl = QLabel(f"Line {i + 1} — scroll down to see more content below.")
        lbl.setStyleSheet(
            f"color: {Palette.TEXT_SECONDARY}; background: transparent; border: none;"
        )
        lay.addWidget(lbl)
    return w


# ── Main window ───────────────────────────────────────────────────────────────

class DemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Custom Containers — Demo")
        self.resize(900, 700)

        # ── Root: sidebar nav ─────────────────────────────────────────
        self._sidebar = SidebarTabWidget()
        self.setCentralWidget(self._sidebar)

        self._sidebar.add_tab("🏠", "Scroll Area",   self._build_scroll())
        self._sidebar.add_tab("💊", "Pill Tabs",      self._build_pill())
        self._sidebar.add_tab("—",  "Underline Tabs", self._build_underline())
        self._sidebar.add_tab("▸",  "Accordion",      self._build_accordion())
        self._sidebar.add_tab("⇔",  "Splitter",       self._build_splitter())
        self._sidebar.add_tab("⧉",  "Stacked",        self._build_stacked())
        self._sidebar.add_separator()
        self._sidebar.add_tab("☰",  "Drawer",         self._build_drawer())

    # ── Pages ─────────────────────────────────────────────────────────

    def _build_scroll(self) -> QWidget:
        scroll = BaseScrollArea()
        scroll.setWidget(_text_block(30))
        return scroll

    def _build_pill(self) -> QWidget:
        wrapper = QWidget()
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(24, 24, 24, 24)
        tabs = PillTabWidget()
        tabs.add_tab("Overview",  _page("Overview"))
        tabs.add_tab("Analytics", _page("Analytics"))
        tabs.add_tab("Members",   _page("Members"))
        tabs.add_tab("Settings",  _page("Settings"))
        lay.addWidget(tabs)
        return wrapper

    def _build_underline(self) -> QWidget:
        wrapper = QWidget()
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(24, 24, 24, 24)
        tabs = UnderlineTabWidget()
        tabs.add_tab("Details",  _page("Details"))
        tabs.add_tab("Activity", _page("Activity"))
        tabs.add_tab("Files",    _page("Files"))
        tabs.add_tab("Insights", _page("Insights"))
        lay.addWidget(tabs)
        return wrapper

    def _build_accordion(self) -> QWidget:
        scroll = BaseScrollArea()
        acc = AccordionWidget(exclusive=True)

        for title, lines, expanded in [
            ("General Settings",  6,  True),
            ("Notifications",     5,  False),
            ("Security",          7,  False),
            ("Billing",           4,  False),
            ("Danger Zone",       3,  False),
        ]:
            acc.add_section(title, _text_block(lines), expanded=expanded)

        scroll.setWidget(acc)
        return scroll

    def _build_splitter(self) -> QWidget:
        outer = SplitterWidget(Qt.Orientation.Vertical)

        top = SplitterWidget(Qt.Orientation.Horizontal)
        top.add_pane(_page("Left Pane",   Palette.SURFACE), stretch=1)
        top.add_pane(_page("Right Pane",  Palette.BASE),    stretch=2)
        top.set_sizes([260, 540])

        outer.add_pane(top,              stretch=3)
        outer.add_pane(_page("Bottom Pane", Palette.ELEVATED), stretch=1)
        outer.set_sizes([480, 160])
        return outer

    def _build_stacked(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setStyleSheet(f"background: {Palette.BASE};")
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        stack = StackedWidget(transition="fade")
        stack.add_page(_page("Page One",   Palette.SURFACE))
        stack.add_page(_page("Page Two",   Palette.ELEVATED))
        stack.add_page(_page("Page Three", Palette.BASE))

        btn_row = QHBoxLayout()
        for i, (label, mode) in enumerate([
            ("← Slide Right", "slide_right"),
            ("Fade →",         "fade"),
            ("Slide Left →",   "slide_left"),
        ]):
            btn = QPushButton(label)
            idx = i
            btn.clicked.connect(
                lambda _, x=idx, m=mode: stack.set_current_index(x, m)
            )
            btn_row.addWidget(btn)

        lay.addLayout(btn_row)
        lay.addWidget(stack, 1)
        return wrapper

    def _build_drawer(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setStyleSheet(f"background: {Palette.BASE};")
        lay = QVBoxLayout(wrapper)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(16)

        lay.addWidget(HeadingLabel("Drawer Demo", level=2))
        lay.addWidget(SubtitleLabel("Click a button to open a drawer from any edge."))

        drawer_left  = DrawerWidget(wrapper, edge="left",   size=260)
        drawer_right = DrawerWidget(wrapper, edge="right",  size=260)
        drawer_top   = DrawerWidget(wrapper, edge="top",    size=200)
        drawer_bot   = DrawerWidget(wrapper, edge="bottom", size=200)

        for drawer, title in [
            (drawer_left,  "☰  Navigation"),
            (drawer_right, "⚙  Properties"),
            (drawer_top,   "🔍  Search"),
            (drawer_bot,   "📋  Console"),
        ]:
            drawer.layout().addWidget(HeadingLabel(title, level=3))
            drawer.layout().addWidget(
                CaptionLabel("Click the scrim or call drawer.close().")
            )
            drawer.layout().addStretch()

        btn_row_1 = QHBoxLayout()
        btn_row_2 = QHBoxLayout()

        for label, drawer in [("← Left", drawer_left),
                               ("Right →", drawer_right)]:
            b = QPushButton(label)
            b.clicked.connect(drawer.open)
            btn_row_1.addWidget(b)

        for label, drawer in [("↑ Top", drawer_top),
                               ("↓ Bottom", drawer_bot)]:
            b = QPushButton(label)
            b.clicked.connect(drawer.open)
            btn_row_2.addWidget(b)

        lay.addLayout(btn_row_1)
        lay.addLayout(btn_row_2)
        return wrapper


def main() -> None:
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    win = DemoWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()