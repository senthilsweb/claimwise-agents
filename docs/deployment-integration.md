# Deployment & Integration

At the end you will know how to configure the agents, how to run them
(locally and, eventually, in AWS), and every way to call them.

## Configuration

All configuration lives in one `.env` file at the repo root (copy from
`.env.sample`; `.env` is gitignored — never commit it). Every variable is
loaded once, in `agents/config.py`. The complete table of every variable
is in [Reference](reference.md#configuration-reference) — the short
version: Bedrock model access, a data target (`duckdb` or `databricks`),
and a set of fully optional observability/memory variables that default
to off.

!!! warning "Never commit secrets"
    `.env` holds real AWS keys, Databricks tokens, and observability API
    keys. Never paste its contents into a commit, a chat log, or a public
    issue.

## Deployment

**Local (built and verified):** `agents/runtime.py` wraps the Supervisor
with [`BedrockAgentCoreApp`](https://github.com/aws/bedrock-agentcore-sdk-python) —
the same agent used everywhere else, only the transport changes (HTTP
`/invocations` instead of a chat loop).

```bash
PORT=18080 make runtime-dev
```

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

### REST API

`agents/runtime.py`'s `/invocations` endpoint, once running (locally via
`make runtime-dev`, or on AgentCore Runtime once deployed):

```bash
curl -s -X POST localhost:18080/invocations \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "What is our overall denial rate?"}'
```

```json
{"result": "The overall denial rate is 14.62%, from the mtr_executive_summary table.\n"}
```

Full request/response shape in [Reference](reference.md#api-reference).

### MCP

**Not built yet.** Exposing the tools (`query_metric`, `get_claim_story`,
etc.) as MCP Gateway targets needs a Lambda-packaging step first — MCP
Gateway targets are `lambda | openApiSchema | mcpServer | smithyModel`,
not a bare Python function. Concrete next commands (once IAM allows it)
are recorded in
[tasks.md](https://github.com/senthilsweb/claimwise-agents/blob/main/openspec/changes/claimwise-revenue-copilot/tasks.md),
Bolt 4.2.

### Python SDK

Every agent is just a function call away — no HTTP needed:

```python
from strands.models import BedrockModel
from agents.contexts.supervisor import build_agent

model = BedrockModel(model_id="us.anthropic.claude-sonnet-5", region_name="us-east-2")
agent = build_agent(model)
result = agent("What is our overall denial rate?")
print(result)
```

### CLI

```bash
make run                        # Supervisor, the full crew
make run AGENT=analyst          # or one specialist directly:
make run AGENT=investigator     #   analyst | investigator | advisor | steward
make run AGENT=advisor
make run AGENT=steward
```

### Event Driven

Not applicable — this project has no queue or event-bus trigger (SQS,
SNS, EventBridge, Kafka). It's called directly, synchronously, either
locally or over HTTP.

## What next

- The complete configuration table and API schema → [Reference](reference.md)
- Tracing every call you just made → [Operations](operations.md)
