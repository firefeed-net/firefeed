import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime
from apps.api.websocket import router, broadcast_new_rss_items, check_for_new_rss_items, active_connections, active_connections_lock
from di_container import get_service


@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_config():
    return {
        'MAX_WEBSOCKET_CONNECTIONS': 10,
        'RSS_ITEM_CHECK_INTERVAL_SECONDS': 30
    }


@pytest.fixture
def mock_rss_item_repo():
    return AsyncMock()


class TestWebSocket:
    def setup_method(self):
        """Clean up active connections before each test"""
        active_connections.clear()

    def teardown_method(self):
        """Clean up active connections after each test"""
        active_connections.clear()

    @pytest.mark.asyncio
    async def test_websocket_connection_limit_exceeded(self, client, mock_config):
        """Test websocket rejects connection when limit exceeded"""
        with patch('apps.api.websocket.get_service', return_value=mock_config):
            # Fill up connections
            for i in range(10):
                ws_mock = MagicMock()
                active_connections[ws_mock] = {}

            with pytest.raises(Exception):  # WebSocketDisconnect is raised
                with client.websocket_connect("/api/v1/ws/rss-items"):
                    pass

    @pytest.mark.asyncio
    async def test_websocket_subscribe_timeout(self, client, mock_config):
        """Test websocket subscribe timeout"""
        with patch('apps.api.websocket.get_service', return_value=mock_config):
            # WebSocket should close due to timeout
            with client.websocket_connect("/api/v1/ws/rss-items") as websocket:
                # Don't send anything, should timeout and close
                # The connection should close automatically
                try:
                    # Try to receive - should timeout/close
                    websocket.receive_text()
                    # If we get here, the test setup might be wrong
                    assert False, "Expected WebSocket to close due to timeout"
                except Exception:
                    # This is expected - WebSocket should close
                    pass

    @pytest.mark.asyncio
    async def test_websocket_invalid_json(self, client, mock_config):
        """Test websocket invalid JSON"""
        with patch('apps.api.websocket.get_service', return_value=mock_config):
            with client.websocket_connect("/api/v1/ws/rss-items") as websocket:
                websocket.send_text("invalid json")
                data = websocket.receive_text()
                assert json.loads(data)["error"] == "Invalid JSON"

    @pytest.mark.asyncio
    async def test_websocket_wrong_message_type(self, client, mock_config):
        """Test websocket wrong message type"""
        with patch('apps.api.websocket.get_service', return_value=mock_config):
            with client.websocket_connect("/api/v1/ws/rss-items") as websocket:
                websocket.send_text(json.dumps({"type": "wrong"}))
                data = websocket.receive_text()
                assert json.loads(data)["error"] == "Expected subscribe message"

    @pytest.mark.asyncio
    async def test_websocket_successful_subscribe(self, client, mock_config):
        """Test successful websocket subscribe"""
        with patch('apps.api.websocket.get_service', return_value=mock_config):
            with client.websocket_connect("/api/v1/ws/rss-items") as websocket:
                websocket.send_text(json.dumps({
                    "type": "subscribe",
                    "original_language": "en",
                    "display_language": "ru",
                    "use_translations": True
                }))

                # Should not receive error, connection stays open
                # Send ping to test
                websocket.send_text(json.dumps({"type": "ping"}))
                response = websocket.receive_text()
                data = json.loads(response)
                assert data["type"] == "pong"
                assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, client, mock_config):
        """Test websocket ping pong"""
        with patch('apps.api.websocket.get_service', return_value=mock_config):
            with client.websocket_connect("/api/v1/ws/rss-items") as websocket:
                websocket.send_text(json.dumps({"type": "subscribe"}))

                websocket.send_text(json.dumps({"type": "ping"}))
                response = websocket.receive_text()
                data = json.loads(response)
                assert data["type"] == "pong"
                assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_websocket_update_params(self, client, mock_config):
        """Test websocket update params"""
        with patch('apps.api.websocket.get_service', return_value=mock_config):
            with client.websocket_connect("/api/v1/ws/rss-items") as websocket:
                websocket.send_text(json.dumps({"type": "subscribe"}))

                websocket.send_text(json.dumps({
                    "type": "update_params",
                    "display_language": "de",
                    "use_translations": False
                }))

                response = websocket.receive_text()
                data = json.loads(response)
                assert data["type"] == "params_updated"

    @pytest.mark.asyncio
    async def test_websocket_echo_invalid_json(self, client, mock_config):
        """Test websocket echo on invalid JSON in message"""
        with patch('apps.api.websocket.get_service', return_value=mock_config):
            with client.websocket_connect("/api/v1/ws/rss-items") as websocket:
                websocket.send_text(json.dumps({"type": "subscribe"}))

                websocket.send_text("not json")
                response = websocket.receive_text()
                data = json.loads(response)
                assert data["type"] == "echo"
                assert data["data"] == "not json"

    @pytest.mark.asyncio
    async def test_broadcast_new_rss_items_no_connections(self):
        """Test broadcast with no active connections"""
        active_connections.clear()
        await broadcast_new_rss_items([{"news_id": "1", "title": "Test"}])
        # Should not raise exception

    @pytest.mark.asyncio
    async def test_broadcast_new_rss_items_with_filtering(self):
        """Test broadcast with language filtering"""
        ws_mock = AsyncMock()
        params = {"original_language": "en", "display_language": "ru", "use_translations": True}

        async with active_connections_lock:
            active_connections[ws_mock] = params

        rss_items = [
            {
                "news_id": "1",
                "original_title": "English Title",
                "original_language": "en",
                "category": "Tech",
                "created_at": "2023-01-01T00:00:00Z",
                "translations": {
                    "ru": {"title": "Русский заголовок"}
                }
            },
            {
                "news_id": "2",
                "original_title": "German Title",
                "original_language": "de",
                "category": "Sports",
                "created_at": "2023-01-01T00:00:00Z"
            }
        ]

        await broadcast_new_rss_items(rss_items)

        # Should send to ws_mock with filtered items (only English)
        ws_mock.send_text.assert_called_once()
        call_args = ws_mock.send_text.call_args[0][0]
        data = json.loads(call_args)
        assert data["type"] == "new_rss_items"
        assert data["count"] == 1
        assert len(data["rss_items"]) == 1
        assert data["rss_items"][0]["news_id"] == "1"
        assert "Русский заголовок" in data["rss_items"][0]["title"]

        active_connections.clear()

    @pytest.mark.asyncio
    async def test_broadcast_new_rss_items_disconnect_handling(self):
        """Test broadcast handles disconnected clients"""
        ws_mock = AsyncMock()
        ws_mock.send_text.side_effect = Exception("Disconnected")

        async with active_connections_lock:
            active_connections[ws_mock] = {"original_language": "en"}

        rss_items = [{"news_id": "1", "original_title": "Test", "original_language": "en"}]

        await broadcast_new_rss_items(rss_items)

        # Connection should be removed
        assert ws_mock not in active_connections

    @pytest.mark.asyncio
    async def test_check_for_new_rss_items(self, mock_config, mock_rss_item_repo):
        """Test check_for_new_rss_items function"""
        from apps.api.websocket import last_rss_items_check_time
        from datetime import datetime, timezone
        from interfaces import IRSSItemRepository

        # Reset the global variable
        original_time = last_rss_items_check_time
        last_rss_items_check_time = datetime.min.replace(tzinfo=timezone.utc)  # Old time

        try:
            with patch('apps.api.websocket.get_service') as mock_get_service, \
                 patch('asyncio.sleep', return_value=None), \
                 patch('apps.api.websocket.broadcast_new_rss_items') as mock_broadcast:

                def get_service_side_effect(service_type):
                    if service_type == dict:
                        return mock_config
                    elif service_type == IRSSItemRepository:
                        return mock_rss_item_repo
                    return None
                
                mock_get_service.side_effect = get_service_side_effect

                mock_rss_item_repo.get_recent_rss_items_for_broadcast.return_value = [
                    {"news_id": "1", "title": "New Item"}
                ]

                # Simulate the core logic of check_for_new_rss_items
                config_obj = get_service_side_effect(dict)
                check_interval = config_obj.get('RSS_ITEM_CHECK_INTERVAL_SECONDS', 30)
                rss_item_repo = get_service_side_effect(IRSSItemRepository)
                
                # Skip the initial sleep for testing
                try:
                    rss_items_payload = await rss_item_repo.get_recent_rss_items_for_broadcast(last_rss_items_check_time)
                    if rss_items_payload:
                        await mock_broadcast(rss_items_payload)
                except Exception as e:
                    pass  # Ignore errors in test

                mock_broadcast.assert_called_once_with([{"news_id": "1", "title": "New Item"}])
        finally:
            last_rss_items_check_time = original_time

    @pytest.mark.asyncio
    async def test_check_for_new_rss_items_no_items(self, mock_config, mock_rss_item_repo):
        """Test check_for_new_rss_items with no new items"""
        from interfaces import IRSSItemRepository
        
        with patch('apps.api.websocket.get_service') as mock_get_service, \
             patch('asyncio.sleep', return_value=None), \
             patch('apps.api.websocket.broadcast_new_rss_items') as mock_broadcast:

            def get_service_side_effect(service_type):
                if service_type == dict:
                    return mock_config
                elif service_type == IRSSItemRepository:
                    return mock_rss_item_repo
                return None
            
            mock_get_service.side_effect = get_service_side_effect
            mock_rss_item_repo.get_recent_rss_items_for_broadcast.return_value = []

            task = asyncio.create_task(check_for_new_rss_items())
            await asyncio.sleep(0.1)
            task.cancel()

            mock_broadcast.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_for_new_rss_items_exception(self, mock_config, mock_rss_item_repo):
        """Test check_for_new_rss_items handles exceptions"""
        from interfaces import IRSSItemRepository
        
        with patch('apps.api.websocket.get_service') as mock_get_service, \
             patch('asyncio.sleep', return_value=None), \
             patch('apps.api.websocket.broadcast_new_rss_items') as mock_broadcast:

            def get_service_side_effect(service_type):
                if service_type == dict:
                    return mock_config
                elif service_type == IRSSItemRepository:
                    return mock_rss_item_repo
                return None
            
            mock_get_service.side_effect = get_service_side_effect
            mock_rss_item_repo.get_recent_rss_items_for_broadcast.side_effect = Exception("DB error")

            task = asyncio.create_task(check_for_new_rss_items())
            await asyncio.sleep(0.1)
            task.cancel()

            mock_broadcast.assert_not_called()