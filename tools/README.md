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
