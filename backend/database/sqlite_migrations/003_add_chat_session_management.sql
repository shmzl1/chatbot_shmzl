ALTER TABLE chat_sessions ADD COLUMN title TEXT NOT NULL DEFAULT '';
ALTER TABLE chat_sessions ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0;
ALTER TABLE chat_sessions ADD COLUMN archived_at TEXT;

UPDATE chat_sessions
SET user_id = (SELECT id FROM users LIMIT 1)
WHERE user_id IS NULL
  AND (SELECT COUNT(*) FROM users) = 1;

UPDATE chat_sessions
SET title = COALESCE(
    NULLIF(
        substr(
            trim(
                replace(
                    replace(
                        replace(
                            (
                                SELECT t.user_message
                                FROM chat_turns t
                                WHERE t.session_id = chat_sessions.id
                                ORDER BY t.id ASC
                                LIMIT 1
                            ),
                            char(13),
                            ' '
                        ),
                        char(10),
                        ' '
                    ),
                    char(9),
                    ' '
                )
            ),
            1,
            40
        ),
        ''
    ),
    '未命名对话'
)
WHERE trim(title) = '';

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_archive_updated
ON chat_sessions(user_id, is_archived, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_turns_session_created
ON chat_turns(session_id, created_at, id);
