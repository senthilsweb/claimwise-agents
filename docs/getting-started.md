# Getting Started

At the end you will have run the agents locally, first for free with no
AWS account needed, then for real against a live model.

## Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- A built Claimwise gold layer (`rcm.duckdb`) — see the
  [Claimwise repo](https://github.com/senthilsweb/claimwise)
  (`make setup deps build` there)
- For live model calls: an AWS account with Bedrock model access (see
  Path 2 below)

## Installation

```bash
git clone https://github.com/senthilsweb/claimwise-agents.git
cd claimwise-agents
cp .env.sample .env
make setup
```

## Project Structure

```
agents/
  contexts/     one file per bounded-context agent, plus supervisor.py
  tools/        the tools each agent is allowed to call
  eval/         tool_smoke (no LLM) + golden/claim/routing evals
  config.py     env-driven settings
  data.py       read-only adapter (DuckDB/Databricks)
  runtime.py    the AgentCore Runtime HTTP entrypoint
  cli.py        the local chat entrypoint
docs/           this site
openspec/       specs and change proposals
```

The full tree, the load-bearing files, and the patterns to know before
editing are on their own page: [Code Tour](code-tour.md).

## Quick Start — zero AWS cost (2 minutes)

Edit `.env` and point `DUCKDB_PATH` at your built `rcm.duckdb`, then:

```bash
make smoke
```

```
31/31 checks passed.
```

This proves the data adapter, every tool, and the trust boundary (no
agent can write) all work — without a single model call.

## First Conversation

Add Bedrock access (model ID, region, credentials — see
[Configuration](configuration.md)), then:

```bash
make run
```

```
Claimwise Supervisor (full crew) — ask a question (Ctrl-D to quit).
Target: reading the gold layer from DuckDB.
Tracing: off (no LANGSMITH_*/ARIZE_*/OTEL_* env set).

> What is our overall denial rate?

The overall denial rate is 14.62%, from the mtr_executive_summary table.
```

## What next

- What each agent actually does → [Architecture](architecture.md)
- Every way to call the agents, with real output → [Examples](examples.md)
