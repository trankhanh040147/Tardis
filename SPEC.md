# TARDIS Project Specification

## 1. Purpose

TARDIS is an **execution-first learning engine** for software and systems engineering. The project prioritizes measurable performance in hands-on challenges over passive reading.

Core principle:
- **SQLite is the source of truth** for learning state and telemetry.
- **Workflows are behavior contracts** for agent operations.
- **Markdown is export exhaust** for review and portability.

## 2. Scope

This specification covers the local-first TARDIS scaffold in this repository, including:
- Data model and persistence (`db/`)
- Deterministic toolchain (`tools/`)
- SOP-style agent workflows (`workflows/`)
- Runtime configuration (`config/`)
- CLI command routing (`tools/tardis_cli.py`)

## 3. System Model (WAT)

The project follows the WAT model:

1. **Workflows**
   - Markdown SOPs defining objective, required inputs, exact steps, outputs, and edge-case handling.
2. **Agents**
   - Execute commands by following workflows and invoking deterministic tools.
3. **Tools**
   - Python scripts with explicit inputs/outputs and deterministic behavior.

## 4. Functional Requirements

### FR-1: Persistent Learning State
- The system must persist concept graph and execution telemetry in SQLite.
- The schema must include concept nodes, prerequisite edges, and execution events.
- Schema initialization must be provided via `tools/init_db.py`.

### FR-2: Deterministic Command Router
- The system must expose a single command surface through `tools/tardis_cli.py`.
- Supported commands:
  - `drill`
  - `sandbox`
  - `tree`
  - `export`
- Router must support optional config path override with `--config`.

### FR-3: Drill Flow Support
- `drill` must accept an optional topic and category.
- If no topic is provided, the router must suggest one from due/weak concepts.
- Output must be machine-readable JSON that includes mode and next-step guidance.

### FR-4: Sandbox Provision/Validation Flow
- `sandbox` must provision an isolated challenge by topic.
- System must support fixture override options:
  - `python_race_condition`
  - `docker_compose_config`
- Validation flow must support running deterministic commands against a sandbox path.

### FR-5: Mastery Tree Rendering
- `tree` must render a chat-friendly mastery DAG view.
- Category filtering must be supported.

### FR-6: Export State to Markdown
- `export` must generate markdown outputs suitable for offline/vault review.
- Outputs must include a mastery overview and per-node history files.
- Export directory must be configurable.

### FR-7: Scheduling and Ranking
- Scheduler must rank candidate concepts using a weighted score informed by:
  - review due status
  - weak mastery
  - challenge scarcity
  - recent misconception signal
- Scheduler must return top-N candidates and support category filtering.

### FR-8: BKT Telemetry Loop
- The system must support updating mastery via Bayesian Knowledge Tracing.
- Drill/sandbox sessions must be loggable with attempts, time-to-resolution, success state, mode, and notes.
- Misconception detection thresholds must be configurable.

## 5. Non-Functional Requirements

### NFR-1: Determinism and Testability
- Tools must use explicit CLI arguments and deterministic logic.
- Tools should fail loudly with useful errors.

### NFR-2: Local-First Operation
- Core functionality must run locally with SQLite.
- Temporary artifacts should be written to `.tmp/` only.

### NFR-3: Interface Consistency
- Prefer machine-readable outputs (JSON/CSV/files).
- Avoid interactive prompts unless explicitly required by a workflow.

### NFR-4: Maintainability
- Keep tool behavior and workflow contracts separated.
- Use `_tool_template.py` and `_workflow_template.md` conventions for expansion.

## 6. Data and Configuration Requirements

- `config/tardis_settings.json` must contain runtime settings (including misconception thresholds).
- `db/schema.sql` defines canonical database schema.
- `db/seed_concepts.json` provides optional seed data for initialization.

## 7. Directory and Artifact Requirements

- `tools/` for deterministic execution scripts only.
- `workflows/` for SOP-style behavior definitions.
- `db/` for schema and database assets.
- `.tmp/` for disposable intermediates.
- `.env` (local only) for secrets; must not be committed.

## 8. Acceptance Criteria

A setup is compliant with this specification when:

1. `python tools/init_db.py` completes successfully and initializes schema.
2. `python tools/tardis_cli.py drill` returns JSON with mode/topic/next step.
3. `python tools/tardis_cli.py sandbox --topic "<topic>"` provisions a sandbox payload.
4. `python tools/tardis_cli.py tree` renders mastery output.
5. `python tools/tardis_cli.py export` emits markdown artifacts to configured path.
6. Scheduler returns ranked candidates via `python tools/scheduler.py`.
7. Session outcomes can be logged through `tools/bkt_engine.py`.

## 9. Out of Scope (Current Scaffold)

- Full production service deployment architecture.
- Multi-user auth and remote tenancy.
- Rich UI layer beyond CLI/chat-friendly outputs.
- Complete fixture library for all concept categories.

## 10. Future Enhancements

- Add broader fixture coverage per category.
- Add adversarial scenario synthesis from weakest DAG nodes.
- Add unit tests for BKT updates, scheduler ranking, and sandbox validation.
- Add optional ANSI color enhancement in tree rendering.
