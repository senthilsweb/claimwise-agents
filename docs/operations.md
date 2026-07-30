# Operations

At the end you will know how to watch what the agents are doing, what
runs automatically, what has real cost or risk, and every failure this
project has actually hit — with its fix.

## Logging

`agents/runtime.py` (via `BedrockAgentCoreApp`) emits structured JSON logs
per invocation, including a request ID and timing:

```json
{"timestamp": "2026-07-29T23:52:03.513Z", "level": "INFO", "message": "Invocation completed successfully (3.483s)", "logger": "bedrock_agentcore.app", "requestId": "46045734-c546-4912-92a1-2d43a9aa654f"}
```

## Metrics

No dedicated metrics dashboard yet. Token usage and per-call latency are
visible per-trace in whichever tracing backend is configured (see
Tracing, below) rather than aggregated separately.

## Tracing

Three backends, all optional and off by default, freely combinable — set
any combination in `.env` and every call exports the full trace (every
prompt, every tool call with its real inputs/outputs, every model
response) to all of them at once:

| Backend | Env vars |
|---|---|
| [LangSmith](https://smith.langchain.com) | `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` |
| [Arize AX](https://app.arize.com) | `ARIZE_SPACE_ID`, `ARIZE_API_KEY`, `ARIZE_PROJECT_NAME` |
| Any generic OTLP/HTTP collector | `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS` |

`agents/telemetry.py` wires it up — no code change needed to turn any of
these on or off. Content is unredacted by default (see the module's
docstring for the one env var that would turn redaction on).

An HTTP 200 from an OTLP endpoint only proves the payload was *accepted*
— not that it's stored or queryable. Verify a backend directly, e.g. for
a generic OTLP collector:

```python
import requests, time
resp = requests.post(
    "https://<your-instance>/api/default/_search?type=traces",
    headers={"Authorization": "Basic <your-token>"},
    json={"query": {
        "sql": "SELECT trace_id, service_name, operation_name, start_time "
               "FROM \"default\" WHERE service_name = 'strands-agents' "
               "ORDER BY start_time DESC LIMIT 5",
        "start_time": int((time.time() - 300) * 1_000_000),
        "end_time": int(time.time() * 1_000_000),
    }},
)
```

A real query against a live run returns rows like:

```
{'operation_name': 'chat', 'service_name': 'strands-agents', 'trace_id': '701214ed7bf8a5683518b0fbe74f6698'}
{'operation_name': 'execute_event_loop_cycle', 'service_name': 'strands-agents', ...}
{'operation_name': 'execute_tool get_claim_story', 'service_name': 'strands-agents', ...}
```

## Health Checks

`agents/runtime.py` exposes `/ping`:

```bash
curl -s localhost:18080/ping
# {"status":"Healthy","time_of_last_update":1785368934}
```

## Scaling

Not yet load-tested. Each invocation builds a fresh Supervisor (and its
four specialists) rather than reusing shared state, so there's no
shared-state concern to solve before scaling horizontally — see the
shared-Supervisor bug below for why that matters.

## Performance

Observed locally against `amazon.nova-lite-v1:0`: single-specialist
questions typically answer in 3–4 seconds; multi-tool Supervisor
questions (routing plus one specialist call) in a similar range. Not yet
measured against a frontier model or under concurrent load.

## Cost Considerations

- Model calls are billed per Bedrock's normal pricing; `amazon.nova-lite-v1:0`
  is negligible cost per call and was used for early development
  specifically for that reason.
- `run_dq_checks` runs a real `dbt test` subprocess (~5 seconds on
  DuckDB) on every call — cheap, but not free of latency.
- The live AgentCore Runtime deployment creates real, billed AWS
  resources: a Runtime endpoint, an AgentCore Memory resource, and an S3
  bucket for deployment artifacts. This is why deploying it was treated
  as a deliberate step requiring an explicit IAM decision, not a casual
  one — see [Deployment & Integration](deployment-integration.md).

## Runbook

### What runs automatically

| What | Trigger |
|---|---|
| Nothing in the product itself | No scheduled jobs, no cron |
| The docs site build | Push touching `docs/**` or `mkdocs.yml` |

### Failures seen so far, and their fixes

**DuckDB lock conflict on `run_dq_checks`.** It failed every time it ran
*after* any other tool in the same process — dbt's DuckDB adapter always
opens read-write, even for `dbt test`, and our own cached read-only
connection was still holding the file's lock. Fixed with
`release_duckdb_connection()`, called right before the subprocess.
Confirmed: `make smoke` went from 27/29 to 29/29.

**A shared Supervisor would have leaked conversations across requests.**
The first draft of `agents/runtime.py` built one Supervisor at module
load and reused it for every HTTP invocation. Since Strands `Agent`
objects hold conversation state, that would have leaked one caller's
conversation into another's. Caught before it ever shipped — fixed to
build a fresh Supervisor per invocation.

**The agent summed a breakdown table instead of reading the pre-aggregated
one.** Asked for total open AR — a number that already exists in
`mtr_executive_summary.open_ar` — the model queried the 40-row
`mtr_ar_aging` breakdown instead and summed it itself, producing **four
different wrong totals** across four attempts. Fixed with an explicit
prompt rule: prefer the most aggregated table; never sum rows yourself.

**Wrong tool chosen for an exact claim lookup.** Asked for a claim's
status by its exact code, the Claims Investigator called `list_claims`
(which has no `claim_code` filter) instead of `get_claim_story`, and
reported a false "not found." Fixed with an explicit routing rule.

**Bedrock model access blocked by an AWS Marketplace payment issue.**
Anthropic's models on Bedrock are billed through Marketplace — a separate
check from IAM model-access permissions. A fresh account without a valid
payment method attached gets `INVALID_PAYMENT_INSTRUMENT` on the first
real streaming call. Fix: add a payment method under **Billing → Payment
preferences**. Amazon's own Nova models bypass Marketplace billing
entirely, which is why they were used as a stand-in while this cleared.
Since resolved — the live deployment runs the intended model, Claude
Sonnet 5.

**`numpy` too new to have a wheel for the deploy target.** The first live
`agentcore deploy` attempt failed at the dependency-build step:
`numpy==2.5.1` (pulled in transitively via `databricks-sql-connector` →
`pandas`) had no published wheel for the aarch64-manylinux targets
AgentCore's `direct_code_deploy` cross-compiles for, and the build step
refuses to build from source. Fix: pinned `numpy<2.5` in `pyproject.toml`
(resolved to 2.4.6) — same `databricks-sql-connector` behavior, just an
older `numpy` release with wheels actually published for this platform.

**Deploying without `--env` crashes the Runtime, and `agentcore invoke`
reports the wrong symptom.** The first successful deploy had no
environment variables set, so the Runtime crashed immediately on
`BEDROCK_MODEL_ID is not set`. `agentcore invoke` reported this as
`Runtime initialization time exceeded` — a generic timeout, not the real
cause. The actual error only appeared in the CloudWatch runtime logs
(`aws logs tail /aws/bedrock-agentcore/runtimes/<agent>-DEFAULT
--log-stream-name-prefix "<date>/[runtime-logs"`). Fix: redeploy with
every required `--env` set (`AGENT_TARGET=databricks`, `BEDROCK_MODEL_ID`,
`DATABRICKS_*`) — `DUCKDB_PATH` is a local file path and is meaningless
on the cloud runtime, so the live deployment always targets Databricks.
Lesson: when `agentcore invoke` reports a timeout, check the CloudWatch
logs before assuming it's actually slow — it may be crashing instantly.

### Recovery procedures

None of the failures above required a manual recovery step beyond the
fix itself — each was a code or deploy-command fix, not an operational
incident requiring rollback. `agentcore deploy --auto-update-on-conflict`
safely redeploys over an existing agent (used for the `--env` fix above);
`agentcore status` and the CloudWatch log commands are the first things
to check if a live invocation misbehaves.

## What next

- The complete configuration and API reference → [Reference](reference.md)
