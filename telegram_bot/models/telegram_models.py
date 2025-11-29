# telegram_bot/models/telegram_models.py - Telegram-specific data structures
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TelegramPublication:
    """Telegram publication tracking structure."""
    translation_id: Optional[int]
    channel_id: int
    message_id: int


@dataclass
class FeedLimits:
    """Feed publication limits structure."""
    cooldown_minutes: int
    max_news_per_hour: int