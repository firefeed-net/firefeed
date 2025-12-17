import pytest
from datetime import datetime
from apps.api.models import (
    UserApiKeyBase,
    UserApiKeyCreate,
    UserApiKeyUpdate,
    UserApiKeyResponse,
)


class TestUserApiKeyBase:
    def test_valid_user_api_key_base(self):
        key = UserApiKeyBase(limits={"requests_per_day": 1000, "requests_per_hour": 100})
        assert key.limits["requests_per_day"] == 1000
        assert key.limits["requests_per_hour"] == 100

    def test_default_limits(self):
        key = UserApiKeyBase()
        assert key.limits["requests_per_day"] == 1000
        assert key.limits["requests_per_hour"] == 100


class TestUserApiKeyCreate:
    def test_valid_user_api_key_create(self):
        key = UserApiKeyCreate(limits={"requests_per_day": 500})
        assert key.limits["requests_per_day"] == 500


class TestUserApiKeyUpdate:
    def test_valid_user_api_key_update(self):
        update = UserApiKeyUpdate(is_active=False, limits={"requests_per_day": 2000})
        assert update.is_active is False
        assert update.limits["requests_per_day"] == 2000

    def test_partial_update(self):
        update = UserApiKeyUpdate(is_active=True)
        assert update.is_active is True
        assert update.limits is None


class TestUserApiKeyResponse:
    def test_valid_user_api_key_response(self):
        created_at = datetime.now()
        key = UserApiKeyResponse(
            id=1,
            user_id=123,
            is_active=True,
            created_at=created_at,
            limits={"requests_per_day": 1000}
        )
        assert key.id == 1
        assert key.user_id == 123
        assert key.is_active is True
        assert key.created_at == created_at
        assert key.expires_at is None