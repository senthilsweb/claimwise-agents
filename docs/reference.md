# Reference

At the end you will have the complete technical detail: every
configuration variable, the API shape, error codes, and answers to the
questions most likely to come up.

## Configuration Reference

### Model (Amazon Bedrock)

| Variable | Required | Meaning |
|---|---|---|
| `AWS_REGION` | yes | Region your Bedrock model access is in. |
| `AWS_PROFILE` | one of these two | A named AWS CLI profile — boto3's normal credential chain. |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | one of these two | Raw keys, if you prefer them over a profile. boto3 picks these up automatically once set. |
| `BEDROCK_MODEL_ID` | yes | The exact model or inference-profile ID to call. Never hardcoded anywhere in the code. |

### Data target

| Variable | Required | Meaning |
|---|---|---|
| `AGENT_TARGET` | yes | `duckdb` (dev, zero infra) or `databricks` (prod). |
| `DUCKDB_PATH` | if `AGENT_TARGET=duckdb` | Path to the Claimwise repo's built `rcm.duckdb`. |
| `CLAIMWISE_DBT_PATH` | Data Steward only | The Claimwise dbt-pipeline repo root — `run_dq_checks` runs `dbt test` there; `get_lineage` reads its `target/manifest.json`. |
| `DATABRICKS_HOST` / `DATABRICKS_HTTP_PATH` / `DATABRICKS_TOKEN` | if `AGENT_TARGET=databricks` | Read-only warehouse credentials. |
| `DATABRICKS_CATALOG` | if `AGENT_TARGET=databricks` | Defaults to `workspace`. |

### Observability (all optional)

| Variable | Meaning |
|---|---|
| `LANGSMITH_TRACING` | `true` to export traces to LangSmith. |
| `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT` | LangSmith project credentials. |
| `ARIZE_SPACE_ID` / `ARIZE_API_KEY` / `ARIZE_PROJECT_NAME` | Arize AX credentials. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` / `OTEL_EXPORTER_OTLP_HEADERS` | Any generic OTLP/HTTP collector. |

### AgentCore Memory (optional, currently untested)

| Variable | Meaning |
|---|---|
| `MEMORY_ID` | Blank by default — Memory stays fully disabled. |
| `MEMORY_ACTOR_ID` | A placeholder actor identity (default `demo-user`). |

## API Reference

### `GET /ping`

```json
{"status": "Healthy", "time_of_last_update": 1785368934}
```

### `POST /invocations`

Request:

```json
{"prompt": "What is our overall denial rate?"}
```

Response:

```json
{"result": "The overall denial rate is 14.62%, from the mtr_executive_summary table.\n"}
```

Empty or missing `prompt` returns an error without calling the model:

```json
{"error": "payload must include a non-empty 'prompt' field"}
```

## MCP Tool Reference

Not published yet — see [Deployment & Integration](deployment-integration.md#mcp).

## Error Codes

| Error | Where | Meaning |
|---|---|---|
| `ReadOnlyViolation` | `agents/data.py` | A tool tried to run something other than a plain `SELECT`/`WITH` statement — rejected before it reached a connection. |
| `RuntimeError: <VAR> is not set` | `agents/config.py`'s `require()` | A required environment variable is missing. |
| `{"error": "payload must include a non-empty 'prompt' field"}` | `agents/runtime.py` | The `/invocations` request had no `prompt`. |
| `AccessDeniedException: ... INVALID_PAYMENT_INSTRUMENT` | Bedrock (AWS-side) | AWS Marketplace billing issue, not an IAM permissions issue — see [Operations](operations.md#runbook). |

## FAQ

**Why one agent per bounded context, instead of one agent with every
tool?** Because a single agent with every tool has no boundary telling it
which data belongs together, which words mean what, or who owns a given
rule. Splitting by bounded context means each agent's system prompt only
ever carries one context's vocabulary, and its tools are the *only* way
it can touch data. Full reasoning in the
[design doc](https://github.com/senthilsweb/claimwise-agents/blob/main/openspec/changes/claimwise-revenue-copilot/design.md).

**Why is live cloud deployment paused?** Not a bug — a deliberate choice
about IAM scope. See [Deployment & Integration](deployment-integration.md)
and
[tasks.md](https://github.com/senthilsweb/claimwise-agents/blob/main/openspec/changes/claimwise-revenue-copilot/tasks.md)
Bolt 4.

**Why test with a cheap Nova model instead of Claude?** Claude Sonnet 5
was temporarily blocked by an AWS Marketplace payment issue unrelated to
model access itself. Amazon's Nova models are billed directly, so they
were a genuine free stand-in for verifying the *code* while that cleared.
The tool layer is proven correct independently via `make smoke` (31
checks, zero LLM calls), so the eval results say something real about the
agent design even on a small model.

**Does any agent ever write to the warehouse?** No — see
[Architecture](architecture.md#tool-calling).

**What happens if an agent is asked for a number that isn't tracked?** It
says so plainly instead of estimating one — every agent's system prompt
states this rule explicitly.

**Where is the writing standard for these docs?** The shared
[documentation style guide](https://senthilsweb.github.io/ai-agents/style-guide/),
plus the `ai-agent-docs` skill that defines this six-section structure.

## Known Limitations

- No MCP Gateway (needs a Lambda-packaging step not yet built).
- No live AgentCore Memory (needs IAM permissions not yet granted).
- No cloud deployment yet — Runtime is verified locally only.
- No load testing performed.
- Tested primarily against a small model (`amazon.nova-lite-v1:0`), not
  the intended production model (Claude Sonnet 5), while a billing issue
  was unresolved.

## Future Enhancements

- Resume `agentcore configure`/`deploy` once the IAM decision is
  revisited (see [Deployment & Integration](deployment-integration.md)).
- Package the tools as a Lambda handler and stand up the MCP Gateway.
- Create a live AgentCore Memory resource and verify the session/actor
  wiring already in `agents/runtime.py`.
- Migrate the Databricks credential from a plaintext `.env` token to
  AgentCore Identity's credential vending.
- Re-run the full eval suite against Claude Sonnet 5 once Marketplace
  billing clears, and compare against the Nova Lite baseline.
