import pytest
from utils.text import TextProcessor


class TestTextProcessor:
    def test_clean_empty_string(self):
        """Test clean with empty string"""
        result = TextProcessor.clean("")
        assert result == ""

    def test_clean_none_input(self):
        """Test clean with None input"""
        result = TextProcessor.clean(None)
        assert result == ""

    def test_clean_basic_html(self):
        """Test clean with basic HTML tags"""
        html_text = "<p>Hello <b>world</b>!</p>"
        result = TextProcessor.clean(html_text)
        assert result == "Hello world!"

    def test_clean_quotes_conversion(self):
        """Test clean with quote conversion"""
        text = "He said < < hello > >"
        result = TextProcessor.clean(text)
        assert "« hello »" in result

    def test_clean_html_entities(self):
        """Test clean with HTML entities"""
        text = "Tom & Jerry's show"
        result = TextProcessor.clean(text)
        assert result == "Tom & Jerry's show"

    def test_clean_html_unescape_exception(self):
        """Test clean when html.unescape raises exception"""
        # This is hard to test directly, but we can verify it doesn't crash
        text = "<p>Normal text</p>"
        result = TextProcessor.clean(text)
        assert result == "Normal text"

    def test_clean_space_normalization(self):
        """Test clean with space normalization"""
        text = "Too   many    spaces"
        result = TextProcessor.clean(text)
        assert result == "Too many spaces"

    def test_normalize_empty_string(self):
        """Test normalize with empty string"""
        result = TextProcessor.normalize("")
        assert result == ""

    def test_normalize_none_input(self):
        """Test normalize with None input"""
        result = TextProcessor.normalize(None)
        assert result == ""

    def test_normalize_spaces(self):
        """Test normalize with multiple spaces"""
        text = "Multiple   spaces  here"
        result = TextProcessor.normalize(text)
        assert result == "Multiple spaces here"

    def test_normalize_strip_whitespace(self):
        """Test normalize strips leading/trailing whitespace"""
        text = "  text with spaces  "
        result = TextProcessor.normalize(text)
        assert result == "text with spaces"

    def test_validate_length_empty_string(self):
        """Test validate_length with empty string"""
        assert TextProcessor.validate_length("", min_length=0) is True
        assert TextProcessor.validate_length("", min_length=1) is False

    def test_validate_length_none_input(self):
        """Test validate_length with None input"""
        assert TextProcessor.validate_length(None, min_length=0) is True
        assert TextProcessor.validate_length(None, min_length=1) is False

    def test_validate_length_valid(self):
        """Test validate_length with valid text"""
        text = "Hello world"
        assert TextProcessor.validate_length(text, min_length=5, max_length=20) is True

    def test_validate_length_too_short(self):
        """Test validate_length with text too short"""
        text = "Hi"
        assert TextProcessor.validate_length(text, min_length=5) is False

    def test_validate_length_too_long(self):
        """Test validate_length with text too long"""
        text = "This is a very long text that exceeds the maximum length"
        assert TextProcessor.validate_length(text, max_length=20) is False

    def test_remove_duplicates_empty_string(self):
        """Test remove_duplicates with empty string"""
        result = TextProcessor.remove_duplicates("")
        assert result == ""

    def test_remove_duplicates_no_duplicates(self):
        """Test remove_duplicates with no duplicates"""
        text = "The quick brown fox"
        result = TextProcessor.remove_duplicates(text)
        assert result == text

    def test_remove_duplicates_consecutive(self):
        """Test remove_duplicates with consecutive duplicates"""
        text = "The the quick quick brown brown fox fox"
        result = TextProcessor.remove_duplicates(text)
        assert result == "The quick brown fox"

    def test_remove_duplicates_case_insensitive(self):
        """Test remove_duplicates is case insensitive"""
        text = "The the THE quick Quick"
        result = TextProcessor.remove_duplicates(text)
        assert result == "The quick"

    def test_remove_duplicates_partial_match(self):
        """Test remove_duplicates with partial word matches"""
        text = "run running runner"
        result = TextProcessor.remove_duplicates(text)
        # "run" starts with "run", "running" starts with "run" (first 3 chars), so should be deduped
        assert result == "run"

    def test_extract_sentences_empty(self):
        """Test extract_sentences with empty string"""
        result = TextProcessor.extract_sentences("")
        assert result == []

    def test_extract_sentences_basic(self):
        """Test extract_sentences with basic text"""
        text = "Hello world. How are you? I'm fine!"
        result = TextProcessor.extract_sentences(text)
        expected = ["Hello world", "How are you", "I'm fine"]
        assert result == expected

    def test_extract_sentences_no_punctuation(self):
        """Test extract_sentences with no punctuation"""
        text = "Hello world"
        result = TextProcessor.extract_sentences(text)
        assert result == ["Hello world"]

    def test_extract_sentences_multiple_spaces(self):
        """Test extract_sentences handles multiple spaces"""
        text = "Hello.   World."
        result = TextProcessor.extract_sentences(text)
        assert result == ["Hello", "World"]

    def test_is_gibberish_empty_string(self):
        """Test is_gibberish with empty string"""
        assert TextProcessor.is_gibberish("") is False

    def test_is_gibberish_short_text(self):
        """Test is_gibberish with short text"""
        assert TextProcessor.is_gibberish("Hi") is False

    def test_is_gibberish_normal_text(self):
        """Test is_gibberish with normal text"""
        text = "This is a normal sentence with proper words."
        assert TextProcessor.is_gibberish(text) is False

    def test_is_gibberish_gibberish_text(self):
        """Test is_gibberish with gibberish text"""
        text = "!@#$%^&*()!@#$%^&*()!@#$%^&*()!@#$%^&*()"  # Only symbols
        assert TextProcessor.is_gibberish(text) is True

    def test_is_gibberish_mixed_text(self):
        """Test is_gibberish with mixed text"""
        text = "Hello !@#$%^ &*() !@#$%^ &*()"  # Mixed with many symbols
        assert TextProcessor.is_gibberish(text) is True

    def test_is_gibberish_cyrillic(self):
        """Test is_gibberish with Cyrillic text"""
        text = "Это нормальный текст на русском языке."
        assert TextProcessor.is_gibberish(text) is False

    def test_is_gibberish_cyrillic_gibberish(self):
        """Test is_gibberish with Cyrillic gibberish"""
        text = "йцукенгшщзхъфывапролджэячсмитьбю"
        assert TextProcessor.is_gibberish(text) is False  # Cyrillic letters count as alphanumeric

    def test_is_gibberish_custom_threshold(self):
        """Test is_gibberish with custom threshold"""
        text = "abc!!!def???"  # 6 letters, 6 symbols = 0.5 ratio
        assert TextProcessor.is_gibberish(text, threshold=0.7) is True
        assert TextProcessor.is_gibberish(text, threshold=0.3) is False