# telegram_bot/utils/formatting_utils.py - Message formatting utilities
from telegram_bot.translations import TRANSLATED_FROM_LABELS, READ_MORE_LABELS, SOURCE_LABELS


def format_personal_rss_message(title: str, content: str, source: str, category: str, lang_note: str, user_lang: str, source_url: str) -> str:
    """Formats personal RSS message for user."""
    content_text = (
        f"🔥 <b>{title}</b>\n"
        f"\n\n{content}\n"
        f"\nFROM: {source}\n"
        f"CATEGORY: {category}\n{lang_note}\n"
        f"⚡ <a href='{source_url}'>{READ_MORE_LABELS.get(user_lang, 'Read more')}</a>"
    )
    return content_text


def format_channel_rss_message(title: str, content: str, lang_note: str, hashtags: str, source_url: str = None) -> str:
    """Formats RSS message for channel publication."""
    content_text = f"<b>{title}</b>\n"
    if content and content.strip():
        content_text += f"\n{content}\n"
    if source_url:
        content_text += f"\n🔗 <a href=\"{source_url}\">{SOURCE_LABELS.get('en', 'Source')}</a>\n"
    content_text += f"{lang_note}{hashtags}"
    return content_text


def create_lang_note(target_lang: str, original_lang: str) -> str:
    """Creates language note for translated content."""
    if target_lang != original_lang:
        return f"\n{TRANSLATED_FROM_LABELS.get(target_lang, 'Translated from')} {original_lang.upper()}\n"
    return ""


def create_hashtags(category: str, source: str) -> str:
    """Creates hashtags for channel messages."""
    return f"\n#{category} #{source}"


def truncate_caption(caption: str, max_length: int = 1024) -> str:
    """Truncates caption to fit Telegram limits."""
    if len(caption) <= max_length:
        return caption

    base_text = f"<b>{caption.split('<b>')[1].split('</b>')[0]}</b>"
    lang_note = ""
    hashtags = ""

    # Try to extract language note and hashtags
    lines = caption.split('\n')
    for line in reversed(lines):
        if line.startswith('#'):
            hashtags = '\n' + line
            break
        elif 'Translated from' in line or 'Переведено с' in line or 'Übersetzt von' in line or 'Traduit de' in line:
            lang_note = '\n' + line

    # Remove extracted lang_note and hashtags from caption to avoid duplication
    cleaned_caption = caption
    if lang_note:
        cleaned_caption = cleaned_caption.replace(lang_note, '')
    if hashtags:
        cleaned_caption = cleaned_caption.replace(hashtags, '')

    max_content_length = max_length - len(base_text) - len(lang_note) - len(hashtags)
    if max_content_length > 0:
        content_part = cleaned_caption.split('\n\n')[1] if '\n\n' in cleaned_caption else ""
        truncated_content = content_part[: max_content_length - 3] + "..." if content_part else ""
        return f"{base_text}\n{truncated_content}{lang_note}{hashtags}"
    else:
        return f"{base_text}{lang_note}{hashtags}"[:max_length-3] + "..."