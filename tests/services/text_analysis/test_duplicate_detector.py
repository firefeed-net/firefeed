import pytest
from unittest.mock import AsyncMock, patch
from services.text_analysis.duplicate_detector import FireFeedDuplicateDetector


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def detector(mock_repo):
    with patch('services.text_analysis.duplicate_detector.get_service') as mock_get_service, \
         patch('services.text_analysis.duplicate_detector.FireFeedEmbeddingsProcessor') as mock_processor_class:

        mock_config = type('Config', (), {
            'deduplication': type('Deduplication', (), {
                'embedding_models': type('Models', (), {'sentence_transformer_model': 'test-model'})(),
                'similarity_threshold': 0.8
            })()
        })()
        mock_get_service.return_value = mock_config

        mock_processor = AsyncMock()
        mock_processor_class.return_value = mock_processor

        return FireFeedDuplicateDetector(mock_repo)


class TestFireFeedDuplicateDetector:
    @pytest.mark.asyncio
    async def test_generate_embedding(self, detector):
        detector.processor.combine_texts = AsyncMock(return_value="combined text")
        detector.processor.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])

        result = await detector.generate_embedding("title", "content", "en")

        assert result == [0.1, 0.2, 0.3]
        detector.processor.combine_texts.assert_called_once()
        detector.processor.generate_embedding.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_embedding(self, detector, mock_repo):
        await detector.save_embedding("item123", [0.1, 0.2, 0.3])

        mock_repo.save_embedding.assert_called_once_with("item123", [0.1, 0.2, 0.3])

    @pytest.mark.asyncio
    async def test_is_duplicate_by_url(self, detector, mock_repo):
        mock_repo.check_duplicate_by_url = AsyncMock(return_value={"news_id": "dup123"})

        is_dup, info = await detector.is_duplicate("title", "content", "http://example.com", "en")

        assert is_dup is True
        assert info["news_id"] == "dup123"

    @pytest.mark.asyncio
    async def test_is_duplicate_not_duplicate(self, detector, mock_repo):
        mock_repo.check_duplicate_by_url = AsyncMock(return_value=None)
        detector.processor.combine_texts = AsyncMock(return_value="combined")
        detector.processor.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        mock_repo.get_similar_rss_items_by_embedding = AsyncMock(return_value=[])
        detector.processor.get_dynamic_threshold = AsyncMock(return_value=0.8)

        is_dup, info = await detector.is_duplicate("title", "content", "http://example.com", "en")

        assert is_dup is False
        assert info is None

    @pytest.mark.asyncio
    async def test_process_rss_item_unique(self, detector, mock_repo):
        mock_repo.get_embedding_by_news_id = AsyncMock(return_value=None)
        detector.processor.combine_texts = AsyncMock(return_value="combined")
        detector.processor.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        mock_repo.get_similar_rss_items_by_embedding = AsyncMock(return_value=[])
        detector.processor.get_dynamic_threshold = AsyncMock(return_value=0.8)

        result = await detector.process_rss_item("item123", "title", "content", "en")

        assert result is True
        mock_repo.save_embedding.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_rss_items_without_embeddings(self, detector, mock_repo):
        mock_repo.get_rss_items_without_embeddings = AsyncMock(return_value=[{"news_id": "1"}])

        result = await detector.get_rss_items_without_embeddings(10)

        assert len(result) == 1
        assert result[0]["news_id"] == "1"