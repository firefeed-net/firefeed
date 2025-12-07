import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from services.rss import RSSManager
from utils.media_extractors import extract_image_from_rss_item, extract_video_from_rss_item


@pytest.mark.asyncio
class TestRSSManager:
    @pytest.fixture
    def rss_manager(self):
        return RSSManager()

    @pytest.fixture
    def mock_pool(self):
        pool = AsyncMock()
        return pool

    @pytest.fixture
    def mock_conn(self):
        conn = AsyncMock()
        return conn

    @pytest.fixture
    def mock_cur(self):
        cur = AsyncMock()
        return cur

    async def test_get_pool(self, rss_manager, mock_pool):
        with patch('rss_manager.get_shared_db_pool', return_value=mock_pool):
            result = await rss_manager.get_pool()
            assert result == mock_pool

    async def test_close_pool(self, rss_manager):
        await rss_manager.close_pool()

    async def test_get_all_active_feeds_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone = AsyncMock(side_effect=[
            (1, 'http://example.com/rss', 'Test Feed', 'en', 1, 1, 'BBC', 'Tech'),
            None
        ])
        mock_cur.description = [('id',), ('url',), ('name',), ('language',), ('source_id',), ('category_id',), ('source_name',), ('category_name',)]

        result = await rss_manager.get_all_active_feeds()
        assert len(result) == 1
        assert result[0]['name'] == 'Test Feed'

    async def test_get_all_active_feeds_failure(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.execute.side_effect = Exception("DB error")

        result = await rss_manager.get_all_active_feeds()
        assert result == []

    async def test_get_feeds_by_category_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone = AsyncMock(side_effect=[
            (1, 'http://example.com/rss', 'Test Feed', 'en', 1, 1, 'BBC', 'Tech'),
            None
        ])
        mock_cur.description = [('id',), ('url',), ('name',), ('language',), ('source_id',), ('category_id',), ('source_name',), ('category_name',)]

        result = await rss_manager.get_feeds_by_category('Tech')
        assert len(result) == 1
        assert result[0]['category'] == 'Tech'

    async def test_get_feeds_by_language_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone = AsyncMock(side_effect=[
            (1, 'http://example.com/rss', 'Test Feed', 'en', 1, 1, 'BBC', 'Tech'),
            None
        ])
        mock_cur.description = [('id',), ('url',), ('name',), ('language',), ('source_id',), ('category_id',), ('source_name',), ('category_name',)]

        result = await rss_manager.get_feeds_by_language('en')
        assert len(result) == 1
        assert result[0]['lang'] == 'en'

    async def test_get_feeds_by_source_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone = AsyncMock(side_effect=[
            (1, 'http://example.com/rss', 'Test Feed', 'en', 1, 1, 'BBC', 'Tech'),
            None
        ])
        mock_cur.description = [('id',), ('url',), ('name',), ('language',), ('source_id',), ('category_id',), ('source_name',), ('category_name',)]

        result = await rss_manager.get_feeds_by_source('BBC')
        assert len(result) == 1
        assert result[0]['source'] == 'BBC'

    async def test_add_feed_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone = AsyncMock(side_effect=[(1,), (1,)])

        result = await rss_manager.add_feed('http://example.com/rss', 'Tech', 'BBC', 'en')
        assert result is True

    async def test_add_feed_category_not_found(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = None

        result = await rss_manager.add_feed('http://example.com/rss', 'NonExistent', 'BBC', 'en')
        assert result is False

    async def test_update_feed_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone = AsyncMock(side_effect=[(1,), (1,)])
        mock_cur.rowcount = 1

        result = await rss_manager.update_feed(1, name='Updated Feed')
        assert result is True

    async def test_delete_feed_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.rowcount = 1

        result = await rss_manager.delete_feed(1)
        assert result is True

    async def test_get_feed_cooldown_minutes_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = (30,)

        result = await rss_manager.get_feed_cooldown_minutes(1)
        assert result == 30

    async def test_get_feed_cooldown_minutes_default(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = None

        result = await rss_manager.get_feed_cooldown_minutes(1)
        assert result == 60

    async def test_get_max_news_per_hour_for_feed_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = (5,)

        result = await rss_manager.get_max_news_per_hour_for_feed(1)
        assert result == 5

    async def test_get_last_published_time_for_feed_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = (datetime.utcnow(),)

        result = await rss_manager.get_last_published_time_for_feed(1)
        assert isinstance(result, datetime)

    async def test_get_recent_rss_items_count_for_feed_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
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

        news_id = rss_manager.generate_news_id(title, content, link, feed_id)
        assert isinstance(news_id, str)
        assert len(news_id) == 64  # SHA256 hex length

    async def test_check_for_duplicates_false(self, rss_manager):
        with patch('rss_manager.FireFeedDuplicateDetector') as mock_detector_class:
            mock_detector = AsyncMock()
            mock_detector.is_duplicate_strict.return_value = (False, {})
            mock_detector_class.return_value = mock_detector

            result = await rss_manager.check_for_duplicates("title", "content", "link", "en")
            assert result is False

    async def test_check_for_duplicates_true(self, rss_manager):
        with patch('rss_manager.FireFeedDuplicateDetector') as mock_detector_class:
            mock_detector = AsyncMock()
            mock_detector.is_duplicate_strict.return_value = (True, {"news_id": "duplicate_id"})
            mock_detector_class.return_value = mock_detector

            result = await rss_manager.check_for_duplicates("title", "content", "link", "en")
            assert result is True

    async def test_validate_rss_feed_success(self, rss_manager):
        with patch('feedparser.parse') as mock_parse:
            mock_feed = MagicMock()
            mock_feed.bozo = False
            mock_feed.entries = [{"title": "Test Entry"}]
            mock_parse.return_value = mock_feed

            headers = {"User-Agent": "Test"}
            result = await rss_manager.validate_rss_feed("http://example.com/rss", headers)
            assert result is True

    async def test_validate_rss_feed_no_entries(self, rss_manager):
        with patch('feedparser.parse') as mock_parse:
            mock_feed = MagicMock()
            mock_feed.bozo = False
            mock_feed.entries = []
            mock_parse.return_value = mock_feed

            headers = {"User-Agent": "Test"}
            result = await rss_manager.validate_rss_feed("http://example.com/rss", headers)
            assert result is False

    async def test_save_rss_item_to_db_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = (1,)  # category_id

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

    async def test_save_rss_item_to_db_category_not_found(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = None  # category not found

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

    async def test_save_translations_to_db_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone.return_value = ("en", "Original Title", "Original Content")

        translations = {
            "ru": {"title": "Русский заголовок", "content": "Русский контент"},
            "de": {"title": "Deutscher Titel", "content": "Deutscher Inhalt"}
        }

        result = await rss_manager.save_translations_to_db("test_news_id", translations)
        assert result is True

    async def test_save_translations_to_db_empty_translations(self, rss_manager):
        result = await rss_manager.save_translations_to_db("test_news_id", {})
        assert result is True

    async def test_save_translations_to_db_invalid_translations(self, rss_manager):
        result = await rss_manager.save_translations_to_db("test_news_id", "invalid")
        assert result is False

    async def test_extract_image_from_rss_item_media_thumbnail(self):
        item = {
            "media_thumbnail": [{"url": "http://example.com/image.jpg"}]
        }
        result = await extract_image_from_rss_item(item)
        assert result == "http://example.com/image.jpg"

    async def test_extract_image_from_rss_item_enclosure(self):
        item = {
            "enclosures": [{"type": "image/jpeg", "href": "http://example.com/image.jpg"}]
        }
        result = await extract_image_from_rss_item(item)
        assert result == "http://example.com/image.jpg"

    async def test_extract_image_from_rss_item_no_image(self):
        item = {"title": "Test Item"}
        result = await extract_image_from_rss_item(item)
        assert result is None

    async def test_extract_video_from_rss_item_enclosure(self):
        item = {
            "enclosures": [{"type": "video/mp4", "href": "http://example.com/video.mp4"}]
        }
        result = await extract_video_from_rss_item(item)
        assert result == "http://example.com/video.mp4"

    async def test_extract_video_from_rss_item_no_video(self):
        item = {"title": "Test Item"}
        result = await extract_video_from_rss_item(item)
        assert result is None

    async def test_fetch_unprocessed_rss_items_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.fetchone = AsyncMock(side_effect=[
            ("news_id", "Title", "Content", "en", "image.jpg", 1, 1, None, datetime.utcnow(), datetime.utcnow(), "Tech", "BBC", "http://example.com"),
            None
        ])
        mock_cur.description = [('news_id',), ('original_title',), ('original_content',), ('original_language',), ('image_filename',), ('category_id',), ('rss_feed_id',), ('telegram_published_at',), ('created_at',), ('updated_at',), ('category_name',), ('source_name',), ('source_url',)]

        result = await rss_manager.fetch_unprocessed_rss_items()
        assert len(result) == 1
        assert result[0]['news_id'] == 'news_id'

    async def test_cleanup_duplicates_success(self, rss_manager, mock_pool, mock_conn, mock_cur):
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
        mock_cur.rowcount = 5

        result = await rss_manager.cleanup_duplicates()
        assert result == []

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
        storage.save_rss_item.return_value = None  # simulate validator/storage rejecting item

        fetcher = AsyncMock()
        fetcher.fetch_feed.return_value = [
            {"title": "A", "content": "C", "link": "L"},
            {"title": "B", "content": "D", "link": "L2"},
        ]

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
        assert storage.save_rss_item.await_count == 2

    @pytest.mark.asyncio
    async def test_process_rss_feed_saves_valid_items_and_queues_translation_when_enabled(self, monkeypatch):
        # Arrange
        storage = AsyncMock()
        storage.get_feed_cooldown.return_value = 0
        storage.get_feed_max_news_per_hour.return_value = 100
        storage.get_recent_items_count.return_value = 0
        storage.get_last_published_time.return_value = None
        storage.save_rss_item.side_effect = ["id1", "id2"]

        fetcher = AsyncMock()
        fetcher.fetch_feed.return_value = [
            {"title": "A", "content": "C"},
            {"title": "B", "content": "D"},
        ]

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

        # Enable translation via config.services_config.get_service_config
        class Cfg:
            class translation:
                translation_enabled = True
        monkeypatch.setattr("services.rss.rss_manager.get_service_config", lambda: Cfg)

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
        storage.db_pool = AsyncMock()
        # emulate async iteration over cursor
        class Cursor:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass
            async def execute(self, q):
                pass
            def __aiter__(self):
                self._rows = [
                    (1, "http://a", "A", "en", 1, 1, "S", "C", 0, 0),
                    (2, "http://b", "B", "en", 1, 1, "S", "C", 0, 0),
                ]
                self._i = 0
                return self
            async def __anext__(self):
                if self._i >= len(self._rows):
                    raise StopAsyncIteration
                row = self._rows[self._i]
                self._i += 1
                return row
        class Conn:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc, tb):
                pass
            def cursor(self):
                return Cursor()
        storage.db_pool.acquire.return_value = Conn()

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
        monkeypatch.setattr("services.rss.rss_manager.get_service", lambda t: {"DEFAULT_USER_AGENT": "UA"})

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
        monkeypatch.setattr("services.rss.rss_manager.get_service", lambda t: {"DEFAULT_USER_AGENT": "UA"})

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