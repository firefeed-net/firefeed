import mysql.connector
from mysql.connector import Error
import os
import sys

# Добавляем корень проекта в путь поиска модулей, чтобы импортировать config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем настройки (адаптируйте под вашу структуру config.py)
from config import DB_CONFIG

def get_db_connection():
    """Создает и возвращает подключение к базе данных."""
    try:
        # Убедитесь, что эти переменные окружения установлены
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("[DB] Подключение к MySQL установлено.")
            return connection
    except Error as e:
        print(f"[DB] Ошибка при подключении к MySQL: {e}")
        return None

def close_db_connection(connection):
    """Закрывает подключение к базе данных."""
    if connection and connection.is_connected():
        connection.close()
        print("[DB] Подключение к MySQL закрыто.")

# --- Альтернатива с контекстным менеджером (рекомендуется) ---
from contextlib import contextmanager

@contextmanager
def get_db():
    """Контекстный менеджер для получения подключения к БД."""
    connection = get_db_connection()
    try:
        yield connection
    finally:
        if connection:
            close_db_connection(connection)

# Использование:
# with get_db() as db:
#     if db:
#         cursor = db.cursor(dictionary=True)
#         # ... выполнение запросов ...
#         cursor.close()
#     else:
#         raise HTTPException(status_code=500, detail="Не удалось подключиться к БД")