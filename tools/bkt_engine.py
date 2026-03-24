#!/usr/bin/env python3
"""Update concept mastery using a lightweight BKT model."""

from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from _tardis_common import (
    ROOT,
    connect_database,
    ensure_schema,
    load_settings,
    resolve_database_path,
)


@dataclass
class Event:
    node_id: str
    attempts: int
    time_to_resolution_sec: float
    success: bool
    mode: str
    session_id: str
    note: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recalculate mastery for a concept node")
    parser.add_argument("--node-id", required=True, help="Concept node identifier")
    parser.add_argument("--attempts", type=int, required=True, help="Number of attempts")
    parser.add_argument(
        "--time-to-resolution-sec",
        type=float,
        required=True,
        help="Time spent before resolution",
    )
    parser.add_argument(
        "--success",
        required=True,
        choices=["true", "false"],
        help="Whether the challenge was solved",
    )
    parser.add_argument(
        "--mode",
        default="manual",
        choices=["drill", "sandbox", "manual"],
        help="Learning mode for this event",
    )
    parser.add_argument(
        "--session-id",
        default=f"session-{uuid.uuid4()}",
        help="Session identifier to tie related events together",
    )
    parser.add_argument("--note", default="", help="Free-form annotation")
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "tardis_settings.json"),
        help="Path to JSON settings file",
    )
    return parser.parse_args()


def bounded(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def bkt_update(p_known: float, p_learn: float, p_guess: float, p_slip: float, success: bool) -> float:
    if success:
        numerator = p_known * (1 - p_slip)
        denominator = numerator + ((1 - p_known) * p_guess)
    else:
        numerator = p_known * p_slip
        denominator = numerator + ((1 - p_known) * (1 - p_guess))

    posterior = numerator / denominator if denominator else p_known
    posterior_plus_learning = posterior + ((1 - posterior) * p_learn)
    return bounded(posterior_plus_learning)


def detect_misconception(settings: dict, event: Event) -> bool:
    thresholds = settings["misconception"]
    return (not event.success) and (
        event.attempts >= thresholds["max_attempts_without_success"]
        or event.time_to_resolution_sec >= thresholds["slow_resolution_seconds"]
    )


def fetch_node(connection, node_id: str):
    row = connection.execute(
        """
        SELECT node_id, mastery_level, bkt_p_known, bkt_p_learn, bkt_p_guess, bkt_p_slip,
               challenge_count, success_count
        FROM concepts_dag
        WHERE node_id = ?;
        """,
        (node_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Node '{node_id}' does not exist. Seed or insert concepts first.")
    return row


def apply_prerequisite_decay(connection, node_id: str, attempts: int) -> int:
    parent_rows = connection.execute(
        """
        SELECT e.parent_node_id, e.penalty_weight
        FROM dag_edges e
        WHERE e.child_node_id = ?;
        """,
        (node_id,),
    ).fetchall()

    updates = 0
    for parent in parent_rows:
        penalty = parent["penalty_weight"] * max(1, attempts / 2)
        connection.execute(
            """
            UPDATE concepts_dag
            SET mastery_level = MAX(0.0, mastery_level - ?),
                updated_at = datetime('now')
            WHERE node_id = ?;
            """,
            (penalty, parent["parent_node_id"]),
        )
        updates += 1
    return updates


def compute_next_review(settings: dict, updated_mastery: float, success: bool) -> str:
    review = settings["review"]
    if not success:
        return f"+{review['hard_interval_minutes']} minutes"
    if updated_mastery >= 0.8:
        return f"+{review['easy_interval_days']} days"
    return f"+{review['normal_interval_days']} days"


def main() -> None:
    args = parse_args()
    settings = load_settings(Path(args.config))
    db_path = resolve_database_path(settings)
    event = Event(
        node_id=args.node_id,
        attempts=args.attempts,
        time_to_resolution_sec=args.time_to_resolution_sec,
        success=args.success == "true",
        mode=args.mode,
        session_id=args.session_id,
        note=args.note,
    )

    connection = connect_database(db_path)
    ensure_schema(connection)
    node = fetch_node(connection, event.node_id)

    updated_known = bkt_update(
        p_known=node["bkt_p_known"],
        p_learn=node["bkt_p_learn"],
        p_guess=node["bkt_p_guess"],
        p_slip=node["bkt_p_slip"],
        success=event.success,
    )
    misconception = detect_misconception(settings, event)
    review_modifier = compute_next_review(settings, updated_mastery=updated_known, success=event.success)

    connection.execute(
        """
        UPDATE concepts_dag
        SET mastery_level = ?,
            bkt_p_known = ?,
            challenge_count = challenge_count + 1,
            success_count = success_count + ?,
            next_review_ts = datetime('now', ?),
            updated_at = datetime('now')
        WHERE node_id = ?;
        """,
        (
            updated_known,
            updated_known,
            1 if event.success else 0,
            review_modifier,
            event.node_id,
        ),
    )

    prerequisite_updates = 0
    if not event.success:
        prerequisite_updates = apply_prerequisite_decay(connection, event.node_id, event.attempts)

    connection.execute(
        """
        INSERT INTO execution_events (
            session_id, node_id, mode, attempts, time_to_resolution_sec, success,
            misconception_flag, note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            event.session_id,
            event.node_id,
            event.mode,
            event.attempts,
            event.time_to_resolution_sec,
            1 if event.success else 0,
            1 if misconception else 0,
            event.note,
        ),
    )
    connection.commit()

    print(
        json.dumps(
            {
                "status": "ok",
                "node_id": event.node_id,
                "mastery_level": round(updated_known, 4),
                "misconception_flag": misconception,
                "prerequisites_penalized": prerequisite_updates,
                "database_path": str(db_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
