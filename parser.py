import feedparser
import asyncio
import re
import pytz
from datetime import datetime
from config import CATEGORIES

MAX_ENTRIES_PER_FEED = 10
MAX_TOTAL_NEWS = 100

async def fetch_news():
    all_news = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}
    
    for category, sources in CATEGORIES.items():
        for source in sources:
            feed = feedparser.parse(source['url'], request_headers=headers)
            
            # Берем только первые N записей (самые свежие)
            for entry in feed.entries[:MAX_ENTRIES_PER_FEED]:
                # Генерируем уникальный ID на основе ссылки и даты
                news_id = f"{entry.link}_{entry.published_parsed}"
                
                news_item = {
                    'id': news_id,
                    'title': entry.title,
                    'description': entry.description,
                    'link': entry.link,
                    'published': datetime(*entry.published_parsed[:6], tzinfo=pytz.utc),
                    'category': category,
                    'lang': source['lang'],
                    'source': source['source']
                }
                all_news.append(news_item)
    
    return sorted(all_news, key=lambda x: x['published'], reverse=True)[:MAX_TOTAL_NEWS]