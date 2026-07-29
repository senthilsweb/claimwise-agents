"""Local chat entrypoint — `make run` (Supervisor, the full crew) or
`make run AGENT=<name>` to talk to one specialist directly.
"""

import sys

from agents import config
from agents.contexts.advisor import build_agent as build_advisor
from agents.contexts.claims_investigator import build_agent as build_investigator
from agents.contexts.revenue_analyst import build_agent as build_analyst
from agents.contexts.steward import build_agent as build_steward
from agents.contexts.supervisor import build_agent as build_supervisor
from agents.models import get_model
from agents.telemetry import setup_telemetry

_AGENTS = {
    "supervisor": ("Supervisor (full crew)", build_supervisor),
    "analyst": ("Revenue Analyst", build_analyst),
    "investigator": ("Claims Investigator", build_investigator),
    "advisor": ("Denials & AR Advisor", build_advisor),
    "steward": ("Data Steward", build_steward),
}


def main() -> None:
    choice = sys.argv[1] if len(sys.argv) > 1 else "supervisor"
    if choice not in _AGENTS:
        print(f"Unknown agent '{choice}'. Choose one of: {', '.join(_AGENTS)}")
        sys.exit(1)
    name, build_agent = _AGENTS[choice]

    tracing_on = setup_telemetry()
    agent = build_agent(get_model())
    target = "Databricks" if config.AGENT_TARGET == "databricks" else "DuckDB"
    print(f"Claimwise {name} — ask a question (Ctrl-D to quit).")
    print(f"Target: reading the gold layer from {target}.")
    print(f"Tracing: {'on' if tracing_on else 'off (no LANGSMITH_*/ARIZE_*/OTEL_* env set)'}.\n")

    while True:
        try:
            question = input("> ").strip()
        except EOFError:
            print()
            break
        if not question:
            continue
        result = agent(question)
        print(f"\n{result}\n")


if __name__ == "__main__":
    main()
