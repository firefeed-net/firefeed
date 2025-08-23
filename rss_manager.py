import mysql.connector
from mysql.connector import Error
import hashlib
import feedparser
import asyncio
import re
import pytz
from datetime import datetime
from dateutil import parser
from config import DB_CONFIG, MAX_ENTRIES_PER_FEED, MAX_TOTAL_NEWS
from translator import prepare_translations

class RSSManager:
    def __init__(self):
        self.connection = None

    def get_db_connection(self):
        """Установить или восстановить соединение с базой данных"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**DB_CONFIG)
                print("✅ Подключение к БД установлено")
            return self.connection
        except Error as e:
            print(f"❌ Ошибка подключения к MySQL: {e}")
            return None

    def get_all_feeds(self):
        """Получить все RSS-ленты"""
        connection = self.get_db_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM rss_feeds")
            return cursor.fetchall()
        except Error as e:
            print(f"Ошибка при получении данных: {e}")
            return []
        finally:
            cursor.close()
    
    def get_all_active_feeds(self):
        """
        Получает список активных RSS-лент с информацией об источнике и категории.
        """
        connection = self.get_db_connection()
        if not connection:
            print("[DB] Ошибка подключения к БД в get_all_active_feeds")
            return []

        feeds = []
        cursor = connection.cursor(dictionary=True)
        try:
            # JOIN для получения связанных данных
            query = """
                SELECT 
                    f.id AS feed_id,
                    f.url AS feed_url,
                    f.name AS feed_name,
                    f.language AS feed_lang,
                    s.name AS source_name,
                    s.id AS source_id,
                    c.name AS category_name,
                    c.display_name AS category_display_name
                FROM rss_feeds f
                JOIN sources s ON f.source_id = s.id
                LEFT JOIN categories c ON f.category_id = c.id -- LEFT JOIN, т.к. category_id может быть NULL
                WHERE f.is_active = 1
            """
            cursor.execute(query)
            results = cursor.fetchall()
            
            for row in results:
                feeds.append({
                    'id': row['feed_id'],
                    'url': row['feed_url'].strip(), # Убедимся, что нет лишних пробелов
                    'name': row['feed_name'],
                    'lang': row['feed_lang'],
                    'source': row['source_name'], # Имя источника
                    'source_id': row['source_id'],
                    'category': row['category_name'] if row['category_name'] else 'uncategorized', # Имя категории или дефолт
                    'category_display': row['category_display_name'] # Отображаемое имя категории
                })
            
        except mysql.connector.Error as err:
            print(f"[DB] Ошибка в get_all_active_feeds: {err}")
        finally:
            cursor.close()
            connection.close()
            
        return feeds
    
    def get_feeds_by_category(self, category):
        """Получить RSS-ленты по категории"""
        connection = self.get_db_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor(dictionary=True)
        try:
            query = "SELECT * FROM rss_feeds WHERE category = %s AND is_active = TRUE"
            cursor.execute(query, (category,))
            return cursor.fetchall()
        except Error as e:
            print(f"Ошибка при получении данных: {e}")
            return []
        finally:
            cursor.close()
    
    def get_feeds_by_lang(self, lang):
        """Получить RSS-ленты по языку"""
        connection = self.get_db_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor(dictionary=True)
        try:
            query = "SELECT * FROM rss_feeds WHERE lang = %s AND is_active = TRUE"
            cursor.execute(query, (lang,))
            return cursor.fetchall()
        except Error as e:
            print(f"Ошибка при получении данных: {e}")
            return []
        finally:
            cursor.close()
    
    def get_feeds_by_source(self, source):
        """Получить RSS-ленты по источнику"""
        connection = self.get_db_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor(dictionary=True)
        try:
            query = "SELECT * FROM rss_feeds WHERE source = %s AND is_active = TRUE"
            cursor.execute(query, (source,))
            return cursor.fetchall()
        except Error as e:
            print(f"Ошибка при получении данных: {e}")
            return []
        finally:
            cursor.close()
    
    def add_feed(self, category, url, lang, source):
        """Добавить новую RSS-ленту"""
        connection = self.get_db_connection()
        if connection is None:
            return False
        
        cursor = connection.cursor()
        try:
            query = """
            INSERT INTO rss_feeds (category, url, lang, source)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (category, url, lang, source))
            connection.commit()
            return True
        except Error as e:
            print(f"Ошибка при добавлении данных: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
    
    def update_feed(self, feed_id, category=None, url=None, lang=None, source=None, is_active=None):
        """Обновить RSS-ленту"""
        connection = self.get_db_connection()
        if connection is None:
            return False
        
        cursor = connection.cursor()
        try:
            updates = []
            values = []
            
            if category is not None:
                updates.append("category = %s")
                values.append(category)
            if url is not None:
                updates.append("url = %s")
                values.append(url)
            if lang is not None:
                updates.append("lang = %s")
                values.append(lang)
            if source is not None:
                updates.append("source = %s")
                values.append(source)
            if is_active is not None:
                updates.append("is_active = %s")
                values.append(is_active)
            
            if not updates:
                return False
                
            values.append(feed_id)
            query = f"UPDATE rss_feeds SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, values)
            connection.commit()
            return True
        except Error as e:
            print(f"Ошибка при обновлении данных: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
    
    def delete_feed(self, feed_id):
        """Удалить RSS-ленту"""
        connection = self.get_db_connection()
        if connection is None:
            return False
        
        cursor = connection.cursor()
        try:
            query = "DELETE FROM rss_feeds WHERE id = %s"
            cursor.execute(query, (feed_id,))
            connection.commit()
            return True
        except Error as e:
            print(f"Ошибка при удалении данных: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
    
    def get_categories(self):
        """Получить список всех категорий"""
        connection = self.get_db_connection()
        if connection is None:
            print("Нет подключения к БД для get_categories")
            return []
        
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT DISTINCT category FROM rss_feeds WHERE is_active = TRUE")
            return [row[0] for row in cursor.fetchall()]
        except Error as e:
            print(f"Ошибка при получении категорий: {e}")
            return []
        finally:
            cursor.close()
    
    def is_news_new(self, title, content, url):
        """
        Проверяет, является ли новость новой, сверяя хэши заголовка и содержимого с БД.
        Считается дубликатом, если совпадает заголовок ИЛИ содержимое.
        """
        title_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()
        # Увеличиваем длину проверяемого контента, если 500 символов недостаточно
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest() # Проверяем весь контент?
        # Или оставить 500: content_hash = hashlib.sha256(content[:500].encode('utf-8')).hexdigest()
        
        connection = self.get_db_connection()
        if not connection:
            # В случае ошибки БД лучше считать новость НЕ новой, чтобы не дублировать
            print("[DB] [is_news_new] Ошибка подключения к БД. Считаем новость НЕ новой.")
            return False 

        cursor = connection.cursor()
        try:
            # Проверяем существование по title_hash ИЛИ content_hash
            query = """
                SELECT 1 FROM published_news 
                WHERE title_hash = %s OR content_hash = %s 
                LIMIT 1
            """
            cursor.execute(query, (title_hash, content_hash))
            result = cursor.fetchone()
            
            # Если результат есть (result не None), новость считается НЕ новой
            is_duplicate = result is not None
            if is_duplicate:
                print(f"[DB] [is_news_new] Новость '{title[:30]}...' ОТМЕЧЕНА как дубликат по хэшу.")
            else:
                print(f"[DB] [is_news_new] Новость '{title[:30]}...' ПРИНЯТА как новая.")
            
            return not is_duplicate # Возвращаем True, если НЕ дубликат
            
        except mysql.connector.Error as err:
            print(f"[DB] [is_news_new] Ошибка БД: {err}")
            # В случае ошибки БД лучше считать новость НЕ новой
            return False 
        finally:
            cursor.close()
            connection.close()

    def mark_as_published(self, title, content, url, original_language, translations_dict, category=None):
        """
        Сохраняет информацию о опубликованной новости с проверкой уникальности (хэши).
        Сохраняет оригинальные данные и переводы новости для API.
        """
        # 1. Генерируем ID ОДИН РАЗ
        title_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()
        content_hash = hashlib.sha256(content[:500].encode('utf-8')).hexdigest()
        news_id = f"{title_hash}_{content_hash}"
        short_id = news_id[:20] + "..." if len(news_id) > 20 else news_id
        print(f"[DB] [mark_as_published] Начало обработки для ID: {short_id}")

        connection = self.get_db_connection()
        if connection is None:
            print(f"[DB] [ERROR] Не удалось получить подключение к БД для ID {short_id}")
            return False

        cursor = connection.cursor()
        try:
            # --- Попробуем явно отключить autocommit для этой операции, если он вдруг включен ---
            # connection.autocommit = False # Обычно это делается при создании соединения
            
            # --- ГАРАНТИРУЕМ существование записи в published_news ---

            # 2a. Подробный лог запроса к published_news
            query_published_news = """
            INSERT INTO published_news (id, title_hash, content_hash, source_url, published_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE 
                source_url = VALUES(source_url),
                published_at = NOW()
            """
            params_news = (news_id, title_hash, content_hash, url)
            print(f"[DB] [mark_as_published] Подготовка запроса к 'published_news' (ID: {short_id})")
            print(f"[DB] [mark_as_published]   SQL: {query_published_news}")
            print(f"[DB] [mark_as_published]   Параметры: news_id='{news_id}', title_hash='{title_hash[:10]}...', content_hash='{content_hash[:10]}...', url='{url}'")

            cursor.execute(query_published_news, params_news)
            rows_affected_news = cursor.rowcount
            print(f"[DB] [mark_as_published] Запрос к 'published_news' выполнен. ROWS AFFECTED: {rows_affected_news} (ID: {short_id})")

            # --- ВАЖНО: Коммитим сразу после вставки в родительскую таблицу ---
            # Это должно гарантировать, что запись видна для последующих запросов
            connection.commit()
            print(f"[DB] [mark_as_published] Коммит после вставки в 'published_news' выполнен. (ID: {short_id})")
            # ---------------------------------------------------------------

            # 2b. Проверяем существование ПОСЛЕ коммита
            check_query = "SELECT 1 FROM published_news WHERE id = %s LIMIT 1"
            print(f"[DB] [mark_as_published] Выполнение проверочного SELECT (ID: {short_id})")
            cursor.execute(check_query, (news_id,))
            exists_in_parent = cursor.fetchone()
            
            if not exists_in_parent:
                # Критическая ошибка
                error_msg = f"[DB] [CRITICAL] Запись в 'published_news' НЕ существует после КОММИТА! FK constraint будет нарушено. (ID: {short_id})"
                print(error_msg)
                # Попробуем выбрать все поля для отладки
                debug_query = "SELECT id, title_hash, content_hash FROM published_news WHERE id = %s OR title_hash = %s OR content_hash = %s LIMIT 5"
                debug_params = (news_id, title_hash, content_hash)
                print(f"[DB] [DEBUG] Выполнение отладочного запроса по ID, title_hash, content_hash...")
                cursor.execute(debug_query, debug_params)
                debug_results = cursor.fetchall()
                if debug_results:
                    print(f"[DB] [DEBUG] Найдены потенциально конфликтующие записи в 'published_news':")
                    for row in debug_results:
                        print(f"  - ID: {row[0]}, Title_Hash: {row[1][:20]}..., Content_Hash: {row[2][:20]}...")
                else:
                    print(f"[DB] [DEBUG] Записи с таким ID, title_hash или content_hash в 'published_news' НЕ НАЙДЕНЫ.")
                raise Exception(error_msg)
            else:
                print(f"[DB] [mark_as_published] Подтверждено: запись в 'published_news' существует ПОСЛЕ КОММИТА. (ID: {short_id})")
            # -------------------------------------------------------------

            # 3. ВСТАВЛЯЕМ или ОБНОВЛЯЕМ в дочерней таблице published_news_data
            query_published_news_data = """
            INSERT INTO published_news_data 
            (news_id, original_title, original_content, original_language, category, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                original_title = VALUES(original_title),
                original_content = VALUES(original_content),
                original_language = VALUES(original_language),
                category = VALUES(category),
                updated_at = NOW()
            """
            print(f"[DB] [mark_as_published] Подготовка запроса к 'published_news_data' (ID: {short_id})")
            cursor.execute(query_published_news_data, (
                news_id,
                title, 
                content, 
                original_language, 
                category
            ))
            print(f"[DB] [mark_as_published] Выполнен запрос к 'published_news_data'. (ID: {short_id})")

            # 4. ВСТАВЛЯЕМ или ОБНОВЛЯЕМ переводы в news_translations
            # ... (ваш код для вставки переводов) ...
            print(f"[DB] [mark_as_published] Обработка переводов завершена. (ID: {short_id})")
            
            # --- Финальный коммит (на случай, если предыдущий был отдельным) ---
            # connection.commit() # Уже сделан выше
            print(f"[DB] [SUCCESS] Новость и переводы сохранены: {short_id}")
            return True
            
        except mysql.connector.Error as err:
            print(f"[DB] [ERROR] Ошибка БД при сохранении (ID: {short_id}): {err}")
            connection.rollback()
            return False
        except Exception as e: # Ловим все остальные исключения, включая наше критическое
            print(f"[DB] [ERROR] Неожиданная ошибка в mark_as_published (ID: {short_id}): {e}")
            import traceback
            traceback.print_exc()
            connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
    
    async def fetch_news(self):
        """Асинхронная функция для получения новостей из RSS-лент"""
        seen_keys = set()
        all_news = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }

        try:
            # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
            # Получаем список активных фидов (список словарей)
            active_feeds = self.get_all_active_feeds()
            print(f"[RSS] Найдено {len(active_feeds)} активных RSS-лент.")

            # Итерируемся по списку фидов
            # for category, sources in self.get_all_active_feeds(): # <-- СТАРЫЙ способ, вызывает ошибку
            for feed_info in active_feeds: # <-- НОВЫЙ способ
                # Извлекаем информацию из словаря feed_info
                # feed_url = feed_info['url']
                # feed_category = feed_info['category']
                # feed_lang = feed_info['lang']
                # feed_source = feed_info['source']
                
                try:
                    print(f"[RSS] Парсинг ленты: {feed_info['name']} ({feed_info['url']})")
                    feed = feedparser.parse(feed_info['url'], request_headers=headers)
                    
                    # Логируем ошибки парсинга
                    if getattr(feed, 'bozo', 0):
                        exc = getattr(feed, 'bozo_exception', None)
                        if exc:
                            error_type = type(exc).__name__
                            print(f"[RSS] Ошибка парсинга ({error_type}) в {feed_info['url']}: {str(exc)[:200]}")
                except Exception as e:
                    print(f"[RSS] Сетевая ошибка для {feed_info['url']}: {str(e)}")
                    continue
                
                # Пропускаем ленту, если нет записей
                if not feed.entries:
                    print(f"[RSS] Нет записей в {feed_info['url']}")
                    continue
                    
                for entry in feed.entries[:MAX_ENTRIES_PER_FEED]:
                    # Защита от отсутствия title
                    title = getattr(entry, 'title', 'Untitled').strip()
                    description = entry.get('description', '')
                    
                    # Пропускаем новости с идентичными заголовком и описанием
                    if title == description:
                        continue
                        
                    normalized_title = re.sub(r'\s+', ' ', title).lower()
                    # --- Возможно, стоит уточнить уникальный ключ ---
                    # unique_key = (feed_info['source'], normalized_title)
                    unique_key = (feed_info['source'], feed_info['category'], normalized_title) # Уникальнее
                    
                    # Пропускаем уже обработанные в текущей сессии
                    if unique_key in seen_keys:
                        continue
                    seen_keys.add(unique_key)
                    
                    entry_link = entry.get('link', '#')
                    
                    # Проверяем уникальность через БД (хэши)
                    if not self.is_news_new(title, description, entry_link):
                        continue

                    # Обработка даты с fallback
                    pub_date = getattr(entry, 'published', None)
                    if pub_date:
                        try:
                            published = parser.parse(pub_date).replace(tzinfo=pytz.utc)
                        except Exception as e: # Ловим конкретное исключение
                            print(f"[RSS] Ошибка парсинга даты '{pub_date}': {e}. Используется текущее время.")
                            published = datetime.now(pytz.utc)
                    else:
                        published = datetime.now(pytz.utc)
                    
                    # --- Создание news_item с данными из feed_info ---
                    news_item = {
                        'id': f"{entry_link}_{pub_date}", # Или другой уникальный ID
                        'title': title,
                        'description': description,
                        'link': entry_link,
                        'published': published,
                        # --- Данные берутся из feed_info ---
                        'category': feed_info['category'], # <-- Категория из БД
                        'lang': feed_info['lang'],         # <-- Язык из БД
                        'source': feed_info['source'],     # <-- Источник из БД
                        # --- Дополнительные данные (если нужно) ---
                        # 'feed_id': feed_info['id'],
                        # 'feed_name': feed_info['name'],
                    }
                    
                    all_news.append(news_item)
            
        except Exception as e:
            # Выводим traceback для лучшей отладки
            import traceback
            print(f"❌ Ошибка в fetch_news: {e}")
            traceback.print_exc() # Добавит стек вызовов в лог
        
        sorted_news = sorted(all_news, key=lambda x: x['published'], reverse=True)
        final_news = sorted_news[:MAX_TOTAL_NEWS]
        print(f"[RSS] Всего собрано уникальных новостей: {len(final_news)}")
        return final_news
    
    def close_connection(self):
        """Закрыть соединение с базой данных"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
            print("🔌 Соединение с БД закрыто")
