"""
src/models/book_store.py
------------------------
In-memory book collection with optional JSON persistence.
"""

from __future__ import annotations

import json
import os
from typing import Callable, List, Optional

from src.models.book import Book


class BookStore:
    """
    Manages the list of books in memory and persists them to a JSON file.

    Parameters
    ----------
    path : str | None
        Path to the JSON file used for persistence.
        Pass ``None`` (default) to operate purely in memory.

    Usage::

        store = BookStore("books.json")
        store.add(Book(title="Dune", authors="Frank Herbert"))
        all_books = store.all()
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self._path: Optional[str] = path
        self._books: List[Book] = []
        self._listeners: List[Callable[[], None]] = []
        if path and os.path.isfile(path):
            self._load()

    # ── Public API ─────────────────────────────────────────────────────────

    def all(self) -> List[Book]:
        """Return a shallow copy of the book list."""
        return list(self._books)

    def get(self, book_id: str) -> Optional[Book]:
        """Return the book with the given id, or None."""
        for b in self._books:
            if b.book_id == book_id:
                return b
        return None

    def add(self, book: Book) -> None:
        """Append a book and persist."""
        self._books.append(book)
        self._save()
        self._notify()

    def update(self, book: Book) -> None:
        """Replace an existing book (matched by book_id) and persist."""
        for i, b in enumerate(self._books):
            if b.book_id == book.book_id:
                self._books[i] = book
                self._save()
                self._notify()
                return
        raise KeyError(f"Book with id {book.book_id!r} not found.")

    def remove(self, book_id: str) -> None:
        """Delete a book by id and persist."""
        before = len(self._books)
        self._books = [b for b in self._books if b.book_id != book_id]
        if len(self._books) < before:
            self._save()
            self._notify()

    def count(self) -> int:
        return len(self._books)

    def filter(
        self,
        *,
        status: Optional[str] = None,
        genre: Optional[str]  = None,
        query: Optional[str]  = None,
    ) -> List[Book]:
        """Return books matching ALL provided filters (case-insensitive)."""
        result = self._books
        if status:
            result = [b for b in result
                      if b.reading_status.lower() == status.lower()]
        if genre:
            result = [b for b in result
                      if b.genre.lower() == genre.lower()]
        if query:
            q = query.lower()
            result = [
                b for b in result
                if q in b.title.lower()
                or q in b.authors.lower()
                or q in b.isbn10.lower()
                or q in b.isbn13.lower()
            ]
        return list(result)

    # ── Change notifications ───────────────────────────────────────────────

    def on_change(self, callback: Callable[[], None]) -> None:
        """Register a callback that is called whenever the store changes."""
        self._listeners.append(callback)

    def _notify(self) -> None:
        for cb in self._listeners:
            cb()

    # ── Persistence ────────────────────────────────────────────────────────

    def _save(self) -> None:
        if not self._path:
            return
        data = [b.to_dict() for b in self._books]
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, self._path)

    def _load(self) -> None:
        with open(self._path, "r", encoding="utf-8") as fh:  # type: ignore[arg-type]
            content = fh.read().strip()
        if not content:
            return
        raw = json.loads(content)
        self._books = [Book.from_dict(item) for item in raw]
