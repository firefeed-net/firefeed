# telegram_bot/config.py - Bot configuration constants
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
BOT_API_KEY = os.getenv("BOT_API_KEY")  # API key for bot authentication

# Webhook connection configuration
WEBHOOK_CONFIG = {
    "listen": os.getenv("WEBHOOK_LISTEN", "127.0.0.1"),
    "port": int(os.getenv("WEBHOOK_PORT", 5000)),
    "url_path": os.getenv("WEBHOOK_URL_PATH", "webhook"),
    "webhook_url": os.getenv("WEBHOOK_URL"),
}

# FireFeed Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Dictionary of channel IDs for different languages
CHANNEL_IDS = {"ru": "-1002584789230", "de": "-1002959373215", "fr": "-1002910849909", "en": "-1003035894895"}

CHANNEL_CATEGORIES = {"world", "technology", "lifestyle", "politics", "economy", "autos", "sports"}

# TTL for cleaning expired data (24 hours)
USER_DATA_TTL_SECONDS = 24 * 60 * 60