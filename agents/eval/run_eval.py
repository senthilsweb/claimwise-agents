"""Full agent eval — `make eval`. Requires Bedrock model access (AWS creds).

Runs each golden question through the real Revenue Analyst agent and checks
that the expected number (fetched independently from the gold layer) shows
up in the agent's answer. Deterministic exact-match on the number — no
LLM-as-judge.
"""

import sys

from agents.contexts.revenue_analyst import build_agent
from agents.eval.golden_questions import GOLDEN_QUESTIONS
from agents.models import get_model


def _normalize(text: str) -> str:
    """Strip thousands separators so '4,729,526.38' matches '4729526.38'."""
    return text.replace(",", "")


def main() -> int:
    agent = build_agent(get_model())
    passed = 0

    for gq in GOLDEN_QUESTIONS:
        expected = gq.expected()
        answer = str(agent(gq.question))
        ok = _normalize(expected) in _normalize(answer)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {gq.id}: expected '{expected}' in answer to \"{gq.question}\"")
        if not ok:
            print(f"       got: {answer.strip()[:200]}")
        passed += ok

    total = len(GOLDEN_QUESTIONS)
    print(f"\n{passed}/{total} golden questions passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
