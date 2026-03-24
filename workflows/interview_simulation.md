# interview_simulation

## Objective

Run a high-pressure conceptual interview (`/drill`) that measures real systems-thinking under realistic constraints and logs the result into TARDIS.

## Required Inputs

- `topic` (optional): interview concept. If absent, infer from `tools/scheduler.py`.
- `difficulty_band`: target role level (default: middle backend engineer).
- `session_id`: unique identifier for event logging.
- `max_rounds`: Socratic rounds before forced conclusion (default: 6).

## Tools

- `tools/tardis_cli.py drill` - selects/echoes topic for the session.
- `tools/scheduler.py` - fallback topic source when no topic is provided.
- Web search tool (agent-native) - fetches current constraints and failure modes.
- `tools/bkt_engine.py` - records event and updates mastery.

## Steps

1. Resolve topic:
   - If user provided a topic, use it.
   - Else run `python tools/tardis_cli.py drill` and pick the suggested topic.
2. Run mandatory web research:
   - Search for up-to-date production constraints, failure patterns, and interview-style expectations for the topic.
   - Extract 3-5 concrete constraints (latency, throughput, cost, durability, R/W ratio, region assumptions).
3. Generate the prompt:
   - Create one flawed architecture scenario with explicit SLAs and trade-offs.
   - Include at least one hidden failure mode likely to trap shallow reasoning.
4. Conduct Socratic rounds:
   - Ask one hard follow-up at a time.
   - Do not provide direct solution until candidate reasoning is exhausted.
   - Force quantification (p99, retries, partition strategy, backpressure, idempotency).
5. Evaluate:
   - Mark success only if proposal addresses core constraints and failure mode mitigation.
   - Estimate attempts and time-to-resolution.
6. Update TARDIS:
   - Run `tools/bkt_engine.py` with attempts/time/success and concise note.
7. Return:
   - Explain strengths, gaps, and concrete next challenge.

## Output

- Primary: evaluated conceptual interview session in chat.
- Logged artifact: row in `execution_events` + updated `concepts_dag` mastery.

## Edge Cases and Recovery

- Unknown topic:
  - Fall back to scheduler candidate and explicitly disclose the selected node.
- Web results are weak/outdated:
  - Broaden query with year + vendor docs + postmortem keywords.
- User asks for immediate answer:
  - Provide a concise answer after at least one probing question, then continue evaluation.

## Learning Notes

- Track recurring misconception patterns in `note` field for future adversarial scenario generation.
- If misconception triggers frequently with low interview quality, tune thresholds in `config/tardis_settings.json`.
