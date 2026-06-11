ALTER TABLE long_term_memories
    ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS is_editable BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS read_policy TEXT NOT NULL DEFAULT 'relevant',
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active',
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS use_count INTEGER NOT NULL DEFAULT 0;

ALTER TABLE relationship_memory_events
    ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS is_editable BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS read_policy TEXT NOT NULL DEFAULT 'relevant',
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active',
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS use_count INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_long_term_memories_prompt_policy
ON long_term_memories(character_id, status, read_policy, is_pinned, importance DESC, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_relationship_memory_events_prompt_policy
ON relationship_memory_events(character_id, status, read_policy, is_pinned, importance DESC, updated_at DESC);
