#!/usr/bin/env python3
"""Provision and validate isolated sandbox challenges."""

from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from pathlib import Path

from _tardis_common import ROOT, load_settings


PYTHON_RACE_MAIN = """from concurrent.futures import ThreadPoolExecutor


def increment_without_lock(iterations: int = 10_000) -> int:
    counter = {"value": 0}

    def worker() -> None:
        for _ in range(iterations):
            # Intentionally racy read-modify-write sequence.
            value = counter["value"]
            value += 1
            counter["value"] = value

    with ThreadPoolExecutor(max_workers=8) as pool:
        for _ in range(8):
            pool.submit(worker)

    return counter["value"]
"""

PYTHON_RACE_TEST = """from main import increment_without_lock


def test_increment_without_lock_is_correct():
    result = increment_without_lock(iterations=2000)
    expected = 8 * 2000
    # This intentionally fails in many runs due to data races.
    assert result == expected
"""

DOCKER_COMPOSE_BROKEN = """services:
  app:
    image: postgres:16
    environmnt:
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
"""

DOCKER_COMPOSE_NOTE = """# Broken on purpose

Fix this compose file so it validates with:

docker compose config
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Provision or validate TARDIS sandbox challenges")
    subparsers = parser.add_subparsers(dest="action", required=True)

    provision = subparsers.add_parser("provision", help="Create a new broken sandbox")
    provision.add_argument("--topic", required=True, help="Challenge topic label")
    provision.add_argument(
        "--fixture",
        default=None,
        choices=["python_race_condition", "docker_compose_config"],
        help="Fixture to materialize",
    )
    provision.add_argument(
        "--config",
        default=str(ROOT / "config" / "tardis_settings.json"),
        help="Path to JSON settings file",
    )

    validate = subparsers.add_parser("validate", help="Run tests/commands inside a sandbox")
    validate.add_argument("--sandbox-path", required=True, help="Absolute path to sandbox directory")
    validate.add_argument(
        "--validation-command",
        default="python -m pytest -q",
        help="Validation command to execute in the sandbox",
    )

    return parser.parse_args()


def write_python_race_fixture(target_dir: Path) -> None:
    (target_dir / "main.py").write_text(PYTHON_RACE_MAIN, encoding="utf-8")
    (target_dir / "test_main.py").write_text(PYTHON_RACE_TEST, encoding="utf-8")
    (target_dir / "README.md").write_text(
        "Fix `main.py` so `python -m pytest -q` passes consistently.\n",
        encoding="utf-8",
    )


def write_docker_fixture(target_dir: Path) -> None:
    (target_dir / "docker-compose.yml").write_text(DOCKER_COMPOSE_BROKEN, encoding="utf-8")
    (target_dir / "README.md").write_text(DOCKER_COMPOSE_NOTE, encoding="utf-8")


def provision(topic: str, fixture: str | None, config_path: str) -> dict:
    settings = load_settings(Path(config_path))
    sandbox_cfg = settings["sandbox"]
    chosen_fixture = fixture or sandbox_cfg["default_fixture"]

    base_dir = Path(sandbox_cfg["base_tmp_dir"])
    if not base_dir.is_absolute():
        base_dir = ROOT / base_dir
    base_dir.mkdir(parents=True, exist_ok=True)

    sandbox_id = f"sandbox-{uuid.uuid4().hex[:8]}"
    sandbox_path = base_dir / sandbox_id
    sandbox_path.mkdir(parents=True, exist_ok=False)

    if chosen_fixture == "python_race_condition":
        write_python_race_fixture(sandbox_path)
    elif chosen_fixture == "docker_compose_config":
        write_docker_fixture(sandbox_path)
    else:
        raise ValueError(f"Unsupported fixture: {chosen_fixture}")

    return {
        "status": "ok",
        "topic": topic,
        "fixture": chosen_fixture,
        "sandbox_path": str(sandbox_path),
    }


def validate(sandbox_path: str, command: str) -> dict:
    sandbox_dir = Path(sandbox_path)
    if not sandbox_dir.exists():
        raise FileNotFoundError(f"Sandbox path does not exist: {sandbox_path}")

    result = subprocess.run(
        command,
        shell=True,
        cwd=sandbox_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    passed = result.returncode == 0
    hint = ""
    if "No module named pytest" in (result.stderr or ""):
        hint = "Install pytest in your environment, e.g. `python -m pip install pytest`."
    return {
        "status": "ok",
        "sandbox_path": str(sandbox_dir),
        "command": command,
        "passed": passed,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "hint": hint,
    }


def main() -> None:
    args = parse_args()

    if args.action == "provision":
        payload = provision(topic=args.topic, fixture=args.fixture, config_path=args.config)
    elif args.action == "validate":
        payload = validate(sandbox_path=args.sandbox_path, command=args.validation_command)
    else:
        raise ValueError(f"Unknown action: {args.action}")

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
