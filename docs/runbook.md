# Runbook

At the end you will know what runs automatically (nothing, currently),
what has real cost or risk, and every failure this project has actually
hit — with its fix.

## What runs automatically

| What | Trigger |
|---|---|
| Nothing | This project has no scheduled jobs, no cron, and no CI pipeline of its own yet. The only automation is the [docs site build](https://github.com/senthilsweb/claimwise-agents/blob/main/.github/workflows/docs.yml), which runs on a push touching `docs/**` or `mkdocs.yml`. |

## Procedures with cost or risk

**Deploying to Bedrock AgentCore's cloud runtime** creates real, billed
AWS resources (ECR, CodeBuild, a live Runtime endpoint) and is not
trivially reversible. This is why it's currently **paused** rather than
attempted casually — see [Deployment](deployment.md) for the full
reasoning. Do not run `agentcore configure` / `agentcore deploy` without
first confirming the IAM decision still holds.

**Running `dbt test` via the Data Steward's `run_dq_checks`** executes a
real subprocess against the Claimwise repo (~5 seconds on DuckDB). It's
read-only in effect (it only runs tests, never `dbt build`), but it does
briefly take a lock on the DuckDB file — see the failure below.

## Failures seen so far, and their fixes

### DuckDB lock conflict on `run_dq_checks`

**What happened:** `run_dq_checks` failed every time it ran *after* any
other tool had already run in the same process. dbt's own DuckDB adapter
always opens the database read-write — even for `dbt test` — and our own
cached read-only connection (in `agents/data.py`) was still holding a
lock on the same file, so dbt's subprocess couldn't acquire its own lock.

**Fix:** `agents/data.py` now exposes `release_duckdb_connection()`,
called right before the subprocess whenever `AGENT_TARGET=duckdb`. The
connection reopens lazily the next time any tool queries it. Confirmed
fixed: `make smoke` went from 27/29 to 29/29 the moment this landed.

### A shared Supervisor would have leaked conversations across requests

**What happened:** the first draft of `agents/runtime.py` built one
Supervisor at module load and reused it for every HTTP invocation. Since
Strands `Agent` objects hold conversation history internally, and the
Runtime process serves many unrelated invocations over its lifetime, this
would have let one caller's conversation bleed into another's.

**Fix:** caught before it ever shipped, during code review — a fresh
Supervisor (and its four specialists) is built per invocation instead,
matching the pattern already used throughout the eval suites.

### The agent summed a breakdown table instead of reading the pre-aggregated one

**What happened:** asked for total open accounts receivable — a single
number that already exists in `mtr_executive_summary.open_ar` — the model
instead queried the 40-row `mtr_ar_aging` breakdown table and tried to sum
it itself. Across four separate attempts it produced **four different
wrong totals**: 3,141,463.58 / 3,027,091.31 / 3,530,868.05 / 2,490,780.69 —
none matching the true value, 4,729,526.38.

**Fix:** an explicit prompt rule — prefer the most aggregated table that
already has the number you need; never sum or average across tool-call
rows yourself. Confirmed fixed on re-test. The same underlying lesson
shows up again in `get_claim_story`: it computes `total_collected` and
`amount_outstanding` in Python, so the model is never asked to do that
arithmetic in the first place.

### Wrong tool chosen for an exact claim lookup

**What happened:** asked for the status of a claim by its exact business
code, the Claims Investigator called `list_claims` (which has no
`claim_code` filter at all) instead of `get_claim_story` (the only tool
that accepts one), got an empty result, and reported a false "claim not
found" — for a claim that deterministically exists.

**Fix:** an explicit prompt rule — if the question already names a
specific claim code, always call `get_claim_story` directly. Confirmed
fixed: full, correct narration returned on re-test.

### Bedrock model access blocked by an AWS Marketplace payment issue

**What happened:** Anthropic's models on Bedrock are billed through AWS
Marketplace, which is a separate check from IAM model-access permissions.
A brand-new account without a valid payment method attached gets
`AccessDeniedException: INVALID_PAYMENT_INSTRUMENT` on the *first* real
(streaming) model call — even though a single non-streaming test call can
briefly appear to succeed.

**Fix:** add a valid payment method under **Billing → Payment
preferences**. While that's pending, **Amazon's own Nova models bypass
Marketplace billing entirely** (they're billed directly by AWS) — this
project's evals were run against `amazon.nova-lite-v1:0` for exactly this
reason. See [FAQ](faq.md) for why that doesn't invalidate the results.

## What next

- The full reasoning behind the paused cloud deploy → [Deployment](deployment.md)
- Quick answers to likely questions → [FAQ](faq.md)
