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

## Live Cloud Deployment

The Supervisor is deployed on Amazon Bedrock AgentCore's managed Runtime,
running Claude Sonnet 5 against the live Databricks warehouse — see
[Deployment & Integration](deployment-integration.md) for how it got
there. Talk to it with the `agentcore` CLI itself:

```bash
export AWS_PROFILE=claimwise AWS_REGION=us-east-2 AGENTCORE_SUPPRESS_RECOMMENDATION=1
agentcore invoke '{"prompt": "What is our overall denial rate?"}'
```

```
Response:
{"result": "Our overall denial rate is **14.62%** — that's the percentage of all
claims currently in \"Denied\" status, per Claimwise's executive summary
metrics.\n"}
```

A claim question, routed to the Claims Investigator:

```bash
agentcore invoke '{"prompt": "What is the status of claim CLM48516149?"}'
```

```
{"result": "**Claim CLM48516149** (patient Amy Potter, payer Kaiser Permanente,
billed $4,218.95):\n\n- **Current status: Appealed**\n- Timeline: Filed on
2026-07-12 → a payment processing activity on 2026-07-13 led to a denial → an
appeal was submitted on 2026-07-14.\n- **$0 collected so far** — the full
$4,218.95 remains outstanding while the appeal is pending.\n"}
```

A portfolio question, routed to the Denials & AR Advisor — notice Claude
Sonnet 5 adds real synthesis on top of the tool's numbers ("$2.23 written
off for every $1 recovered") while staying grounded in what
`appeal_outcomes` actually returned:

```bash
agentcore invoke '{"prompt": "Are appeals worth the effort for us?"}'
```

```
{"result": "## Are appeals worth the effort? — Short answer: **Selectively yes,
but not as a blanket strategy.**\n\n**The numbers:**\n- **Success rate:** Only
30.9% of appealed claims (600 of 1,944) actually collect.\n- **Dollars:** $1.51M
is recovered via successful appeals vs. **$3.37M that's appealed but never
collected** — roughly $2.23 written off for every $1 recovered.\n..."}
```

And the Data Steward, honestly reporting an infrastructure gap rather
than guessing — `CLAIMWISE_DBT_PATH` isn't set on the cloud Runtime, since
it points at a local filesystem path:

```bash
agentcore invoke '{"prompt": "Can I trust todays numbers? Run a check."}'
```

```
{"result": "I ran the trust check, and it **failed to execute** — not a data
issue, but an infrastructure one: the environment variable CLAIMWISE_DBT_PATH
isn't set, so the test suite couldn't even start.\n\n**Bottom line: I can't
confirm today's numbers are trustworthy.** ..."}
```

## MCP

Planned. Exposing the tools (`query_metric`, `get_claim_story`, etc.) as
MCP Gateway targets needs a Lambda-packaging step first — see
[Deployment & Integration](deployment-integration.md#mcp).

## Event Driven

Not applicable — this project has no queue or event-bus trigger. It's
called directly, synchronously, either locally or over HTTP.

## What next

- Every environment variable used above → [Configuration](configuration.md)
- How to deploy this so these examples work against a live cloud endpoint → [Deployment & Integration](deployment-integration.md)
