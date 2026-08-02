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
about the agent design even on a small model. Full suite details and
current results → [Evals](evals.md).

**Does any agent ever write to the warehouse?** No — see
[Architecture](architecture.md#tool-calling).

**What happens if an agent is asked for a number that isn't tracked?** It
says so plainly instead of estimating one — every agent's system prompt
states this rule explicitly.

**Where is the writing standard for these docs?** The shared
[documentation style guide](https://senthilsweb.github.io/ai-agents/style-guide/),
plus the `ai-agent-docs` skill that defines this page structure.

## Known Limitations

- Read-only, by construction — there is no code path that writes to the
  warehouse.
- The data is synthetic: realistic distributions, but a generated
  company.
- Integration surfaces today are the CLI, the REST API, and the browser
  chat widget; conversations reach the agent through those only.
- No load testing has been performed against the live deployment.

## Roadmap

- [x] CLI (`make run`) — local chat with any specialist or the full crew
- [x] REST API (`/invocations`) — local and on the live AgentCore Runtime
- [x] Live AgentCore deployment with full observability (CloudWatch/X-Ray
      plus optional LangSmith / Arize AX / generic OTLP export)
- [x] Browser chat widget (`chat-adapter/` + mcp-chat-client, `make chat`)
- [x] Deterministic eval suite (18/19 against live data)
- [ ] MCP Gateway (tools packaged as Lambda targets)
- [ ] Microsoft Teams bridge (same adapter contract as the widget)
- [ ] Memory cross-turn recall verification
- [ ] AgentCore Identity credential vending for the Databricks token
- [ ] Load testing against the live Runtime

The working detail behind the unchecked items lives in the
[task register](https://github.com/senthilsweb/claimwise-agents/blob/main/openspec/changes/claimwise-revenue-copilot/tasks.md)
— docs describe what *is*; the register records what's *next*.
