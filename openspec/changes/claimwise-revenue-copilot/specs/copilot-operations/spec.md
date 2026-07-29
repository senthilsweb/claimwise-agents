# Spec: copilot-operations

## ADDED Requirements

### Requirement: Local-first dev loop
The full crew SHALL run on a laptop against DuckDB with no AWS resources except Bedrock model calls. `make setup` then `make run` SHALL be sufficient.

#### Scenario: Fresh clone
- **WHEN** a new user clones the repo, copies `.env.sample`, and points `DUCKDB_PATH` at a built claimwise database
- **THEN** `make run` answers metric questions locally

### Requirement: Deterministic evals against the metric tables
The eval suite SHALL compare agent answers to values queried live from the same `mtr_*` tables (exact match for numbers, structural match for stories and routing). No LLM-judge in v1.

#### Scenario: Eval run
- **WHEN** `make eval` runs
- **THEN** every metric question's number equals the live table value, and failures name the question, expected, and actual

### Requirement: Deploy parity
The eval suite SHALL pass against the deployed AgentCore runtime on the prod target before the deployment is considered done.

#### Scenario: Post-deploy check
- **WHEN** B4 completes
- **THEN** the same golden questions are replayed through the AgentCore endpoint and pass

### Requirement: Every answer is traceable
Observability SHALL record, per question: routed agent(s), tools called, and tables read.

#### Scenario: Surprising number
- **WHEN** a user doubts an answer
- **THEN** the trace shows which `mtr_*` table produced it, one hop from the dashboard's own source
