import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from apps.rss_parser.services import RSSManager
from utils.media_extractors import extract_image_from_rss_item, extract_video_from_rss_item
from repositories import RSSFeedRepository, RSSItemRepository


class TestRSSManager:
    @pytest.fixture
    def rss_manager(self):
        from unittest.mock import AsyncMock
        return RSSManager(
            rss_fetcher=AsyncMock(),
            rss_validator=AsyncMock(),
            rss_storage=AsyncMock(),
            media_extractor=AsyncMock(),
            translation_service=AsyncMock(),
            duplicate_detector=AsyncMock(),
            translator_queue=AsyncMock(),
            maintenance_service=AsyncMock()
        )

    @pytest.fixture
    def mock_pool(self):
        pool = MagicMock()
        return pool

    @pytest.fixture
    def mock_conn(self):
        conn = MagicMock()
        return conn

    @pytest.fixture
    def mock_cur(self):
        cur = MagicMock()
        return cur


    @pytest.mark.asyncio
    async def test_get_all_active_feeds_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        with patch.object(RSSFeedRepository, 'get_all_active_feeds', return_value=[
            {"id": 1, "url": "http://example.com/rss", "name": "Test Feed", "lang": "en", "source_id": 1, "category_id": 1, "source": "BBC", "category": "Tech"}
        ]):
            result = await rss_manager.get_all_active_feeds()
            assert len(result) == 1
            assert result[0]['name'] == 'Test Feed'

    @pytest.mark.anyio
    async def test_get_all_active_feeds_failure(self, rss_manager, mock_pool, mock_conn, mock_cur):
        with patch.object(RSSFeedRepository, 'get_all_active_feeds', side_effect=Exception("DB error")):
            result = await rss_manager.get_all_active_feeds()
            assert result == []

    @pytest.mark.asyncio
    async def test_get_feeds_by_category_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        with patch.object(RSSFeedRepository, 'get_feeds_by_category', return_value=[
            {"id": 1, "url": "http://example.com/rss", "name": "Test Feed", "lang": "en", "source_id": 1, "category_id": 1, "source": "BBC", "category": "Tech"}
        ]):
            result = await rss_manager.get_feeds_by_category('Tech')
            assert len(result) == 1
            assert result[0]['category'] == 'Tech'

    @pytest.mark.asyncio
    async def test_get_feeds_by_language_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        with patch.object(RSSFeedRepository, 'get_feeds_by_language', return_value=[
            {"id": 1, "url": "http://example.com/rss", "name": "Test Feed", "lang": "en", "source_id": 1, "category_id": 1, "source": "BBC", "category": "Tech"}
        ]):
            result = await rss_manager.get_feeds_by_language('en')
            assert len(result) == 1
            assert result[0]['lang'] == 'en'

    @pytest.mark.asyncio
    async def test_get_feeds_by_source_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        with patch.object(RSSFeedRepository, 'get_feeds_by_source', return_value=[
            {"id": 1, "url": "http://example.com/rss", "name": "Test Feed", "lang": "en", "source_id": 1, "category_id": 1, "source": "BBC", "category": "Tech"}
        ]):
            result = await rss_manager.get_feeds_by_source('BBC')
            assert len(result) == 1
            assert result[0]['source'] == 'BBC'

    @pytest.mark.asyncio
    async def test_add_feed_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        rss_manager.rss_storage.add_feed.return_value = True
        rss_manager.rss_storage.db_pool = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone = AsyncMock(side_effect=[(1,), (1,)])

        result = await rss_manager.add_feed('http://example.com/rss', 'Tech', 'BBC', 'en')
        assert result is True

    @pytest.mark.asyncio
    async def test_add_feed_category_not_found(self, rss_manager, mock_pool, mock_conn, mock_cur):
        rss_manager.rss_storage.add_feed.return_value = False
        rss_manager.rss_storage.db_pool = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = None

        result = await rss_manager.add_feed('http://example.com/rss', 'NonExistent', 'BBC', 'en')
        assert result is False

    @pytest.mark.asyncio
    async def test_update_feed_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        rss_manager.rss_storage.update_feed.return_value = True
        rss_manager.rss_storage.db_pool = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone = AsyncMock(side_effect=[(1,), (1,)])
        mock_cur.rowcount = 1

        result = await rss_manager.update_feed(1, name='Updated Feed')
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_feed_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        rss_manager.rss_storage.delete_feed.return_value = True
        rss_manager.rss_storage.db_pool = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.rowcount = 1

        result = await rss_manager.delete_feed(1)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_feed_cooldown_minutes_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        rss_manager.rss_storage.get_feed_cooldown.return_value = 30
        rss_manager.rss_storage.db_pool = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = (30,)

        result = await rss_manager.get_feed_cooldown_minutes(1)
        assert result == 30

    @pytest.mark.asyncio
    async def test_get_feed_cooldown_minutes_default(self, rss_manager, mock_pool, mock_conn, mock_cur):
        rss_manager.rss_storage.get_feed_cooldown.return_value = None
        rss_manager.rss_storage.db_pool = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = None

        result = await rss_manager.get_feed_cooldown_minutes(1)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_max_news_per_hour_for_feed_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        rss_manager.rss_storage.get_feed_max_news_per_hour.return_value = 5
        rss_manager.rss_storage.db_pool = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = (5,)

        result = await rss_manager.get_max_news_per_hour_for_feed(1)
        assert result == 5

    @pytest.mark.asyncio
    async def test_get_last_published_time_for_feed_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        rss_manager.rss_storage.get_last_published_time.return_value = datetime.now(timezone.utc)
        rss_manager.rss_storage.db_pool = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = (datetime.now(timezone.utc),)

        result = await rss_manager.get_last_published_time_for_feed(1)
        assert isinstance(result, datetime)

    @pytest.mark.asyncio
    async def test_get_recent_rss_items_count_for_feed_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        rss_manager.rss_storage.get_recent_items_count.return_value = 5
        rss_manager.rss_storage.db_pool = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = (5,)

        result = await rss_manager.get_recent_rss_items_count_for_feed(1, 60)
        assert result == 5

    def test_generate_news_id(self, rss_manager):
        title = "Test Title"
        content = "Test Content"
        link = "http://example.com"
        feed_id = 1

        rss_manager.rss_fetcher.generate_news_id = MagicMock(return_value="a" * 64)
        news_id = rss_manager.generate_news_id(title, content, link, feed_id)
        assert isinstance(news_id, str)
        assert len(news_id) == 64  # SHA256 hex length

    @pytest.mark.asyncio
    async def test_check_for_duplicates_false(self, rss_manager):
        rss_manager.rss_fetcher.check_for_duplicates.return_value = False

        result = await rss_manager.check_for_duplicates("title", "content", "link", "en")
        assert result is False

    @pytest.mark.asyncio
    async def test_check_for_duplicates_true(self, rss_manager):
        rss_manager.rss_fetcher.check_for_duplicates.return_value = True

        result = await rss_manager.check_for_duplicates("title", "content", "link", "en")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_rss_feed_success(self, rss_manager):
        rss_manager.rss_validator.validate_feed.return_value = True
        headers = {"User-Agent": "Test"}
        result = await rss_manager.validate_rss_feed("http://example.com/rss", headers)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_rss_feed_no_entries(self, rss_manager):
        rss_manager.rss_validator.validate_feed.return_value = False
        headers = {"User-Agent": "Test"}
        result = await rss_manager.validate_rss_feed("http://example.com/rss", headers)
        assert result is False

    @pytest.mark.asyncio
    async def test_save_rss_item_to_db_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        with patch.object(RSSItemRepository, 'save_rss_item', return_value="test_news_id"):
            rss_item = {
                "id": "test_news_id",
                "title": "Test Title",
                "content": "Test Content",
                "lang": "en",
                "category": "Tech",
                "source": "BBC",
                "link": "http://example.com",
                "image_filename": "test.jpg"
            }

            result = await rss_manager.save_rss_item_to_db(rss_item, 1)
            assert result == "test_news_id"

    @pytest.mark.asyncio
    async def test_save_rss_item_to_db_category_not_found(self, rss_manager, mock_pool, mock_conn, mock_cur):
        with patch.object(RSSItemRepository, 'save_rss_item', return_value=None):
            rss_item = {
                "id": "test_news_id",
                "title": "Test Title",
                "content": "Test Content",
                "lang": "en",
                "category": "NonExistent",
                "source": "BBC",
                "link": "http://example.com",
                "image_filename": "test.jpg"
            }

            result = await rss_manager.save_rss_item_to_db(rss_item, 1)
            assert result is None

    @pytest.mark.asyncio
    async def test_save_translations_to_db_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        rss_manager.rss_storage.save_translations.return_value = True
        rss_manager.rss_storage.db_pool = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = ("en", "Original Title", "Original Content")

        translations = {
            "ru": {"title": "Русский заголовок", "content": "Русский контент"},
            "de": {"title": "Deutscher Titel", "content": "Deutscher Inhalt"}
        }

        result = await rss_manager.save_translations_to_db("test_news_id", translations)
        assert result is True

    @pytest.mark.asyncio
    async def test_save_translations_to_db_empty_translations(self, rss_manager):
        rss_manager.rss_storage.save_translations.return_value = True
        result = await rss_manager.save_translations_to_db("test_news_id", {})
        assert result is True

    @pytest.mark.asyncio
    async def test_save_translations_to_db_invalid_translations(self, rss_manager):
        rss_manager.rss_storage.save_translations.return_value = False
        result = await rss_manager.save_translations_to_db("test_news_id", "invalid")
        assert result is False

    @pytest.mark.asyncio
    async def test_extract_image_from_rss_item_media_thumbnail(self):
        item = {
            "media_thumbnail": [{"url": "http://example.com/image.jpg"}]
        }
        result = await extract_image_from_rss_item(item)
        assert result == "http://example.com/image.jpg"

    @pytest.mark.asyncio
    async def test_extract_image_from_rss_item_enclosure(self):
        item = {
            "enclosures": [{"type": "image/jpeg", "href": "http://example.com/image.jpg"}]
        }
        result = await extract_image_from_rss_item(item)
        assert result == "http://example.com/image.jpg"

    @pytest.mark.asyncio
    async def test_extract_image_from_rss_item_no_image(self):
        item = {"title": "Test Item"}
        result = await extract_image_from_rss_item(item)
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_video_from_rss_item_enclosure(self):
        item = {
            "enclosures": [{"type": "video/mp4", "href": "http://example.com/video.mp4"}]
        }
        result = await extract_video_from_rss_item(item)
        assert result == "http://example.com/video.mp4"

    @pytest.mark.asyncio
    async def test_extract_video_from_rss_item_no_video(self):
        item = {"title": "Test Item"}
        result = await extract_video_from_rss_item(item)
        assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_duplicates_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        rss_manager.rss_storage.cleanup_duplicates.return_value = None
        rss_manager.rss_storage.db_pool = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.rowcount = 5

        result = await rss_manager.cleanup_duplicates()
        assert result is None

    # New tests for orchestration behaviors in RSSManager.process_rss_feed and process_all_feeds
    @pytest.mark.asyncio
    async def test_process_rss_feed_skips_on_rate_limit_and_cooldown(self):
        # Arrange: mock storage methods to force both rate limit and cooldown skips
        storage = AsyncMock()
        storage.get_feed_cooldown.return_value = 60
        storage.get_feed_max_news_per_hour.return_value = 5
        storage.get_recent_items_count.return_value = 5  # equal to max -> skip by rate limit
        storage.get_last_published_time.return_value = datetime.now(timezone.utc)  # would also imply cooldown

        manager = RSSManager(
            rss_fetcher=AsyncMock(),
            rss_validator=AsyncMock(),
            rss_storage=storage,
            media_extractor=AsyncMock(),
            translation_service=AsyncMock(),
            duplicate_detector=AsyncMock(),
            translator_queue=AsyncMock(),
            maintenance_service=AsyncMock(),
        )

        feed_info = {"id": 1, "name": "Test", "url": "http://feed", "lang": "en"}
        headers = {"User-Agent": "X"}

        # Act
        result = await manager.process_rss_feed(feed_info, headers)

        # Assert
        assert result == []
        storage.get_recent_items_count.assert_awaited_once_with(1, 60)
        storage.get_last_published_time.assert_not_called()  # rate limit short-circuits before cooldown check

    @pytest.mark.asyncio
    async def test_process_rss_feed_skips_invalid_items_not_saved(self):
        # Arrange: allow processing but fetcher returns items
        storage = AsyncMock()
        storage.get_feed_cooldown.return_value = 60
        storage.get_feed_max_news_per_hour.return_value = 10
        storage.get_recent_items_count.return_value = 0
        storage.get_last_published_time.return_value = None

        fetcher = AsyncMock()
        fetcher.fetch_feed.return_value = [
            {"title": "A", "content": "C", "link": "L"},
            {"title": "B", "content": "D", "link": "L2"},
        ]

        mock_repo = AsyncMock()
        mock_repo.save_rss_item.return_value = None
        
        # Create proper async context manager for db_pool
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_repo.db_pool = mock_pool

        with patch('repositories.RSSItemRepository', return_value=mock_repo):
            manager = RSSManager(
                rss_fetcher=fetcher,
                rss_validator=AsyncMock(),
                rss_storage=storage,
                media_extractor=AsyncMock(),
                translation_service=AsyncMock(),
                duplicate_detector=AsyncMock(),
                translator_queue=AsyncMock(),
                maintenance_service=AsyncMock(),
            )

            feed_info = {"id": 2, "name": "Feed", "url": "http://feed", "lang": "en"}

            # Act
            items = await manager.process_rss_feed(feed_info, {"User-Agent": "X"})

            # Assert
            assert items == []

    @pytest.mark.asyncio
    async def test_process_rss_feed_saves_valid_items_and_queues_translation_when_enabled(self, monkeypatch):
        # Arrange
        storage = AsyncMock()
        storage.get_feed_cooldown.return_value = 0
        storage.get_feed_max_news_per_hour.return_value = 100
        storage.get_recent_items_count.return_value = 0
        storage.get_last_published_time.return_value = None

        fetcher = AsyncMock()
        fetcher.fetch_feed.return_value = [
            {"title": "A", "content": "C"},
            {"title": "B", "content": "D"},
        ]

        translator_queue = AsyncMock()

        # Mock save_rss_item_to_db method directly instead of repository
        async def mock_save_rss_item_to_db(rss_item, feed_id):
            # Return a unique ID for each item
            if rss_item["title"] == "A":
                return "id1"
            elif rss_item["title"] == "B":
                return "id2"
            return None

        manager = RSSManager(
            rss_fetcher=fetcher,
            rss_validator=AsyncMock(),
            rss_storage=storage,
            media_extractor=AsyncMock(),
            translation_service=AsyncMock(),
            duplicate_detector=AsyncMock(),
            translator_queue=translator_queue,
            maintenance_service=AsyncMock(),
        )
        
        # Replace the save method with our mock
        manager.save_rss_item_to_db = mock_save_rss_item_to_db

        # Enable translation via config.services_config.get_service_config
        class Cfg:
            class translation:
                translation_enabled = True
        monkeypatch.setattr("apps.rss_parser.services.rss_manager.get_service_config", lambda: Cfg)

        # Act
        items = await manager.process_rss_feed({"id": 3, "name": "Feed", "lang": "en", "url": "u"}, {"User-Agent": "X"})

        # Assert
        assert len(items) == 2
        assert items[0]["id"] == "id1"
        assert items[1]["id"] == "id2"
        assert translator_queue.add_task.await_count == 2

    @pytest.mark.asyncio
    async def test_fetch_rss_items_handles_fetch_errors_per_feed(self, monkeypatch):
        # Arrange: two feeds, one raises
        storage = AsyncMock()
        storage.db_pool = MagicMock()
        
        # Mock the repository method to return feeds directly
        with patch.object(RSSFeedRepository, 'get_all_active_feeds', return_value=[
            {"id": 1, "url": "http://a", "name": "A", "lang": "en", "source_id": 1, "category_id": 1, "source": "S", "category": "C", "is_active": 1, "last_published_time": None, "cooldown_minutes": 0, "max_news_per_hour": 0},
            {"id": 2, "url": "http://b", "name": "B", "lang": "en", "source_id": 1, "category_id": 1, "source": "S", "category": "C", "is_active": 1, "last_published_time": None, "cooldown_minutes": 0, "max_news_per_hour": 0}
        ]):
            fetcher = AsyncMock()
            # fetcher.fetch_feeds returns a list aligned with feeds: one Exception, one list
            fetcher.fetch_feeds.return_value = [Exception("fail"), [{"title": "x", "content": "y"}]]

            manager = RSSManager(
                rss_fetcher=fetcher,
                rss_validator=AsyncMock(),
                rss_storage=storage,
                media_extractor=AsyncMock(),
                translation_service=AsyncMock(),
                duplicate_detector=AsyncMock(),
                translator_queue=AsyncMock(),
                maintenance_service=AsyncMock(),
            )

            # Provide DEFAULT_USER_AGENT
            monkeypatch.setattr("apps.rss_parser.services.rss_manager.get_service", lambda t: {"DEFAULT_USER_AGENT": "UA"})

            # Act
            batches = await manager.fetch_rss_items()

            # Assert
            assert len(batches) == 1
            assert len(batches[0]) == 1

    @pytest.mark.asyncio
    async def test_process_all_feeds_aggregates_results(self, monkeypatch):
        # Arrange: three feeds, one returns exception via gather
        feeds = [
            {"id": 1, "name": "A", "url": "a", "lang": "en"},
            {"id": 2, "name": "B", "url": "b", "lang": "en"},
            {"id": 3, "name": "C", "url": "c", "lang": "en"},
        ]

        storage = AsyncMock()
        storage.db_pool = AsyncMock()
        # Replace get_all_active_feeds to return our feeds directly
        manager = RSSManager(
            rss_fetcher=AsyncMock(),
            rss_validator=AsyncMock(),
            rss_storage=storage,
            media_extractor=AsyncMock(),
            translation_service=AsyncMock(),
            duplicate_detector=AsyncMock(),
            translator_queue=AsyncMock(),
            maintenance_service=AsyncMock(),
        )

        async def fake_get_all_active_feeds():
            return feeds
        manager.get_all_active_feeds = fake_get_all_active_feeds

        # Provide DEFAULT_USER_AGENT
        monkeypatch.setattr("apps.rss_parser.services.rss_manager.get_service", lambda t: {"DEFAULT_USER_AGENT": "UA"})

        # Stub process_rss_feed to return varying results, and one raises
        async def prf(feed, headers):
            if feed["id"] == 2:
                return [{"id": "x"}, {"id": "y"}]
            if feed["id"] == 3:
                raise RuntimeError("boom")
            return []
        manager.process_rss_feed = prf

        # Act
        result = await manager.process_all_feeds()

        # Assert
        assert result["status"] == "completed"
        assert result["total_feeds"] == 3
        assert result["processed_feeds"] == 2  # third had exception
        assert result["total_items"] == 2

    @pytest.mark.asyncio
    async def test_process_rss_feed_cooldown_zero(self, rss_manager):
        """Test process_rss_feed when cooldown is zero"""
        storage = AsyncMock()
        storage.get_feed_cooldown.return_value = 0
        storage.get_feed_max_news_per_hour.return_value = 10
        storage.get_recent_items_count.return_value = 0
        storage.get_last_published_time.return_value = None

        fetcher = AsyncMock()
        fetcher.fetch_feed.return_value = [{"title": "Test", "content": "Content"}]

        manager = RSSManager(
            rss_fetcher=fetcher,
            rss_validator=AsyncMock(),
            rss_storage=storage,
            media_extractor=AsyncMock(),
            translation_service=AsyncMock(),
            duplicate_detector=AsyncMock(),
            translator_queue=AsyncMock(),
            maintenance_service=AsyncMock(),
        )

        with patch.object(manager, 'save_rss_item_to_db', return_value="news_id"):
            result = await manager.process_rss_feed({"id": 1, "name": "Test", "lang": "en", "url": "u"}, {"User-Agent": "X"})

        assert len(result) == 1
        assert result[0]["id"] == "news_id"

    @pytest.mark.asyncio
    async def test_process_rss_feed_no_last_published(self, rss_manager):
        """Test process_rss_feed when no last published time"""
        storage = AsyncMock()
        storage.get_feed_cooldown.return_value = 60
        storage.get_feed_max_news_per_hour.return_value = 10
        storage.get_recent_items_count.return_value = 0
        storage.get_last_published_time.return_value = None

        fetcher = AsyncMock()
        fetcher.fetch_feed.return_value = [{"title": "Test", "content": "Content"}]

        manager = RSSManager(
            rss_fetcher=fetcher,
            rss_validator=AsyncMock(),
            rss_storage=storage,
            media_extractor=AsyncMock(),
            translation_service=AsyncMock(),
            duplicate_detector=AsyncMock(),
            translator_queue=AsyncMock(),
            maintenance_service=AsyncMock(),
        )

        with patch.object(manager, 'save_rss_item_to_db', return_value="news_id"):
            result = await manager.process_rss_feed({"id": 1, "name": "Test", "lang": "en", "url": "u"}, {"User-Agent": "X"})

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_process_rss_feed_save_fails(self, rss_manager):
        """Test process_rss_feed when save_rss_item_to_db fails"""
        storage = AsyncMock()
        storage.get_feed_cooldown.return_value = 0
        storage.get_feed_max_news_per_hour.return_value = 10
        storage.get_recent_items_count.return_value = 0
        storage.get_last_published_time.return_value = None

        fetcher = AsyncMock()
        fetcher.fetch_feed.return_value = [{"title": "Test", "content": "Content"}]

        manager = RSSManager(
            rss_fetcher=fetcher,
            rss_validator=AsyncMock(),
            rss_storage=storage,
            media_extractor=AsyncMock(),
            translation_service=AsyncMock(),
            duplicate_detector=AsyncMock(),
            translator_queue=AsyncMock(),
            maintenance_service=AsyncMock(),
        )

        with patch.object(manager, 'save_rss_item_to_db', return_value=None):
            result = await manager.process_rss_feed({"id": 1, "name": "Test", "lang": "en", "url": "u"}, {"User-Agent": "X"})

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_process_rss_feed_translation_disabled(self, rss_manager, monkeypatch):
        """Test process_rss_feed when translation is disabled"""
        storage = AsyncMock()
        storage.get_feed_cooldown.return_value = 0
        storage.get_feed_max_news_per_hour.return_value = 10
        storage.get_recent_items_count.return_value = 0
        storage.get_last_published_time.return_value = None

        fetcher = AsyncMock()
        fetcher.fetch_feed.return_value = [{"title": "Test", "content": "Content"}]

        translator_queue = AsyncMock()

        manager = RSSManager(
            rss_fetcher=fetcher,
            rss_validator=AsyncMock(),
            rss_storage=storage,
            media_extractor=AsyncMock(),
            translation_service=AsyncMock(),
            duplicate_detector=AsyncMock(),
            translator_queue=translator_queue,
            maintenance_service=AsyncMock(),
        )

        with patch.object(manager, 'save_rss_item_to_db', return_value="news_id"):
            # Disable translation
            class Cfg:
                class translation:
                    translation_enabled = False
            monkeypatch.setattr("apps.rss_parser.services.rss_manager.get_service_config", lambda: Cfg)

            result = await manager.process_rss_feed({"id": 1, "name": "Test", "lang": "en", "url": "u"}, {"User-Agent": "X"})

        assert len(result) == 1
        translator_queue.add_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_rss_feed_no_translator_queue(self, rss_manager):
        """Test process_rss_feed when no translator queue"""
        storage = AsyncMock()
        storage.get_feed_cooldown.return_value = 0
        storage.get_feed_max_news_per_hour.return_value = 10
        storage.get_recent_items_count.return_value = 0
        storage.get_last_published_time.return_value = None

        fetcher = AsyncMock()
        fetcher.fetch_feed.return_value = [{"title": "Test", "content": "Content"}]

        manager = RSSManager(
            rss_fetcher=fetcher,
            rss_validator=AsyncMock(),
            rss_storage=storage,
            media_extractor=AsyncMock(),
            translation_service=AsyncMock(),
            duplicate_detector=AsyncMock(),
            translator_queue=None,  # No queue
            maintenance_service=AsyncMock(),
        )

        with patch.object(manager, 'save_rss_item_to_db', return_value="news_id"):
            result = await manager.process_rss_feed({"id": 1, "name": "Test", "lang": "en", "url": "u"}, {"User-Agent": "X"})

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_on_translation_complete_success(self, rss_manager):
        """Test _on_translation_complete success"""
        rss_manager.save_translations_to_db = AsyncMock(return_value=True)

        translations = {"ru": {"title": "Заголовок", "content": "Контент"}}
        await rss_manager._on_translation_complete(translations, "news_id")

        rss_manager.save_translations_to_db.assert_called_once_with("news_id", translations)

    @pytest.mark.asyncio
    async def test_on_translation_complete_failure(self, rss_manager):
        """Test _on_translation_complete failure"""
        rss_manager.save_translations_to_db = AsyncMock(return_value=False)

        translations = {"ru": {"title": "Заголовок", "content": "Контент"}}
        await rss_manager._on_translation_complete(translations, "news_id")

        rss_manager.save_translations_to_db.assert_called_once_with("news_id", translations)

    @pytest.mark.asyncio
    async def test_on_translation_complete_no_task_id(self, rss_manager):
        """Test _on_translation_complete with no task_id"""
        rss_manager.save_translations_to_db = AsyncMock()

        await rss_manager._on_translation_complete({"ru": {}}, None)

        rss_manager.save_translations_to_db.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_translation_complete_empty_translations(self, rss_manager):
        """Test _on_translation_complete with empty translations"""
        rss_manager.save_translations_to_db = AsyncMock()

        await rss_manager._on_translation_complete({}, "news_id")

        rss_manager.save_translations_to_db.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_translation_error(self, rss_manager):
        """Test _on_translation_error"""
        error_data = {"error": "Translation failed"}
        await rss_manager._on_translation_error(error_data, "task_id")
        # Just checks that no exception is raised

    @pytest.mark.asyncio
    async def test_process_all_feeds_no_feeds(self, rss_manager):
        """Test process_all_feeds when no feeds"""
        with patch.object(rss_manager, 'get_all_active_feeds', return_value=[]):
            result = await rss_manager.process_all_feeds()

        assert result == {"status": "no_feeds", "processed_feeds": 0, "total_items": 0}

    @pytest.mark.asyncio
    async def test_extract_image_from_rss_item_delegates_to_extractor(self, rss_manager):
        """Test extract_image_from_rss_item delegates to media_extractor"""
        rss_manager.media_extractor.extract_image = AsyncMock(return_value="image_url")

        result = await rss_manager.extract_image_from_rss_item({"media_thumbnail": []})

        assert result == "image_url"
        rss_manager.media_extractor.extract_image.assert_called_once_with({"media_thumbnail": []})

    @pytest.mark.asyncio
    async def test_extract_video_from_rss_item_delegates_to_extractor(self, rss_manager):
        """Test extract_video_from_rss_item delegates to media_extractor"""
        rss_manager.media_extractor.extract_video = MagicMock(return_value="video_url")

        result = rss_manager.extract_video_from_rss_item({"enclosures": []})

        assert result == "video_url"
        rss_manager.media_extractor.extract_video.assert_called_once_with({"enclosures": []})

    @pytest.mark.asyncio
    async def test_get_feeds_by_category_failure(self, rss_manager):
        """Test get_feeds_by_category with exception"""
        with patch.object(RSSFeedRepository, 'get_feeds_by_category', side_effect=Exception("DB error")):
            result = await rss_manager.get_feeds_by_category('Tech')
            assert result == []

    @pytest.mark.asyncio
    async def test_get_feeds_by_language_failure(self, rss_manager):
        """Test get_feeds_by_language with exception"""
        with patch.object(RSSFeedRepository, 'get_feeds_by_language', side_effect=Exception("DB error")):
            result = await rss_manager.get_feeds_by_language('en')
            assert result == []

    @pytest.mark.asyncio
    async def test_get_feeds_by_source_failure(self, rss_manager):
        """Test get_feeds_by_source with exception"""
        with patch.object(RSSFeedRepository, 'get_feeds_by_source', side_effect=Exception("DB error")):
            result = await rss_manager.get_feeds_by_source('BBC')
            assert result == []

    @pytest.mark.asyncio
    async def test_fetch_rss_items_no_feeds(self, rss_manager):
        """Test fetch_rss_items when no feeds"""
        with patch.object(rss_manager, 'get_all_active_feeds', return_value=[]):
            result = await rss_manager.fetch_rss_items()
            assert result == []

    @pytest.mark.asyncio
    async def test_process_rss_feed_cooldown_active(self, rss_manager):
        """Test process_rss_feed skips on active cooldown"""
        from datetime import datetime, timezone, timedelta

        storage = AsyncMock()
        storage.get_feed_cooldown.return_value = 60
        storage.get_feed_max_news_per_hour.return_value = 10
        storage.get_recent_items_count.return_value = 5  # below limit
        storage.get_last_published_time.return_value = datetime.now(timezone.utc) - timedelta(minutes=30)  # within cooldown

        fetcher = AsyncMock()

        manager = RSSManager(
            rss_fetcher=fetcher,
            rss_validator=AsyncMock(),
            rss_storage=storage,
            media_extractor=AsyncMock(),
            translation_service=AsyncMock(),
            duplicate_detector=AsyncMock(),
            translator_queue=AsyncMock(),
            maintenance_service=AsyncMock(),
        )

        result = await manager.process_rss_feed({"id": 1, "name": "Test", "lang": "en", "url": "u"}, {"User-Agent": "X"})

        assert result == []
        fetcher.fetch_feed.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_rss_feed_fetch_returns_empty(self, rss_manager):
        """Test process_rss_feed when fetch_feed returns empty list"""
        storage = AsyncMock()
        storage.get_feed_cooldown.return_value = 0
        storage.get_feed_max_news_per_hour.return_value = 10
        storage.get_recent_items_count.return_value = 0
        storage.get_last_published_time.return_value = None

        fetcher = AsyncMock()
        fetcher.fetch_feed.return_value = []  # Empty

        manager = RSSManager(
            rss_fetcher=fetcher,
            rss_validator=AsyncMock(),
            rss_storage=storage,
            media_extractor=AsyncMock(),
            translation_service=AsyncMock(),
            duplicate_detector=AsyncMock(),
            translator_queue=AsyncMock(),
            maintenance_service=AsyncMock(),
        )

        result = await manager.process_rss_feed({"id": 1, "name": "Test", "lang": "en", "url": "u"}, {"User-Agent": "X"})

        assert result == []

    @pytest.mark.asyncio
    async def test_process_rss_feed_save_raises_exception(self, rss_manager):
        """Test process_rss_feed when save_rss_item_to_db raises exception"""
        storage = AsyncMock()
        storage.get_feed_cooldown.return_value = 0
        storage.get_feed_max_news_per_hour.return_value = 10
        storage.get_recent_items_count.return_value = 0
        storage.get_last_published_time.return_value = None

        fetcher = AsyncMock()
        fetcher.fetch_feed.return_value = [{"title": "Test", "content": "Content"}]

        manager = RSSManager(
            rss_fetcher=fetcher,
            rss_validator=AsyncMock(),
            rss_storage=storage,
            media_extractor=AsyncMock(),
            translation_service=AsyncMock(),
            duplicate_detector=AsyncMock(),
            translator_queue=AsyncMock(),
            maintenance_service=AsyncMock(),
        )

        with patch.object(manager, 'save_rss_item_to_db', side_effect=Exception("Save error")):
            result = await manager.process_rss_feed({"id": 1, "name": "Test", "lang": "en", "url": "u"}, {"User-Agent": "X"})

        assert result == []

    @pytest.mark.asyncio
    async def test_process_rss_feed_outer_exception(self, rss_manager):
        """Test process_rss_feed outer exception handling"""
        storage = AsyncMock()
        storage.get_feed_cooldown.side_effect = Exception("Cooldown error")

        fetcher = AsyncMock()

        manager = RSSManager(
            rss_fetcher=fetcher,
            rss_validator=AsyncMock(),
            rss_storage=storage,
            media_extractor=AsyncMock(),
            translation_service=AsyncMock(),
            duplicate_detector=AsyncMock(),
            translator_queue=AsyncMock(),
            maintenance_service=AsyncMock(),
        )

        result = await manager.process_rss_feed({"id": 1, "name": "Test", "lang": "en", "url": "u"}, {"User-Agent": "X"})

        assert result == []

    @pytest.mark.asyncio
    async def test_on_translation_complete_raises_exception(self, rss_manager):
        """Test _on_translation_complete when save_translations_to_db raises exception"""
        rss_manager.save_translations_to_db = AsyncMock(side_effect=Exception("Save error"))

        translations = {"ru": {"title": "Заголовок", "content": "Контент"}}
        await rss_manager._on_translation_complete(translations, "news_id")

        rss_manager.save_translations_to_db.assert_called_once_with("news_id", translations)