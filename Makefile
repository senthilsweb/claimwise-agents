.PHONY: help setup run smoke eval clean

help:
	@echo "Targets:"
	@echo "  setup  - install dependencies (uv sync)"
	@echo "  run    - chat with the Revenue Analyst (needs Bedrock access)"
	@echo "  smoke  - no-LLM check that the data adapter and tools work"
	@echo "  eval   - golden-question eval against the real agent (needs Bedrock access)"
	@echo "  clean  - remove the virtualenv"

setup:
	uv sync

run:
	uv run python -m agents.cli

smoke:
	uv run python -m agents.eval.tool_smoke

eval:
	uv run python -m agents.eval.run_eval

clean:
	rm -rf .venv
