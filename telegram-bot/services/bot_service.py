import asyncio
import logging
import time
from typing import Dict, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import NetworkError, BadRequest, RetryAfter
from telegram.ext import ContextTypes

from ..interfaces.bot_interface import IBotService
from ..interfaces.user_manager_interface import IUserManagerService
from ..interfaces.database_interface import IDatabaseService
from ..models.user_state import UserStateManager
from ..utils.text_processor import TextProcessor
from ..utils.retry_decorator import retry_on_failure

logger = logging.getLogger(__name__)


class BotService(IBotService):
    """Service for Telegram bot operations."""

    def __init__(self, user_manager_service: IUserManagerService, database_service: IDatabaseService,
                 user_state_manager: UserStateManager, send_semaphore: asyncio.Semaphore,
                 get_message, lang_names, translated_from_labels, read_more_labels, source_labels):
        self.user_manager_service = user_manager_service
        self.database_service = database_service
        self.user_state_manager = user_state_manager
        self.send_semaphore = send_semaphore
        self.get_message = get_message
        self.lang_names = lang_names
        self.translated_from_labels = translated_from_labels
        self.read_more_labels = read_more_labels
        self.source_labels = source_labels

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /start command."""
        user = update.effective_user
        user_id = user.id
        lang = await self.get_current_user_language(user_id)
        welcome_text = self.get_message("welcome", lang, user_name=user.first_name)
        await update.message.reply_text(welcome_text, reply_markup=self.get_main_menu_keyboard(lang))
        self.user_state_manager.set_user_current_menu(user_id, {"menu": "main", "last_access": time.time()})

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /settings command."""
        user_id = update.effective_user.id
        try:
            logger.info(f"Loading settings for user {user_id}")
            settings = await self.user_manager_service.get_user_settings(user_id)
            logger.info(f"Loaded settings for user {user_id}: {settings}")
            current_subs = settings["subscriptions"] if isinstance(settings["subscriptions"], list) else []
            self.user_state_manager.set_user_state(user_id, {"current_subs": current_subs, "language": settings["language"], "last_access": time.time()})
            await self._show_settings_menu(context.bot, update.effective_chat.id, user_id)
            self.user_state_manager.set_user_current_menu(user_id, {"menu": "settings", "last_access": time.time()})
        except Exception as e:
            logger.error(f"Error in /settings command for {user_id}: {e}")
            lang = await self.get_current_user_language(user_id)
            await update.message.reply_text(self.get_message("settings_error", lang))

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /help command."""
        user_id = update.effective_user.id
        lang = await self.get_current_user_language(user_id)
        help_text = self.get_message("help_text", lang)
        await update.message.reply_text(help_text, parse_mode="HTML", reply_markup=self.get_main_menu_keyboard(lang))
        self.user_state_manager.set_user_current_menu(user_id, {"menu": "main", "last_access": time.time()})

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /status command."""
        user_id = update.effective_user.id
        lang = await self.get_current_user_language(user_id)
        settings = await self.user_manager_service.get_user_settings(user_id)
        categories = settings["subscriptions"]
        categories_text = ", ".join(categories) if categories else self.get_message("no_subscriptions", lang)
        status_text = self.get_message(
            "status_text", lang, language=self.lang_names.get(settings["language"], "English"), categories=categories_text
        )
        await update.message.reply_text(status_text, parse_mode="HTML", reply_markup=self.get_main_menu_keyboard(lang))
        self.user_state_manager.set_user_current_menu(user_id, {"menu": "main", "last_access": time.time()})

    async def change_language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for language change command."""
        user_id = update.effective_user.id
        lang = await self.get_current_user_language(user_id)
        keyboard = [
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de")],
            [InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr")],
        ]
        await update.message.reply_text(self.get_message("language_select", lang), reply_markup=InlineKeyboardMarkup(keyboard))
        self.user_state_manager.set_user_current_menu(user_id, {"menu": "language", "last_access": time.time()})

    async def link_telegram_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /link command to link Telegram account."""
        user_id = update.effective_user.id
        lang = await self.get_current_user_language(user_id)

        if not context.args:
            await update.message.reply_text(
                "Usage: /link <link_code>\n\n" "Get the link code in your personal account on the site.",
                reply_markup=self.get_main_menu_keyboard(lang),
            )
            self.user_state_manager.set_user_current_menu(user_id, {"menu": "main", "last_access": time.time()})
            return

        link_code = context.args[0].strip()

        # Check code via UserManager
        success = await self.user_manager_service.confirm_telegram_link(user_id, link_code)

        if success:
            await update.message.reply_text(
                "✅ Your Telegram account has been successfully linked to your site account!\n\n"
                "Now you can manage settings through the site or bot.",
                reply_markup=self.get_main_menu_keyboard(lang),
            )
        else:
            await update.message.reply_text(
                "❌ Link code is invalid or expired.\n\n"
                "Please generate a new code in your personal account on the site.",
                reply_markup=self.get_main_menu_keyboard(lang),
            )

        self.user_state_manager.set_user_current_menu(user_id, {"menu": "main", "last_access": time.time()})

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for callback buttons."""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        try:
            if user_id not in self.user_state_manager.user_states:
                subs = await self.user_manager_service.get_subscribers_for_category("")  # This might need adjustment
                current_subs = []  # Placeholder
                self.user_state_manager.set_user_state(user_id, {"current_subs": current_subs, "language": await self.get_current_user_language(user_id), "last_access": time.time()})
            state = self.user_state_manager.get_user_state(user_id)
            current_lang = state["language"]
            if query.data.startswith("toggle_"):
                category = query.data.split("_", 1)[1]
                current_subs = state["current_subs"]
                if category in current_subs:
                    current_subs.remove(category)
                else:
                    current_subs.append(category)
                state["current_subs"] = current_subs
                try:
                    await query.message.delete()
                except Exception:
                    pass
                await self._show_settings_menu_from_callback(context.bot, query.message.chat_id, user_id)
            elif query.data == "save_settings":
                # Save category names as strings
                logger.info(
                    f"Saving settings for user {user_id}: subscriptions={state['current_subs']}, language={state['language']}"
                )
                result = await self.user_manager_service.save_user_settings(user_id, state["current_subs"], state["language"])
                logger.info(f"Save result for user {user_id}: {result}")
                self.user_state_manager.user_states.pop(user_id, None)
                try:
                    await query.message.delete()
                except Exception:
                    pass
                user = await context.bot.get_chat(user_id)
                welcome_text = (
                    self.get_message("settings_saved", current_lang)
                    + "\n"
                    + self.get_message("welcome", current_lang, user_name=user.first_name)
                )
                await context.bot.send_message(
                    chat_id=user_id, text=welcome_text, reply_markup=self.get_main_menu_keyboard(current_lang)
                )
                self.user_state_manager.set_user_current_menu(user_id, {"menu": "main", "last_access": time.time()})
            elif query.data.startswith("lang_"):
                lang = query.data.split("_", 1)[1]
                await self.set_current_user_language(user_id, lang)
                if user_id in self.user_state_manager.user_states:
                    self.user_state_manager.user_states[user_id]["language"] = lang
                try:
                    await query.message.delete()
                except Exception:
                    pass
                user = await context.bot.get_chat(user_id)
                welcome_text = (
                    self.get_message("language_changed", lang, language=self.lang_names.get(lang, "English"))
                    + "\n"
                    + self.get_message("welcome", lang, user_name=user.first_name)
                )
                await context.bot.send_message(
                    chat_id=user_id, text=welcome_text, reply_markup=self.get_main_menu_keyboard(lang)
                )
                self.user_state_manager.set_user_current_menu(user_id, {"menu": "main", "last_access": time.time()})
            elif query.data == "change_lang":
                current_lang = await self.get_current_user_language(user_id)
                keyboard = [
                    [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
                    [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
                    [InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de")],
                    [InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr")],
                ]
                await query.message.edit_text(
                    text=self.get_message("language_select", current_lang), reply_markup=InlineKeyboardMarkup(keyboard)
                )
                self.user_state_manager.set_user_current_menu(user_id, {"menu": "language", "last_access": time.time()})
        except Exception as e:
            logger.error(f"Error processing button for {user_id}: {e}")
            current_lang = await self.get_current_user_language(user_id)
            await context.bot.send_message(
                chat_id=user_id,
                text=self.get_message("button_error", current_lang),
                reply_markup=self.get_main_menu_keyboard(current_lang),
            )
            self.user_state_manager.set_user_current_menu(user_id, {"menu": "main", "last_access": time.time()})

    async def handle_menu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for menu selection."""
        user_id = update.effective_user.id
        lang = await self.get_current_user_language(user_id)
        text = update.message.text
        menu_actions = {
            self.get_message("menu_settings", lang): self.settings_command,
            self.get_message("menu_help", lang): self.help_command,
            self.get_message("menu_status", lang): self.status_command,
            self.get_message("menu_language", lang): self.change_language_command,
        }
        action = menu_actions.get(text)
        if action:
            await action(update, context)
            return
        all_languages = ["en", "ru", "de", "fr"]
        for check_lang in all_languages:
            if text in [self.get_message(f"menu_{m}", check_lang) for m in ["settings", "help", "status", "language"]]:
                await self.set_current_user_language(user_id, check_lang)
                new_menu_actions = {
                    self.get_message("menu_settings", check_lang): self.settings_command,
                    self.get_message("menu_help", check_lang): self.help_command,
                    self.get_message("menu_status", check_lang): self.status_command,
                    self.get_message("menu_language", check_lang): self.change_language_command,
                }
                new_action = new_menu_actions.get(text)
                if new_action:
                    await new_action(update, context)
                return
        logger.info(f"Unknown menu selection for {user_id}: {text}")

    async def debug(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for debug messages."""
        user_id = update.effective_user.id
        lang = await self.get_current_user_language(user_id)
        await update.message.reply_text(self.get_message("bot_active", lang), reply_markup=self.get_main_menu_keyboard(lang))
        self.user_state_manager.set_user_current_menu(user_id, {"menu": "main", "last_access": time.time()})

    @retry_on_failure()
    async def send_personal_rss_items(self, prepared_rss_item, subscribers_cache=None):
        """Sends personal RSS items to subscribers."""
        # Implementation from bot.py
        news_id = prepared_rss_item.original_data.get("id")
        logger.info(f"Sending personal RSS item: {prepared_rss_item.original_data['title'][:50]}...")
        category = prepared_rss_item.original_data.get("category")
        if not category:
            logger.warning(f"RSS item {news_id} has no category")
            return

        # Use subscribers cache if provided
        if subscribers_cache is not None:
            subscribers = subscribers_cache.get(category, [])
        else:
            # Fallback to old method if cache not provided
            subscribers = await self.user_manager_service.get_subscribers_for_category(category)

        if not subscribers:
            logger.debug(f"No subscribers for category {category}")
            return
        translations_cache = prepared_rss_item.translations
        original_rss_item_lang = prepared_rss_item.original_data.get("lang", "")

        for i, user in enumerate(subscribers):
            try:
                user_id = user["id"]
                user_lang = user.get("language_code", "en")

                # Check if item has content in user's language
                title_to_send = None
                content_to_send = None

                # If user's language matches item's original language
                if user_lang == original_rss_item_lang:
                    title_to_send = prepared_rss_item.original_data["title"]
                    content_to_send = prepared_rss_item.original_data.get("content", "")
                # Otherwise, look for translation in user's language
                elif user_lang in translations_cache and translations_cache[user_lang]:
                    translation_data = translations_cache[user_lang]
                    title_to_send = translation_data.get("title", "")
                    content_to_send = translation_data.get("content", "")

                # If no suitable content, skip user
                if not title_to_send or not title_to_send.strip():
                    logger.debug(f"Skipping user {user_id} - no content in language {user_lang}")
                    continue

                title_to_send = TextProcessor.clean(title_to_send)
                content_to_send = TextProcessor.clean(content_to_send)

                lang_note = ""
                if user_lang != original_rss_item_lang:
                    lang_note = (
                        f"\n🌐 {self.translated_from_labels.get(user_lang, 'Translated from')} {original_rss_item_lang.upper()}\n"
                    )
                content_text = (
                    f"🔥 <b>{title_to_send}</b>\n"
                    f"\n\n{content_to_send}\n"
                    f"\nFROM: {prepared_rss_item.original_data.get('source', 'Unknown Source')}\n"
                    f"CATEGORY: {category}\n{lang_note}\n"
                    f"⚡ <a href='{prepared_rss_item.original_data.get('link', '#')}'>{self.read_more_labels.get(user_lang, 'Read more')}</a>"
                )
                image_filename = prepared_rss_item.image_filename
                logger.debug(f"send_personal_rss_items image_filename = {image_filename}")

                # Note: Image validation and sending logic would need bot instance, so this is simplified
                # In full implementation, inject bot or use context

            except Exception as e:
                logger.error(f"Error sending personal RSS item to user {user.get('id', 'Unknown ID')}: {e}")

    @retry_on_failure()
    async def post_to_channel(self, prepared_rss_item):
        """Publishes RSS item to Telegram channels."""
        # Implementation from bot.py, but needs bot instance
        # This is a placeholder; full implementation requires bot context
        pass

    def get_main_menu_keyboard(self, lang="en"):
        """Creates main menu keyboard."""
        return ReplyKeyboardMarkup(
            [
                [KeyboardButton(self.get_message("menu_settings", lang)), KeyboardButton(self.get_message("menu_help", lang))],
                [KeyboardButton(self.get_message("menu_status", lang)), KeyboardButton(self.get_message("menu_language", lang))],
            ],
            resize_keyboard=True,
            input_field_placeholder=self.get_message("menu_placeholder", lang),
        )

    async def set_current_user_language(self, user_id: int, lang: str):
        """Sets user language in DB and memory."""
        await self.user_manager_service.set_user_language(user_id, lang)

    async def get_current_user_language(self, user_id: int) -> str:
        """Gets current user language from memory or DB."""
        state = self.user_state_manager.get_user_language(user_id)
        if state:
            return state["language"]
        lang = await self.user_manager_service.get_user_language(user_id)
        if lang:
            self.user_state_manager.set_user_language(user_id, lang)
        return lang or "en"

    async def cleanup_expired_user_data(self, context=None):
        """Clears expired user data (older than 24 hours)."""
        states, menus, langs = self.user_state_manager.cleanup_expired_data()
        if states or menus or langs:
            logger.info(f"[CLEANUP] Cleared expired data: states={states}, menus={menus}, langs={langs}")

    async def _show_settings_menu(self, bot, chat_id: int, user_id: int):
        """Displays settings menu."""
        state = self.user_state_manager.get_user_state(user_id)
        if not state:
            return
        current_subs = state["current_subs"]
        current_lang = state["language"]
        try:
            # Need to inject API client for categories
            # Placeholder
            categories = []  # await self.api_client_service.get_categories()
            keyboard = []
            for category in categories:
                category_name = category.get("name", str(category))
                is_selected = category_name in current_subs
                text = f"{'✅ ' if is_selected else '🔲 '}{category_name.capitalize()}"
                keyboard.append([InlineKeyboardButton(text, callback_data=f"toggle_{category_name}")])
            keyboard.append([InlineKeyboardButton(self.get_message("save_button", current_lang), callback_data="save_settings")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await bot.send_message(
                chat_id=chat_id, text=self.get_message("settings_title", current_lang), reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error in _show_settings_menu for {user_id}: {e}")

    async def _show_settings_menu_from_callback(self, bot, chat_id: int, user_id: int):
        """Displays settings menu from callback."""
        await self._show_settings_menu(bot, chat_id, user_id)