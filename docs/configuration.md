# Configuration

At the end you will know every environment variable this project reads,
grouped by what it controls, and which ones are required versus optional.

All configuration lives in one `.env` file at the repo root (copy it from
`.env.sample`; `.env` itself is gitignored — never commit it). Every
variable is loaded once, in `agents/config.py`.

!!! warning "Never commit secrets"
    `.env` holds real AWS keys, Databricks tokens, and observability API
    keys. It is gitignored on purpose. Never paste its contents into a
    commit, a chat log, or a public issue.

## Model (Amazon Bedrock)

| Variable | Required | Meaning |
|---|---|---|
| `AWS_REGION` | yes | Region your Bedrock model access is in. |
| `AWS_PROFILE` | one of these two | A named AWS CLI profile — boto3's normal credential chain. |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | one of these two | Raw keys, if you prefer them over a profile. boto3 picks these up automatically once set; `AWS_PROFILE` is ignored if both keys are present. |
| `BEDROCK_MODEL_ID` | yes | The exact model or inference-profile ID to call. Never hardcoded anywhere in the code — see [Runbook](runbook.md) for a real case where the bare model ID and the inference-profile ID were different strings for the same model. |

## Data target

| Variable | Required | Meaning |
|---|---|---|
| `AGENT_TARGET` | yes | `duckdb` (dev, zero infra) or `databricks` (prod). Every tool's SQL is portable across both. |
| `DUCKDB_PATH` | if `AGENT_TARGET=duckdb` | Path to the Claimwise repo's built `rcm.duckdb`. |
| `CLAIMWISE_DBT_PATH` | Data Steward only | The Claimwise dbt-pipeline repo root — `run_dq_checks` runs `dbt test` there; `get_lineage` reads its `target/manifest.json`. |
| `DATABRICKS_HOST` / `DATABRICKS_HTTP_PATH` / `DATABRICKS_TOKEN` | if `AGENT_TARGET=databricks` | Read-only warehouse credentials. Agents have no code path that can write — see [The Agents](the-agents.md). |
| `DATABRICKS_CATALOG` | if `AGENT_TARGET=databricks` | Defaults to `workspace`. |

## Observability (all optional)

Every one of these is off by default and independently switchable — see
[Observability](observability.md) for what each one shows you.

| Variable | Meaning |
|---|---|
| `LANGSMITH_TRACING` | `true` to export traces to LangSmith. |
| `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT` | LangSmith project credentials. |
| `ARIZE_SPACE_ID` / `ARIZE_API_KEY` / `ARIZE_PROJECT_NAME` | Arize AX credentials. Set either one and traces start exporting. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` / `OTEL_EXPORTER_OTLP_HEADERS` | Any generic OTLP/HTTP collector — accepts either an org/stream base URL or a full `.../v1/traces` URL, both get normalized. |

## AgentCore Memory (optional, currently untested)

| Variable | Meaning |
|---|---|
| `MEMORY_ID` | Blank by default — Memory stays fully disabled and behavior is identical to not having this section at all. Needs a live AgentCore Memory resource; see [Deployment](deployment.md). |
| `MEMORY_ACTOR_ID` | A placeholder actor identity (default `demo-user`) — a real deployment would derive this from the caller's authenticated identity, not a fixed string. |

## What next

- What each agent does with these settings → [The Agents](the-agents.md)
- Turning tracing on and verifying it → [Observability](observability.md)
