PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS concepts_dag (
    node_id TEXT PRIMARY KEY,
    concept_name TEXT NOT NULL,
    category TEXT NOT NULL,
    mastery_level REAL NOT NULL DEFAULT 0.15 CHECK (mastery_level >= 0.0 AND mastery_level <= 1.0),
    bkt_p_known REAL NOT NULL DEFAULT 0.15 CHECK (bkt_p_known >= 0.0 AND bkt_p_known <= 1.0),
    bkt_p_learn REAL NOT NULL DEFAULT 0.10 CHECK (bkt_p_learn >= 0.0 AND bkt_p_learn <= 1.0),
    bkt_p_guess REAL NOT NULL DEFAULT 0.20 CHECK (bkt_p_guess >= 0.0 AND bkt_p_guess <= 1.0),
    bkt_p_slip REAL NOT NULL DEFAULT 0.10 CHECK (bkt_p_slip >= 0.0 AND bkt_p_slip <= 1.0),
    challenge_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    next_review_ts TEXT NOT NULL DEFAULT (datetime('now')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS dag_edges (
    parent_node_id TEXT NOT NULL,
    child_node_id TEXT NOT NULL,
    penalty_weight REAL NOT NULL DEFAULT 0.08 CHECK (penalty_weight >= 0.0),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (parent_node_id, child_node_id),
    FOREIGN KEY (parent_node_id) REFERENCES concepts_dag(node_id) ON DELETE CASCADE,
    FOREIGN KEY (child_node_id) REFERENCES concepts_dag(node_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS execution_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('drill', 'sandbox', 'manual')),
    attempts INTEGER NOT NULL CHECK (attempts >= 1),
    time_to_resolution_sec REAL NOT NULL CHECK (time_to_resolution_sec >= 0),
    success INTEGER NOT NULL CHECK (success IN (0, 1)),
    misconception_flag INTEGER NOT NULL CHECK (misconception_flag IN (0, 1)),
    note TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (node_id) REFERENCES concepts_dag(node_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_concepts_category ON concepts_dag(category);
CREATE INDEX IF NOT EXISTS idx_concepts_next_review ON concepts_dag(next_review_ts);
CREATE INDEX IF NOT EXISTS idx_events_node_time ON execution_events(node_id, created_at DESC);
