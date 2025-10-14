-- Create articles table
CREATE TABLE IF NOT EXISTS public.articles (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    user_id INTEGER NOT NULL DEFAULT 1,
    ticker VARCHAR(10) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    source VARCHAR(255) NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    canonical_hash VARCHAR(64) NOT NULL
);

-- Create index on canonical_hash for deduplication
CREATE INDEX IF NOT EXISTS idx_articles_canonical_hash ON public.articles(canonical_hash);
CREATE INDEX IF NOT EXISTS idx_articles_ticker ON public.articles(ticker);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON public.articles(published_at DESC);

-- Create events table
CREATE TABLE IF NOT EXISTS public.events (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    user_id INTEGER NOT NULL DEFAULT 1,
    article_url TEXT NOT NULL,
    about_ticker BOOLEAN NOT NULL DEFAULT TRUE,
    sentiment FLOAT NOT NULL CHECK (sentiment >= -1.0 AND sentiment <= 1.0),
    stance VARCHAR(50) NOT NULL,
    event_type VARCHAR(100),
    summary TEXT NOT NULL,
    FOREIGN KEY (article_url) REFERENCES public.articles(url) ON DELETE CASCADE
);

-- Create index on article_url for joins
CREATE INDEX IF NOT EXISTS idx_events_article_url ON public.events(article_url);
CREATE INDEX IF NOT EXISTS idx_events_sentiment ON public.events(sentiment);

-- Create scores table
CREATE TABLE IF NOT EXISTS public.scores (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    user_id INTEGER NOT NULL DEFAULT 1,
    article_url TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 1 AND score <= 10),
    rationale TEXT NOT NULL,
    FOREIGN KEY (article_url) REFERENCES public.articles(url) ON DELETE CASCADE
);

-- Create index on article_url for joins
CREATE INDEX IF NOT EXISTS idx_scores_article_url ON public.scores(article_url);
CREATE INDEX IF NOT EXISTS idx_scores_score ON public.scores(score);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_articles_updated_at BEFORE UPDATE ON public.articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON public.events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scores_updated_at BEFORE UPDATE ON public.scores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE public.articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scores ENABLE ROW LEVEL SECURITY;

-- Create policies for user_id filtering
CREATE POLICY "Users can view their own articles" ON public.articles
    FOR SELECT USING (user_id = current_setting('request.jwt.claim.sub', true)::integer OR user_id = 1);

CREATE POLICY "Users can insert their own articles" ON public.articles
    FOR INSERT WITH CHECK (user_id = current_setting('request.jwt.claim.sub', true)::integer OR user_id = 1);

CREATE POLICY "Users can update their own articles" ON public.articles
    FOR UPDATE USING (user_id = current_setting('request.jwt.claim.sub', true)::integer OR user_id = 1);

CREATE POLICY "Users can view their own events" ON public.events
    FOR SELECT USING (user_id = current_setting('request.jwt.claim.sub', true)::integer OR user_id = 1);

CREATE POLICY "Users can insert their own events" ON public.events
    FOR INSERT WITH CHECK (user_id = current_setting('request.jwt.claim.sub', true)::integer OR user_id = 1);

CREATE POLICY "Users can update their own events" ON public.events
    FOR UPDATE USING (user_id = current_setting('request.jwt.claim.sub', true)::integer OR user_id = 1);

CREATE POLICY "Users can view their own scores" ON public.scores
    FOR SELECT USING (user_id = current_setting('request.jwt.claim.sub', true)::integer OR user_id = 1);

CREATE POLICY "Users can insert their own scores" ON public.scores
    FOR INSERT WITH CHECK (user_id = current_setting('request.jwt.claim.sub', true)::integer OR user_id = 1);

CREATE POLICY "Users can update their own scores" ON public.scores
    FOR UPDATE USING (user_id = current_setting('request.jwt.claim.sub', true)::integer OR user_id = 1);

