.PHONY: help setup run runtime-dev smoke eval chat clean

help:
	@echo "Targets:"
	@echo "  setup        - install dependencies (uv sync)"
	@echo "  run          - chat with an agent locally (needs Bedrock access)"
	@echo "                 make run                        -> Supervisor, the full crew (default)"
	@echo "                 make run AGENT=analyst          -> Revenue Analyst"
	@echo "                 make run AGENT=investigator     -> Claims Investigator"
	@echo "                 make run AGENT=advisor          -> Denials & AR Advisor"
	@echo "                 make run AGENT=steward          -> Data Steward"
	@echo "  runtime-dev  - serve the Supervisor over HTTP via the AgentCore Runtime"
	@echo "                 entrypoint (agents/runtime.py), for local testing before"
	@echo "                 a real cloud deploy. PORT=18080 make runtime-dev to avoid"
	@echo "                 clashing with anything already on 8080."
	@echo "  smoke        - no-LLM check that the data adapter, tools, and the Runtime"
	@echo "                 app itself all work"
	@echo "  eval         - golden-question + routing eval against the full crew (needs Bedrock access)"
	@echo "  chat         - browser chat widget against the DEPLOYED agent (docker compose;"
	@echo "                 needs AGENT_RUNTIME_ARN in .env — see chat-adapter/README.md)"
	@echo "  clean        - remove the virtualenv"

setup:
	uv sync

AGENT ?= supervisor
run:
	uv run python -m agents.cli $(AGENT)

PORT ?= 8080
runtime-dev:
	PORT=$(PORT) uv run python -m agents.runtime

smoke:
	uv run python -m agents.eval.tool_smoke

eval:
	uv run python -m agents.eval.run_eval

chat:
	docker compose up

clean:
	rm -rf .venv
