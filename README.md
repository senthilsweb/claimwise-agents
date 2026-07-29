# Claimwise Agents

Multi-agent showcase built with [Strands Agents](https://strandsagents.com) and deployed on [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/). One agent per bounded context, over the [Claimwise](https://github.com/senthilsweb/claimwise) dbt semantic layer.

**Project name: Claimwise Revenue Copilot.** The [Revenue Pulse dashboard](https://github.com/senthilsweb/claimwise/tree/main/dashboards) shows the numbers. This copilot explains them.

## The idea

Claimwise is a healthcare billing (RCM) pipeline: hospital treats patients, claims go to payers, some get denied, staff appeal, money arrives slowly. Its gold layer is organized as bounded contexts — `clinical`, `billing`, `admin` — with a metric layer (`mtr_*` tables) where every KPI is defined once.

This repo makes that design executable:

- Each bounded context becomes **one agent** with its own vocabulary and tools.
- A **supervisor** routes questions between them (agents-as-tools).
- Agents answer metric questions **only from the metric layer** — read, never recompute.
- All agents are **read-only**. The trust boundary is enforced, not promised.

The full reasoning is in the article: Domain-Driven Design for AI — bounded contexts, ubiquitous language, and why agents need them.

## The agents

| Agent | Bounded context | Answers |
|---|---|---|
| Revenue Analyst | gold/metrics | "What is our denial rate?" — reads `mtr_claims_funnel` |
| Claims Investigator | gold/billing | "Why is this claim unpaid?" — narrates filed → denied → appealed → collected |
| Denials & AR Advisor | gold/billing | "Which payer is hurting us? Are appeals worth it?" |
| Data Steward | pipeline governance | "Can I trust these numbers today?" — dbt test status, lineage |
| Supervisor | context map | routes by vocabulary |

## Stack

- Python + Strands Agents SDK (agent loop, tools, agents-as-tools)
- Amazon Bedrock (models) + AgentCore (Runtime, Gateway, Identity, Memory, Observability)
- Data: DuckDB locally (`rcm.duckdb` from the claimwise repo), Databricks SQL in prod

## Quickstart

```bash
git clone https://github.com/senthilsweb/claimwise-agents.git
cd claimwise-agents
cp .env.sample .env   # point DUCKDB_PATH at your built claimwise/dbt-pipeline/rcm.duckdb

make setup   # uv sync
make smoke   # no-LLM check: data adapter + tools work against the real gold layer
```

`make smoke` needs nothing but a built DuckDB file — no AWS, no Bedrock. It
proves the read-only guard, the metric allowlist, and every `mtr_*` table
actually resolve.

Talking to the agent needs an AWS account with Bedrock model access:

```bash
aws sso login          # or however you authenticate
# set BEDROCK_MODEL_ID in .env to a Claude model id you have access to
make run                # chat with the Revenue Analyst
make eval                # golden questions, checked against live gold-layer values
```

## Observability

Optional, both off by default. Set `LANGSMITH_TRACING=true` + `LANGSMITH_API_KEY`
and/or `ARIZE_SPACE_ID` + `ARIZE_API_KEY` in `.env` and every `make run` /
`make eval` call dual-exports full traces — every prompt, every tool call
with its inputs and outputs, every model response — to
[LangSmith](https://smith.langchain.com) and [Arize AX](https://app.arize.com)
via OpenTelemetry. `agents/telemetry.py` wires it up; no code changes needed
to turn it on or off. Content is unredacted by default (see the module's
docstring for the one env var that would turn redaction on).

## Structure

```
openspec/           specs and change proposals (start here — the intent lives here)
agents/
  config.py          env-driven settings
  data.py            read-only adapter (DuckDB/Databricks), enforces the trust boundary
  models.py           Bedrock model factory
  cli.py              chat entrypoint (make run)
  tools/metrics.py    query_metric / explain_metric — the metrics glossary + allowlist
  contexts/           one file per bounded-context agent
  eval/               tool_smoke (no LLM) + golden-question eval (needs Bedrock)
```

Work follows AI-DLC: **Intent → Execution → Operations**. The intent for the first release is documented in [`openspec/changes/claimwise-revenue-copilot/`](openspec/changes/claimwise-revenue-copilot/).

## Related

- [claimwise](https://github.com/senthilsweb/claimwise) — the dbt pipeline, gold layer, and dashboard this copilot reads
- [Strands Agents](https://github.com/strands-agents/sdk-python)
