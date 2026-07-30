# Commands

At the end you will know every `make` target, what each needs (nothing?
Bedrock? DuckDB?), and what real output looks like.

## `make setup`

Installs dependencies with `uv sync`. Needs nothing but `uv` itself.

## `make smoke`

The no-LLM check — proves the data adapter, every tool, the read-only
guard, and the AgentCore Runtime app itself all work, with zero model
calls and zero AWS calls. Needs a built `rcm.duckdb` (see
[Getting Started](getting-started.md)).

```bash
make smoke
```

```
Metric catalog and explain_metric:
  [PASS] explain_metric('mtr_executive_summary')
  ...
Steward tools (run_dq_checks / get_lineage / glossary_lookup):
  [PASS] run_dq_checks actually runs dbt test
  ...
AgentCore Runtime app (agents/runtime.py, no model call):
  [PASS] runtime app /ping responds
  [PASS] runtime app rejects an empty prompt without calling the model

31/31 checks passed.
```

## `make run`

Chat with one agent locally. Needs Bedrock model access — see
[Getting Started](getting-started.md).

```bash
make run                        # Supervisor, the full crew (default)
make run AGENT=analyst          # Revenue Analyst only
make run AGENT=investigator     # Claims Investigator only
make run AGENT=advisor          # Denials & AR Advisor only
make run AGENT=steward          # Data Steward only
```

## `make runtime-dev`

Serves the same Supervisor over HTTP, the way AgentCore Runtime would call
it — see [Deployment](deployment.md) for the full walkthrough.

```bash
PORT=18080 make runtime-dev
```

```bash
curl -s localhost:18080/ping
# {"status":"Healthy","time_of_last_update":1785368934}

curl -s -X POST localhost:18080/invocations \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "What is our overall denial rate?"}'
# {"result": "The overall denial rate is 14.62%, from the mtr_executive_summary table.\n"}
```

## `make eval`

Runs the full deterministic eval suite against a real model: 5 golden
questions (Revenue Analyst), 4 claim questions (Claims Investigator), and
10 routing questions (does the Supervisor call the right specialist?).
Every expected value is fetched independently from the gold layer or the
same tool the agent uses — no LLM-as-judge.

```bash
make eval
```

```
=== Revenue Analyst ===
[PASS] denial_rate: expected '14.62' in answer to "What is our overall denial rate?"
...
5/5 passed.
=== Claims Investigator ===
...
4/4 passed.
=== Supervisor routing ===
...
10/10 passed.
TOTAL: 19/19 passed.
```

## `make clean`

Removes the virtualenv (`.venv`). Nothing else — no data, no `.env`, no
config.

## What next

- What each agent actually does with these commands → [The Agents](the-agents.md)
- Running the Supervisor as a real HTTP service → [Deployment](deployment.md)
