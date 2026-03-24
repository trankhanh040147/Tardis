# export_state

## Objective

Generate markdown exhaust for offline review while keeping SQLite as the source of truth.

## Required Inputs

- `vault_dir` (optional): target markdown vault path.

## Tools

- `tools/markdown_exporter.py` - serializes current mastery + event history.

## Steps

1. Run `python tools/markdown_exporter.py [--vault-dir <path>]`.
2. Confirm `mastery_overview.md` and per-node files are generated.
3. Share the export path with the user.

## Output

- Obsidian-compatible markdown files in configured vault directory.

## Edge Cases and Recovery

- Export path inaccessible:
  - Fall back to `.tmp/obsidian-vault` and report fallback path.
