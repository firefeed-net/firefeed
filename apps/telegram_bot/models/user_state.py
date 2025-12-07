# telegram_bot/models/user_state.py - User state data structures
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class UserState:
    """User state structure."""
    current_subs: list
    language: str
    last_access: float


@dataclass
class UserMenu:
    """User menu state structure."""
    menu: str
    last_access: float


@dataclass
class UserLanguage:
    """User language state structure."""
    language: str
    last_access: float