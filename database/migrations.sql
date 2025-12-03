CREATE TABLE IF NOT EXISTS rss_items_telegram_bot_published (
    id SERIAL PRIMARY KEY,
    news_id VARCHAR(255),
    translation_id INTEGER,
    recipient_type VARCHAR(10) NOT NULL CHECK (recipient_type IN ('channel', 'user')),
    recipient_id BIGINT NOT NULL,
    message_id BIGINT,
    language VARCHAR(5),
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (news_id, translation_id, recipient_type, recipient_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_rss_bot_published_news_id ON rss_items_telegram_bot_published (news_id);
CREATE INDEX IF NOT EXISTS idx_rss_bot_published_translation_id ON rss_items_telegram_bot_published (translation_id);
CREATE INDEX IF NOT EXISTS idx_rss_bot_published_recipient ON rss_items_telegram_bot_published (recipient_type, recipient_id);
CREATE INDEX IF NOT EXISTS idx_rss_bot_published_sent_at ON rss_items_telegram_bot_published (sent_at);

-- Step 2: Migrate data from rss_items_telegram_published (translations to channels)
INSERT INTO rss_items_telegram_bot_published (
    news_id,
    translation_id,
    recipient_type,
    recipient_id,
    message_id,
    sent_at,
    created_at,
    updated_at
)
SELECT
    nt.news_id,
    rtp.translation_id,
    'channel'::VARCHAR(10),
    rtp.channel_id,
    rtp.message_id,
    rtp.published_at,
    rtp.created_at,
    rtp.updated_at
FROM rss_items_telegram_published rtp
JOIN news_translations nt ON rtp.translation_id = nt.id
ON CONFLICT (news_id, translation_id, recipient_type, recipient_id) DO NOTHING;

-- Step 3: Migrate data from rss_items_telegram_published_originals (originals to channels)
INSERT INTO rss_items_telegram_bot_published (
    news_id,
    translation_id,
    recipient_type,
    recipient_id,
    message_id,
    sent_at,
    created_at,
    updated_at
)
SELECT
    rtpo.news_id,
    NULL::INTEGER,
    'channel'::VARCHAR(10),
    rtpo.channel_id,
    rtpo.message_id,
    rtpo.created_at::timestamp with time zone,
    rtpo.created_at::timestamp with time zone,
    rtpo.created_at::timestamp with time zone
FROM rss_items_telegram_published_originals rtpo
ON CONFLICT (news_id, translation_id, recipient_type, recipient_id) DO NOTHING;
