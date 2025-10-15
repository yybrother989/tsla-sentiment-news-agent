-- Complete sentiment analysis table with all fields
-- Migration: 001_create_sentiment_analysis_table.sql

-- Drop existing table if it exists
DROP TABLE IF EXISTS sentiment_analysis CASCADE;

-- Create comprehensive sentiment_analysis table
CREATE TABLE sentiment_analysis (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,
    
    -- User and metadata
    user_id INTEGER NOT NULL DEFAULT 1,
    ticker VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Article identification
    url TEXT NOT NULL UNIQUE,
    canonical_hash VARCHAR(255) NOT NULL,
    
    -- Article content
    title TEXT NOT NULL,
    text TEXT,
    source VARCHAR(255),
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Classification fields
    category VARCHAR(50),
    classification_confidence DECIMAL(3,2) CHECK (classification_confidence >= 0.0 AND classification_confidence <= 1.0),
    classification_rationale TEXT,
    
    -- Sentiment analysis fields
    sentiment_score DECIMAL(3,2) CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0),
    impact_score INTEGER CHECK (impact_score >= 1 AND impact_score <= 5),
    sentiment_confidence DECIMAL(3,2) CHECK (sentiment_confidence >= 0.0 AND sentiment_confidence <= 1.0),
    sentiment_rationale TEXT,
    key_factors TEXT,
    summary TEXT,
    stance VARCHAR(20) CHECK (stance IN ('bullish', 'bearish', 'neutral')),
    
    -- Legacy fields (for backward compatibility)
    sentiment DECIMAL(3,2),
    impact INTEGER,
    event_type VARCHAR(100)
);

-- Add comments for documentation
COMMENT ON TABLE sentiment_analysis IS 'Tesla news articles with classification and sentiment analysis';

COMMENT ON COLUMN sentiment_analysis.user_id IS 'User ID (default: 1)';
COMMENT ON COLUMN sentiment_analysis.ticker IS 'Stock ticker symbol (TSLA)';
COMMENT ON COLUMN sentiment_analysis.url IS 'Article URL (unique identifier)';
COMMENT ON COLUMN sentiment_analysis.canonical_hash IS 'Hash for deduplication';
COMMENT ON COLUMN sentiment_analysis.title IS 'Article headline';
COMMENT ON COLUMN sentiment_analysis.text IS 'Article content/summary';
COMMENT ON COLUMN sentiment_analysis.source IS 'News source (e.g., duckduckgo, yahoo, reuters)';
COMMENT ON COLUMN sentiment_analysis.published_at IS 'Article publication timestamp';

COMMENT ON COLUMN sentiment_analysis.category IS 'News category (Financial, Product, Market, etc.)';
COMMENT ON COLUMN sentiment_analysis.classification_confidence IS 'Classification confidence (0.0 to 1.0)';
COMMENT ON COLUMN sentiment_analysis.classification_rationale IS 'Explanation for category classification';

COMMENT ON COLUMN sentiment_analysis.sentiment_score IS 'Sentiment score from -1.0 (negative) to +1.0 (positive)';
COMMENT ON COLUMN sentiment_analysis.impact_score IS 'Market impact score from 1 (low) to 5 (high)';
COMMENT ON COLUMN sentiment_analysis.sentiment_confidence IS 'Confidence in sentiment analysis from 0.0 to 1.0';
COMMENT ON COLUMN sentiment_analysis.sentiment_rationale IS 'Brief explanation for sentiment and impact scores';
COMMENT ON COLUMN sentiment_analysis.key_factors IS 'Comma-separated key factors that influenced the scoring';
COMMENT ON COLUMN sentiment_analysis.summary IS 'One-sentence summary of the article';
COMMENT ON COLUMN sentiment_analysis.stance IS 'Overall market stance: bullish, bearish, or neutral';

-- Create indexes for better query performance
CREATE INDEX idx_sentiment_analysis_user_id ON sentiment_analysis(user_id);
CREATE INDEX idx_sentiment_analysis_ticker ON sentiment_analysis(ticker);
CREATE INDEX idx_sentiment_analysis_source ON sentiment_analysis(source);
CREATE INDEX idx_sentiment_analysis_published_at ON sentiment_analysis(published_at DESC);
CREATE INDEX idx_sentiment_analysis_created_at ON sentiment_analysis(created_at DESC);

-- Classification indexes
CREATE INDEX idx_sentiment_analysis_category ON sentiment_analysis(category);
CREATE INDEX idx_sentiment_analysis_classification_confidence ON sentiment_analysis(classification_confidence);

-- Sentiment analysis indexes
CREATE INDEX idx_sentiment_analysis_sentiment_score ON sentiment_analysis(sentiment_score);
CREATE INDEX idx_sentiment_analysis_impact_score ON sentiment_analysis(impact_score);
CREATE INDEX idx_sentiment_analysis_sentiment_confidence ON sentiment_analysis(sentiment_confidence);
CREATE INDEX idx_sentiment_analysis_stance ON sentiment_analysis(stance);

-- Composite indexes for common queries
CREATE INDEX idx_sentiment_analysis_category_sentiment ON sentiment_analysis(category, sentiment_score);
CREATE INDEX idx_sentiment_analysis_stance_impact ON sentiment_analysis(stance, impact_score);
CREATE INDEX idx_sentiment_analysis_ticker_published ON sentiment_analysis(ticker, published_at DESC);
CREATE INDEX idx_sentiment_analysis_user_ticker_published ON sentiment_analysis(user_id, ticker, published_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE sentiment_analysis ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for user access
CREATE POLICY sentiment_analysis_user_policy ON sentiment_analysis
    FOR ALL
    USING (user_id = current_setting('app.user_id', TRUE)::INTEGER);

-- Grant access to authenticated users
GRANT ALL ON sentiment_analysis TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE sentiment_analysis_id_seq TO authenticated;

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_sentiment_analysis_updated_at
    BEFORE UPDATE ON sentiment_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

