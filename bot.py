import asyncio
import re
import html
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN, CHANNEL_ID, FIRE_EMOJI, CATEGORIES
from parser import fetch_news
from database import init_db, is_news_new, mark_as_published, get_user_preferences, save_user_preferences, get_all_users

# Добавляем обработчики команд
def setup_handlers(application):
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CallbackQueryHandler(button_handler))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n"
        "Я бот FireFeed - твой персональный агрегатор новостей.\n\n"
        "⚙️ Настрой подписки: /settings\n"
        "ℹ️ Помощь: /help"
    )
    await update.message.reply_text(welcome_text)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показываем меню настроек"""
    user_id = update.effective_user.id
    current_subs = get_user_preferences(user_id)
    
    keyboard = []
    # Создаем кнопки для всех категорий
    for category in CATEGORIES.keys():
        is_selected = category in current_subs
        text = f"{'✅ ' if is_selected else '🔲 '}{category.capitalize()}"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"toggle_{category}")])
    
    # Кнопка сохранения
    keyboard.append([InlineKeyboardButton("💾 Сохранить", callback_data="save_settings")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚙️ Выберите интересующие вас категории:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    current_subs = get_user_preferences(user_id) or []
    
    if query.data.startswith("toggle_"):
        # Переключаем категорию
        category = query.data.split("_")[1]
        
        if category in current_subs:
            current_subs.remove(category)
        else:
            current_subs.append(category)
            
        # Обновляем кнопки
        keyboard = []
        for cat in CATEGORIES.keys():
            is_selected = cat in current_subs
            text = f"{'✅ ' if is_selected else '🔲 '}{cat.capitalize()}"
            keyboard.append([InlineKeyboardButton(text, callback_data=f"toggle_{cat}")])
        
        keyboard.append([InlineKeyboardButton("💾 Сохранить", callback_data="save_settings")])
        
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "save_settings":
        # Сохраняем настройки
        save_user_preferences(user_id, current_subs)
        await query.edit_message_text("✅ Настройки сохранены!\nНовости будут приходить по выбранным категориям.")

def clean_html(raw_html):
    """Удаляет все HTML-теги и преобразует HTML-сущности"""
    if not raw_html:
        return ""
    
    # Удаляем все теги
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
    
    # Заменяем HTML-сущности (например, &amp; → &)
    clean_text = html.unescape(clean_text)
    
    # Удаляем лишние пробелы
    return re.sub(r'\s+', ' ', clean_text).strip()

async def monitor_news_task(context: ContextTypes.DEFAULT_TYPE):
    """Периодическая задача для мониторинга новостей"""
    try:
        print("🔎 Проверка новостей...")
        news_list = await fetch_news()
        for news in news_list:
            if is_news_new(news['id']):
                await post_to_channel(context.bot, news)
    except Exception as e:
        print(f"⚠️ Ошибка мониторинга: {e}")

async def post_to_channel(bot, news_item):
    try:
        # Очищаем описание от HTML
        clean_description = clean_html(news_item['description'])
        hashtags = f"\n#{news_item['category']}_news #{news_item['source']}"
        
        # Форматируем сообщение с категорией
        message = (
            f"{FIRE_EMOJI} <b>{html.escape(news_item['title'])}</b>\n"
            f"{clean_description}\n\n"
            f"⚡ <a href='{news_item['link']}'>Читать полностью</a>"
            f"\n\n{hashtags}"
        )
        
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode='HTML',
            disable_web_page_preview=False
        )
        mark_as_published(news_item['id'])
        print(f"✅ [{news_item['category']}] Опубликовано: {news_item['title'][:50]}...")
    except TelegramError as e:
        print(f"❌ Ошибка отправки: {e}")

async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"⚡ Получено сообщение: {update.message.text}")
    await update.message.reply_text("Бот активен!")

def main():
    """Точка входа с использованием JobQueue"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.ALL, debug))
    
    # Регистрируем периодическую задачу
    job_queue = application.job_queue
    job_queue.run_repeating(
        callback=monitor_news_task, 
        interval=60,  # проверка каждые 60 секунд
        first=1  # запустить через 1 секунду после старта
    )
    
    print("🟢 Бот запущен. Ожидаем команды и мониторим новости...")
    application.run_polling()

if __name__ == "__main__":
     main()