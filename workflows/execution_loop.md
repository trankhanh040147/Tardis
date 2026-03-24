# execution_loop

## Objective

Run a deterministic tactical fixing loop (`/sandbox`) where the learner repairs broken code/configuration under test pressure, then persist performance telemetry.

## Required Inputs

- `topic`: challenge family, e.g. race conditions, docker config, deadlocks.
- `session_id`: unique identifier for event tracking.
- `fixture` (optional): explicit fixture name for sandbox provisioning.
- `validation_command` (optional): defaults to `python -m pytest -q`.

## Tools

- `tools/sandbox_manager.py provision` - creates isolated broken challenge.
- `tools/sandbox_manager.py validate` - runs tests/validation command.
- `tools/bkt_engine.py` - updates mastery and event log.

## Steps

1. Provision challenge:
   - Run sandbox provision command with topic/fixture.
   - Return sandbox path and required validation command.
2. Instruct execution:
   - Tell user to fix files locally until validation passes.
   - Require explicit "validate now" signal or run validation on request.
3. Validate:
   - Run validation command inside sandbox.
   - Capture attempts and elapsed time-to-resolution.
4. Feedback:
   - If failing, provide radical candor:
     - call out misconception pattern precisely
     - point to likely fault class (data race, broken schema key, etc.)
     - avoid giving full patch immediately unless requested
5. Record outcome:
   - Run `tools/bkt_engine.py` with mode `sandbox`.
   - Persist misconception flag when attempts/time exceed configured thresholds.
6. Recommend next action:
   - If success: suggest a harder adversarial variant.
   - If failure: schedule prerequisite node review.

## Output

- In-chat: sandbox status, validation output summary, targeted feedback.
- Persisted: event row + updated concept mastery and review timestamp.

## Edge Cases and Recovery

- Validation command unavailable (e.g., missing pytest/docker):
  - Fall back to static checks or provide installation command and re-run.
- Sandbox folder accidentally deleted:
  - Re-provision a new sandbox and continue same topic.
- User asks for full solution:
  - Provide the patch, but still log as assisted completion with candid note.

## Learning Notes

- Document repeated failure signatures by topic to improve future fixtures.
- Add new fixtures when a topic is saturated and no longer diagnostic.
