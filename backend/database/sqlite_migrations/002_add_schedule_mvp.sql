CREATE TABLE IF NOT EXISTS schedule_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    note TEXT NOT NULL DEFAULT '',
    item_type TEXT NOT NULL DEFAULT 'task'
        CHECK (item_type IN ('task', 'study_point', 'review_point', 'habit')),
    priority INTEGER NOT NULL DEFAULT 3
        CHECK (priority BETWEEN 1 AND 5),
    tags_json TEXT NOT NULL DEFAULT '[]',
    estimated_minutes INTEGER
        CHECK (estimated_minutes IS NULL OR estimated_minutes > 0),
    is_deleted INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_schedule_items_user_type
ON schedule_items(user_id, is_deleted, item_type, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_schedule_items_user_priority
ON schedule_items(user_id, is_deleted, priority, updated_at DESC);

CREATE TABLE IF NOT EXISTS schedule_occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES schedule_items(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scheduled_date TEXT NOT NULL,
    scheduled_time TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'done', 'skipped', 'postponed', 'overdue')),
    completed_at TEXT,
    source_occurrence_id INTEGER REFERENCES schedule_occurrences(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_schedule_occurrences_user_date_status
ON schedule_occurrences(user_id, scheduled_date, status);

CREATE INDEX IF NOT EXISTS idx_schedule_occurrences_item_created
ON schedule_occurrences(item_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_schedule_occurrences_source
ON schedule_occurrences(source_occurrence_id);

CREATE TABLE IF NOT EXISTS schedule_completion_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurrence_id INTEGER NOT NULL REFERENCES schedule_occurrences(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    result TEXT NOT NULL CHECK (result IN ('done', 'skipped', 'postponed')),
    feedback TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_schedule_completion_logs_occurrence
ON schedule_completion_logs(occurrence_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_schedule_completion_logs_user
ON schedule_completion_logs(user_id, created_at DESC);
