"""Observability — dual OTLP export to LangSmith and Arize AX.

Mirrors the env-var contract already used across this account's other
agent projects (job-pilot, agent-job-matcher), so the same LangSmith/Arize
org accounts can be reused here with just a different project name.

Strands' own tracer emits full prompt/response content by default — every
system prompt, tool input, and tool output rides on the span unredacted
unless OTEL_SEMCONV_STABILITY_OPT_IN explicitly opts into redacting it
(see strands.telemetry.tracer.Tracer's docstring). Nothing extra is needed
here to see prompts and queries in the trace; this module only wires up
*where* the spans go.

Call setup_telemetry() once, before the first Agent is built — not from
agents/config.py (which runs on every import, including tool_smoke's
no-LLM checks) but explicitly from cli.py and eval/run_eval.py.
"""

import logging
import os

from agents import config

logger = logging.getLogger(__name__)

_configured = False


def setup_telemetry() -> bool:
    """Wire Strands' tracer to LangSmith and/or Arize AX, if configured.

    Idempotent — safe to call more than once. Returns True if at least one
    exporter was set up, False if tracing stays disabled (no env set).
    """
    global _configured
    if _configured:
        return True
    _configured = True

    if config.ARIZE_PROJECT_NAME:
        # Arize AX keys traces by the "model_id" resource attribute — a
        # span without one is rejected outright, not just unlabeled.
        existing = os.environ.get("OTEL_RESOURCE_ATTRIBUTES", "")
        addition = f"model_id={config.ARIZE_PROJECT_NAME}"
        os.environ["OTEL_RESOURCE_ATTRIBUTES"] = f"{existing},{addition}" if existing else addition

    from strands.telemetry import StrandsTelemetry

    telemetry = StrandsTelemetry()
    exporter_count = 0

    if config.LANGSMITH_TRACING and config.LANGSMITH_API_KEY:
        headers = {"x-api-key": config.LANGSMITH_API_KEY}
        if config.LANGSMITH_PROJECT:
            headers["Langsmith-Project"] = config.LANGSMITH_PROJECT
        telemetry.setup_otlp_exporter(
            endpoint="https://api.smith.langchain.com/otel/v1/traces",
            headers=headers,
        )
        exporter_count += 1
        logger.info("telemetry: exporting to LangSmith (project=%s)", config.LANGSMITH_PROJECT)

    if config.ARIZE_SPACE_ID and config.ARIZE_API_KEY:
        telemetry.setup_otlp_exporter(
            endpoint="https://otlp.arize.com/v1/traces",
            headers={"space_id": config.ARIZE_SPACE_ID, "api_key": config.ARIZE_API_KEY},
        )
        exporter_count += 1
        logger.info("telemetry: exporting to Arize AX (project=%s)", config.ARIZE_PROJECT_NAME)

    if exporter_count == 0:
        logger.info("telemetry: no LangSmith/Arize env configured — tracing disabled")
        return False

    return True
