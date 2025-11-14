import re
import html
import logging

logger = logging.getLogger(__name__)


class TextProcessor:
    """Class for processing and validating text"""

    @staticmethod
    def clean(raw_html: str) -> str:
        """Removes all HTML tags and converts HTML entities"""
        if not raw_html:
            return ""

        # Work with a copy
        clean_text = str(raw_html)

        # Replace special quotes from NLP models
        # Handle various variants: <<, < <, <  < etc.
        clean_text = re.sub(r"<\s*<", "«", clean_text)
        clean_text = re.sub(r">\s*>", "»", clean_text)

        # Remove HTML tags
        clean_text = re.sub(r"<[^>]*>", "", clean_text)

        # Decode HTML entities
        try:
            clean_text = html.unescape(clean_text)
        except Exception:
            # If html.unescape fails, leave as is
            pass

        # Normalize spaces
        clean_text = re.sub(r"\s+", " ", clean_text)

        return clean_text.strip()

    @staticmethod
    def normalize(text: str) -> str:
        """Normalizes spaces in text"""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def validate_length(text: str, min_length: int = 1, max_length: int = 10000) -> bool:
        """Checks text length"""
        if not text:
            return min_length == 0
        return min_length <= len(text) <= max_length

    @staticmethod
    def remove_duplicates(text: str) -> str:
        """Removes consecutive duplicate words"""
        words = text.split()
        if not words:
            return text

        deduped_words = [words[0]]
        for word in words[1:]:
            # Check not only exact match, but also partial
            if word.lower() != deduped_words[-1].lower() and not word.lower().startswith(deduped_words[-1].lower()[:3]):
                deduped_words.append(word)

        return " ".join(deduped_words)

    @staticmethod
    def extract_sentences(text: str, lang_code: str = "en") -> list:
        """Splits text into sentences (simplified version without spaCy)"""
        # Simple heuristic for sentence splitting
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def is_gibberish(text: str, threshold: float = 0.7) -> bool:
        """Checks if text is gibberish"""
        if not text or len(text) < 10:
            return False

        # Check the ratio of letters to total characters
        alphanumeric_chars = len(re.findall(r"[a-zA-Zа-яА-Я0-9]", text))
        total_chars = len(text)

        if total_chars == 0:
            return True

        ratio = alphanumeric_chars / total_chars
        return ratio < threshold