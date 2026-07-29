# Spec: context-agents

## ADDED Requirements

### Requirement: One agent per bounded context, one glossary each
Each agent SHALL carry exactly one bounded context's glossary in its system prompt (metrics, billing, governance). No agent SHALL define terms belonging to another context.

#### Scenario: Billing term asked to the billing agent
- **WHEN** the Claims Investigator is asked about a "collection"
- **THEN** it interprets it as money received against a claim, per its glossary — no other meaning is available to it

### Requirement: Agents are read-only by construction
Warehouse tools SHALL execute SELECT statements only. No code path for INSERT/UPDATE/DELETE/DDL SHALL exist in the tools package.

#### Scenario: Write attempt
- **WHEN** any agent produces a non-SELECT statement for a tool
- **THEN** the tool rejects it before execution and returns an error naming the read-only rule

### Requirement: KPI questions answered from the metric layer only
`query_metric` SHALL accept only allowlisted `mtr_*` tables. Agents SHALL NOT re-aggregate fact tables to answer a KPI question.

#### Scenario: Denial rate
- **WHEN** a user asks "what is our denial rate?"
- **THEN** the answer comes from `mtr_claims_funnel` and matches the dashboard's number exactly

### Requirement: Cross-context questions route through the supervisor
Specialist agents SHALL NOT call each other. The supervisor SHALL route by vocabulary and compose the final answer, referencing entities across contexts by ID only.

#### Scenario: Fuzzy revenue question
- **WHEN** the user asks "revenue looks down this month, what is going on?"
- **THEN** the supervisor consults Analyst → Investigator → Advisor in sequence and composes one answer

### Requirement: Claim stories narrate real rows
`get_claim_story` SHALL return the claim's actual events (filed, status changes, activities, collections) in time order; the narration SHALL contain no facts absent from those rows.

#### Scenario: Unpaid claim
- **WHEN** asked why a specific claim is unpaid
- **THEN** the story states its real status, real appeal events, and real collected-vs-billed amounts
