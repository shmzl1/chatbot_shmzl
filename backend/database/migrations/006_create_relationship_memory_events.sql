CREATE TABLE IF NOT EXISTS relationship_memory_events (
    id BIGSERIAL PRIMARY KEY,
    character_id TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'manual',
    source_id TEXT,
    source_turn_id BIGINT,
    memory_type TEXT NOT NULL DEFAULT 'note',
    content TEXT NOT NULL,
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    importance INTEGER NOT NULL DEFAULT 5 CHECK (importance >= 1 AND importance <= 10),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_relationship_memory_events_character_active
ON relationship_memory_events(character_id, is_active, importance DESC, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_relationship_memory_events_source_turn
ON relationship_memory_events(source_turn_id);
