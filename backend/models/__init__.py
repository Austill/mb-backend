# backend/models/__init__.py

from .user import User
from .journal_entry import JournalEntry

# Optional: you can add __all__ to explicitly define what's exported
__all__ = ["User", "JournalEntry"]
