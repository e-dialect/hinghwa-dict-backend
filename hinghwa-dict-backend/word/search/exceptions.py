class SearchUnavailable(RuntimeError):
    """Raised when the semantic index cannot safely serve a query."""


class SourceScanLimit(RuntimeError):
    """Reconciliation exceeded its explicit CPU/I/O budget; retry, never trust stale data."""
