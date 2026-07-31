"""Full agent eval — `make eval`. Requires Bedrock model access (AWS creds).

Runs each golden question through the real agent for its bounded context
and checks that the expected value (fetched independently, straight off
the gold layer / the same tool the agent uses) shows up in the answer.
Deterministic exact-match — no LLM-as-judge. Also runs the routing
questions through the Supervisor and checks which specialist tool it
actually called.
"""

import sys

from agents.contexts.claims_investigator import build_agent as build_investigator
from agents.contexts.revenue_analyst import build_agent as build_analyst
from agents.contexts.supervisor import build_agent as build_supervisor
from agents.eval.claim_questions import CLAIM_QUESTIONS
from agents.eval.golden_questions import GOLDEN_QUESTIONS
from agents.eval.routing_questions import ROUTING_QUESTIONS
from agents.models import get_model
from agents.telemetry import setup_telemetry


def _normalize(text: str) -> str:
    """Strip thousands separators so '4,729,526.38' matches '4729526.38'."""
    return text.replace(",", "")


def _run_suite(label: str, agent, questions) -> tuple[int, int]:
    """Run one golden-question suite; a question passes when its expected
    value (fetched live) appears in the agent's answer. Returns (passed, total)."""
    print(f"=== {label} ===")
    passed = 0
    for q in questions:
        expected = q.expected()
        answer = str(agent(q.question))
        ok = _normalize(expected) in _normalize(answer)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {q.id}: expected '{expected}' in answer to \"{q.question}\"")
        if not ok:
            print(f"       got: {answer.strip()[:200]}")
        passed += ok
    print(f"{passed}/{len(questions)} passed.\n")
    return passed, len(questions)


def _run_routing_suite(model) -> tuple[int, int]:
    """Run the routing questions through a fresh Supervisor each, checking
    which specialist tool it actually called. Returns (passed, total)."""
    print("=== Supervisor routing ===")
    passed = 0
    for rq in ROUTING_QUESTIONS:
        supervisor = build_supervisor(model)  # fresh per question, no shared conversation
        result = supervisor(rq.question)
        called = set(result.metrics.tool_metrics.keys())
        ok = rq.expected_specialist in called
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {rq.id}: expected '{rq.expected_specialist}' in {sorted(called)}")
        passed += ok
    print(f"{passed}/{len(ROUTING_QUESTIONS)} passed.\n")
    return passed, len(ROUTING_QUESTIONS)


def main() -> int:
    """Run all three suites (Analyst, Investigator, Supervisor routing).

    Needs Bedrock model access — every question is a real agent call.
    Exit code 0 only when every question in every suite passed.
    """
    setup_telemetry()
    model = get_model()

    results = [
        _run_suite("Revenue Analyst", build_analyst(model), GOLDEN_QUESTIONS),
        _run_suite("Claims Investigator", build_investigator(model), CLAIM_QUESTIONS),
        _run_routing_suite(model),
    ]

    total_passed = sum(p for p, _ in results)
    total = sum(t for _, t in results)
    print(f"TOTAL: {total_passed}/{total} passed.")
    return 0 if total_passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
