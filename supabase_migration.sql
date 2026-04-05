-- Run this once in your Supabase SQL Editor to enable verdict caching
-- Project: https://hrnlwbpaaazfarofjbyz.supabase.co

CREATE TABLE IF NOT EXISTS post_verdicts (
  post_id     TEXT PRIMARY KEY,
  verdict     TEXT NOT NULL,
  confidence  INTEGER,
  synthesis   TEXT,
  agents      JSONB,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Optional: index for fast lookups
CREATE INDEX IF NOT EXISTS idx_post_verdicts_verdict ON post_verdicts(verdict);

-- Optional: enable Row Level Security (open for now, lock down in prod)
ALTER TABLE post_verdicts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "allow all" ON post_verdicts FOR ALL USING (true) WITH CHECK (true);
