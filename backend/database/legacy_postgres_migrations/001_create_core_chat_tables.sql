CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    character_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_turns (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    character_id TEXT NOT NULL,
    user_message TEXT NOT NULL,
    reply TEXT NOT NULL,
    emotion TEXT NOT NULL,
    candidates_json JSONB NOT NULL,
    debug_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chat_turns_session_id
ON chat_turns(session_id, id);

CREATE TABLE IF NOT EXISTS long_term_memories (
    id BIGSERIAL PRIMARY KEY,
    character_id TEXT NOT NULL,
    memory_type TEXT NOT NULL DEFAULT 'note',
    content TEXT NOT NULL,
    importance INTEGER NOT NULL DEFAULT 5,
    tags_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_long_term_memories_character
ON long_term_memories(character_id, importance DESC, updated_at DESC);

CREATE TABLE IF NOT EXISTS turn_feedback (
    id BIGSERIAL PRIMARY KEY,
    turn_id BIGINT NOT NULL REFERENCES chat_turns(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_turn_feedback_turn_id
ON turn_feedback(turn_id, created_at DESC);

CREATE TABLE IF NOT EXISTS knowledge_items (
    id BIGSERIAL PRIMARY KEY,
    character_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    tags_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_knowledge_items_character_type
ON knowledge_items(character_id, source_type, updated_at DESC);
