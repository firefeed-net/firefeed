from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PreparedRSSItem:
    """Structure for storing prepared RSS item."""

    original_data: Dict[str, Any]
    translations: Dict[str, Dict[str, str]]
    image_filename: Optional[str]
    feed_id: int