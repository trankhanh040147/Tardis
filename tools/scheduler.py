#!/usr/bin/env python3
"""Pick the next optimal concept node for review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _tardis_common import ROOT, connect_database, ensure_schema, load_settings, resolve_database_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Return the next concept node to study")
    parser.add_argument("--category", default=None, help="Optional category filter (e.g. backend)")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="How many ranked candidates to return",
    )
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "tardis_settings.json"),
        help="Path to JSON settings file",
    )
    return parser.parse_args()


def compute_score(row) -> float:
    due_bonus = 1.0 if row["is_due"] else 0.0
    weak_mastery_bonus = 1.0 - row["mastery_level"]
    scarcity_bonus = 0.2 if row["challenge_count"] == 0 else 0.0
    misconception_bonus = min(0.8, row["recent_misconceptions"] * 0.2)
    return round(due_bonus + weak_mastery_bonus + scarcity_bonus + misconception_bonus, 4)


def main() -> None:
    args = parse_args()
    settings = load_settings(Path(args.config))
    db_path = resolve_database_path(settings)

    connection = connect_database(db_path)
    ensure_schema(connection)

    where_clause = "WHERE 1=1"
    params: list[object] = []
    if args.category:
        where_clause += " AND c.category = ?"
        params.append(args.category)

    rows = connection.execute(
        f"""
        SELECT
            c.node_id,
            c.concept_name,
            c.category,
            c.mastery_level,
            c.challenge_count,
            CASE WHEN datetime(c.next_review_ts) <= datetime('now') THEN 1 ELSE 0 END AS is_due,
            COALESCE((
                SELECT SUM(e.misconception_flag)
                FROM execution_events e
                WHERE e.node_id = c.node_id
                  AND datetime(e.created_at) >= datetime('now', '-14 days')
            ), 0) AS recent_misconceptions
        FROM concepts_dag c
        {where_clause};
        """,
        params,
    ).fetchall()

    ranked = []
    for row in rows:
        score = compute_score(row)
        ranked.append(
            {
                "node_id": row["node_id"],
                "concept_name": row["concept_name"],
                "category": row["category"],
                "mastery_level": round(float(row["mastery_level"]), 4),
                "is_due": bool(row["is_due"]),
                "recent_misconceptions": int(row["recent_misconceptions"]),
                "score": score,
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    output = ranked[: max(1, args.limit)]

    print(
        json.dumps(
            {
                "status": "ok",
                "database_path": str(db_path),
                "category": args.category,
                "candidates": output,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
