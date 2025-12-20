# repositories/source_repository.py - Source repository implementation
import logging
from typing import List, Dict, Any, Optional, Tuple
from interfaces import ISourceRepository

logger = logging.getLogger(__name__)


class SourceRepository(ISourceRepository):
    """PostgreSQL implementation of source repository"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_source_id_by_alias(self, source_alias: str) -> Optional[int]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id FROM sources WHERE alias = %s", (source_alias,))
                row = await cur.fetchone()
                return row[0] if row else None

    async def get_all_sources_list(self, limit: int, offset: int, category_ids: Optional[List[int]] = None) -> Tuple[int, List[Dict[str, Any]]]:
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Build query
                base_query = """
                    SELECT s.id, s.name, s.alias, COUNT(DISTINCT rf.id) as feeds_count
                    FROM sources s
                    LEFT JOIN rss_feeds rf ON s.id = rf.source_id
                """

                conditions = []
                params = []

                if category_ids:
                    conditions.append("rf.category_id = ANY(%s)")
                    params.append(category_ids)

                if conditions:
                    base_query += " WHERE " + " AND ".join(conditions)

                base_query += " GROUP BY s.id, s.name, s.alias ORDER BY s.name LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                await cur.execute(base_query, params)
                results = await cur.fetchall()

                # Get total count
                count_query = """
                    SELECT COUNT(DISTINCT s.id)
                    FROM sources s
                    LEFT JOIN rss_feeds rf ON s.id = rf.source_id
                """
                count_params = []
                if category_ids:
                    count_query += " WHERE rf.category_id = ANY(%s)"
                    count_params.append(category_ids)

                await cur.execute(count_query, count_params)
                total_count = (await cur.fetchone())[0]

                # Convert to list of dicts
                sources = []
                for row in results:
                    sources.append({
                        "id": row[0],
                        "name": row[1],
                        "alias": row[2],
                        "feeds_count": row[3]
                    })

        return total_count, sources