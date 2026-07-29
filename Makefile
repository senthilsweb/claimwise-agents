.PHONY: help setup run smoke eval clean

help:
	@echo "Targets:"
	@echo "  setup  - install dependencies (uv sync)"
	@echo "  run    - chat with an agent (needs Bedrock access)"
	@echo "           make run                       -> Revenue Analyst (default)"
	@echo "           make run AGENT=investigator    -> Claims Investigator"
	@echo "  smoke  - no-LLM check that the data adapter and tools work"
	@echo "  eval   - golden-question eval against both agents (needs Bedrock access)"
	@echo "  clean  - remove the virtualenv"

setup:
	uv sync

AGENT ?= analyst
run:
	uv run python -m agents.cli $(AGENT)

smoke:
	uv run python -m agents.eval.tool_smoke

eval:
	uv run python -m agents.eval.run_eval

clean:
	rm -rf .venv
