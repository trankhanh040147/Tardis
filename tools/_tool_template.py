#!/usr/bin/env python3
"""Template for deterministic WAT tools."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = ROOT / ".tmp"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a deterministic task")
    parser.add_argument("--input", required=True, help="Path to input JSON")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    return parser.parse_args()


def run(input_path: Path, output_path: Path) -> None:
    with input_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    result = {
        "status": "ok",
        "input_keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = TMP_DIR / output_path

    run(input_path=input_path, output_path=output_path)
    print(f"Wrote output to {output_path}")


if __name__ == "__main__":
    main()
