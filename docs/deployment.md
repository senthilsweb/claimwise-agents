# Deployment

At the end you will know how to run the Supervisor as an HTTP service
locally, and the current state of deploying it to Amazon Bedrock
AgentCore's managed cloud runtime.

## Local: the Runtime entrypoint

`agents/runtime.py` wraps the same Supervisor used everywhere else with
[`BedrockAgentCoreApp`](https://github.com/aws/bedrock-agentcore-sdk-python) —
nothing about the agent changes for deployment, only the transport does
(HTTP `/invocations` instead of a local chat loop).

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

A fresh Supervisor (and its four specialists) is built **per invocation**.
Strands `Agent` objects hold conversation state, and this process serves
many unrelated invocations over its lifetime — reusing one `Agent` across
requests would leak one caller's conversation into another's. See
[Runbook](runbook.md) for the story of catching this before it shipped.

## Cloud deployment: currently paused

Real `agentcore configure` / `agentcore deploy` (packaging the Runtime as
a container or direct-code deployment and standing up a live AgentCore
endpoint) is **deliberately paused**, not blocked by a bug. The reasoning:

- The IAM user this project uses was scoped to Bedrock-model-invoke only,
  on purpose.
- A real deploy needs materially more: IAM role creation and passing (the
  toolkit creates the Runtime's execution role on your behalf),
  `bedrock-agentcore:*` control-plane access, and S3 or ECR + CodeBuild
  depending on deployment mode.
- Given the choice between a broad IAM grant, a narrow hand-written
  policy, or pausing, the call made was to pause and verify everything
  else first.

Full reasoning and the exact next commands (including the Gateway
packaging steps, which need a Lambda-wrapping step this project hasn't
built) are recorded in
[tasks.md](https://github.com/senthilsweb/claimwise-agents/blob/main/openspec/changes/claimwise-revenue-copilot/tasks.md),
Bolt 4.

## Memory: code-ready, not yet live

`agents/runtime.py` will build an `AgentCoreMemorySessionManager` — keyed
by the AgentCore request's session ID — whenever `MEMORY_ID` is set in
`.env`. Left blank (the default), the Runtime behaves exactly as it did
before Memory existed: no conversation carries over between invocations.
This is genuinely untested — it needs a live Memory resource, created via
`MemoryClient.create_memory_and_wait(...)`, which needs
`bedrock-agentcore:CreateMemory` — one of the permissions currently
withheld by the pause above.

## What next

- The pause decision, and other real things that broke, in one place → [Runbook](runbook.md)
- Every env var referenced above → [Configuration](configuration.md)
