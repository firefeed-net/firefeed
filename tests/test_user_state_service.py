import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from di_container import di_container

from apps.telegram_bot.services.user_state_service import (
    initialize_user_manager,
    set_current_user_language,
    get_current_user_language,
    update_user_state,
    get_user_state,
    set_user_menu,
    get_user_menu,
    cleanup_expired_data,
    clear_user_state,
)


class TestUserStateService:
    @pytest.mark.anyio
    async def test_initialize_user_manager_idempotent(self):
        # First initialization
        with patch.object(di_container, 'resolve', return_value=AsyncMock()):
            await initialize_user_manager()
            # Second call should not raise and not recreate instance
            await initialize_user_manager()

    @pytest.mark.anyio
    async def test_set_current_user_language_updates_memory_and_calls_manager(self):
        mock_um = AsyncMock()
        with patch('apps.telegram_bot.services.user_state_service.get_service', return_value=mock_um):
            with patch('apps.telegram_bot.services.user_state_service.USER_LANGUAGES', {}):
                import apps.telegram_bot.services.user_state_service as uss
                uss.telegram_user_service = None
                await initialize_user_manager()
                await set_current_user_language(10, 'ru')
                mock_um.set_user_language.assert_called_once_with(10, 'ru')
                assert 10 in __import__('apps.telegram_bot.services.user_state_service', fromlist=['']).USER_LANGUAGES
                assert __import__('apps.telegram_bot.services.user_state_service', fromlist=['']).USER_LANGUAGES[10]['language'] == 'ru'

    @pytest.mark.asyncio
    async def test_get_current_user_language_updates_last_access_for_dict_format(self):
        with patch('apps.telegram_bot.services.user_state_service.USER_LANGUAGES', {42: {"language": "de", "last_access": 0}}):
            lang = await get_current_user_language(42)
            assert lang == 'de'
            assert __import__('apps.telegram_bot.services.user_state_service', fromlist=['']).USER_LANGUAGES[42]['last_access'] > 0

    @pytest.mark.asyncio
    async def test_get_current_user_language_upgrades_old_format(self):
        with patch('apps.telegram_bot.services.user_state_service.USER_LANGUAGES', {7: 'en'}):
            lang = await get_current_user_language(7)
            assert lang == 'en'
            # Ensure upgraded to dict format
            assert isinstance(__import__('apps.telegram_bot.services.user_state_service', fromlist=['']).USER_LANGUAGES[7], dict)
            assert __import__('apps.telegram_bot.services.user_state_service', fromlist=['']).USER_LANGUAGES[7]['language'] == 'en'

    @pytest.mark.anyio
    async def test_get_current_user_language_fetches_from_db_and_caches(self):
        from apps.telegram_bot.services.user_state_service import USER_LANGUAGES
        USER_LANGUAGES.clear()
        mock_um = MagicMock()
        mock_um.get_user_language = AsyncMock(return_value='en')
        with patch('apps.telegram_bot.services.user_state_service.telegram_user_service', mock_um):
            lang = await get_current_user_language(1000)
            assert lang == 'en'

    @pytest.mark.anyio
    async def test_get_current_user_language_default_and_on_exception(self):
        from apps.telegram_bot.services.user_state_service import USER_LANGUAGES
        # When DB returns None -> default to en
        USER_LANGUAGES.clear()
        mock_um = MagicMock()
        mock_um.get_user_language = AsyncMock(return_value=None)
        with patch('apps.telegram_bot.services.user_state_service.telegram_user_service', mock_um):
            lang = await get_current_user_language(2000)
            assert lang == 'en'
        # When exception occurs -> default to en
        USER_LANGUAGES.clear()
        mock_um = MagicMock()
        mock_um.get_user_language = AsyncMock(side_effect=RuntimeError('boom'))
        with patch('apps.telegram_bot.services.user_state_service.telegram_user_service', mock_um):
            lang = await get_current_user_language(2001)
            assert lang == 'en'

    def test_update_and_get_user_state_manage_last_access(self):
        with patch('apps.telegram_bot.services.user_state_service.USER_STATES', {}):
            update_user_state(1, {"step": "start"})
            state = get_user_state(1)
            assert state['step'] == 'start'
            assert state['last_access'] > 0

    def test_set_and_get_user_menu_with_last_access(self):
        with patch('apps.telegram_bot.services.user_state_service.USER_CURRENT_MENUS', {}):
            set_user_menu(2, 'main')
            menu = get_user_menu(2)
            assert menu == 'main'
            assert __import__('apps.telegram_bot.services.user_state_service', fromlist=['']).USER_CURRENT_MENUS[2]['last_access'] > 0

    def test_get_user_menu_when_absent_returns_none(self):
        with patch('apps.telegram_bot.services.user_state_service.USER_CURRENT_MENUS', {}):
            assert get_user_menu(999) is None

    @pytest.mark.anyio
    async def test_cleanup_expired_data_calls_cleanup_utils_and_logs(self):
        with patch('apps.telegram_bot.services.user_state_service.USER_STATES', {1: {"last_access": 0}}), \
             patch('apps.telegram_bot.services.user_state_service.USER_CURRENT_MENUS', {1: {"menu": "main", "last_access": 0}}), \
             patch('apps.telegram_bot.services.user_state_service.USER_LANGUAGES', {1: {"language": "en", "last_access": 0}}), \
             patch('apps.telegram_bot.services.user_state_service.cleanup_expired_user_data', return_value=(1,1,1)) as mock_cleanup, \
             patch('logging.getLogger') as mock_logger:
            logger = MagicMock()
            mock_logger.return_value = logger
            await cleanup_expired_data()
            mock_cleanup.assert_called()
            assert logger.info.called

    def test_clear_user_state_removes_both_state_and_menu(self):
        with patch('apps.telegram_bot.services.user_state_service.USER_STATES', {5: {"last_access": 1}}), \
             patch('apps.telegram_bot.services.user_state_service.USER_CURRENT_MENUS', {5: {"menu": "main", "last_access": 1}}):
            clear_user_state(5)
            assert __import__('apps.telegram_bot.services.user_state_service', fromlist=['']).USER_STATES.get(5) is None
            assert __import__('apps.telegram_bot.services.user_state_service', fromlist=['']).USER_CURRENT_MENUS.get(5) is None
