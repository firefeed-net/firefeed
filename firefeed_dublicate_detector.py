import asyncio
import aiopg
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import logging
from config import DB_CONFIG, NEWS_SIMILARITY_THRESHOLD

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FireFeedDuplicateDetector:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', similarity_threshold: float = NEWS_SIMILARITY_THRESHOLD):
        """
        Инициализация асинхронного детектора дубликатов новостей
        
        Args:
            model_name: Название модели sentence-transformers
            similarity_threshold: Порог схожести для определения дубликатов
        """
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold
        self.embedding_dim = self._get_embedding_dimension()
    
    def _get_embedding_dimension(self) -> int:
        """Получение размерности эмбеддинга модели"""
        sample_text = "test"
        embedding = self.model.encode(sample_text)
        return len(embedding)
    
    async def _get_db_pool(self):
        """Создание пула соединений с базой данных"""
        try:
            pool = await aiopg.create_pool(**DB_CONFIG)
            return pool
        except Exception as e:
            logger.error(f"[DUBLICATE_DETECTOR] Ошибка создания пула соединений: {e}")
            raise
    
    def _combine_text_fields(self, title: str, content: str) -> str:
        """Комбинирование заголовка и содержания для создания эмбеддинга"""
        return f"{title} {content[:500]}"  # Ограничиваем длину для производительности
    
    async def generate_embedding(self, title: str, content: str) -> List[float]:
        """
        Генерация эмбеддинга для новости
        
        Args:
            title: Заголовок новости
            content: Содержание новости
            
        Returns:
            Эмбеддинг новости в виде списка float
        """
        combined_text = self._combine_text_fields(title, content)
        embedding = self.model.encode(combined_text, show_progress_bar=False)
        return embedding.tolist()
    
    async def save_embedding(self, news_id: str, embedding: List[float]):
        """
        Сохранение эмбеддинга в базу данных
        
        Args:
            news_id: ID новости
            embedding: Эмбеддинг новости
        """
        pool = None
        try:
            pool = await self._get_db_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        UPDATE published_news_data 
                        SET embedding = %s 
                        WHERE news_id = %s
                    """, (embedding, news_id))
                    # Убираем await conn.commit() - в aiopg транзакции управляются автоматически
                    logger.debug(f"Эмбеддинг для новости {news_id} успешно сохранен")
        except Exception as e:
            logger.error(f"[DUBLICATE_DETECTOR] Ошибка при сохранении эмбеддинга для новости {news_id}: {e}")
            raise
        finally:
            if pool:
                pool.close()
                await pool.wait_closed()
    
    async def get_similar_news(self, embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Поиск похожих новостей в базе данных
        
        Args:
            embedding: Эмбеддинг для поиска
            limit: Максимальное количество результатов
            
        Returns:
            Список похожих новостей
        """
        pool = None
        try:
            pool = await self._get_db_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # Ищем новости с существующими эмбеддингами
                    # Явно приводим массив к типу vector
                    await cur.execute("""
                        SELECT news_id, original_title, original_content, embedding
                        FROM published_news_data 
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <-> %s::vector 
                        LIMIT %s
                    """, (embedding, limit))
                    
                    results = await cur.fetchall()
                    return [dict(zip([column[0] for column in cur.description], row)) for row in results]
        except Exception as e:
            logger.error(f"[DUBLICATE_DETECTOR] Ошибка при поиске похожих новостей: {e}")
            raise
        finally:
            if pool:
                pool.close()
                await pool.wait_closed()
    
    async def is_duplicate(self, title: str, content: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Проверка, является ли новость дубликатом
        
        Args:
            title: Заголовок новости
            content: Содержание новости
            
        Returns:
            Кортеж: (является_дубликатом, информация_о_дубликате)
        """
        pool = None
        try:
            # Генерируем эмбеддинг для новой новости
            embedding = await self.generate_embedding(title, content)
            
            # Ищем похожие новости
            similar_news = await self.get_similar_news(embedding, limit=5)
            
            # Проверяем схожесть
            for news in similar_news:
                if news['embedding'] is not None:
                    stored_embedding = np.array(news['embedding'])
                    new_embedding = np.array(embedding)
                    
                    similarity = cosine_similarity([stored_embedding], [new_embedding])[0][0]
                    
                    if similarity > self.similarity_threshold:
                        logger.info(f"[DUBLICATE_DETECTOR] Найден дубликат с схожестью {similarity:.4f}")
                        return True, news
            
            return False, None
            
        except Exception as e:
            logger.error(f"[DUBLICATE_DETECTOR] Ошибка при проверке дубликата: {e}")
            raise
        finally:
            if pool:
                pool.close()
                await pool.wait_closed()
    
    async def process_news(self, news_id: str, title: str, content: str) -> bool:
        """
        Полная обработка новости: проверка дубликата и сохранение эмбеддинга
        
        Args:
            news_id: ID новости
            title: Заголовок новости
            content: Содержание новости
            
        Returns:
            True если новость уникальна, False если дубликат
        """
        pool = None
        try:
            # Проверяем на дубликат
            is_dup, duplicate_info = await self.is_duplicate(title, content)
            
            if is_dup:
                logger.info(f"[DUBLICATE_DETECTOR] Новость {news_id} является дубликатом новости {duplicate_info['news_id']}")
                return False
            
            # Если не дубликат, сохраняем эмбеддинг
            embedding = await self.generate_embedding(title, content)
            await self.save_embedding(news_id, embedding)
            
            logger.info(f"[DUBLICATE_DETECTOR] Новость {news_id} уникальна и добавлена в базу")
            return True
            
        except Exception as e:
            logger.error(f"[DUBLICATE_DETECTOR] Ошибка при обработке новости {news_id}: {e}")
            raise
        finally:
            if pool:
                pool.close()
                await pool.wait_closed()