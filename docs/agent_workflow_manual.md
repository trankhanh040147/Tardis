# TARDIS Agent Workflow Manual

This manual explains how an AI agent should execute TARDIS user commands through deterministic tools and workflow SOPs.

## 1) Startup Checklist (Run Once Per Session)

1. Ensure database exists:
   - `python tools/init_db.py`
2. Confirm core workflow files are present:
   - `workflows/interview_simulation.md`
   - `workflows/execution_loop.md`
   - `workflows/tree_view.md`
   - `workflows/export_state.md`
3. Keep SQLite as source of truth. Markdown is export exhaust only.

## 2) Command Routing Map

| User command | Agent action | Primary tool |
| --- | --- | --- |
| `/drill [topic]` | Run conceptual interview simulation | `python tools/tardis_cli.py drill [--topic "..."]` |
| `/sandbox [topic]` | Provision and validate broken exercise | `python tools/tardis_cli.py sandbox --topic "..."` |
| `/tree [category]` | Show mastery DAG in terminal/chat | `python tools/tardis_cli.py tree [--category "..."]` |
| `/export` | Generate markdown vault snapshot | `python tools/tardis_cli.py export` |

## 3) How To Run `/drill`

Follow `workflows/interview_simulation.md`.

1. Resolve topic:
   - If user gave one: use it.
   - Else: `python tools/tardis_cli.py drill` and use suggested topic.
2. Mandatory web research:
   - Collect 3-5 real constraints/failure modes for that topic.
3. Conduct Socratic interview:
   - Force quantified trade-offs (p99, throughput, retries, idempotency).
4. Score the outcome and log event:
   - `python tools/bkt_engine.py --node-id <node_id> --attempts <n> --time-to-resolution-sec <sec> --success <true|false> --mode drill --note "<summary>"`
5. Return strengths, gaps, and next challenge.

## 4) How To Run `/sandbox`

Follow `workflows/execution_loop.md`.

1. Provision sandbox:
   - `python tools/tardis_cli.py sandbox --topic "Race Conditions"`
   - Or direct: `python tools/sandbox_manager.py provision --topic "Race Conditions"`
2. Tell user to fix files in provisioned path.
3. Validate when requested:
   - `python tools/sandbox_manager.py validate --sandbox-path "<path>"`
   - Optional command override:
   - `python tools/sandbox_manager.py validate --sandbox-path "<path>" --validation-command "python -m pytest -q"`
4. Give candid feedback if failing.
5. Log telemetry:
   - `python tools/bkt_engine.py --node-id <node_id> --attempts <n> --time-to-resolution-sec <sec> --success <true|false> --mode sandbox --note "<pattern>"`

## 5) How To Run `/tree`

Follow `workflows/tree_view.md`.

- All categories:
  - `python tools/tardis_cli.py tree`
- One category:
  - `python tools/tardis_cli.py tree --category backend`

Interpretation:

- `[RED]` weak/decaying mastery, urgent review.
- `[YELLOW]` medium mastery.
- `[GREEN]` strong mastery.

## 6) How To Run `/export`

Follow `workflows/export_state.md`.

- Default vault path from config:
  - `python tools/tardis_cli.py export`
- Custom path:
  - `python tools/tardis_cli.py export --vault-dir ".tmp/my-vault"`

Artifacts:

- `mastery_overview.md`
- one markdown file per concept node

## 7) Failure Handling

- Missing pytest:
  - install: `python -m pip install pytest`
- Missing concept/topic mapping:
  - pick from scheduler output: `python tools/scheduler.py`
- Frequent false misconception flags:
  - tune thresholds in `config/tardis_settings.json` under `misconception`.

## 8) Agent Behavior Rules

- Always read the matching workflow SOP before execution.
- Do not skip logging (`bkt_engine.py`) after drill/sandbox completion.
- Keep sessions execution-first; avoid giving full solutions too early.
- Use deterministic tools for side effects, not ad-hoc reasoning-only updates.
