"""
src/ui/dialogs/add_book_dialog.py
----------------------------------
"Add Book" dialog — layout only, no business logic.
"""

from __future__ import annotations

from PySide6.QtCore    import Qt, QSize
from PySide6.QtWidgets import (QDialog, QWidget, QVBoxLayout,
                                QHBoxLayout, QLabel, QSizePolicy,
                                QToolButton, QFileDialog, QTextEdit,
                                QFrame)

from src.ui.themes.theme import Palette

from src.ui.widgets.line_edits        import PrimaryLineEdit, StatusLineEdit
from src.ui.widgets.labels            import (HeadingLabel, CaptionLabel,
                                               SectionDividerLabel)
from src.ui.widgets.selectors         import BaseComboBox, BaseSpinBox
from src.ui.widgets.buttons           import (PrimaryButton, SecondaryButton,
                                               GhostButton, IconButton,
                                               IconTextButton)
from src.ui.widgets.containers        import UnderlineTabWidget, BaseScrollArea
from src.ui.widgets.book_cover        import BookCoverWidget
from src.ui.widgets.rating            import RatingWidget


# ─────────────────────────────────────────────────────────────────────────────
# Layout helpers
# ─────��───────────────────────────────────────────────────────────────────────

_FIELD_H = 38   # canonical height for every single-line input


def _divider() -> QWidget:
    line = QWidget()
    line.setFixedHeight(1)
    line.setStyleSheet(
        f"background-color: {Palette.BORDER}; border: none;"
    )
    return line


def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {Palette.TEXT_SECONDARY};"
        "font-family: 'Roboto', sans-serif;"
        "font-size: 9pt; font-weight: 600;"
        "background: transparent; border: none;"
        "letter-spacing: 0.3px;"
    )
    return lbl


def _field_block(label: str, widget: QWidget,
                 hint: str = "") -> QWidget:
    c = QWidget()
    c.setStyleSheet("background: transparent; border: none;")
    lay = QVBoxLayout(c)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(4)
    lay.addWidget(_field_label(label))
    lay.addWidget(widget)
    if hint:
        lay.addWidget(CaptionLabel(hint))
    return c


def _row(*widgets: QWidget, spacing: int = 12) -> QWidget:
    """
    Horizontal row — no fixed height on the container so children
    (spin boxes, combo boxes) are never clipped.
    """
    c = QWidget()
    c.setStyleSheet("background: transparent; border: none;")
    lay = QHBoxLayout(c)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(spacing)
    for w in widgets:
        lay.addWidget(w, 1)
    return c


def _text_edit(placeholder: str,
               min_h: int = 90, max_h: int = 140) -> QTextEdit:
    te = QTextEdit()
    te.setPlaceholderText(placeholder)
    te.setMinimumHeight(min_h)
    te.setMaximumHeight(max_h)
    te.setStyleSheet(f"""
        QTextEdit {{
            background: {Palette.SURFACE};
            color: {Palette.TEXT_PRIMARY};
            border: 1.5px solid {Palette.BORDER};
            border-radius: 6px;
            padding: 8px;
            font-family: "Roboto", sans-serif;
            font-size: 10pt;
        }}
        QTextEdit:focus {{
            border-color: {Palette.PRIMARY};
            background: {Palette.ELEVATED};
        }}
    """)
    return te


def _date_chip(placeholder: str) -> QToolButton:
    btn = QToolButton()
    btn.setText(f"  📅  {placeholder}  ")
    btn.setFixedHeight(_FIELD_H)
    btn.setSizePolicy(
        QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
    )
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(f"""
        QToolButton {{
            background: {Palette.SURFACE};
            color: {Palette.TEXT_SECONDARY};
            border: 1.5px solid {Palette.BORDER};
            border-radius: 6px;
            padding: 0px 10px;
            font-family: "Roboto", sans-serif;
            font-size: 10pt;
        }}
        QToolButton:hover {{
            border-color: {Palette.PRIMARY};
            color: {Palette.TEXT_PRIMARY};
            background: {Palette.ELEVATED};
        }}
    """)
    return btn


def _form_card(title: str, *field_widgets: QWidget,
               spacing: int = 14) -> QFrame:
    """
    Rounded card for one form section.

    FIX (− symbol): the stylesheet selector is ONLY 'QFrame#FormCard {}'
    — an ID-scoped rule.  It does NOT use a wildcard (*) or a type
    selector that could cascade into QComboBox children.
    QComboBox already has its own instance-level stylesheet applied by
    BaseComboBox.__init__, which takes precedence over any ancestor rule.
    """
    card = QFrame()
    card.setObjectName("FormCard")
    # ID-scoped selector — never bleeds into child widgets
    card.setStyleSheet("""
        QFrame#FormCard {
            background-color: """ + Palette.ELEVATED + """;
            border: 1.5px solid """ + Palette.BORDER + """;
            border-radius: 10px;
        }
    """)

    lay = QVBoxLayout(card)
    lay.setContentsMargins(16, 14, 16, 16)
    lay.setSpacing(spacing)

    title_lbl = QLabel(title)
    title_lbl.setStyleSheet(
        f"color: {Palette.PRIMARY};"
        "font-family: 'Roboto', sans-serif;"
        "font-size: 8.5pt; font-weight: 700;"
        "letter-spacing: 0.8px;"
        "background: transparent; border: none;"
    )
    lay.addWidget(title_lbl)

    for w in field_widgets:
        lay.addWidget(w)

    return card


# ─────────────────────────────────────────────────────────────────────────────
# ISBN lookup bar
# ─────────────────────────────────────────────────────────────────────────────

class _IsbnBar(QWidget):
    """
    ISBN input + Lookup + Clear buttons in one row.

    FIX (alignment): StatusLineEdit is a compound widget whose total
    height (field + status message row) is larger than _FIELD_H.
    The lookup and clear buttons must match the *inner field* height,
    not the full StatusLineEdit height.

    Solution:
      - Read the inner field's sizeHint at construction time.
      - Set both buttons to exactly that height.
      - Use AlignVCenter on the layout so buttons centre against the
        taller StatusLineEdit container.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")

        self.isbn_field = StatusLineEdit(
            placeholder="Enter ISBN-10 or ISBN-13…"
        )

        # Height to match: the inner QLineEdit, not the container
        btn_h = self.isbn_field.field.sizeHint().height()
        btn_h = max(btn_h, _FIELD_H)   # floor at _FIELD_H

        self.lookup_btn = IconTextButton("🔍", "Lookup")
        self.lookup_btn.setFixedHeight(btn_h)

        self.clear_btn = GhostButton("Clear")
        self.clear_btn.setFixedHeight(btn_h)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        # AlignVCenter centres the fixed-height buttons against the
        # taller StatusLineEdit container
        row.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self.isbn_field, 1)
        row.addWidget(self.lookup_btn,
                      alignment=Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self.clear_btn,
                      alignment=Qt.AlignmentFlag.AlignVCenter)

        self.clear_btn.clicked.connect(self._on_clear)
        # TODO: connect self.lookup_btn.clicked → controller

    def _on_clear(self) -> None:
        self.isbn_field.field.clear()
        self.isbn_field.set_normal()

    def set_loading(self) -> None:
        self.isbn_field.set_normal()
        self.isbn_field.field.setPlaceholderText("Looking up…")
        self.lookup_btn.setEnabled(False)

    def set_success(self, msg: str = "Book found!") -> None:
        self.isbn_field.set_success(msg)
        self.lookup_btn.setEnabled(True)

    def set_error(self, msg: str = "ISBN not found.") -> None:
        self.isbn_field.set_error(msg)
        self.lookup_btn.setEnabled(True)

    def set_normal(self) -> None:
        self.isbn_field.set_normal()
        self.isbn_field.field.setPlaceholderText(
            "Enter ISBN-10 or ISBN-13…"
        )
        self.lookup_btn.setEnabled(True)

    def isbn(self) -> str:
        return self.isbn_field.field.text().strip()


# ─────────────────────────────────────────────────────────────────────────────
# Book Details form
# ─────────────────────────────────────────────────────────────────────────────

class _BookDetailsForm(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 24)
        lay.setSpacing(12)

        # ── Core Details ──────────────────────────────────────────────
        self.title_field     = PrimaryLineEdit(placeholder="e.g. Dune")
        self.author_field    = PrimaryLineEdit(
            placeholder="e.g. Frank Herbert"
        )
        self.publisher_field = PrimaryLineEdit(
            placeholder="e.g. Ace Books"
        )
        self.pub_year_spin   = self._make_year_spin()

        lay.addWidget(_form_card(
            "CORE DETAILS",
            _field_block("Title *",          self.title_field),
            _field_block("Author(s) *",      self.author_field,
                         hint="Separate multiple authors with a comma."),
            _row(
                _field_block("Publisher",        self.publisher_field),
                _field_block("Publication Year", self.pub_year_spin),
            ),
        ))

        # ── Classification ────────────────────────────────────────────
        self.genre_combo     = self._make_genre_combo()
        self.format_combo    = self._make_format_combo()
        self.language_combo  = self._make_language_combo()
        self.page_count_spin = self._make_page_spin()

        lay.addWidget(_form_card(
            "CLASSIFICATION",
            _row(
                _field_block("Genre",  self.genre_combo),
                _field_block("Format", self.format_combo),
            ),
            _row(
                _field_block("Language",   self.language_combo),
                _field_block("Page Count", self.page_count_spin),
            ),
        ))

        # ── Identifiers ───────────────────────────────────────────────
        self.isbn10_field = PrimaryLineEdit(placeholder="10-digit ISBN")
        self.isbn13_field = PrimaryLineEdit(placeholder="13-digit ISBN")

        lay.addWidget(_form_card(
            "IDENTIFIERS",
            _row(
                _field_block("ISBN-10", self.isbn10_field),
                _field_block("ISBN-13", self.isbn13_field),
            ),
        ))

        # ── Description ───────────────────────────────────────────────
        self.description_field = _text_edit(
            "Brief synopsis or back-cover text…"
        )
        lay.addWidget(_form_card(
            "DESCRIPTION / SYNOPSIS",
            _field_block("Description", self.description_field),
        ))

        lay.addStretch()

    @staticmethod
    def _make_year_spin() -> BaseSpinBox:
        from datetime import date
        return BaseSpinBox(minimum=1000,
                           maximum=date.today().year + 2,
                           value=date.today().year, step=1)

    @staticmethod
    def _make_page_spin() -> BaseSpinBox:
        return BaseSpinBox(minimum=1, maximum=9999, value=1, step=1)

    @staticmethod
    def _make_genre_combo() -> BaseComboBox:
        cb = BaseComboBox()
        cb.addItems(["Select genre…", "Fiction", "Non-Fiction",
                     "Science Fiction", "Fantasy", "Mystery", "Thriller",
                     "Horror", "Romance", "Biography", "History",
                     "Science", "Self-Help", "Children's",
                     "Graphic Novel", "Poetry", "Other"])
        return cb

    @staticmethod
    def _make_format_combo() -> BaseComboBox:
        cb = BaseComboBox()
        cb.addItems(["Select format…", "Hardcover", "Paperback",
                     "Mass Market Paperback", "E-Book",
                     "Audiobook", "PDF"])
        return cb

    @staticmethod
    def _make_language_combo() -> BaseComboBox:
        cb = BaseComboBox()
        cb.addItems(["English", "Spanish", "French", "German",
                     "Japanese", "Chinese", "Korean", "Portuguese",
                     "Italian", "Russian", "Arabic", "Other"])
        return cb


# ─────────────────────────────────────────────────────────────────────────────
# Reading Status form
# ───────────────────────────────────��─────────────────────────────────────────

class _ReadingStatusForm(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 24)
        lay.setSpacing(12)

        self.status_combo = BaseComboBox()
        self.status_combo.addItems([
            "Unread", "Currently Reading", "Finished",
            "Did Not Finish (DNF)", "On Hold", "Wishlist",
        ])
        lay.addWidget(_form_card(
            "READING STATUS",
            _field_block("Status", self.status_combo),
        ))

        self.start_date_btn  = _date_chip("Start date")
        self.finish_date_btn = _date_chip("Finish date")
        lay.addWidget(_form_card(
            "DATES",
            _row(
                _field_block("Started Reading",  self.start_date_btn),
                _field_block("Finished Reading", self.finish_date_btn),
            ),
        ))

        self.current_page_spin = BaseSpinBox(
            minimum=0, maximum=9999, value=0, step=1
        )
        self.total_pages_spin = BaseSpinBox(
            minimum=1, maximum=9999, value=1, step=1
        )
        lay.addWidget(_form_card(
            "READING PROGRESS",
            _row(
                _field_block("Current Page", self.current_page_spin),
                _field_block("Total Pages",  self.total_pages_spin),
            ),
            CaptionLabel(
                "Progress bar will be shown once a book is saved."
            ),
        ))

        self.notes_field = _text_edit(
            "Your thoughts, highlights, or a personal review…",
            min_h=100, max_h=160,
        )
        lay.addWidget(_form_card(
            "PERSONAL REVIEW",
            _field_block("Notes / Review", self.notes_field),
        ))

        lay.addStretch()


# ─────────────────────────────────────────────────────────────────────────────
# AddBookDialog
# ─────────────────────────────────────────────────────────────────────────────

class AddBookDialog(QDialog):
    """
    Modal "Add Book" dialog.

    Public surface
    --------------
    dlg.details_form   → _BookDetailsForm
    dlg.status_form    → _ReadingStatusForm
    dlg.cover_widget   → BookCoverWidget
    dlg.rating_widget  → RatingWidget
    dlg.isbn_bar       → _IsbnBar
    dlg.collect_data() → dict
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Book")
        self.setModal(True)
        self.setMinimumSize(QSize(860, 620))
        self.resize(QSize(960, 700))
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Palette.BASE};
                border: 1px solid {Palette.BORDER};
                border-radius: 12px;
            }}
        """)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_titlebar())
        root.addWidget(_divider())

        body = QHBoxLayout()
        body.setContentsMargins(24, 20, 24, 20)
        body.setSpacing(24)
        body.addWidget(self._build_left_panel(),  0)
        body.addWidget(self._build_right_panel(), 1)
        root.addLayout(body, 1)

        root.addWidget(_divider())
        root.addWidget(self._build_footer())

    def _build_titlebar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setStyleSheet(
            f"background-color: {Palette.ELEVATED}; border: none;"
        )
        close_btn = IconButton("✕", tooltip="Close", size="sm")
        close_btn.clicked.connect(self.reject)

        title_lbl = HeadingLabel("Add Book", level=3)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        spacer = QWidget()
        spacer.setFixedWidth(close_btn.sizeHint().width())
        spacer.setStyleSheet("background: transparent; border: none;")

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.addWidget(spacer)
        lay.addWidget(title_lbl, 1)
        lay.addWidget(close_btn)
        return bar

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(180)
        panel.setStyleSheet("background: transparent; border: none;")

        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.cover_widget = BookCoverWidget(width=160, height=220,
                                             radius=10)
        self.cover_widget.set_placeholder("", genre="")
        lay.addWidget(self.cover_widget,
                      alignment=Qt.AlignmentFlag.AlignHCenter)

        load_btn = IconTextButton("📁", "Load Cover")
        load_btn.setSizePolicy(QSizePolicy.Policy.Expanding,
                               QSizePolicy.Policy.Fixed)
        load_btn.clicked.connect(self._on_load_cover)
        lay.addWidget(load_btn)

        clear_cover_btn = GhostButton("Clear Cover")
        clear_cover_btn.setSizePolicy(QSizePolicy.Policy.Expanding,
                                      QSizePolicy.Policy.Fixed)
        clear_cover_btn.clicked.connect(self._on_clear_cover)
        lay.addWidget(clear_cover_btn)

        lay.addWidget(_divider())

        rating_lbl = QLabel("Your Rating")
        rating_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        rating_lbl.setStyleSheet(
            f"color: {Palette.TEXT_SECONDARY}; font-size: 9pt;"
            "font-weight: 600; font-family: 'Roboto', sans-serif;"
            "background: transparent; border: none;"
        )
        lay.addWidget(rating_lbl)

        self.rating_widget = RatingWidget(max_stars=5, half_stars=True,
                                           star_size=22)
        lay.addWidget(self.rating_widget,
                      alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch()
        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent; border: none;")

        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self.isbn_bar = _IsbnBar()
        lay.addWidget(self.isbn_bar)

        self.tab_widget = UnderlineTabWidget()

        self.details_form = _BookDetailsForm()
        details_scroll    = BaseScrollArea()
        details_scroll.setWidget(self.details_form)
        self.tab_widget.add_tab("Book Details", details_scroll)

        self.status_form  = _ReadingStatusForm()
        status_scroll     = BaseScrollArea()
        status_scroll.setWidget(self.status_form)
        self.tab_widget.add_tab("Reading Status", status_scroll)

        lay.addWidget(self.tab_widget, 1)
        return panel

    def _build_footer(self) -> QWidget:
        footer = QWidget()
        footer.setFixedHeight(60)
        footer.setStyleSheet(
            f"background-color: {Palette.ELEVATED}; border: none;"
        )
        cancel_btn   = SecondaryButton("Cancel")
        self.add_btn = PrimaryButton("Add Book")
        cancel_btn.clicked.connect(self.reject)
        self.add_btn.clicked.connect(self._on_add)

        lay = QHBoxLayout(footer)
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(10)
        lay.addStretch()
        lay.addWidget(cancel_btn)
        lay.addWidget(self.add_btn)
        return footer

    def _on_load_cover(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Cover Image", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if path:
            self.cover_widget.set_pixmap_from_path(path)

    def _on_clear_cover(self) -> None:
        self.cover_widget.set_placeholder(
            self.details_form.title_field.text(),
            self.details_form.genre_combo.currentText(),
        )

    def _on_add(self) -> None:
        self.accept()   # TODO: validate first

    def collect_data(self) -> dict:
        df = self.details_form
        sf = self.status_form
        return {
            "title":          df.title_field.text().strip(),
            "authors":        df.author_field.text().strip(),
            "publisher":      df.publisher_field.text().strip(),
            "pub_year":       df.pub_year_spin.value(),
            "genre":          df.genre_combo.currentText(),
            "format":         df.format_combo.currentText(),
            "language":       df.language_combo.currentText(),
            "page_count":     df.page_count_spin.value(),
            "isbn10":         df.isbn10_field.text().strip(),
            "isbn13":         df.isbn13_field.text().strip(),
            "description":    df.description_field.toPlainText().strip(),
            "reading_status": sf.status_combo.currentText(),
            "current_page":   sf.current_page_spin.value(),
            "total_pages":    sf.total_pages_spin.value(),
            "notes":          sf.notes_field.toPlainText().strip(),
            "rating":         self.rating_widget.rating(),
            "has_cover":      self.cover_widget.has_cover(),
            "isbn_lookup":    self.isbn_bar.isbn(),
        }