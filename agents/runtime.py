"""Bedrock AgentCore Runtime entrypoint for the Supervisor.

Wraps the same Supervisor built in agents/contexts/supervisor.py — nothing
about the agent changes for deployment; only the transport does (HTTP
/invocations instead of a local chat loop). Local dev/test:

    PORT=18080 uv run python -m agents.runtime
    curl -s localhost:18080/invocations -H 'Content-Type: application/json' \\
      -d '{"prompt": "What is our overall denial rate?"}'

setup_telemetry() is called before BedrockAgentCoreApp() is constructed —
in the real managed runtime, AWS's own ADOT instrumentation sets the global
TracerProvider before any application code runs, so this ordering mainly
matters for local dev: it lets the app's baggage-span-processor attach to
our real (LangSmith/Arize/OpenObserve) provider instead of a throwaway one.

Memory (config.MEMORY_ID) is optional and UNTESTED without a live Memory
resource — see openspec/changes/claimwise-revenue-copilot/tasks.md, B4.4.
When unset (the default), invoke() behaves exactly as it did before Memory
existed: a fresh, memory-less Supervisor per call.
"""

from bedrock_agentcore import BedrockAgentCoreApp

from agents import config
from agents.contexts.supervisor import build_agent
from agents.models import get_model
from agents.telemetry import setup_telemetry

setup_telemetry()
app = BedrockAgentCoreApp()
_model = get_model()  # the model client is stateless and safe to reuse


def _session_manager_for(session_id: str | None):
    if not config.MEMORY_ID:
        return None
    if not session_id:
        return None  # no AgentCore session header (e.g. a bare local curl) — run memory-less
    from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
    from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

    memory_config = AgentCoreMemoryConfig(
        memory_id=config.MEMORY_ID,
        session_id=session_id,
        actor_id=config.MEMORY_ACTOR_ID,
    )
    return AgentCoreMemorySessionManager(memory_config, region_name=config.AWS_REGION)


@app.entrypoint
def invoke(payload: dict, context) -> dict:
    """AgentCore Runtime entrypoint. payload: {"prompt": "<question>"}.

    A fresh Supervisor (and its four specialists) is built per invocation —
    Strands Agent objects hold conversation state, and this process serves
    many unrelated invocations over its lifetime. Reusing one Agent across
    requests would leak one caller's conversation into another's. With
    Memory configured, the Supervisor's own conversation is restored by
    session_id instead of starting blank each time — the specialists still
    don't remember anything; only the Supervisor's dialogue does.
    """
    prompt = payload.get("prompt", "")
    if not prompt:
        return {"error": "payload must include a non-empty 'prompt' field"}
    session_manager = _session_manager_for(getattr(context, "session_id", None))
    agent = build_agent(_model, session_manager=session_manager)
    result = agent(prompt)
    return {"result": str(result)}


if __name__ == "__main__":
    import os

    # AgentCore's managed runtime always uses 8080; PORT lets local testing
    # avoid clashing with something else already bound to it.
    app.run(port=int(os.getenv("PORT", "8080")))
