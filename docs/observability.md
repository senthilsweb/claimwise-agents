# Observability

At the end you will know how to see every prompt, every tool call (with
its real inputs and outputs), and every model response an agent makes —
and how to check it actually landed, not just trust an HTTP 200.

## Three backends, all optional, all off by default

Set any combination of these in `.env` (see [Configuration](configuration.md))
and `agents/telemetry.py` exports the full trace to all of them at once —
they're independent, not either/or:

| Backend | Env vars | What it's for |
|---|---|---|
| [LangSmith](https://smith.langchain.com) | `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` | LangChain's own trace viewer |
| [Arize AX](https://app.arize.com) | `ARIZE_SPACE_ID`, `ARIZE_API_KEY`, `ARIZE_PROJECT_NAME` | LLM-focused observability, model/token metrics |
| Any generic OTLP/HTTP collector | `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS` | e.g. a self-hosted OpenObserve instance |

None of this needs a code change to turn on or off — `setup_telemetry()`
in `agents/telemetry.py` just checks which env vars are set and wires up
that many OTLP exporters against Strands' own tracer.

## Full content, by default

Strands emits full prompt, tool-input, and tool-output content on every
span by default — nothing is redacted unless you explicitly opt into
that via `OTEL_SEMCONV_STABILITY_OPT_IN` (see the docstring in
`agents/telemetry.py`). This means every backend above shows the actual
question, the actual tool calls (`query_metric` with its real SQL and
result rows, `get_claim_story` with the real claim it returned, and so
on), and the actual final answer — not a summary.

## How to verify it's actually working

An HTTP 200 from an OTLP endpoint only means the payload was *accepted* —
it doesn't prove the trace was stored or is queryable. Check the backend
directly:

**OpenObserve** — query the stream via its search API:

```python
import requests, time
resp = requests.post(
    "https://<your-instance>/api/default/_search?type=traces",
    headers={"Authorization": "Basic <your-token>"},
    json={"query": {
        "sql": "SELECT trace_id, service_name, operation_name, start_time "
               "FROM \"default\" WHERE service_name = 'strands-agents' "
               "ORDER BY start_time DESC LIMIT 5",
        "start_time": int((time.time() - 300) * 1_000_000),
        "end_time": int(time.time() * 1_000_000),
    }},
)
```

A real query against a live Claimwise Agents run returns rows like:

```
{'operation_name': 'chat', 'service_name': 'strands-agents', 'trace_id': '701214ed7bf8a5683518b0fbe74f6698'}
{'operation_name': 'execute_event_loop_cycle', 'service_name': 'strands-agents', ...}
{'operation_name': 'execute_tool get_claim_story', 'service_name': 'strands-agents', ...}
```

That's a real span chain from one real question — the top-level `chat`
call, Strands' internal reasoning loop, and the actual tool it decided to
call.

**LangSmith / Arize** — use each platform's own run-query API or just open
the project in their web UI; both show the trace within seconds of a
`make run` or `make eval` call.

## What next

- Every trace field explained in context of what each agent does → [The Agents](the-agents.md)
- Confirming tracing survives the AgentCore Runtime wrapper too → [Deployment](deployment.md)
