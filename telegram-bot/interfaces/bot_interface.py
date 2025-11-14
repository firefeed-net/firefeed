from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from telegram import Update
from telegram.ext import ContextTypes


class IBotService(ABC):
    @abstractmethod
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /start command."""
        pass

    @abstractmethod
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /settings command."""
        pass

    @abstractmethod
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /help command."""
        pass

    @abstractmethod
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /status command."""
        pass

    @abstractmethod
    async def change_language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for language change command."""
        pass

    @abstractmethod
    async def link_telegram_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /link command to link Telegram account."""
        pass

    @abstractmethod
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for callback buttons."""
        pass

    @abstractmethod
    async def handle_menu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for menu selection."""
        pass

    @abstractmethod
    async def debug(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for debug messages."""
        pass

    @abstractmethod
    async def send_personal_rss_items(self, prepared_rss_item, subscribers_cache=None):
        """Sends personal RSS items to subscribers."""
        pass

    @abstractmethod
    async def post_to_channel(self, prepared_rss_item):
        """Publishes RSS item to Telegram channels."""
        pass

    @abstractmethod
    def get_main_menu_keyboard(self, lang="en"):
        """Creates main menu keyboard."""
        pass

    @abstractmethod
    async def set_current_user_language(self, user_id: int, lang: str):
        """Sets user language in DB and memory."""
        pass

    @abstractmethod
    async def get_current_user_language(self, user_id: int) -> str:
        """Gets current user language from memory or DB."""
        pass

    @abstractmethod
    async def cleanup_expired_user_data(self, context=None):
        """Clears expired user data (older than 24 hours)."""
        pass

    @abstractmethod
    async def _show_settings_menu(self, bot, chat_id: int, user_id: int):
        """Displays settings menu."""
        pass

    @abstractmethod
    async def _show_settings_menu_from_callback(self, bot, chat_id: int, user_id: int):
        """Displays settings menu from callback."""
        pass