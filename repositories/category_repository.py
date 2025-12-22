# repositories/category_repository.py - Category repository implementation
import logging
from typing import List, Dict, Any, Optional, Tuple
from interfaces import ICategoryRepository

logger = logging.getLogger(__name__)


class CategoryRepository(ICategoryRepository):
    """PostgreSQL implementation of category repository"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_user_categories(self, user_id: int, source_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                query = "SELECT c.id, c.name FROM user_categories uc JOIN categories c ON uc.category_id = c.id WHERE uc.user_id = %s"
                params = [user_id]

                if source_ids:
                    query += " AND c.id IN (SELECT category_id FROM source_categories WHERE source_id = ANY(%s))"
                    params.append(source_ids)

                await cur.execute(query, params)

                categories = []
                rows = await cur.fetchall()
                for row in rows:
                    categories.append({"id": row[0], "name": row[1]})

                return categories

    async def update_user_categories(self, user_id: int, category_ids: List[int]) -> bool:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute("BEGIN")

                    # Delete existing categories
                    await cur.execute("DELETE FROM user_categories WHERE user_id = %s", (user_id,))

                    # Insert new categories
                    if category_ids:
                        values = [(user_id, cat_id) for cat_id in category_ids]
                        placeholders = ','.join(['(%s, %s)'] * len(category_ids))
                        flattened_values = [item for sublist in values for item in sublist]
                        await cur.execute(
                            f"INSERT INTO user_categories (user_id, category_id) VALUES {placeholders}",
                            flattened_values
                        )

                    await cur.execute("COMMIT")
                    return True

                except Exception as e:
                    await cur.execute("ROLLBACK")
                    logger.error(f"Error updating user categories: {e}")
                    return False

    async def get_all_category_ids(self) -> List[int]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id FROM categories")

                ids = []
                rows = await cur.fetchall()
                for row in rows:
                    ids.append(row[0])

                return ids

    async def get_category_id_by_name(self, category_name: str) -> Optional[int]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
                row = await cur.fetchone()
                return row[0] if row else None

    async def get_all_categories_list(self, limit: int, offset: int, source_ids: Optional[List[int]] = None) -> Tuple[int, List[Dict[str, Any]]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Build query
                base_query = """
                    SELECT c.id, c.name, COUNT(DISTINCT rf.id) as feeds_count
                    FROM categories c
                    LEFT JOIN rss_feeds rf ON c.id = rf.category_id
                """

                conditions = []
                params = []

                if source_ids:
                    base_query += " JOIN sources s ON rf.source_id = s.id"
                    conditions.append("s.id = ANY(%s)")
                    params.append(source_ids)

                if conditions:
                    base_query += " WHERE " + " AND ".join(conditions)

                base_query += " GROUP BY c.id, c.name ORDER BY c.name LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                await cur.execute(base_query, params)
                results = await cur.fetchall()

                # Get total count
                count_query = """
                    SELECT COUNT(DISTINCT c.id)
                    FROM categories c
                    LEFT JOIN rss_feeds rf ON c.id = rf.category_id
                """
                count_params = []
                if source_ids:
                    count_query += " JOIN sources s ON rf.source_id = s.id WHERE s.id = ANY(%s)"
                    count_params.append(source_ids)

                await cur.execute(count_query, count_params)
                total_count = (await cur.fetchone())[0]

                # Convert to list of dicts
                categories = []
                for row in results:
                    categories.append({
                        "id": row[0],
                        "name": row[1],
                        "feeds_count": row[2]
                    })

        return total_count, categories