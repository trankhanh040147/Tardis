# TARDIS: Master Architecture and Execution Plan (Agent-Native)

## Product Intent

TARDIS is an execution-first learning engine for software and systems engineering. It treats passive reading as secondary and prioritizes measurable challenge performance.

Core principle: SQLite is the source of truth, workflows are behavior contracts, and markdown is export exhaust.

## System Layers (WAT-Aligned)

### 1) Data Engine (`db/`)

- `db/schema.sql` defines:
  - `concepts_dag`: node metadata, mastery, BKT parameters, next review time.
  - `dag_edges`: prerequisite relationships and penalty weights.
  - `execution_events`: per-session attempts, resolution time, outcome, misconception flag.
- `tools/init_db.py` initializes schema and optional starter seed data.

### 2) Deterministic Tools (`tools/`)

- `bkt_engine.py`
  - Updates mastery via Bayesian Knowledge Tracing.
  - Applies prerequisite decay on failed child-node execution.
  - Logs to `execution_events`.
- `scheduler.py`
  - Ranks due concepts by mastery weakness + misconception recency.
  - Returns next study candidates.
- `sandbox_manager.py`
  - Provisions isolated broken fixtures for tactical repair.
  - Validates user fixes by running test/verification commands.
- `tree_view.py`
  - Renders a chat-friendly ASCII DAG with mastery status tags.
- `markdown_exporter.py`
  - Exports overview + per-node histories as Obsidian-compatible markdown.
- `tardis_cli.py`
  - Routes `/drill`, `/sandbox`, `/tree`, and `/export` style intents to tools.

### 3) Behavioral Workflows (`workflows/`)

- `interview_simulation.md` defines `/drill` with mandatory web research and Socratic pressure-testing.
- `execution_loop.md` defines `/sandbox` tactical loop from provisioning to validation and candid feedback.
- `tree_view.md` defines `/tree` operator behavior.
- `export_state.md` defines `/export` operator behavior.

## Command Mapping

| User Intent | Router Command | Primary Tool Path |
|---|---|---|
| `/drill [topic]` | `python tools/tardis_cli.py drill --topic "...optional..."` | workflow + scheduler + bkt update |
| `/sandbox [topic]` | `python tools/tardis_cli.py sandbox --topic "..."` | sandbox provision/validate + bkt update |
| `/tree [category]` | `python tools/tardis_cli.py tree --category "...optional..."` | tree rendering |
| `/export` | `python tools/tardis_cli.py export` | markdown exporter |

## Misconception and Self-Improvement Loop

- Misconception criteria are configurable in `config/tardis_settings.json`:
  - max failed attempts threshold
  - slow resolution threshold
- `bkt_engine.py` marks misconception events and schedules earlier review for weak nodes.
- Agent should periodically inspect event patterns and adjust thresholds/weights when false positives or false negatives emerge.

## Immediate Next Milestones

1. Add more fixtures per category (`fixtures/`) and map them in `sandbox_manager.py`.
2. Add a script for adversarial scenario synthesis from weakest DAG nodes.
3. Add unit tests for BKT update math, scheduler ranking, and sandbox validation behavior.
4. Add optional ANSI color output for `tree_view.py` when terminal supports it.
