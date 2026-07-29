"""Local chat entrypoint for the Revenue Analyst — `make run`."""

from agents import config
from agents.contexts.revenue_analyst import build_agent
from agents.models import get_model


def main() -> None:
    agent = build_agent(get_model())
    target = "Databricks" if config.AGENT_TARGET == "databricks" else "DuckDB"
    print("Claimwise Revenue Analyst — ask a KPI question (Ctrl-D to quit).")
    print(f"Target: reading the gold layer from {target}.\n")

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
