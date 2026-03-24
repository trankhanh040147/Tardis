# Tardis

Tardis is organized around the WAT model: **Workflows, Agents, Tools**.

## TARDIS Command Surface

This repository now includes a local-first TARDIS scaffold with SQLite as the primary engine.

### Quick Start

1. Initialize DB and seed DAG:
   - `python tools/init_db.py`
2. Ask for next concept candidate:
   - `python tools/scheduler.py`
3. Run command router:
   - `python tools/tardis_cli.py drill`
   - `python tools/tardis_cli.py sandbox --topic "Race Conditions"`
   - `python tools/tardis_cli.py tree`
   - `python tools/tardis_cli.py export`
4. Read architecture:
   - `docs/tardis_master_architecture.md`

## Project Setup

1. Copy `.env.example` to `.env` and fill in required secrets.
2. Keep deterministic execution scripts in `tools/`.
3. Keep workflow SOPs in `workflows/`.
4. Use `.tmp/` for disposable intermediate files only.

## Directory Structure

- `.tmp/` - temporary files and scratch outputs (ignored by git)
- `tools/` - deterministic scripts used by workflows
- `workflows/` - markdown SOPs that define inputs, steps, and outputs
- `.env` - local secrets and API keys (not committed)
- `credentials.json`, `token.json` - local Google OAuth credentials (not committed)

## Operating Principle

Use workflows for decision logic and deterministic tools for execution. Keep final deliverables in cloud services, and treat local intermediates as replaceable.
