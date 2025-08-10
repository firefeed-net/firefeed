import sqlite3

def init_db():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS published_news (
            id TEXT PRIMARY KEY,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def is_news_new(news_id: str) -> bool:
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM published_news WHERE id=?", (news_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return not exists

def mark_as_published(news_id: str):
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO published_news (id) VALUES (?)", (news_id,))
    conn.commit()
    conn.close()
