#!/usr/bin/env python3
"""Render a simple ASCII skill tree from the SQLite DAG."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from _tardis_common import ROOT, connect_database, ensure_schema, load_settings, resolve_database_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render DAG concepts as an ASCII tree")
    parser.add_argument("--category", default=None, help="Optional category filter")
    parser.add_argument(
        "--format",
        choices=["ascii", "json"],
        default="ascii",
        help="Output format",
    )
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "tardis_settings.json"),
        help="Path to JSON settings file",
    )
    return parser.parse_args()


def color_tag(mastery: float) -> str:
    if mastery >= 0.8:
        return "[GREEN]"
    if mastery >= 0.5:
        return "[YELLOW]"
    return "[RED]"


def build_ascii(nodes, edges) -> str:
    children_by_parent = defaultdict(list)
    parents_by_child = defaultdict(set)
    node_by_id = {node["node_id"]: node for node in nodes}

    for edge in edges:
        children_by_parent[edge["parent_node_id"]].append(edge["child_node_id"])
        parents_by_child[edge["child_node_id"]].add(edge["parent_node_id"])

    roots = sorted(
        [node["node_id"] for node in nodes if node["node_id"] not in parents_by_child],
        key=lambda node_id: (node_by_id[node_id]["category"], node_by_id[node_id]["concept_name"]),
    )

    lines: list[str] = []

    def walk(node_id: str, prefix: str = "", is_last: bool = True, show_branch: bool = False) -> None:
        node = node_by_id[node_id]
        mastery = float(node["mastery_level"])
        branch_prefix = ""
        if show_branch:
            branch_prefix = "└── " if is_last else "├── "
        lines.append(
            f"{prefix}{branch_prefix}{node['concept_name']} ({node['node_id']}) "
            f"{color_tag(mastery)} mastery={mastery:.2f}"
        )
        sorted_children = sorted(children_by_parent.get(node_id, []), key=lambda cid: node_by_id[cid]["concept_name"])
        child_prefix = prefix + ("    " if is_last else "│   ") if show_branch else prefix
        for idx, child_id in enumerate(sorted_children):
            walk(
                child_id,
                prefix=child_prefix,
                is_last=idx == len(sorted_children) - 1,
                show_branch=True,
            )

    if not roots:
        return "No concepts loaded."

    for root in roots:
        walk(root, show_branch=False)
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def main() -> None:
    args = parse_args()
    settings = load_settings(Path(args.config))
    db_path = resolve_database_path(settings)

    connection = connect_database(db_path)
    ensure_schema(connection)

    where_clause = "WHERE 1=1"
    params: list[object] = []
    if args.category:
        where_clause += " AND category = ?"
        params.append(args.category)

    nodes = connection.execute(
        f"""
        SELECT node_id, concept_name, category, mastery_level
        FROM concepts_dag
        {where_clause}
        ORDER BY category ASC, concept_name ASC;
        """,
        params,
    ).fetchall()
    node_ids = [row["node_id"] for row in nodes]

    if node_ids:
        placeholders = ",".join("?" for _ in node_ids)
        edges = connection.execute(
            f"""
            SELECT parent_node_id, child_node_id
            FROM dag_edges
            WHERE parent_node_id IN ({placeholders}) AND child_node_id IN ({placeholders});
            """,
            [*node_ids, *node_ids],
        ).fetchall()
    else:
        edges = []

    if args.format == "json":
        payload = [
            {
                "node_id": row["node_id"],
                "concept_name": row["concept_name"],
                "category": row["category"],
                "mastery_level": float(row["mastery_level"]),
            }
            for row in nodes
        ]
        print(json.dumps({"status": "ok", "nodes": payload}, indent=2))
    else:
        print(build_ascii(nodes, edges))


if __name__ == "__main__":
    main()
