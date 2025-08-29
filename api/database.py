import aiopg
import os
import sys

# Добавляем корень проекта в путь поиска модулей, чтобы импортировать config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем настройки (адаптируйте под вашу структуру config.py)
from config import DB_CONFIG

async def get_db_pool():
    """Создает и возвращает пул подключений к базе данных."""
    try:
        # Создаем пул соединений
        pool = await aiopg.create_pool(**DB_CONFIG)
        print("[DB] Пул подключений к PostgreSQL создан.")
        return pool
    except Exception as e:
        print(f"[DB] Ошибка при создании пула подключений к PostgreSQL: {e}")
        return None

async def close_db_pool(pool):
    """Закрывает пул подключений к базе данных."""
    if pool:
        pool.close()
        await pool.wait_closed()
        print("[DB] Пул подключений к PostgreSQL закрыт.")

# --- Асинхронный контекстный менеджер (рекомендуется) ---
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db():
    """Асинхронный контекстный менеджер для получения пула подключений к БД."""
    pool = await get_db_pool()
    try:
        yield pool
    finally:
        if pool:
            await close_db_pool(pool)

# --- Для обратной совместимости или одноразовых подключений ---
async def get_single_connection():
    """Создает и возвращает одиночное подключение к базе данных."""
    try:
        # Создаем одиночное соединение
        connection = await aiopg.connect(**DB_CONFIG)
        print("[DB] Подключение к PostgreSQL установлено.")
        return connection
    except Exception as e:
        print(f"[DB] Ошибка при подключении к PostgreSQL: {e}")
        return None

async def close_single_connection(connection):
    """Закрывает одиночное подключение к базе данных."""
    if connection:
        connection.close()
        await connection.wait_closed()
        print("[DB] Подключение к PostgreSQL закрыто.")

# --- Асинхронный контекстный менеджер для одиночного подключения ---
@asynccontextmanager
async def get_single_db():
    """Асинхронный контекстный менеджер для получения одиночного подключения к БД."""
    connection = await get_single_connection()
    try:
        yield connection
    finally:
        if connection:
            await close_single_connection(connection)