#!/usr/bin/env python3
"""Initialize TARDIS SQLite schema and optional seed data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _tardis_common import (
    ROOT,
    connect_database,
    ensure_schema,
    load_settings,
    resolve_database_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize the TARDIS database")
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "tardis_settings.json"),
        help="Path to JSON settings file",
    )
    parser.add_argument(
        "--seed",
        default=str(ROOT / "db" / "seed_concepts.json"),
        help="Path to JSON concept seed file",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Initialize schema only",
    )
    return parser.parse_args()


def upsert_seed_data(connection, seed_payload: dict) -> tuple[int, int]:
    concept_rows = seed_payload.get("concepts", [])
    edge_rows = seed_payload.get("edges", [])

    for row in concept_rows:
        connection.execute(
            """
            INSERT INTO concepts_dag (node_id, concept_name, category)
            VALUES (?, ?, ?)
            ON CONFLICT(node_id) DO UPDATE SET
                concept_name = excluded.concept_name,
                category = excluded.category,
                updated_at = datetime('now');
            """,
            (row["node_id"], row["concept_name"], row["category"]),
        )

    for row in edge_rows:
        connection.execute(
            """
            INSERT OR IGNORE INTO dag_edges (parent_node_id, child_node_id)
            VALUES (?, ?);
            """,
            (row["parent_node_id"], row["child_node_id"]),
        )

    connection.commit()
    return len(concept_rows), len(edge_rows)


def main() -> None:
    args = parse_args()
    settings = load_settings(Path(args.config))
    db_path = resolve_database_path(settings)

    connection = connect_database(db_path)
    ensure_schema(connection)

    concepts_loaded = 0
    edges_loaded = 0
    if not args.skip_seed:
        seed_payload = json.loads(Path(args.seed).read_text(encoding="utf-8"))
        concepts_loaded, edges_loaded = upsert_seed_data(connection, seed_payload)

    print(
        json.dumps(
            {
                "status": "ok",
                "database_path": str(db_path),
                "seeded_concepts": concepts_loaded,
                "seeded_edges": edges_loaded,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
