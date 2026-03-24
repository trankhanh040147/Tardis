#!/usr/bin/env python3
"""Export TARDIS mastery state as Obsidian-compatible markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _tardis_common import ROOT, connect_database, ensure_schema, load_settings, resolve_database_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export DAG mastery and history as markdown")
    parser.add_argument(
        "--vault-dir",
        default=None,
        help="Output directory for markdown vault (defaults to config.export.vault_dir)",
    )
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "tardis_settings.json"),
        help="Path to JSON settings file",
    )
    return parser.parse_args()


def status_emoji(mastery: float) -> str:
    if mastery >= 0.8:
        return "🟢"
    if mastery >= 0.5:
        return "🟡"
    return "🔴"


def main() -> None:
    args = parse_args()
    settings = load_settings(Path(args.config))
    db_path = resolve_database_path(settings)

    vault_dir = Path(args.vault_dir) if args.vault_dir else Path(settings["export"]["vault_dir"])
    if not vault_dir.is_absolute():
        vault_dir = ROOT / vault_dir
    vault_dir.mkdir(parents=True, exist_ok=True)

    connection = connect_database(db_path)
    ensure_schema(connection)

    concepts = connection.execute(
        """
        SELECT node_id, concept_name, category, mastery_level, next_review_ts, challenge_count, success_count
        FROM concepts_dag
        ORDER BY category ASC, mastery_level ASC, concept_name ASC;
        """
    ).fetchall()

    overview_lines = [
        "# TARDIS Mastery Overview",
        "",
        "| Status | Concept | Category | Mastery | Challenges | Success Rate | Next Review |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in concepts:
        attempts = int(row["challenge_count"])
        successes = int(row["success_count"])
        success_rate = (successes / attempts * 100.0) if attempts else 0.0
        mastery = float(row["mastery_level"])
        overview_lines.append(
            f"| {status_emoji(mastery)} | [[{row['node_id']}]] | {row['category']} | "
            f"{mastery:.2f} | {attempts} | {success_rate:.1f}% | {row['next_review_ts']} |"
        )

    (vault_dir / "mastery_overview.md").write_text("\n".join(overview_lines) + "\n", encoding="utf-8")

    for row in concepts:
        events = connection.execute(
            """
            SELECT mode, attempts, time_to_resolution_sec, success, misconception_flag, note, created_at
            FROM execution_events
            WHERE node_id = ?
            ORDER BY created_at DESC
            LIMIT 25;
            """,
            (row["node_id"],),
        ).fetchall()

        concept_lines = [
            f"# {row['concept_name']}",
            "",
            f"- Node ID: `{row['node_id']}`",
            f"- Category: `{row['category']}`",
            f"- Mastery: `{float(row['mastery_level']):.2f}`",
            f"- Next review: `{row['next_review_ts']}`",
            "",
            "## Recent Events",
            "",
            "| Time | Mode | Attempts | Resolution (s) | Success | Misconception | Notes |",
            "|---|---|---:|---:|---|---|---|",
        ]
        for event in events:
            concept_lines.append(
                f"| {event['created_at']} | {event['mode']} | {event['attempts']} | "
                f"{float(event['time_to_resolution_sec']):.1f} | "
                f"{'yes' if event['success'] else 'no'} | "
                f"{'yes' if event['misconception_flag'] else 'no'} | "
                f"{event['note'] or ''} |"
            )

        (vault_dir / f"{row['node_id']}.md").write_text("\n".join(concept_lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "database_path": str(db_path),
                "vault_dir": str(vault_dir),
                "exported_concepts": len(concepts),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
