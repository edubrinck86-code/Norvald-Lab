"""Infrastructure for detecting structural changes without exposing a vendor API."""

from .models import Change, ChangeSet
from .deepdiff_adapter import diff_structures

__all__ = ["Change", "ChangeSet", "diff_structures"]

