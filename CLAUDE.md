# CLAUDE.md

## What this repo is

Claimwise Revenue Copilot — multi-agent showcase on Strands Agents + Amazon Bedrock AgentCore, reading the Claimwise dbt gold layer (sibling repo: `github.com/senthilsweb/claimwise`, locally at `/Users/krs/work/data-pipelines/claimwise`). One agent per bounded context (clinical / billing / admin / metrics), supervisor on top.

## Workflow (non-negotiable)

- **OpenSpec first.** Nontrivial changes start as `openspec/changes/<name>/` with `proposal.md`, `design.md`, `tasks.md`. No code before the intent is written.
- **AI-DLC phases: Intent → Execution → Operations.** Intent = proposal + design. Execution = bolts (B1, B2, …) — disjoint-file bolts fan out to parallel subagents. Operations = validation against real runs (evals, deploy checks), then update specs and memory.
- **Docs simple and clean.** README stays ~100 lines. Plain short sentences. No extra details.

## Conventions

- All credentials via environment variables (`.env`, never committed; `.env.sample` is the contract).
- Agents are **read-only** on the warehouse. No tool may write to gold/silver/bronze. This is the trust boundary — do not relax it without a new openspec change.
- **Metric-first**: KPI questions are answered from `mtr_*` tables only. Agents never re-aggregate facts. If a needed metric is missing, the fix is a new `mtr_*` model in the claimwise repo, not a bigger query here.
- Each agent's system prompt carries only its own context's glossary (ubiquitous language). Cross-context questions go through the supervisor.
- Dual target like the pipeline: DuckDB for dev (`AGENT_TARGET=duckdb`, zero infra), Databricks SQL for prod. Tools must work on both — portable SQL only, unquoted identifiers.
- Evals are deterministic where possible: golden questions with expected numbers computed from the metric tables themselves.

## Gotchas

- The local DuckDB file is built by the claimwise repo (`make setup deps build` there); this repo only reads it.
- Databricks serverless rejects double-quoted identifiers — same rule as the pipeline: never quote identifiers in SQL.
- `agents/data.py` caches one read-only DuckDB connection per process. The Data Steward's `run_dq_checks` shells out to `dbt test`, which always opens the file read-write — it calls `release_duckdb_connection()` first, or it hits a lock conflict (see docs Runbook).
- Runtime entrypoints (`agents/runtime.py`) must build a fresh `Agent` per invocation, never reuse one across requests — Strands `Agent` objects hold conversation state.

## Docs

Content structure follows the **`ai-agent-docs`** skill — six sections
(Overview, Getting Started, Architecture, Deployment & Integration,
Operations, Reference), framework-agnostic. This is the standard for
**any agent repo we build**, not specific to this one. Publishing
mechanics (MkDocs Material, GitHub Pages, the workflow) follow the
**`mkdocs-site`** skill, per the usual convention. Use both together
when writing or reorganizing docs for an agent project.

Every command, every env var, and the full agent design are in the
published wiki (`docs/`, built by `mkdocs`) — see
[docs/index.md](docs/index.md) or the live site at
https://senthilsweb.github.io/claimwise-agents/. This file stays short and
behavioral; don't duplicate wiki content back into it.
