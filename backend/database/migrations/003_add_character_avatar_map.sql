CREATE TABLE IF NOT EXISTS character_avatar_map (
    character_id TEXT PRIMARY KEY,
    avatar_url TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_character_avatar_map_character_id
ON character_avatar_map(character_id);
