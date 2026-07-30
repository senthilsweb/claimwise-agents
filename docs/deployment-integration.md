# Deployment & Integration

At the end you will know how to run the agents locally, how they're
deployed live on AWS today, and which integration method to reach for.

## Configuration

Every variable is in [Configuration](configuration.md) — the short
version: Bedrock model access, a data target (`duckdb` or `databricks`),
and a set of fully optional observability/memory variables that default
to off.

## Deployment

**Local:** `agents/runtime.py` wraps the Supervisor with
[`BedrockAgentCoreApp`](https://github.com/aws/bedrock-agentcore-sdk-python) —
the same agent used everywhere else, only the transport changes (HTTP
`/invocations` instead of a chat loop). See [Examples](examples.md#rest-api)
for a full runnable walkthrough.

**AWS AgentCore Runtime — live.** The same Runtime is deployed to Amazon
Bedrock AgentCore's managed cloud service. Deploying it needed IAM
permissions beyond this project's original Bedrock-model-invoke-only
scope — `IAMFullAccess` (the toolkit creates the Runtime's execution role
on your behalf), `BedrockAgentCoreFullAccess` (the control plane), and
`AmazonS3FullAccess` (the deployment artifact bucket, for
`direct_code_deploy` — no Docker needed):

```bash
export AWS_PROFILE=claimwise AWS_REGION=us-east-2 AGENTCORE_SUPPRESS_RECOMMENDATION=1

agentcore configure --entrypoint agents/runtime.py --name claimwise_supervisor \
  --region us-east-2 --non-interactive

agentcore deploy --agent claimwise_supervisor \
  --env "AGENT_TARGET=databricks" \
  --env "BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-5" \
  --env "AWS_REGION=us-east-2" \
  --env "DATABRICKS_HOST=..." --env "DATABRICKS_HTTP_PATH=..." \
  --env "DATABRICKS_TOKEN=..." --env "DATABRICKS_CATALOG=workspace"
```

`DUCKDB_PATH` is a local file path — meaningless on the cloud runtime, so
the live deployment always targets Databricks, never DuckDB. Full
worked examples against the live endpoint (`agentcore invoke`) are in
[Examples](examples.md).

Two real problems hit during this deploy, both fixed — see
[Operations](operations.md#runbook) for the full story: a `numpy`
version pinned too new to have a published ARM64 wheel (packaging
failure), and forgetting `--env` on the first deploy (the Runtime
crashed on a missing `BEDROCK_MODEL_ID`, surfaced by `agentcore invoke`
as a generic timeout — the real cause only showed up in CloudWatch logs).

**Docker, AWS Lambda, Kubernetes:** not part of this project's deployment
story — AgentCore Runtime is the only cloud target designed for.

## Integration Methods

Which method to reach for — every one has a full runnable example in
[Examples](examples.md):

| Method | When to use it |
|---|---|
| CLI (`make run`) | Interactive local testing, one specialist or the full crew |
| REST (`/invocations`) | Calling from anything that speaks HTTP, or once deployed to AgentCore Runtime |
| Python SDK | Embedding an agent directly in another Python process |
| MCP | **Not built yet** — needs a Lambda-packaging step first, see below |
| Event Driven (SQS/SNS/EventBridge/Kafka) | Not applicable — this project has no queue or event-bus trigger |
| Agent-to-Agent | Already how the Supervisor calls its four specialists internally — see [Architecture](architecture.md#agent-to-agent-communication) |

### MCP

Exposing the tools (`query_metric`, `get_claim_story`, etc.) as MCP
Gateway targets needs a Lambda-packaging step first — MCP Gateway targets
are `lambda | openApiSchema | mcpServer | smithyModel`, not a bare Python
function. Concrete next commands (once IAM allows it) are recorded in
[tasks.md](https://github.com/senthilsweb/claimwise-agents/blob/main/openspec/changes/claimwise-revenue-copilot/tasks.md),
Bolt 4.2.

## What next

- Every runnable example, with real output → [Examples](examples.md)
- Tracing every call you make → [Operations](operations.md)
