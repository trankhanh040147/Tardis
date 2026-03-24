# Tools

This folder contains deterministic scripts used by workflows.

## Tool Design Rules

- Keep inputs explicit (CLI args, files, environment variables).
- Keep outputs explicit (JSON, CSV, or files in `.tmp/`).
- Fail loudly with useful error messages.
- Keep logic deterministic and testable.
- Avoid interactive prompts unless a workflow requires them.

## Suggested Script Contract

- Parse arguments with `argparse`.
- Load secrets from `.env`.
- Write intermediates to `.tmp/`.
- Return machine-readable output when possible.

Use `tools/_tool_template.py` as a starting point for new scripts.

## TARDIS Core Tools

- `init_db.py` - initializes SQLite schema and seed concepts.
- `bkt_engine.py` - updates mastery and logs execution events.
- `scheduler.py` - ranks next concept candidates for review.
- `sandbox_manager.py` - provisions and validates broken sandboxes.
- `tree_view.py` - prints an ASCII mastery tree.
- `markdown_exporter.py` - exports SQLite state to markdown files.
- `tardis_cli.py` - command router for drill/sandbox/tree/export flows.
