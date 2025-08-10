import feedparser
import asyncio
from datetime import datetime
import pytz
from config import RSS_URLS

async def fetch_news():
    all_news = []
    for url in RSS_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            # Генерируем уникальный ID на основе ссылки и даты
            news_id = f"{entry.link}_{entry.published_parsed}"
            
            news_item = {
                'id': news_id,
                'title': entry.title,
                'description': entry.description,
                'link': entry.link,
                'published': datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
            }
            all_news.append(news_item)
    
    # Сортируем по дате публикации (новые сверху)
    return sorted(all_news, key=lambda x: x['published'], reverse=True)