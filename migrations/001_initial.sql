CREATE TABLE IF NOT EXISTS deals (
    id TEXT PRIMARY KEY,
    content_hash TEXT UNIQUE,
    raw_text TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    last_error TEXT,

    -- Extracted fields (nullable until extraction completes)
    company_name TEXT,
    founders TEXT,
    sector TEXT,
    geography TEXT,
    stage TEXT,
    round_size TEXT,
    metrics TEXT,
    investment_brief TEXT,
    tags TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
CREATE INDEX IF NOT EXISTS idx_deals_created ON deals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_deals_content_hash ON deals(content_hash);
