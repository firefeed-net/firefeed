# telegram_bot/models/rss_item.py - RSS item data structures
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class PreparedRSSItem:
    """Structure for storing prepared RSS item."""

    original_data: Dict[str, Any]
    translations: Dict[str, Dict[str, str]]
    image_filename: Optional[str]
    video_filename: Optional[str]
    feed_id: int