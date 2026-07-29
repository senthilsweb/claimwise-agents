"""Local chat entrypoint for the Revenue Analyst — `make run`."""

from agents import config
from agents.contexts.revenue_analyst import build_agent
from agents.models import get_model
from agents.telemetry import setup_telemetry


def main() -> None:
    tracing_on = setup_telemetry()
    agent = build_agent(get_model())
    target = "Databricks" if config.AGENT_TARGET == "databricks" else "DuckDB"
    print("Claimwise Revenue Analyst — ask a KPI question (Ctrl-D to quit).")
    print(f"Target: reading the gold layer from {target}.")
    print(f"Tracing: {'on' if tracing_on else 'off (no LANGSMITH_*/ARIZE_* env set)'}.\n")

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
