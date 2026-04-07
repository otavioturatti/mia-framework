"""MIA Framework — Custom exceptions."""


class MiaError(Exception):
    """Raised when a MIA operation fails (invalid file, missing sheet, I/O error)."""
