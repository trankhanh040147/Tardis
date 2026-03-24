#!/usr/bin/env python3
"""Command router for agent-native TARDIS operations."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from _tardis_common import ROOT, connect_database, ensure_schema, load_settings, resolve_database_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TARDIS command router")
    subparsers = parser.add_subparsers(dest="command", required=True)

    drill = subparsers.add_parser("drill", help="Prepare conceptual interview simulation payload")
    drill.add_argument("--topic", default=None, help="Specific concept topic")
    drill.add_argument("--category", default=None, help="Optional category for auto-selected topic")

    sandbox = subparsers.add_parser("sandbox", help="Provision an execution sandbox")
    sandbox.add_argument("--topic", required=True, help="Challenge topic")
    sandbox.add_argument(
        "--fixture",
        default=None,
        choices=["python_race_condition", "docker_compose_config"],
        help="Optional fixture override",
    )

    tree = subparsers.add_parser("tree", help="Render the current skill tree")
    tree.add_argument("--category", default=None, help="Category filter")

    export = subparsers.add_parser("export", help="Export markdown for offline review")
    export.add_argument("--vault-dir", default=None, help="Output vault directory")

    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "tardis_settings.json"),
        help="Path to settings file",
    )
    return parser.parse_args()


def run_python_tool(script_name: str, extra_args: list[str]) -> dict:
    command = [sys.executable, str(ROOT / "tools" / script_name), *extra_args]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    payload = {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    if result.returncode != 0:
        raise RuntimeError(json.dumps(payload, indent=2))
    return payload


def suggest_topic(settings_path: Path, category: str | None) -> str | None:
    settings = load_settings(settings_path)
    db_path = resolve_database_path(settings)
    connection = connect_database(db_path)
    ensure_schema(connection)

    where_clause = "WHERE datetime(next_review_ts) <= datetime('now')"
    params: list[object] = []
    if category:
        where_clause += " AND category = ?"
        params.append(category)

    row = connection.execute(
        f"""
        SELECT concept_name
        FROM concepts_dag
        {where_clause}
        ORDER BY mastery_level ASC, challenge_count ASC
        LIMIT 1;
        """,
        params,
    ).fetchone()
    return row["concept_name"] if row else None


def main() -> None:
    args = parse_args()
    settings_path = Path(args.config)

    if args.command == "drill":
        topic = args.topic or suggest_topic(settings_path=settings_path, category=args.category)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "mode": "drill",
                    "topic": topic,
                    "next_step": "Read workflows/interview_simulation.md and run web research for realistic constraints.",
                },
                indent=2,
            )
        )
    elif args.command == "sandbox":
        cmd = ["provision", "--topic", args.topic]
        if args.fixture:
            cmd.extend(["--fixture", args.fixture])
        cmd.extend(["--config", str(settings_path)])
        output = run_python_tool("sandbox_manager.py", cmd)
        print(output["stdout"])
    elif args.command == "tree":
        cmd = []
        if args.category:
            cmd.extend(["--category", args.category])
        output = run_python_tool("tree_view.py", cmd)
        print(output["stdout"])
    elif args.command == "export":
        cmd = []
        if args.vault_dir:
            cmd.extend(["--vault-dir", args.vault_dir])
        cmd.extend(["--config", str(settings_path)])
        output = run_python_tool("markdown_exporter.py", cmd)
        print(output["stdout"])
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
