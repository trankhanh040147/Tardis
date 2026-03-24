# tree_view

## Objective

Render the current mastery DAG as an at-a-glance skill tree for motivation and triage.

## Required Inputs

- `category` (optional): category filter.

## Tools

- `tools/tree_view.py` - outputs ASCII or JSON graph view.

## Steps

1. Run `python tools/tree_view.py [--category <category>]`.
2. If no category is provided, include full graph output.
3. Highlight decaying nodes (`[RED]`) as immediate targets.

## Output

- ASCII tree in chat, optionally scoped by category.

## Edge Cases and Recovery

- No concepts loaded:
  - Ask user to initialize and seed DB with `python tools/init_db.py`.
