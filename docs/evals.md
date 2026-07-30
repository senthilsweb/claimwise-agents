# Evals

At the end you will know the two eval suites this project runs, what
each one actually checks, and the one real gotcha hit while building
them.

Both are deterministic — exact-match against a value fetched
independently from the gold layer, never an LLM judging another LLM's
answer. `agents/eval/` is the code; `make smoke` and `make eval` are how
you run it.

## No-LLM smoke suite (`make smoke`)

Exercises the same tool and data-adapter code path every agent uses —
`query_metric`, `get_claim_story`, `run_dq_checks`, the read-only guard,
even the Runtime app's `/ping` — without spending a single model call.
Catches a broken connection, a bad table name, or a missing env var
before you pay for a Bedrock call to find out.

| Category | Checks |
|---|---|
| Metric catalog + `explain_metric`/`query_metric` | Every published `mtr_*` table |
| Billing tools | `list_claims`, `get_claim_story` — including a known appealed claim, a known collected claim, and an unknown one |
| Advisor tools | `payer_scorecard`, `ar_aging`, `appeal_outcomes` |
| Steward tools | `run_dq_checks` (a real `dbt test` run), `get_lineage`, `glossary_lookup` |
| Guardrails | `query_metric` rejects a non-metric table; `run_select` rejects a write statement |
| Runtime app | `/ping` responds; an empty prompt is rejected without calling the model |

```
$ make smoke
...
31/31 checks passed.
```

## LLM eval suite (`make eval`)

Runs real questions through the real agents against live Bedrock —
currently Claude Sonnet 5 against DuckDB. Deterministic exact-match, not
an LLM judge: each question's expected value is fetched independently,
straight off the gold tables (or the same tool the agent uses, for
claim-level questions), then checked as a substring of the agent's
actual answer.

| Suite | Questions | What it proves |
|---|---|---|
| Revenue Analyst (`golden_questions.py`) | 5 | KPI answers match the gold metric tables exactly |
| Claims Investigator (`claim_questions.py`) | 4 | Single-claim answers match `get_claim_story`'s real output |
| Supervisor routing (`routing_questions.py`) | 10 | The Supervisor calls the *right specialist tool* — checked via `result.metrics.tool_metrics`, never by reading the prose, so a correct-sounding answer routed to the wrong specialist still fails |

```
$ make eval
=== Revenue Analyst ===
[PASS] denial_rate: expected '14.62' in answer to "What is our overall denial rate?"
[PASS] collection_rate: expected '48.02' in answer to "What is our overall collection rate?"
[PASS] open_ar: expected '4729526.38' in answer to "How much money do we have in open accounts receivable right now?"
[PASS] denied_claim_count: expected '731' in answer to "How many claims have been denied?"
[PASS] worst_payer: expected 'UnitedHealthcare' in answer to "Which payer has the highest denial rate?"
5/5 passed.

=== Claims Investigator ===
3/4 passed.

=== Supervisor routing ===
10/10 passed.

TOTAL: 18/19 passed.
```

### The one FAIL, and why it isn't an agent bug

`claim_questions.py` asks for the status of `CLM00000000` — a claim
code that doesn't exist — and expects the substring `"not"` in the
answer, on the assumption the agent would say something like "claim not
found." What Claude Sonnet 5 actually said:

> No claim with code CLM00000000 exists in the system — please
> double-check the claim code.

That's the correct behavior — an honest not-found, no guessing, exactly
what every agent's system prompt requires. It fails only because the
word "not" never literally appears in that sentence. The eval's
assertion is too narrow, not the agent's answer. Left as-is for now
rather than loosening the assertion to match one specific phrasing —
worth revisiting if the wording keeps drifting.

## What next

- Every failure this project has actually hit, with its fix → [Operations](operations.md#runbook)
- The full configuration and API reference → [Reference](reference.md)
