import pytest
from pydantic import ValidationError
from datetime import datetime
from apps.api.models import (
    LanguageTranslation,
    RSSItem,
    CategoryItem,
    SourceItem,
    LanguageItem,
    PaginatedResponse,
    HTTPError,
    UserBase,
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    Token,
    TokenData,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerificationRequest,
    SuccessResponse,
    UserRSSFeedBase,
    UserRSSFeedCreate,
    UserRSSFeedUpdate,
    UserRSSFeedResponse,
    UserCategoriesUpdate,
    UserCategoriesResponse,
    TelegramLinkResponse,
    TelegramLinkStatusResponse,
)


class TestLanguageTranslation:
    def test_valid_language_translation(self):
        translation = LanguageTranslation(title="Test Title", content="Test Content")
        assert translation.title == "Test Title"
        assert translation.content == "Test Content"

    def test_optional_fields_none(self):
        translation = LanguageTranslation()
        assert translation.title is None
        assert translation.content is None


class TestRSSItem:
    def test_valid_rss_item(self):
        item = RSSItem(
            news_id="123",
            original_title="Test Title",
            original_content="Test Content",
            original_language="en",
        )
        assert item.news_id == "123"
        assert item.original_title == "Test Title"
        assert item.original_content == "Test Content"
        assert item.original_language == "en"
        assert item.image_url is None

    def test_rss_item_with_optional_fields(self):
        translations = {"es": LanguageTranslation(title="Título de Prueba")}
        item = RSSItem(
            news_id="123",
            original_title="Test Title",
            original_content="Test Content",
            original_language="en",
            image_url="http://example.com/image.jpg",
            category="Tech",
            source="BBC",
            source_url="http://bbc.com",
            published_at="2023-01-01T00:00:00Z",
            translations=translations,
        )
        assert item.image_url == "http://example.com/image.jpg"
        assert item.category == "Tech"
        assert item.translations["es"].title == "Título de Prueba"


class TestCategoryItem:
    def test_valid_category_item(self):
        category = CategoryItem(id=1, name="Technology")
        assert category.id == 1
        assert category.name == "Technology"


class TestSourceItem:
    def test_valid_source_item(self):
        source = SourceItem(id=1, name="BBC", description="British Broadcasting Corporation")
        assert source.id == 1
        assert source.name == "BBC"
        assert source.description == "British Broadcasting Corporation"

    def test_source_item_without_description(self):
        source = SourceItem(id=1, name="BBC")
        assert source.description is None


class TestLanguageItem:
    def test_valid_language_item(self):
        language = LanguageItem(language="en")
        assert language.language == "en"


class TestPaginatedResponse:
    def test_valid_paginated_response(self):
        items = [CategoryItem(id=1, name="Tech"), CategoryItem(id=2, name="Sports")]
        response = PaginatedResponse[CategoryItem](count=2, results=items)
        assert response.count == 2
        assert len(response.results) == 2
        assert response.results[0].name == "Tech"


class TestHTTPError:
    def test_valid_http_error(self):
        error = HTTPError(detail="Not Found")
        assert error.detail == "Not Found"


class TestUserBase:
    def test_valid_user_base(self):
        user = UserBase(email="test@example.com", language="en")
        assert user.email == "test@example.com"
        assert user.language == "en"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserBase(email="invalid-email", language="en")


class TestUserCreate:
    def test_valid_user_create(self):
        user = UserCreate(email="test@example.com", password="password123", language="en")
        assert user.email == "test@example.com"
        assert user.password == "password123"

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", password="short")


class TestUserLogin:
    def test_valid_user_login(self):
        login = UserLogin(username="test@example.com", password="password123")
        assert login.username == "test@example.com"
        assert login.password == "password123"


class TestUserUpdate:
    def test_valid_user_update(self):
        update = UserUpdate(email="new@example.com", language="es")
        assert update.email == "new@example.com"
        assert update.language == "es"

    def test_partial_update(self):
        update = UserUpdate(email="new@example.com")
        assert update.email == "new@example.com"
        assert update.language is None


class TestUserResponse:
    def test_valid_user_response(self):
        created_at = datetime.now()
        user = UserResponse(
            id=1,
            email="test@example.com",
            language="en",
            is_active=True,
            is_verified=True,
            is_deleted=False,
            created_at=created_at,
        )
        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_verified is True
        assert user.is_deleted is False
        assert user.created_at == created_at


class TestToken:
    def test_valid_token(self):
        token = Token(access_token="abc123", token_type="bearer", expires_in=3600)
        assert token.access_token == "abc123"
        assert token.token_type == "bearer"
        assert token.expires_in == 3600


class TestTokenData:
    def test_valid_token_data(self):
        data = TokenData(user_id=123)
        assert data.user_id == 123

    def test_none_user_id(self):
        data = TokenData()
        assert data.user_id is None


class TestPasswordResetRequest:
    def test_valid_password_reset_request(self):
        request = PasswordResetRequest(email="test@example.com")
        assert request.email == "test@example.com"


class TestPasswordResetConfirm:
    def test_valid_password_reset_confirm(self):
        confirm = PasswordResetConfirm(token="abc123", new_password="newpassword123")
        assert confirm.token == "abc123"
        assert confirm.new_password == "newpassword123"

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            PasswordResetConfirm(token="abc123", new_password="short")


class TestEmailVerificationRequest:
    def test_valid_email_verification_request(self):
        request = EmailVerificationRequest(email="test@example.com", code="123456")
        assert request.email == "test@example.com"
        assert request.code == "123456"

    def test_code_too_short(self):
        with pytest.raises(ValidationError):
            EmailVerificationRequest(email="test@example.com", code="12345")

    def test_code_too_long(self):
        with pytest.raises(ValidationError):
            EmailVerificationRequest(email="test@example.com", code="1234567")


class TestSuccessResponse:
    def test_valid_success_response(self):
        response = SuccessResponse(message="Operation successful")
        assert response.message == "Operation successful"


class TestUserRSSFeedBase:
    def test_valid_user_rss_feed_base(self):
        feed = UserRSSFeedBase(url="http://example.com/rss", name="Test Feed", category_id=1, language="en")
        assert feed.url == "http://example.com/rss"
        assert feed.name == "Test Feed"
        assert feed.category_id == 1
        assert feed.language == "en"


class TestUserRSSFeedCreate:
    def test_valid_user_rss_feed_create(self):
        feed = UserRSSFeedCreate(url="http://example.com/rss", name="Test Feed")
        assert feed.url == "http://example.com/rss"
        assert feed.name == "Test Feed"


class TestUserRSSFeedUpdate:
    def test_valid_user_rss_feed_update(self):
        update = UserRSSFeedUpdate(name="New Name", category_id=2, is_active=False)
        assert update.name == "New Name"
        assert update.category_id == 2
        assert update.is_active is False


class TestUserRSSFeedResponse:
    def test_valid_user_rss_feed_response(self):
        created_at = datetime.now()
        feed = UserRSSFeedResponse(
            id="1",
            user_id=123,
            url="http://example.com/rss",
            name="Test Feed",
            category_id=1,
            language="en",
            is_active=True,
            created_at=created_at,
        )
        assert feed.id == "1"
        assert feed.user_id == 123
        assert feed.url == "http://example.com/rss"
        assert feed.is_active is True


class TestUserCategoriesUpdate:
    def test_valid_user_categories_update(self):
        update = UserCategoriesUpdate(category_ids={1, 2, 3})
        assert update.category_ids == {1, 2, 3}


class TestUserCategoriesResponse:
    def test_valid_user_categories_response(self):
        response = UserCategoriesResponse(category_ids=[1, 2, 3])
        assert response.category_ids == [1, 2, 3]


class TestTelegramLinkResponse:
    def test_valid_telegram_link_response(self):
        response = TelegramLinkResponse(link_code="abc123", instructions="Scan the code")
        assert response.link_code == "abc123"
        assert response.instructions == "Scan the code"


class TestTelegramLinkStatusResponse:
    def test_valid_telegram_link_status_response(self):
        response = TelegramLinkStatusResponse(is_linked=True, telegram_id=12345, linked_at="2023-01-01T00:00:00Z")
        assert response.is_linked is True
        assert response.telegram_id == 12345
        assert response.linked_at == "2023-01-01T00:00:00Z"

    def test_not_linked(self):
        response = TelegramLinkStatusResponse(is_linked=False)
        assert response.is_linked is False
        assert response.telegram_id is None
        assert response.linked_at is None