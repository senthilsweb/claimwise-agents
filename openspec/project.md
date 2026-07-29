# Project Context

## Purpose
Claimwise Revenue Copilot: a multi-agent showcase where each bounded context of the Claimwise gold layer becomes one agent. Built with Strands Agents, deployed on Amazon Bedrock AgentCore. Companion repo to `github.com/senthilsweb/claimwise` (the dbt pipeline it reads).

## Tech Stack
- Python 3.12+, Strands Agents SDK
- Amazon Bedrock (models), Bedrock AgentCore (Runtime, Gateway, Identity, Memory, Observability)
- DuckDB (dev, reads the claimwise repo's `rcm.duckdb`) / Databricks SQL (prod)
- Make (task runner), uv (env/deps)

## Conventions
- AI-DLC phases: **Intent → Execution → Operations**. Intent = openspec proposal + design. Execution = bolts (disjoint-file, parallel subagents). Operations = evals and live validation.
- Agents are read-only on the warehouse; KPI questions answered from `mtr_*` metric tables only (never re-aggregate facts).
- One glossary per agent (ubiquitous language); cross-context routing through the supervisor only.
- Credentials via env vars only; `.env.sample` is the contract.
- Portable SQL (DuckDB + Databricks), unquoted identifiers.
- Docs simple and clean; README ~100 lines.

## Structure
- `openspec/` — specs and change proposals
- `agents/` — agent code (arrives via bolts: tools, contexts, supervisor, entrypoints)

## Roadmap
- Change 1: `claimwise-revenue-copilot` — four context agents + supervisor, local DuckDB first, then AgentCore deploy
- Later: propose/dispose write path (appeal recommendations as proposals gated by rules) — separate change, not in v1
