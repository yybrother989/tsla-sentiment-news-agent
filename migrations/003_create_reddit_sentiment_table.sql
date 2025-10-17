-- Reddit sentiment table for high-engagement r/wallstreetbets posts
-- Migration: 003_create_reddit_sentiment_table.sql

DROP TABLE IF EXISTS reddit_sentiment CASCADE;

CREATE TABLE reddit_sentiment (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    ticker VARCHAR(10) NOT NULL,
    
    post_id TEXT NOT NULL UNIQUE,
    post_url TEXT NOT NULL,
    subreddit VARCHAR(100) NOT NULL DEFAULT 'wallstreetbets',
    
    author_username VARCHAR(100),
    title TEXT NOT NULL,
    text TEXT,
    flair TEXT,
    
    upvote_count INTEGER CHECK (upvote_count >= 0),
    upvote_ratio DECIMAL(4,3) CHECK (upvote_ratio >= 0.000 AND upvote_ratio <= 1.000),
    comment_count INTEGER CHECK (comment_count >= 0),
    award_count INTEGER CHECK (award_count >= 0),
    
    is_pinned BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    
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

-- Indexes for efficient queries
CREATE UNIQUE INDEX idx_reddit_sentiment_post_id ON reddit_sentiment(post_id);
CREATE UNIQUE INDEX idx_reddit_sentiment_post_url ON reddit_sentiment(post_url);
CREATE INDEX idx_reddit_sentiment_user_id ON reddit_sentiment(user_id);
CREATE INDEX idx_reddit_sentiment_ticker ON reddit_sentiment(ticker);
CREATE INDEX idx_reddit_sentiment_subreddit ON reddit_sentiment(subreddit);
CREATE INDEX idx_reddit_sentiment_posted_at ON reddit_sentiment(posted_at DESC);
CREATE INDEX idx_reddit_sentiment_collected_at ON reddit_sentiment(collected_at DESC);
CREATE INDEX idx_reddit_sentiment_author_username ON reddit_sentiment(author_username);
CREATE INDEX idx_reddit_sentiment_sentiment_label ON reddit_sentiment(sentiment_label);
CREATE INDEX idx_reddit_sentiment_upvote_count ON reddit_sentiment(upvote_count DESC);

-- Row level security
ALTER TABLE reddit_sentiment ENABLE ROW LEVEL SECURITY;

CREATE POLICY reddit_sentiment_user_policy ON reddit_sentiment
    FOR ALL USING (user_id = current_setting('app.current_user_id', TRUE)::INTEGER);

-- Comments
COMMENT ON TABLE reddit_sentiment IS 'High-engagement r/wallstreetbets posts with sentiment analysis results';
COMMENT ON COLUMN reddit_sentiment.user_id IS 'User identifier (default: 1)';
COMMENT ON COLUMN reddit_sentiment.ticker IS 'Stock ticker symbol (e.g. TSLA)';
COMMENT ON COLUMN reddit_sentiment.post_id IS 'Unique Reddit post identifier';
COMMENT ON COLUMN reddit_sentiment.post_url IS 'Canonical Reddit post URL';
COMMENT ON COLUMN reddit_sentiment.subreddit IS 'Subreddit name (e.g. wallstreetbets)';
COMMENT ON COLUMN reddit_sentiment.author_username IS 'Reddit username of post author';
COMMENT ON COLUMN reddit_sentiment.title IS 'Post title';
COMMENT ON COLUMN reddit_sentiment.text IS 'Post content/body text';
COMMENT ON COLUMN reddit_sentiment.flair IS 'Post flair category';
COMMENT ON COLUMN reddit_sentiment.upvote_count IS 'Total upvotes at collection time';
COMMENT ON COLUMN reddit_sentiment.upvote_ratio IS 'Upvote ratio (0-1)';
COMMENT ON COLUMN reddit_sentiment.comment_count IS 'Number of comments';
COMMENT ON COLUMN reddit_sentiment.award_count IS 'Number of Reddit awards received';
COMMENT ON COLUMN reddit_sentiment.posted_at IS 'Timestamp when post was created on Reddit';
COMMENT ON COLUMN reddit_sentiment.collected_at IS 'Timestamp when data was collected';
COMMENT ON COLUMN reddit_sentiment.sentiment_score IS 'Sentiment score from -1 (bearish) to +1 (bullish)';
COMMENT ON COLUMN reddit_sentiment.sentiment_label IS 'Categorical sentiment: bullish, bearish, or neutral';
COMMENT ON COLUMN reddit_sentiment.sentiment_confidence IS 'Confidence score for sentiment classification (0-1)';
COMMENT ON COLUMN reddit_sentiment.sentiment_rationale IS 'LLM explanation for sentiment classification';
COMMENT ON COLUMN reddit_sentiment.key_themes IS 'Comma-separated key themes from the post';
COMMENT ON COLUMN reddit_sentiment.sentiment_index IS 'Weighted sentiment metric combining score and engagement';

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_reddit_sentiment_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER reddit_sentiment_updated_at
    BEFORE UPDATE ON reddit_sentiment
    FOR EACH ROW
    EXECUTE FUNCTION update_reddit_sentiment_updated_at();

