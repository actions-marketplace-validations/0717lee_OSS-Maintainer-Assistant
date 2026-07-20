"""Memory / similarity index for duplicate detection."""
from .store import TfidfIndex, build_index

__all__ = ["TfidfIndex", "build_index"]
