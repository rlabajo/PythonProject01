"""
theme.py
--------
Modern professional dark theme for PySide6 applications.

Design System:
  - Base:         #0A0A0A  (near-pure black)
  - Surface:      #111111  (widget backgrounds)
  - Elevated:     #1A1A1A  (raised surfaces, cards)
  - Border:       #2A2A2A  (subtle dividers)
  - Muted:        #3A3A3A  (disabled / inactive borders)
  - Primary:      #2979FF  (electric blue accent)
  - Primary Hover:#448AFF
  - Primary Press:#1565C0
  - Text Primary: #EFEFEF  (main text)
  - Text Secondary:#9E9E9E (secondary / placeholder)
  - Text Disabled:#555555
  - Error:        #F44336
  - Warning:      #FFA726
  - Success:      #66BB6A
  - Font:         Roboto, 10pt
"""

from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtWidgets import QApplication


# ---------------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------------
class Palette:
    BASE            = "#0A0A0A"
    SURFACE         = "#111111"
    ELEVATED        = "#1A1A1A"
    BORDER          = "#2A2A2A"
    BORDER_MUTED    = "#3A3A3A"

    PRIMARY         = "#2979FF"
    PRIMARY_HOVER   = "#448AFF"
    PRIMARY_PRESSED = "#1565C0"
    PRIMARY_TEXT    = "#FFFFFF"

    TEXT_PRIMARY    = "#EFEFEF"
    TEXT_SECONDARY  = "#9E9E9E"
    TEXT_DISABLED   = "#555555"
    TEXT_ON_PRIMARY = "#FFFFFF"

    SELECTION_BG    = "#2979FF"
    SELECTION_FG    = "#FFFFFF"

    ERROR           = "#F44336"
    WARNING         = "#FFA726"
    SUCCESS         = "#66BB6A"

    SCROLLBAR_BG    = "#0F0F0F"
    SCROLLBAR_HANDLE= "#2A2A2A"
    SCROLLBAR_HOVER = "#2979FF"

    TOOLTIP_BG      = "#1E1E1E"
    TOOLTIP_BORDER  = "#2979FF"


# ---------------------------------------------------------------------------
# QSS Stylesheet
# ---------------------------------------------------------------------------
DARK_STYLESHEET = f"""
/* ── Global ────────────────────────────────────────────────────── */
* {{
    font-family: "Roboto", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
    color: {Palette.TEXT_PRIMARY};
    selection-background-color: {Palette.SELECTION_BG};
    selection-color: {Palette.SELECTION_FG};
    outline: none;
}}

QWidget {{
    background-color: {Palette.BASE};
    color: {Palette.TEXT_PRIMARY};
    border: none;
}}

QWidget:disabled {{
    color: {Palette.TEXT_DISABLED};
}}

/* ── Main Window & Dialogs ──────────────────────────────────────── */
QMainWindow,
QDialog {{
    background-color: {Palette.BASE};
}}

QMainWindow::separator {{
    background: {Palette.BORDER};
    width: 1px;
    height: 1px;
}}

/* ── Frame ───────────────────────────────────────────────────────── */
QFrame {{
    background-color: {Palette.SURFACE};
    border: 1px solid {Palette.BORDER};
    border-radius: 6px;
}}

QFrame[frameShape="0"] {{   /* NoFrame */
    background-color: transparent;
    border: none;
}}

/* ── Labels ──────────────────────────────────────────────────────── */
QLabel {{
    background-color: transparent;
    border: none;
    color: {Palette.TEXT_PRIMARY};
    padding: 2px;
}}

QLabel:disabled {{
    color: {Palette.TEXT_DISABLED};
}}

/* ── Push Button ─────────────────────────────────────────────────── */
QPushButton {{
    background-color: {Palette.PRIMARY};
    color: {Palette.PRIMARY_TEXT};
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-weight: 600;
    letter-spacing: 0.4px;
    min-height: 32px;
}}

QPushButton:hover {{
    background-color: {Palette.PRIMARY_HOVER};
}}

QPushButton:pressed {{
    background-color: {Palette.PRIMARY_PRESSED};
}}

QPushButton:disabled {{
    background-color: {Palette.ELEVATED};
    color: {Palette.TEXT_DISABLED};
}}

QPushButton:flat {{
    background-color: transparent;
    color: {Palette.PRIMARY};
    border: none;
}}

QPushButton:flat:hover {{
    color: {Palette.PRIMARY_HOVER};
    background-color: rgba(41, 121, 255, 0.08);
    border-radius: 6px;
}}

/* Outlined / secondary button — use setProperty("secondary", True) */
QPushButton[secondary="true"] {{
    background-color: transparent;
    color: {Palette.PRIMARY};
    border: 1.5px solid {Palette.PRIMARY};
    border-radius: 6px;
}}

QPushButton[secondary="true"]:hover {{
    background-color: rgba(41, 121, 255, 0.10);
    border-color: {Palette.PRIMARY_HOVER};
    color: {Palette.PRIMARY_HOVER};
}}

QPushButton[secondary="true"]:pressed {{
    background-color: rgba(41, 121, 255, 0.18);
}}

/* ── Tool Button ─────────────────────────────────────────────────── */
QToolButton {{
    background-color: transparent;
    color: {Palette.TEXT_PRIMARY};
    border: none;
    border-radius: 5px;
    padding: 5px;
    min-width: 28px;
    min-height: 28px;
}}

QToolButton:hover {{
    background-color: {Palette.ELEVATED};
    color: {Palette.PRIMARY};
}}

QToolButton:pressed {{
    background-color: rgba(41, 121, 255, 0.15);
}}

QToolButton:checked {{
    background-color: rgba(41, 121, 255, 0.15);
    color: {Palette.PRIMARY};
    border: 1px solid {Palette.PRIMARY};
}}

QToolButton::menu-indicator {{
    image: none;
}}

/* ── Line Edit ───────────────────────────────────────────────────── */
QLineEdit {{
    background-color: {Palette.SURFACE};
    color: {Palette.TEXT_PRIMARY};
    border: 1.5px solid {Palette.BORDER};
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 30px;
    selection-background-color: {Palette.SELECTION_BG};
    selection-color: {Palette.SELECTION_FG};
}}

QLineEdit:focus {{
    border-color: {Palette.PRIMARY};
    background-color: {Palette.ELEVATED};
}}

QLineEdit:hover:!focus {{
    border-color: {Palette.BORDER_MUTED};
}}

QLineEdit:disabled {{
    background-color: {Palette.BASE};
    color: {Palette.TEXT_DISABLED};
    border-color: {Palette.BORDER};
}}

QLineEdit::placeholder {{
    color: {Palette.TEXT_SECONDARY};
}}

/* ── Text Edit / Plain Text Edit ─────────────────────────────────── */
QTextEdit,
QPlainTextEdit {{
    background-color: {Palette.SURFACE};
    color: {Palette.TEXT_PRIMARY};
    border: 1.5px solid {Palette.BORDER};
    border-radius: 6px;
    padding: 8px;
    selection-background-color: {Palette.SELECTION_BG};
    selection-color: {Palette.SELECTION_FG};
}}

QTextEdit:focus,
QPlainTextEdit:focus {{
    border-color: {Palette.PRIMARY};
    background-color: {Palette.ELEVATED};
}}

/* ── Spin Box ────────────────────────────────────────────────────── */
QSpinBox,
QDoubleSpinBox {{
    background-color: {Palette.SURFACE};
    color: {Palette.TEXT_PRIMARY};
    border: 1.5px solid {Palette.BORDER};
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 30px;
}}

QSpinBox:focus,
QDoubleSpinBox:focus {{
    border-color: {Palette.PRIMARY};
}}

QSpinBox::up-button,
QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 18px;
    border-left: 1px solid {Palette.BORDER};
    background-color: {Palette.ELEVATED};
    border-top-right-radius: 5px;
}}

QSpinBox::down-button,
QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 18px;
    border-left: 1px solid {Palette.BORDER};
    background-color: {Palette.ELEVATED};
    border-bottom-right-radius: 5px;
}}

QSpinBox::up-button:hover,
QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover,
QDoubleSpinBox::down-button:hover {{
    background-color: {Palette.PRIMARY};
}}

/* ── Combo Box ────────────────────────────────────────────��──────── */
QComboBox {{
    background-color: {Palette.SURFACE};
    color: {Palette.TEXT_PRIMARY};
    border: 1.5px solid {Palette.BORDER};
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 30px;
}}

QComboBox:focus {{
    border-color: {Palette.PRIMARY};
}}

QComboBox:hover {{
    border-color: {Palette.BORDER_MUTED};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid {Palette.BORDER};
    background-color: transparent;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}}

QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {Palette.TEXT_SECONDARY};
}}

QComboBox::down-arrow:hover {{
    border-top-color: {Palette.PRIMARY};
}}

QComboBox QAbstractItemView {{
    background-color: {Palette.ELEVATED};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER};
    border-radius: 6px;
    selection-background-color: {Palette.PRIMARY};
    selection-color: {Palette.TEXT_ON_PRIMARY};
    padding: 4px;
    outline: none;
}}

QComboBox QAbstractItemView::item {{
    min-height: 28px;
    padding: 4px 8px;
    border-radius: 4px;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: rgba(41, 121, 255, 0.12);
    color: {Palette.PRIMARY_HOVER};
}}

/* ── Check Box ───────────────────────────────────────────────────── */
QCheckBox {{
    spacing: 8px;
    color: {Palette.TEXT_PRIMARY};
    background-color: transparent;
    border: none;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1.5px solid {Palette.BORDER_MUTED};
    border-radius: 4px;
    background-color: {Palette.SURFACE};
}}

QCheckBox::indicator:hover {{
    border-color: {Palette.PRIMARY};
}}

QCheckBox::indicator:checked {{
    background-color: {Palette.PRIMARY};
    border-color: {Palette.PRIMARY};
    image: none;  /* Replace with a checkmark image asset if desired */
}}

QCheckBox::indicator:checked:hover {{
    background-color: {Palette.PRIMARY_HOVER};
}}

QCheckBox::indicator:disabled {{
    border-color: {Palette.TEXT_DISABLED};
    background-color: {Palette.BASE};
}}

/* ── Radio Button ────────────────────────────────────────────────── */
QRadioButton {{
    spacing: 8px;
    color: {Palette.TEXT_PRIMARY};
    background-color: transparent;
    border: none;
}}

QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1.5px solid {Palette.BORDER_MUTED};
    border-radius: 8px;
    background-color: {Palette.SURFACE};
}}

QRadioButton::indicator:hover {{
    border-color: {Palette.PRIMARY};
}}

QRadioButton::indicator:checked {{
    background-color: {Palette.PRIMARY};
    border-color: {Palette.PRIMARY};
}}

/* ── Slider ──────────────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    border: none;
    height: 4px;
    background-color: {Palette.BORDER};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background-color: {Palette.PRIMARY};
    border-radius: 2px;
    height: 4px;
}}

QSlider::handle:horizontal {{
    background-color: {Palette.PRIMARY};
    border: 2px solid {Palette.BASE};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background-color: {Palette.PRIMARY_HOVER};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}

QSlider::groove:vertical {{
    border: none;
    width: 4px;
    background-color: {Palette.BORDER};
    border-radius: 2px;
}}

QSlider::sub-page:vertical {{
    background-color: {Palette.PRIMARY};
    border-radius: 2px;
    width: 4px;
}}

QSlider::handle:vertical {{
    background-color: {Palette.PRIMARY};
    border: 2px solid {Palette.BASE};
    width: 14px;
    height: 14px;
    margin: 0 -5px;
    border-radius: 7px;
}}

/* ── Progress Bar ────────────────────────────────────────────────── */
QProgressBar {{
    background-color: {Palette.SURFACE};
    border: none;
    border-radius: 5px;
    height: 8px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background-color: {Palette.PRIMARY};
    border-radius: 5px;
}}

/* ── Scroll Bar ─────────────────────────────────────────────────���── */
QScrollBar:vertical {{
    background-color: {Palette.SCROLLBAR_BG};
    width: 8px;
    margin: 0;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background-color: {Palette.SCROLLBAR_HANDLE};
    border-radius: 4px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {Palette.SCROLLBAR_HOVER};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {Palette.SCROLLBAR_BG};
    height: 8px;
    margin: 0;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background-color: {Palette.SCROLLBAR_HANDLE};
    border-radius: 4px;
    min-width: 24px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {Palette.SCROLLBAR_HOVER};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* ── Tab Widget ──────────────────────────────────────────────────── */
QTabWidget::pane {{
    background-color: {Palette.SURFACE};
    border: 1px solid {Palette.BORDER};
    border-radius: 0 6px 6px 6px;
}}

QTabBar::tab {{
    background-color: {Palette.BASE};
    color: {Palette.TEXT_SECONDARY};
    border: none;
    padding: 8px 18px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
}}

QTabBar::tab:hover {{
    color: {Palette.TEXT_PRIMARY};
    background-color: {Palette.ELEVATED};
}}

QTabBar::tab:selected {{
    background-color: {Palette.SURFACE};
    color: {Palette.PRIMARY};
    border-bottom: 2px solid {Palette.PRIMARY};
    font-weight: 600;
}}

/* ── Table View / Tree View ──────────────────────────────────────── */
QTableView,
QTreeView,
QListView {{
    background-color: {Palette.SURFACE};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER};
    border-radius: 6px;
    gridline-color: {Palette.BORDER};
    selection-background-color: {Palette.PRIMARY};
    selection-color: {Palette.TEXT_ON_PRIMARY};
    outline: none;
    alternate-background-color: {Palette.ELEVATED};
}}

QTableView::item,
QTreeView::item,
QListView::item {{
    padding: 5px 8px;
    border: none;
}}

QTableView::item:hover,
QTreeView::item:hover,
QListView::item:hover {{
    background-color: rgba(41, 121, 255, 0.10);
}}

QTableView::item:selected,
QTreeView::item:selected,
QListView::item:selected {{
    background-color: {Palette.PRIMARY};
    color: {Palette.TEXT_ON_PRIMARY};
}}

QHeaderView {{
    background-color: {Palette.BASE};
    border: none;
}}

QHeaderView::section {{
    background-color: {Palette.BASE};
    color: {Palette.TEXT_SECONDARY};
    border: none;
    border-right: 1px solid {Palette.BORDER};
    border-bottom: 1px solid {Palette.BORDER};
    padding: 6px 10px;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 9pt;
    letter-spacing: 0.6px;
}}

QHeaderView::section:hover {{
    color: {Palette.TEXT_PRIMARY};
    background-color: {Palette.ELEVATED};
}}

/* ── Menu Bar ────────────────────────────────────────────────────── */
QMenuBar {{
    background-color: {Palette.BASE};
    color: {Palette.TEXT_PRIMARY};
    border-bottom: 1px solid {Palette.BORDER};
    padding: 2px 4px;
    spacing: 2px;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 5px 10px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {Palette.ELEVATED};
    color: {Palette.PRIMARY};
}}

QMenuBar::item:pressed {{
    background-color: rgba(41, 121, 255, 0.15);
}}

/* ── Menu ────────────────────────────────────────────────────────── */
QMenu {{
    background-color: {Palette.ELEVATED};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.BORDER};
    border-radius: 8px;
    padding: 6px 4px;
}}

QMenu::item {{
    background-color: transparent;
    padding: 7px 24px 7px 12px;
    border-radius: 5px;
    margin: 1px 4px;
}}

QMenu::item:selected {{
    background-color: rgba(41, 121, 255, 0.14);
    color: {Palette.PRIMARY_HOVER};
}}

QMenu::item:disabled {{
    color: {Palette.TEXT_DISABLED};
}}

QMenu::separator {{
    height: 1px;
    background-color: {Palette.BORDER};
    margin: 5px 12px;
}}

QMenu::indicator {{
    width: 14px;
    height: 14px;
}}

/* ── Status Bar ──────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {Palette.BASE};
    color: {Palette.TEXT_SECONDARY};
    border-top: 1px solid {Palette.BORDER};
    font-size: 9pt;
}}

QStatusBar::item {{
    border: none;
}}

/* ── Tool Bar ────────────────────────────────────────────────────── */
QToolBar {{
    background-color: {Palette.BASE};
    border-bottom: 1px solid {Palette.BORDER};
    spacing: 4px;
    padding: 4px;
}}

QToolBar::separator {{
    width: 1px;
    background-color: {Palette.BORDER};
    margin: 4px 6px;
}}

/* ── Dock Widget ─────────────────────────────────────────────────── */
QDockWidget {{
    background-color: {Palette.BASE};
    color: {Palette.TEXT_PRIMARY};
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

QDockWidget::title {{
    background-color: {Palette.ELEVATED};
    padding: 6px 10px;
    border-bottom: 1px solid {Palette.BORDER};
    font-weight: 600;
    text-align: left;
}}

/* ── Group Box ───────────────────────────────────────────────────── */
QGroupBox {{
    background-color: {Palette.SURFACE};
    border: 1px solid {Palette.BORDER};
    border-radius: 8px;
    margin-top: 14px;
    padding: 14px 8px 8px 8px;
    font-weight: 600;
    color: {Palette.TEXT_SECONDARY};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: -1px;
    padding: 0 6px;
    background-color: {Palette.SURFACE};
    color: {Palette.PRIMARY};
    font-weight: 700;
    font-size: 9.5pt;
    letter-spacing: 0.4px;
}}

/* ── Tooltip ─────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {Palette.TOOLTIP_BG};
    color: {Palette.TEXT_PRIMARY};
    border: 1px solid {Palette.TOOLTIP_BORDER};
    border-radius: 5px;
    padding: 5px 10px;
    font-size: 9pt;
}}

/* ── Splitter ────────────────────────────────────────────────────── */
QSplitter::handle {{
    background-color: {Palette.BORDER};
}}

QSplitter::handle:horizontal {{
    width: 1px;
}}

QSplitter::handle:vertical {{
    height: 1px;
}}

QSplitter::handle:hover {{
    background-color: {Palette.PRIMARY};
}}

/* ── Stacked Widget ──────────────────────────────────────────────── */
QStackedWidget {{
    background-color: {Palette.BASE};
    border: none;
}}

/* ── Dialog Button Box ───────────────────────────────��───────────── */
QDialogButtonBox QPushButton {{
    min-width: 80px;
}}

/* ── Message Box ─────────────────────────────────────────────────── */
QMessageBox {{
    background-color: {Palette.ELEVATED};
    color: {Palette.TEXT_PRIMARY};
}}

QMessageBox QLabel {{
    color: {Palette.TEXT_PRIMARY};
}}

/* ── Calendar Widget ─────────────────────────────────────────────── */
QCalendarWidget QWidget {{
    background-color: {Palette.SURFACE};
    color: {Palette.TEXT_PRIMARY};
}}

QCalendarWidget QAbstractItemView:enabled {{
    background-color: {Palette.SURFACE};
    color: {Palette.TEXT_PRIMARY};
    selection-background-color: {Palette.PRIMARY};
    selection-color: {Palette.TEXT_ON_PRIMARY};
}}

QCalendarWidget QToolButton {{
    color: {Palette.PRIMARY};
    font-weight: bold;
    background-color: transparent;
}}
"""


# ---------------------------------------------------------------------------
# Font Setup
# ---------------------------------------------------------------------------
def load_roboto_font() -> None:
    """
    Attempt to load Roboto from the system.
    If unavailable, Qt will gracefully fall back to the closest sans-serif.
    To guarantee Roboto, bundle .ttf files and use:
        QFontDatabase.addApplicationFont(":/fonts/Roboto-Regular.ttf")
    """
    # If you have bundled Roboto fonts (optional):
    # QFontDatabase.addApplicationFont("fonts/Roboto-Regular.ttf")
    # QFontDatabase.addApplicationFont("fonts/Roboto-Bold.ttf")
    # QFontDatabase.addApplicationFont("fonts/Roboto-Medium.ttf")
    pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def apply_dark_theme(app: QApplication) -> None:
    """
    Apply the full dark theme to a QApplication instance.

    Usage::

        from PySide6.QtWidgets import QApplication
        from theme import apply_dark_theme
        import sys

        app = QApplication(sys.argv)
        apply_dark_theme(app)

        # ... build your UI here ...

        sys.exit(app.exec())
    """
    # Use Qt Fusion style as the base for consistent cross-platform rendering
    app.setStyle("Fusion")

    # Load fonts (add font files to project if bundling Roboto)
    load_roboto_font()

    # Set global default font
    font = QFont("Roboto", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # Apply the stylesheet
    app.setStyleSheet(DARK_STYLESHEET)