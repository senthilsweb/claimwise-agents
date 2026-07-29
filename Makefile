.PHONY: help setup run smoke eval clean

help:
	@echo "Targets:"
	@echo "  setup  - install dependencies (uv sync)"
	@echo "  run    - chat with an agent (needs Bedrock access)"
	@echo "           make run                        -> Supervisor, the full crew (default)"
	@echo "           make run AGENT=analyst          -> Revenue Analyst"
	@echo "           make run AGENT=investigator     -> Claims Investigator"
	@echo "           make run AGENT=advisor          -> Denials & AR Advisor"
	@echo "           make run AGENT=steward          -> Data Steward"
	@echo "  smoke  - no-LLM check that the data adapter and tools work"
	@echo "  eval   - golden-question + routing eval against the full crew (needs Bedrock access)"
	@echo "  clean  - remove the virtualenv"

setup:
	uv sync

AGENT ?= supervisor
run:
	uv run python -m agents.cli $(AGENT)

smoke:
	uv run python -m agents.eval.tool_smoke

eval:
	uv run python -m agents.eval.run_eval

clean:
	rm -rf .venv
