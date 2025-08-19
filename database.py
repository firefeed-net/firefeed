import mysql.connector
import json
import time
import hashlib
from functools import lru_cache
from config import DB_CONFIG
from urllib.parse import urlparse

USER_CACHE = {}
CACHE_EXPIRY = 300  # 5 минут

def get_db_connection():
    """Создает и возвращает соединение с MySQL"""
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    """Инициализация структуры базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Таблица для опубликованных новостей (id изменен на VARCHAR)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS published_news (
            id VARCHAR(255) PRIMARY KEY,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица настроек пользователя
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id BIGINT PRIMARY KEY,
            subscriptions VARCHAR(255),
            language VARCHAR(2) DEFAULT 'en'
        )
    ''')
    
    conn.commit()
    conn.close()

def is_news_new(title, content, url, publish_date, check_period_hours=24):
    """
    Проверяет уникальность новости
    """
    # Генерируем хеши
    title_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()
    content_hash = hashlib.sha256(content[:500].encode('utf-8')).hexdigest()  # Первые 500 символов
    
    connection = get_db_connection()
    if connection is None:
        return True
    
    try:
        cursor = connection.cursor()
        
        # Проверяем по хешам за указанный период
        query = """
        SELECT COUNT(*) FROM published_news 
        WHERE (title_hash = %s OR content_hash = %s)
        AND published_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        """
        cursor.execute(query, (title_hash, content_hash, check_period_hours))
        count = cursor.fetchone()[0]
        
        return count == 0
        
    except Exception as e:
        print(f"Ошибка проверки уникальности: {e}")
        return True
    finally:
        cursor.close()
        connection.close()

def generate_news_id(url, publish_date):
    """Генерация ID в вашем формате"""
    return f"{url}_time.struct_time({publish_date})"

def mark_as_published(title, content, url, publish_date):
    """
    Сохраняет информацию о опубликованной новости
    """
    title_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()
    content_hash = hashlib.sha256(content[:500].encode('utf-8')).hexdigest()
    news_id = generate_news_id(url, publish_date)
    
    connection = get_db_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Вставляем запись
        query = """
        INSERT INTO published_news (id, title_hash, content_hash, source_url, published_at)
        VALUES (%s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE published_at = NOW()
        """
        cursor.execute(query, (news_id, title_hash, content_hash, url))
        connection.commit()
        return True
        
    except Exception as e:
        print(f"Ошибка сохранения публикации: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()

def get_user_settings(user_id):
    """Возвращает все настройки пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT subscriptions, language FROM user_preferences WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "subscriptions": json.loads(result[0]) if result[0] else [],
            "language": result[1]
        }
    return {
        "subscriptions": [],
        "language": "en"
    }

def save_user_settings(user_id, subscriptions, language):
    """Сохраняет все настройки пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Используем ON DUPLICATE KEY UPDATE вместо INSERT OR REPLACE
    cursor.execute('''
        INSERT INTO user_preferences (user_id, subscriptions, language)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            subscriptions = VALUES(subscriptions),
            language = VALUES(language)
    ''', (user_id, json.dumps(subscriptions), language))
    
    conn.commit()
    conn.close()

def get_all_users():
    """Получаем список всех пользователей"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM user_preferences")
    user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return user_ids

def get_cached_preferences(user_id):
    """Кеширование настроек пользователя"""
    if user_id in USER_CACHE and time.time() - USER_CACHE[user_id]['timestamp'] < CACHE_EXPIRY:
        return USER_CACHE[user_id]['preferences']
    
    prefs = get_user_preferences(user_id)
    USER_CACHE[user_id] = {
        'preferences': prefs,
        'timestamp': time.time()
    }
    return prefs

@lru_cache(maxsize=100)
def get_user_settings_cached(user_id):
    """Кешированная версия получения настроек"""
    return get_user_settings(user_id)

def get_user_preferences(user_id):
    """Возвращает только подписки пользователя"""
    return get_user_settings_cached(user_id)["subscriptions"]

def get_user_language(user_id):
    """Возвращает только язык пользователя"""
    return get_user_settings_cached(user_id)["language"]

def set_user_language(user_id, lang_code):
    """Устанавливает язык пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_preferences (user_id, language)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE language = VALUES(language)
    ''', (user_id, lang_code))
    conn.commit()
    conn.close()

def get_subscribers_for_category(category):
    """Получает подписчиков для определенной категории"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id, subscriptions, language 
        FROM user_preferences
    ''')
    
    subscribers = []
    for row in cursor.fetchall():
        user_id, subscriptions_json, language = row
        
        try:
            subscriptions_list = json.loads(subscriptions_json) if subscriptions_json else []
            
            if 'all' in subscriptions_list or category in subscriptions_list:
                user = {
                    'id': user_id,
                    'language_code': language if language else 'en'
                }
                subscribers.append(user)
                
        except json.JSONDecodeError:
            print(f"Invalid JSON for user {user_id}: {subscriptions_json}")
            continue
    
    conn.close()
    return subscribers