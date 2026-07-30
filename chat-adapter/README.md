# chat-adapter

A ~100-line FastAPI service that lets the
[mcp-chat-client](https://github.com/senthilsweb/mcp-chat-client) browser
widget converse with the Supervisor deployed on Bedrock AgentCore. The
browser can't call AgentCore directly — `InvokeAgentRuntime` needs
SigV4-signed requests, and AWS credentials never belong in a browser — so
this adapter sits in between and translates:

```
widget ──POST /chat/stream──▶ chat-adapter ──InvokeAgentRuntime──▶ AgentCore
       ◀── SSE text chunks ──┘                (SigV4, us-east-2)
```

`agents/` is the agent itself; this folder is only the transport bridge —
nothing about the agent changes.

## Run

| I want to… | Run this |
|---|---|
| Full stack (widget + adapter) | `make chat` from the repo root, then open <http://localhost:3000> |
| Adapter only, no checkout | `docker run --rm -p 8006:8006 -e AGENT_RUNTIME_ARN=… -e AWS_REGION=us-east-2 -v ~/.aws:/root/.aws:ro ghcr.io/senthilsweb/claimwise-chat-adapter:latest` |
| Adapter only, from source | `uv run uvicorn app:app --port 8006` from this folder |

The public image (`ghcr.io/senthilsweb/claimwise-chat-adapter`, amd64 +
arm64) is rebuilt by
[`.github/workflows/publish-chat-adapter.yml`](../.github/workflows/publish-chat-adapter.yml)
on every push to `main` that touches this folder — tags: `latest`,
`main`, `sha-<short>`.

Needs `AGENT_RUNTIME_ARN` in the repo-root `.env` (the `agent_arn` from
`.bedrock_agentcore.yaml`) plus working AWS credentials with
`bedrock-agentcore:InvokeAgentRuntime` on that ARN.

Smoke test without the widget:

```bash
curl -N localhost:8006/chat/stream -H 'Content-Type: application/json' \
  -d '{"message": "What is our overall denial rate?"}'
```

## What it translates

| Widget contract | AgentCore side |
|---|---|
| `POST /chat/stream` `{message, session_id?, history?}` | `InvokeAgentRuntime` with `payload={"prompt": …}` |
| `session_id` (any string, optional) | padded/sanitized to the required 33-char `runtimeSessionId` |
| `history` (the widget resends its transcript each turn) | folded into the prompt — the runtime builds a fresh Supervisor per call, so context must travel with the request |
| SSE `data: {"type":"text","content":…}` … `data: [DONE]` | the runtime's JSON `{"result": …}` (or relayed chunk-by-chunk if the entrypoint is ever made streaming) |
| `data: {"action": …}` live status line | emitted once up front — a Supervisor answer can take a minute or two |

CORS is wide open — this is a local test bridge. Put it behind an API key
check (the widget passes custom headers via `config.headers`) before
exposing it anywhere public.
