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
                # print("✅ Подключение к БД установлено")
            return self.connection
        except Error as e:
            print(f"❌ Ошибка подключения к MySQL: {e}")
            return None

    def get_all_feeds(self):
        """
        Получает список активных RSS-лент с информацией об источнике и категории.
        """
        connection = self.get_db_connection()
        if not connection:
            print("[DB] Ошибка подключения к БД в get_all_eeds")
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
    
    def get_feeds_by_category(self, category_name):
        """Получить активные RSS-ленты по имени категории."""
        connection = self.get_db_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor(dictionary=True)
        try:
            # Используем JOIN для поиска по имени категории
            query = """
                SELECT rf.*, c.name as category_name, s.name as source_name
                FROM rss_feeds rf
                JOIN categories c ON rf.category_id = c.id
                JOIN sources s ON rf.source_id = s.id
                WHERE c.name = %s AND rf.is_active = TRUE
            """
            cursor.execute(query, (category_name,))
            return cursor.fetchall()
        except mysql.connector.Error as e: # Уточняем тип исключения
            print(f"Ошибка при получении фидов по категории '{category_name}': {e}")
            return []
        finally:
            cursor.close()

    def get_feeds_by_lang(self, lang):
        """Получить активные RSS-ленты по языку."""
        connection = self.get_db_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor(dictionary=True)
        try:
            # Поле 'language' остается в rss_feeds
            query = "SELECT rf.*, c.name as category_name, s.name as source_name FROM rss_feeds rf JOIN categories c ON rf.category_id = c.id JOIN sources s ON rf.source_id = s.id WHERE rf.language = %s AND rf.is_active = TRUE"
            cursor.execute(query, (lang,))
            return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Ошибка при получении фидов по языку '{lang}': {e}")
            return []
        finally:
            cursor.close()

    def get_feeds_by_source(self, source_name):
        """Получить активные RSS-ленты по имени источника."""
        connection = self.get_db_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor(dictionary=True)
        try:
            # Используем JOIN для поиска по имени источника
            query = """
                SELECT rf.*, c.name as category_name, s.name as source_name
                FROM rss_feeds rf
                JOIN categories c ON rf.category_id = c.id
                JOIN sources s ON rf.source_id = s.id
                WHERE s.name = %s AND rf.is_active = TRUE
            """
            cursor.execute(query, (source_name,))
            return cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"Ошибка при получении фидов по источнику '{source_name}': {e}")
            return []
        finally:
            cursor.close()

    def add_feed(self, category_name, url, language, source_name):
        """Добавить новую RSS-ленту, используя имена категории и источника."""
        connection = self.get_db_connection()
        if connection is None:
            print("Ошибка: Невозможно подключиться к БД в add_feed.")
            return False

        cursor = connection.cursor()
        try:
            # 1. Получить ID категории по имени
            cursor.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
            cat_result = cursor.fetchone()
            if not cat_result:
                print(f"Ошибка: Категория '{category_name}' не найдена в таблице 'categories'.")
                return False # Или можно сначала создать категорию
            category_id = cat_result[0]

            # 2. Получить ID источника по имени
            cursor.execute("SELECT id FROM sources WHERE name = %s", (source_name,))
            src_result = cursor.fetchone()
            if not src_result:
                print(f"Ошибка: Источник '{source_name}' не найден в таблице 'sources'.")
                return False # Или можно сначала создать источник
            source_id = src_result[0]

            # 3. Вставить новую ленту с полученными ID
            # Предполагаем, что 'name' для ленты генерируется или передается отдельно.
            # Здесь используем URL как временное имя или часть имени.
            feed_name = url.split('/')[-1] or "Новая лента" # Простой способ генерации имени
            query = """
                INSERT INTO rss_feeds (source_id, url, name, category_id, language, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            # is_active по умолчанию TRUE, но явно укажем
            cursor.execute(query, (source_id, url, feed_name, category_id, language, True))
            connection.commit()
            print(f"Лента '{url}' успешно добавлена.")
            return True
        except mysql.connector.Error as e:
            print(f"Ошибка БД при добавлении фида: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()

    def update_feed(self, feed_id, category_name=None, url=None, language=None, source_name=None, is_active=None, feed_name=None):
        """Обновить RSS-ленту, используя имена категории и источника."""
        connection = self.get_db_connection()
        if connection is None:
            return False

        cursor = connection.cursor()
        try:
            updates = []
            values = []
            
            # Обработка изменения категории по имени
            if category_name is not None:
                cursor.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
                cat_result = cursor.fetchone()
                if cat_result:
                    updates.append("category_id = %s")
                    values.append(cat_result[0])
                else:
                    print(f"Предупреждение: Категория '{category_name}' не найдена. Поле category_id не обновлено.")
            
            # Обработка изменения источника по имени
            if source_name is not None:
                cursor.execute("SELECT id FROM sources WHERE name = %s", (source_name,))
                src_result = cursor.fetchone()
                if src_result:
                    updates.append("source_id = %s")
                    values.append(src_result[0])
                else:
                    print(f"Предупреждение: Источник '{source_name}' не найден. Поле source_id не обновлено.")

            # Обработка других полей
            if url is not None:
                updates.append("url = %s")
                values.append(url)
            if language is not None:
                updates.append("language = %s")
                values.append(language)
            if is_active is not None:
                updates.append("is_active = %s")
                values.append(is_active)
            if feed_name is not None: # Если имя ленты передается отдельно
                updates.append("name = %s")
                values.append(feed_name)

            if not updates:
                print("Нет полей для обновления.")
                return False
                
            values.append(feed_id)
            query = f"UPDATE rss_feeds SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, values)
            connection.commit()
            affected_rows = cursor.rowcount
            if affected_rows > 0:
                print(f"Лента с ID {feed_id} успешно обновлена.")
            else:
                print(f"Лента с ID {feed_id} не найдена или не была изменена.")
            return affected_rows > 0
        except mysql.connector.Error as e:
            print(f"Ошибка БД при обновлении фида с ID {feed_id}: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()

    def delete_feed(self, feed_id):
        """Удалить RSS-ленту по ID."""
        connection = self.get_db_connection()
        if connection is None:
            return False
        
        cursor = connection.cursor()
        try:
            # Удаление по ID ленты остается прежним
            query = "DELETE FROM rss_feeds WHERE id = %s"
            cursor.execute(query, (feed_id,))
            connection.commit()
            affected_rows = cursor.rowcount
            if affected_rows > 0:
                print(f"Лента с ID {feed_id} успешно удалена.")
            else:
                print(f"Лента с ID {feed_id} не найдена.")
            return affected_rows > 0
        except mysql.connector.Error as e:
            print(f"Ошибка БД при удалении фида с ID {feed_id}: {e}")
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
            get_categories_query = """
                SELECT DISTINCT c.name AS category
                FROM categories c
                JOIN rss_feeds rf ON c.id = rf.category_id
                WHERE rf.is_active = TRUE
                ORDER BY c.name;
            """

            cursor.execute(get_categories_query)
            return [row[0] for row in cursor.fetchall()]
        except Error as e:
            print(f"Ошибка при получении категорий: {e}")
            return []
        finally:
            cursor.close()
    
    def is_news_new(self, title_hash, content_hash, url):
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

            return not is_duplicate # Возвращаем True, если НЕ дубликат
            
        except mysql.connector.Error as err:
            print(f"[DB] [is_news_new] Ошибка БД: {err}")
            # В случае ошибки БД лучше считать новость НЕ новой
            return False 
        finally:
            cursor.close()
            connection.close()

    def mark_as_published(self, title, content, url, original_language, translations_dict, category_name=None, image_filename=None):
        """
        Сохраняет информацию о опубликованной новости с проверкой уникальности (хэши).
        Сохраняет оригинальные данные и переводы новости для API.

        :param category_name: название категории (опционально)
        :param image_filename: имя файла изображения (опционально)
        """
        # 1. Генерируем ID ОДИН РАЗ
        title_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        news_id = f"{title_hash}_{content_hash}"
        short_id = news_id[:20] + "..." if len(news_id) > 20 else news_id
        print(f"[DB] [mark_as_published] Начало обработки для ID: {short_id}")

        connection = self.get_db_connection()
        if connection is None:
            print(f"[DB] [ERROR] Не удалось получить подключение к БД для ID {short_id}")
            return False

        cursor = connection.cursor()
        try:
            # --- Получаем category_id по названию категории ---
            category_id = None
            if category_name:
                category_query = "SELECT id FROM categories WHERE name = %s LIMIT 1"
                cursor.execute(category_query, (category_name,))
                category_result = cursor.fetchone()
                if category_result:
                    category_id = category_result[0]
                else:
                    print(f"[DB] [WARN] Категория '{category_name}' не найдена в таблице categories")

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
            # Обновленный запрос с category_id вместо category
            query_published_news_data = """
            INSERT INTO published_news_data 
            (news_id, original_title, original_content, original_language, category_id, image_filename, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
                original_title = VALUES(original_title),
                original_content = VALUES(original_content),
                original_language = VALUES(original_language),
                category_id = VALUES(category_id),
                image_filename = VALUES(image_filename),
                updated_at = NOW()
            """
            print(f"[DB] [mark_as_published] Подготовка запроса к 'published_news_data' (ID: {short_id})")
            cursor.execute(query_published_news_data, (
                news_id,
                title, 
                content, 
                original_language, 
                category_id,
                image_filename
            ))
            print(f"[DB] [mark_as_published] Выполнен запрос к 'published_news_data'. (ID: {short_id})")

            # 4. ВСТАВЛЯЕМ или ОБНОВЛЯЕМ переводы в news_translations
            for lang_code, trans_data in translations_dict.items():
                # Проверка на поддерживаемые языки и наличие данных
                if lang_code in ['ru', 'en', 'de', 'fr'] and isinstance(trans_data, dict):
                    trans_title = trans_data.get('title', title) # fallback на оригинал
                    trans_content = trans_data.get('description', content) # fallback на оригинал
                    
                    query_translation = """
                    INSERT INTO news_translations (news_id, language, translated_title, translated_content, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                        translated_title = VALUES(translated_title),
                        translated_content = VALUES(translated_content),
                        updated_at = NOW()
                    """
                    cursor.execute(query_translation, (news_id, lang_code, trans_title, trans_content))
            
            connection.commit()
            print(f"[DB] [SUCCESS] Новость и переводы сохранены: {short_id}")
            print(f"[DB] [mark_as_published] Обработка переводов завершена. (ID: {short_id})")
            
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
            # Получаем список активных фидов (список словарей)
            active_feeds = self.get_all_active_feeds()
            print(f"[RSS] Найдено {len(active_feeds)} активных RSS-лент.")

            for feed_info in active_feeds:
                # Извлекаем информацию из словаря feed_info
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
                    title_hash = hashlib.sha256(title.encode('utf-8')).hexdigest()
                    content_hash = hashlib.sha256(description.encode('utf-8')).hexdigest()

                    if not self.is_news_new(title_hash, content_hash, entry_link):
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
                        'id': f"{title_hash}_{content_hash}",
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
