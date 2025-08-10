import sqlite3
import json

USER_CACHE = {}
CACHE_EXPIRY = 300  # 5 минут

def init_db():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS published_news (
            id TEXT PRIMARY KEY,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Новая таблица для пользователей и их подписок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY,
            subscriptions TEXT  -- JSON-строка с категориями
        )
    ''')
    conn.commit()
    conn.close()

def is_news_new(news_id: str) -> bool:
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM published_news WHERE id=?", (news_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return not exists

def mark_as_published(news_id: str):
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO published_news (id) VALUES (?)", (news_id,))
    conn.commit()
    conn.close()

def get_user_preferences(user_id):
    """Получаем настройки пользователя"""
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute("SELECT subscriptions FROM user_preferences WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        return json.loads(result[0])
    return []

def save_user_preferences(user_id, categories):
    """Сохраняем настройки пользователя"""
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    subscriptions = json.dumps(categories)
    
    cursor.execute('''
        INSERT OR REPLACE INTO user_preferences (user_id, subscriptions)
        VALUES (?, ?)
    ''', (user_id, subscriptions))
    
    conn.commit()
    conn.close()

def get_all_users():
    """Получаем список всех пользователей"""
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM user_preferences")
    user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return user_ids

def get_cached_preferences(user_id):
    if user_id in USER_CACHE and time.time() - USER_CACHE[user_id]['timestamp'] < CACHE_EXPIRY:
        return USER_CACHE[user_id]['preferences']
    
    prefs = get_user_preferences(user_id)
    USER_CACHE[user_id] = {
        'preferences': prefs,
        'timestamp': time.time()
    }
    return prefs

