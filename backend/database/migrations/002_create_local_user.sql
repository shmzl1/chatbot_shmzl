CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT,
    password_hash TEXT NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_lower
ON users (LOWER(username));

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower
ON users (LOWER(email))
WHERE email IS NOT NULL AND email <> '';

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_singleton
ON users ((true));
