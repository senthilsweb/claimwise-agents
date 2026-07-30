# Examples

At the end you will have a complete catalog of every way to call the
agents, each one runnable exactly as shown, with real output.

## CLI

```bash
make run                        # Supervisor, the full crew
make run AGENT=analyst          # or one specialist directly:
make run AGENT=investigator     #   analyst | investigator | advisor | steward
make run AGENT=advisor
make run AGENT=steward
```

```
Claimwise Supervisor (full crew) — ask a question (Ctrl-D to quit).
Target: reading the gold layer from DuckDB.
Tracing: off (no LANGSMITH_*/ARIZE_*/OTEL_* env set).

> What is our overall denial rate?

The overall denial rate is 14.62%, from the mtr_executive_summary table.
```

## REST API

`agents/runtime.py`'s `/invocations` endpoint, running locally via
`make runtime-dev` (or on AgentCore Runtime once deployed — see
[Deployment & Integration](deployment-integration.md)):

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

A question routed to a different specialist:

```bash
curl -s -X POST localhost:18080/invocations \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "What is the status of claim CLM48516149?"}'
```

```json
{"result": "The status of claim CLM48516149 for Amy Potter, submitted to Kaiser Permanente, is currently Appealed. The claim was initially submitted on July 12, 2026, processed for payment on July 13, 2026, and subsequently appealed on July 14, 2026. Currently, there are no collections against this claim, and the full amount of $4218.95 is still outstanding.\n"}
```

Full request/response schema in [Reference](reference.md#api-reference).

## Python SDK

Every agent is just a function call away — no HTTP needed:

```python
from strands.models import BedrockModel
from agents.contexts.supervisor import build_agent

model = BedrockModel(model_id="us.anthropic.claude-sonnet-5", region_name="us-east-2")
agent = build_agent(model)
result = agent("What is our overall denial rate?")
print(result)
```

Talking to one specialist directly instead of the Supervisor:

```python
from agents.contexts.claims_investigator import build_agent as build_investigator

investigator = build_investigator(model)
print(investigator("What is the status of claim CLM48516149?"))
```

## MCP

**Not built yet.** Exposing the tools (`query_metric`, `get_claim_story`,
etc.) as MCP Gateway targets needs a Lambda-packaging step first — see
[Deployment & Integration](deployment-integration.md#mcp).

## Event Driven

Not applicable — this project has no queue or event-bus trigger. It's
called directly, synchronously, either locally or over HTTP.

## What next

- Every environment variable used above → [Configuration](configuration.md)
- How to deploy this so these examples work against a live cloud endpoint → [Deployment & Integration](deployment-integration.md)
