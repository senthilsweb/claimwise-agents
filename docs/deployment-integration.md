# Deployment & Integration

At the end you will know how to run the agents (locally and, eventually,
in AWS) and which integration method to reach for.

## Configuration

Every variable is in [Configuration](configuration.md) — the short
version: Bedrock model access, a data target (`duckdb` or `databricks`),
and a set of fully optional observability/memory variables that default
to off.

## Deployment

**Local (built and verified):** `agents/runtime.py` wraps the Supervisor
with [`BedrockAgentCoreApp`](https://github.com/aws/bedrock-agentcore-sdk-python) —
the same agent used everywhere else, only the transport changes (HTTP
`/invocations` instead of a chat loop). See [Examples](examples.md#rest-api)
for a full runnable walkthrough.

**AWS AgentCore Runtime (currently paused):** deploying this same
Runtime to Amazon Bedrock AgentCore's managed cloud service —
`agentcore configure` / `agentcore deploy` — is a deliberate pause, not a
blocker:

- The IAM user this project uses was scoped to Bedrock-model-invoke
  only, on purpose.
- A real deploy needs materially more: IAM role creation and passing
  (the toolkit creates the Runtime's execution role on your behalf),
  full `bedrock-agentcore:*` control-plane access, and S3 or ECR +
  CodeBuild depending on deployment mode.
- Given the choice between a broad IAM grant, a narrow hand-written
  policy, or pausing, the call was to pause and verify everything else
  first.

Full reasoning and the exact next commands are in
[tasks.md](https://github.com/senthilsweb/claimwise-agents/blob/main/openspec/changes/claimwise-revenue-copilot/tasks.md),
Bolt 4.

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
