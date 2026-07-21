-- Recreates concept_content with a `level` dimension added, matching the
-- existing 1-10 MCQ difficulty ladder (config.py's LEVELS). Safe to drop
-- and recreate since existing rows are early test data, not production
-- content anything depends on yet.
DROP TABLE IF EXISTS concept_content;

CREATE TABLE concept_content (
  concept_id text PRIMARY KEY,
  topic_id text NOT NULL REFERENCES topics(topic_id),
  level integer NOT NULL CHECK (level BETWEEN 1 AND 10),
  depth text NOT NULL CHECK (depth IN ('quick', 'standard', 'deep_dive')),
  explanation_text text NOT NULL,
  india_example text NOT NULL,
  exam_tags text[] DEFAULT '{}',
  generated_by text,
  verified boolean DEFAULT false,
  quality_score numeric,
  created_at timestamptz DEFAULT now(),
  UNIQUE(topic_id, level, depth)
);

CREATE INDEX idx_concept_content_topic_level ON concept_content(topic_id, level);

