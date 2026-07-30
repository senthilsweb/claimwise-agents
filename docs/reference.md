# Reference

At the end you will have the complete technical detail: the API schema,
error codes, and answers to the questions most likely to come up.

For the full configuration variable table, see its own page:
[Configuration](configuration.md). For a worked example of every call
below with real output, see [Examples](examples.md).

## API Reference

The schema only — see [Examples](examples.md#rest-api) for a worked
call with real output.

### `GET /ping`

Response: `{"status": "Healthy", "time_of_last_update": <unix timestamp>}`

### `POST /invocations`

Request: `{"prompt": "<question>"}`

Response: `{"result": "<answer text>"}`

Empty or missing `prompt` returns an error without calling the model:
`{"error": "payload must include a non-empty 'prompt' field"}`

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

**Was live cloud deployment ever actually blocked?** No, just deliberately
paused for a while — the IAM user was scoped down on purpose, and
resuming meant an explicit decision about how far to widen it. Full
story, including the two real bugs hit during the actual deploy, in
[Deployment & Integration](deployment-integration.md),
[Operations](operations.md#runbook), and
[tasks.md](https://github.com/senthilsweb/claimwise-agents/blob/main/openspec/changes/claimwise-revenue-copilot/tasks.md)
Bolt 4.

**Why were early evals run on a cheap Nova model instead of Claude?**
Claude Sonnet 5 was temporarily blocked by an AWS Marketplace payment
issue unrelated to model access itself (since resolved — the live
deployment runs Sonnet 5). Amazon's Nova models are billed directly, so
they were a genuine free stand-in for verifying the *code* while that
cleared. The tool layer is proven correct independently via `make smoke`
(31 checks, zero LLM calls), so those eval results said something real
about the agent design even on a small model.

**Does any agent ever write to the warehouse?** No — see
[Architecture](architecture.md#tool-calling).

**What happens if an agent is asked for a number that isn't tracked?** It
says so plainly instead of estimating one — every agent's system prompt
states this rule explicitly.

**Where is the writing standard for these docs?** The shared
[documentation style guide](https://senthilsweb.github.io/ai-agents/style-guide/),
plus the `ai-agent-docs` skill that defines this page structure.

## Known Limitations

- No MCP Gateway (needs a Lambda-packaging step not yet built).
- Memory is live but not yet verified to persist across turns in the
  same session.
- No load testing performed against the live deployment.
- Two AgentCore observability permissions still missing
  (`logs:CreateLogGroup`, `logs:PutDeliverySource`) — the deploy and
  every invocation work fine without them; only full X-Ray trace
  delivery is affected.
- This project's own triple OTLP export (LangSmith/Arize/OpenObserve)
  is not yet enabled on the live cloud deployment — only AgentCore's
  built-in CloudWatch/X-Ray observability is.

## Future Enhancements

- Package the tools as a Lambda handler and stand up the MCP Gateway.
- Verify Memory actually recalls across two calls in the same session
  (the resource is live; this specific behavior isn't proven yet).
- Grant the two remaining CloudWatch Logs permissions and enable this
  project's own OTLP export (LangSmith/Arize/OpenObserve) on the live
  deployment, alongside AgentCore's built-in observability.
- Migrate the Databricks credential from a plaintext `.env`/`--env` value
  to AgentCore Identity's credential vending.
- Re-run the full eval suite against the live cloud deployment (Claude
  Sonnet 5, Databricks) and compare against the earlier local Nova Lite
  baseline.
