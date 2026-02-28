"""
src/models/book.py
------------------
Book data model.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Book:
    """Represents a single book entry in the library."""

    title:          str
    authors:        str
    publisher:      str      = ""
    pub_year:       int      = 0
    genre:          str      = ""
    format:         str      = ""
    language:       str      = "English"
    page_count:     int      = 0
    isbn10:         str      = ""
    isbn13:         str      = ""
    description:    str      = ""
    reading_status: str      = "Unread"
    current_page:   int      = 0
    total_pages:    int      = 0
    notes:          str      = ""
    rating:         float    = 0.0
    cover_path:     str      = ""
    book_id:        str      = field(default_factory=lambda: str(uuid.uuid4()))
    added_at:       str      = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )

    # ── Helpers ────────────────────────────────────────────────────────────

    def progress(self) -> float:
        """Reading progress as 0.0–1.0.  Returns 0 if no page data."""
        if self.total_pages > 0 and self.reading_status == "Currently Reading":
            return min(self.current_page / self.total_pages, 1.0)
        if self.reading_status == "Finished":
            return 1.0
        return 0.0

    def to_dict(self) -> dict:
        return {
            "book_id":        self.book_id,
            "added_at":       self.added_at,
            "title":          self.title,
            "authors":        self.authors,
            "publisher":      self.publisher,
            "pub_year":       self.pub_year,
            "genre":          self.genre,
            "format":         self.format,
            "language":       self.language,
            "page_count":     self.page_count,
            "isbn10":         self.isbn10,
            "isbn13":         self.isbn13,
            "description":    self.description,
            "reading_status": self.reading_status,
            "current_page":   self.current_page,
            "total_pages":    self.total_pages,
            "notes":          self.notes,
            "rating":         self.rating,
            "cover_path":     self.cover_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Book":
        return cls(
            book_id        = data.get("book_id",         str(uuid.uuid4())),
            added_at       = data.get("added_at",        ""),
            title          = data.get("title",           ""),
            authors        = data.get("authors",         ""),
            publisher      = data.get("publisher",       ""),
            pub_year       = int(data.get("pub_year",    0)),
            genre          = data.get("genre",           ""),
            format         = data.get("format",          ""),
            language       = data.get("language",        "English"),
            page_count     = int(data.get("page_count",  0)),
            isbn10         = data.get("isbn10",          ""),
            isbn13         = data.get("isbn13",          ""),
            description    = data.get("description",     ""),
            reading_status = data.get("reading_status",  "Unread"),
            current_page   = int(data.get("current_page", 0)),
            total_pages    = int(data.get("total_pages",   0)),
            notes          = data.get("notes",           ""),
            rating         = float(data.get("rating",    0.0)),
            cover_path     = data.get("cover_path",      ""),
        )

    @classmethod
    def from_dialog_data(cls, data: dict) -> "Book":
        """Create a Book from the dict returned by AddBookDialog.collect_data()."""
        return cls(
            title          = data.get("title",           ""),
            authors        = data.get("authors",         ""),
            publisher      = data.get("publisher",       ""),
            pub_year       = int(data.get("pub_year",    0)),
            genre          = data.get("genre",           ""),
            format         = data.get("format",          ""),
            language       = data.get("language",        "English"),
            page_count     = int(data.get("page_count",  0)),
            isbn10         = data.get("isbn10",          ""),
            isbn13         = data.get("isbn13",          ""),
            description    = data.get("description",     ""),
            reading_status = data.get("reading_status",  "Unread"),
            current_page   = int(data.get("current_page", 0)),
            total_pages    = int(data.get("total_pages",   0)),
            notes          = data.get("notes",           ""),
            rating         = float(data.get("rating",    0.0)),
        )
