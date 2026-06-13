CREATE TABLE IF NOT EXISTS persona_turn_feedback (
    id BIGSERIAL PRIMARY KEY,
    character_id TEXT NOT NULL,
    session_id TEXT,
    turn_id BIGINT,
    user_message TEXT NOT NULL,
    assistant_message TEXT NOT NULL,
    rating TEXT NOT NULL,
    issue_tags_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    comment TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_persona_turn_feedback_character_created
    ON persona_turn_feedback (character_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_persona_turn_feedback_turn
    ON persona_turn_feedback (turn_id);
