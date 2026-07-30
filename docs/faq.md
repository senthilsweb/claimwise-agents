# FAQ

## Why one agent per bounded context, instead of one agent with every tool?

Because a single agent with every tool has no boundary telling it which
data belongs together, which words mean what, or who owns a given rule —
exactly the problem Domain-Driven Design solves for people. Splitting by
bounded context means each agent's system prompt only ever carries one
context's vocabulary, and its tools are the *only* way it can touch data
— it structurally cannot reach into another context's tables. Full
reasoning in the
[design doc](https://github.com/senthilsweb/claimwise-agents/blob/main/openspec/changes/claimwise-revenue-copilot/design.md).

## Why is live cloud deployment paused?

Not a bug — a deliberate choice. The IAM user this project uses was
scoped to Bedrock-model-invoke only, on purpose, and a real
`agentcore deploy` needs materially broader permissions (IAM role
creation, full `bedrock-agentcore:*` control plane, S3/ECR/CodeBuild).
Given a choice between a broad grant, a narrow hand-written policy, or
pausing, the call was to pause and verify everything else first. See
[Deployment](deployment.md) and
[tasks.md](https://github.com/senthilsweb/claimwise-agents/blob/main/openspec/changes/claimwise-revenue-copilot/tasks.md)
Bolt 4 for the full record.

## Why test with a cheap Nova model instead of Claude?

Claude Sonnet 5 was temporarily blocked by an AWS Marketplace payment
issue unrelated to model access itself (see [Runbook](runbook.md)).
Amazon's own Nova models are billed directly, not through Marketplace, so
they were a genuine free stand-in for verifying the *code* end-to-end
while that cleared. The tool layer itself is proven correct independently
via `make smoke` — 31 checks, zero LLM calls — so the eval results on
Nova Lite say something real about the agent design, even on a small
model that isn't the intended production choice.

## Does any agent ever write to the warehouse?

No. Every SQL statement passes through one function
(`agents/data.py`'s `run_select`) that rejects anything that isn't a
plain `SELECT`/`WITH` before it reaches a connection — tested directly,
not just assumed. See [The Agents](the-agents.md).

## What happens if an agent is asked for a number that isn't tracked?

It says so plainly instead of estimating one. Every agent's system prompt
states this rule explicitly, and the Revenue Analyst's `query_metric` can
only reach an allowlist of six published tables — there's no path to
quietly compute a substitute number from raw facts.

## Where is the writing standard for these docs?

The shared
[documentation style guide](https://senthilsweb.github.io/ai-agents/style-guide/)
(canonical copy in the `ai-agents` repo) — it covers wiki pages, README
front doors, and command/example conventions for every senthilsweb repo
that publishes docs this way.
