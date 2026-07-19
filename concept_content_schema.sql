CREATE TABLE concept_content (
  concept_id text PRIMARY KEY,
  topic_id text NOT NULL REFERENCES topics(topic_id),
  depth text NOT NULL CHECK (depth IN ('quick', 'standard', 'deep_dive')),
  explanation_text text NOT NULL,
  india_example text NOT NULL,
  exam_tags text[] DEFAULT '{}',
  generated_by text,
  verified boolean DEFAULT false,
  quality_score numeric,
  created_at timestamptz DEFAULT now(),
  UNIQUE(topic_id, depth)
);

CREATE INDEX idx_concept_content_topic ON concept_content(topic_id);

