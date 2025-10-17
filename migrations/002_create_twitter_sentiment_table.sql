-- Twitter sentiment table for high-engagement tweets
-- Migration: 002_create_twitter_sentiment_table.sql

DROP TABLE IF EXISTS twitter_sentiment CASCADE;

CREATE TABLE twitter_sentiment (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    ticker VARCHAR(10) NOT NULL,

    tweet_id TEXT NOT NULL UNIQUE,
    tweet_url TEXT NOT NULL,
    conversation_id TEXT,

    author_id TEXT,
    author_handle VARCHAR(50),
    author_name TEXT,
    author_username VARCHAR(50),

    text TEXT NOT NULL,
    language VARCHAR(10),
    hashtags TEXT,
    mentions TEXT,

    like_count INTEGER CHECK (like_count >= 0),
    reply_count INTEGER CHECK (reply_count >= 0),
    retweet_count INTEGER CHECK (retweet_count >= 0),
    quote_count INTEGER CHECK (quote_count >= 0),
    bookmark_count INTEGER CHECK (bookmark_count >= 0),
    view_count BIGINT CHECK (view_count >= 0),

    posted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    sentiment_score DECIMAL(4,3) CHECK (sentiment_score >= -1.000 AND sentiment_score <= 1.000),
    sentiment_label VARCHAR(20) CHECK (sentiment_label IN ('bullish', 'bearish', 'neutral')),
    sentiment_confidence DECIMAL(4,3) CHECK (sentiment_confidence >= 0.000 AND sentiment_confidence <= 1.000),
    sentiment_rationale TEXT,
    key_themes TEXT,

    sentiment_index DECIMAL(5,3),
    notes TEXT,

    raw_payload JSONB
);

COMMENT ON TABLE twitter_sentiment IS 'High-engagement Tesla tweets with sentiment analysis results';
COMMENT ON COLUMN twitter_sentiment.user_id IS 'User identifier (default: 1)';
COMMENT ON COLUMN twitter_sentiment.ticker IS 'Stock ticker symbol (default TSLA)';
COMMENT ON COLUMN twitter_sentiment.tweet_id IS 'Unique tweet identifier';
COMMENT ON COLUMN twitter_sentiment.tweet_url IS 'Canonical tweet URL';
COMMENT ON COLUMN twitter_sentiment.author_handle IS 'Tweet author handle (without @)';
COMMENT ON COLUMN twitter_sentiment.author_name IS 'Tweet author display name';
COMMENT ON COLUMN twitter_sentiment.author_username IS 'Tweet author username (alternative to handle)';
COMMENT ON COLUMN twitter_sentiment.text IS 'Tweet content text';
COMMENT ON COLUMN twitter_sentiment.language IS 'Tweet language code (ISO-639-1)';
COMMENT ON COLUMN twitter_sentiment.hashtags IS 'Comma-separated hashtags extracted from the tweet';
COMMENT ON COLUMN twitter_sentiment.mentions IS 'Comma-separated user handles mentioned';
COMMENT ON COLUMN twitter_sentiment.like_count IS 'Total likes at collection time';
COMMENT ON COLUMN twitter_sentiment.reply_count IS 'Total replies at collection time';
COMMENT ON COLUMN twitter_sentiment.retweet_count IS 'Total retweets at collection time';
COMMENT ON COLUMN twitter_sentiment.quote_count IS 'Total quote tweets at collection time';
COMMENT ON COLUMN twitter_sentiment.bookmark_count IS 'Total bookmarks at collection time';
COMMENT ON COLUMN twitter_sentiment.view_count IS 'Total views/impressions when available';
COMMENT ON COLUMN twitter_sentiment.posted_at IS 'Timestamp when the tweet was posted';
COMMENT ON COLUMN twitter_sentiment.collected_at IS 'Timestamp when the tweet was collected';
COMMENT ON COLUMN twitter_sentiment.sentiment_score IS 'LLM-derived sentiment score (-1 to +1)';
COMMENT ON COLUMN twitter_sentiment.sentiment_label IS 'Discrete sentiment category';
COMMENT ON COLUMN twitter_sentiment.sentiment_confidence IS 'Confidence score for sentiment label';
COMMENT ON COLUMN twitter_sentiment.sentiment_rationale IS 'Explanation for the sentiment assessment';
COMMENT ON COLUMN twitter_sentiment.key_themes IS 'Comma-separated key themes detected in the tweet';
COMMENT ON COLUMN twitter_sentiment.sentiment_index IS 'Run-level sentiment index stored with each record when applicable';
COMMENT ON COLUMN twitter_sentiment.notes IS 'Optional analyst notes';
COMMENT ON COLUMN twitter_sentiment.raw_payload IS 'Raw JSON payload returned by Browser Use extraction';

CREATE UNIQUE INDEX idx_twitter_sentiment_tweet_url ON twitter_sentiment(tweet_url);
CREATE INDEX idx_twitter_sentiment_user_id ON twitter_sentiment(user_id);
CREATE INDEX idx_twitter_sentiment_ticker ON twitter_sentiment(ticker);
CREATE INDEX idx_twitter_sentiment_posted_at ON twitter_sentiment(posted_at DESC);
CREATE INDEX idx_twitter_sentiment_collected_at ON twitter_sentiment(collected_at DESC);
CREATE INDEX idx_twitter_sentiment_author_handle ON twitter_sentiment(author_handle);
CREATE INDEX idx_twitter_sentiment_author_username ON twitter_sentiment(author_username);
CREATE INDEX idx_twitter_sentiment_sentiment_label ON twitter_sentiment(sentiment_label);

ALTER TABLE twitter_sentiment ENABLE ROW LEVEL SECURITY;

CREATE POLICY twitter_sentiment_user_policy ON twitter_sentiment
    FOR ALL
    USING (user_id = current_setting('app.user_id', TRUE)::INTEGER);

GRANT ALL ON twitter_sentiment TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE twitter_sentiment_id_seq TO authenticated;

CREATE TRIGGER update_twitter_sentiment_updated_at
    BEFORE UPDATE ON twitter_sentiment
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

