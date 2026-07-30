# Overview

## Purpose

Healthcare billing teams ask an analyst to write SQL every time they need
an answer to a question like:

- "What's our denial rate?"
- "Why is this claim unpaid?"
- "Which payer is hurting us?"

**Claimwise Revenue Copilot** answers those questions directly, in plain
English, by reading the [Claimwise](https://github.com/senthilsweb/claimwise)
dbt pipeline's gold layer — the same clean, tested tables that already
feed the [Revenue Pulse dashboard](https://github.com/senthilsweb/claimwise/tree/main/dashboards).

The design choice this project exists to demonstrate: Claimwise's gold
layer is already organized as **bounded contexts** (a Domain-Driven Design
idea) —

- `clinical`
- `billing`
- `admin`
- `metrics` — where every KPI is defined once

Instead of one agent with every tool, this project gives **each bounded
context its own agent**, with its own vocabulary and its own tools, plus
a Supervisor that routes each question to whichever specialist owns it.

## Use Cases

- *"What is our overall denial rate?"* — a company-wide KPI, answered from
  the published metric layer.
- *"Why is claim CLM48516149 still unpaid?"* — a single claim's real
  history, narrated in the order it actually happened.
- *"Which payer is hurting us? Are appeals worth the effort?"* — a
  portfolio-level pattern across many claims and payers.
- *"Can I trust today's numbers?"* — a live answer, backed by actually
  running the pipeline's data-quality tests, not a guess.

## Capabilities

- Answers KPI, single-claim, and portfolio-level billing questions from
  real gold-layer data — every number traceable to the table it came from.
- Routes a question to the right specialist automatically (the
  Supervisor), and composes an answer when a question needs more than one.
- Runs identically against DuckDB (local, zero infra) or Databricks
  (production warehouse) — the same tools, same SQL, same rules.
- Exports full traces (every prompt, every tool call, every response) to
  any combination of LangSmith, Arize AX, and a generic OTLP collector.

## Limitations

- **Read-only.** No agent can write to the warehouse — there is no code
  path for it, not just a prompt instruction. See [Architecture](architecture.md).
- **No live cloud deployment yet.** The AgentCore Runtime is built and
  verified locally over real HTTP, but deploying it to AWS's managed
  runtime is currently paused — see [Deployment & Integration](deployment-integration.md).
- **No MCP Gateway yet.** Exposing the tools as MCP targets needs a
  Lambda-packaging step this project hasn't built — see
  [Deployment & Integration](deployment-integration.md).
- **Memory is code-ready but untested** — it needs a live AgentCore
  Memory resource this account can't create yet.
- Tested primarily against `amazon.nova-lite-v1:0` while Claude Sonnet 5
  access was blocked by an unrelated AWS billing issue — see
  [Reference](reference.md#faq) for why that doesn't invalidate the
  results.

## Bounded Context

| | |
|---|---|
| **Responsibilities** | Answer billing/KPI/claim questions in plain English, read-only, from the Claimwise gold layer |
| **Upstream systems** | The Claimwise dbt pipeline (bronze → silver → gold), and its published `mtr_*` metric layer |
| **Downstream systems** | None yet — this is a conversational surface, not (yet) feeding another system |
| **Collaborating agents** | Internally: Revenue Analyst, Claims Investigator, Denials & AR Advisor, Data Steward, coordinated by one Supervisor |
| **External services** | Amazon Bedrock (models); optionally LangSmith, Arize AX, or any OTLP collector for tracing |

## What next

- Run it yourself, free, in a few minutes → [Getting Started](getting-started.md)
- How the five agents actually work → [Architecture](architecture.md)
