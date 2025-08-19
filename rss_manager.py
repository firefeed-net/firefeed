import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG


class RSSManager:
    def __init__(self):
        self.connection = self.get_db_connection()
    
    def get_db_connection(self):
        """Создает и возвращает соединение с MySQL"""
        return mysql.connector.connect(**DB_CONFIG)

    def get_all_feeds(self):
        """Получить все RSS-ленты"""
        if self.connection is None:
            return []
        
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM rss_feeds")
            return cursor.fetchall()
        except Error as e:
            print(f"Ошибка при получении данных: {e}")
            return []
        finally:
            cursor.close()
    
    def get_all_active_feeds(self):
        """Получить все RSS-ленты сгруппированные по категориям"""
        if self.connection is None:
            return {}
        
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT category, url, lang, source FROM rss_feeds WHERE is_active = TRUE ORDER BY category")
            feeds = cursor.fetchall()
            
            # Группируем по категориям как в исходном CATEGORIES
            categories = {}
            for feed in feeds:
                category = feed['category']
                if category not in categories:
                    categories[category] = []
                
                categories[category].append({
                    'url': feed['url'],
                    'lang': feed['lang'],
                    'source': feed['source']
                })
            
            return categories
            
        except Error as e:
            print(f"Ошибка при получении данных: {e}")
            return {}
        finally:
            cursor.close()
    
    def get_feeds_by_category(self, category):
        """Получить RSS-ленты по категории"""
        if self.connection is None:
            return []
        
        cursor = self.connection.cursor(dictionary=True)
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
        if self.connection is None:
            return []
        
        cursor = self.connection.cursor(dictionary=True)
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
        if self.connection is None:
            return []
        
        cursor = self.connection.cursor(dictionary=True)
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
        if self.connection is None:
            return False
        
        cursor = self.connection.cursor()
        try:
            query = """
            INSERT INTO rss_feeds (category, url, lang, source)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (category, url, lang, source))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Ошибка при добавлении данных: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def update_feed(self, feed_id, category=None, url=None, lang=None, source=None, is_active=None):
        """Обновить RSS-ленту"""
        if self.connection is None:
            return False
        
        cursor = self.connection.cursor()
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
            self.connection.commit()
            return True
        except Error as e:
            print(f"Ошибка при обновлении данных: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def delete_feed(self, feed_id):
        """Удалить RSS-ленту"""
        if self.connection is None:
            return False
        
        cursor = self.connection.cursor()
        try:
            query = "DELETE FROM rss_feeds WHERE id = %s"
            cursor.execute(query, (feed_id,))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Ошибка при удалении данных: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def get_categories(self):
        """Получить список всех категорий"""
        if self.connection is None:
            return []
        
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT DISTINCT category FROM rss_feeds WHERE is_active = TRUE")
            return [row[0] for row in cursor.fetchall()]
        except Error as e:
            print(f"Ошибка при получении категорий: {e}")
            return []
        finally:
            cursor.close()
    
    def close_connection(self):
        """Закрыть соединение с базой данных"""
        if self.connection:
            self.connection.close()