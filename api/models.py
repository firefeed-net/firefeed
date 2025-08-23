from pydantic import BaseModel
from typing import Optional, List

# Модель для представления одного перевода
class Translation(BaseModel):
    language: str
    title: str
    content: str

# Модель для представления новости в API
class NewsItem(BaseModel):
    news_id: str
    original_title: str
    original_content: str
    original_language: str
    category: Optional[str] = None
    title_ru: Optional[str] = None
    content_ru: Optional[str] = None
    title_en: Optional[str] = None
    content_en: Optional[str] = None
    title_de: Optional[str] = None
    content_de: Optional[str] = None
    title_fr: Optional[str] = None
    content_fr: Optional[str] = None
    source_url: Optional[str] = None
    published_at: Optional[str] = None # ISO формат даты-времени

    class Config:
        from_attributes = True # Для совместимости с ORM (если будете использовать)

# Модели для списков
class CategoryItem(BaseModel):
    category: str

class LanguageItem(BaseModel):
    language: str

# Модель для ответа с ошибкой (опционально, но полезно)
class HTTPError(BaseModel):
    detail: str
