"""FastAPI bridge between the mcp-chat-client widget and Bedrock AgentCore.

The widget (https://github.com/senthilsweb/mcp-chat-client) speaks a small
REST/SSE contract: POST {message, session_id?, history?} to /chat/stream,
then render `data: {"type":"text","content":...}` chunks until `data: [DONE]`.
AgentCore Runtime speaks InvokeAgentRuntime with SigV4 auth, which a browser
can never do. This service translates one contract into the other — the agent
itself (agents/runtime.py) is untouched.

Run locally:   uv run uvicorn app:app --port 8006     (from this folder)
Run the stack: docker compose up --build               (from the repo root)
"""

import json
import os
import re
import uuid
from pathlib import Path

import boto3
from botocore.config import Config
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Reuse the repo-root .env (AWS creds, region) when run outside compose.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

AGENT_RUNTIME_ARN = os.getenv("AGENT_RUNTIME_ARN", "")
if not AGENT_RUNTIME_ARN:
    raise RuntimeError(
        "Set AGENT_RUNTIME_ARN to the deployed runtime's ARN "
        "(agent_arn in .bedrock_agentcore.yaml) — see .env.sample"
    )
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")

# The Supervisor fans out to specialists, so a single answer can take a few
# minutes — botocore's default 60s read timeout would cut it off mid-run.
_agentcore = boto3.client(
    "bedrock-agentcore",
    region_name=AWS_REGION,
    config=Config(connect_timeout=10, read_timeout=900, retries={"max_attempts": 1}),
)

app = FastAPI(title="claimwise-chat-adapter")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class Turn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    history: list[Turn] | None = None


MAX_HISTORY_TURNS = 10


def _runtime_session_id(session_id: str | None) -> str:
    """AgentCore requires a 33-100 char session id of [A-Za-z0-9_-]."""
    if not session_id:
        return f"chat-{uuid.uuid4().hex}"
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "-", session_id)
    return cleaned.ljust(33, "x")[:100]


def _build_prompt(req: ChatRequest) -> str:
    """Fold the widget's transcript into the prompt.

    agents/runtime.py builds a fresh Supervisor per invocation and AgentCore
    Memory is off by default, so multi-turn context has to travel with each
    request — and the widget already sends its full transcript every turn.
    """
    if not req.history:
        return req.message
    turns = req.history[-MAX_HISTORY_TURNS:]
    transcript = "\n".join(f"{t.role}: {t.content}" for t in turns)
    return (
        "Earlier turns of this conversation, oldest first:\n"
        f"{transcript}\n\n"
        f"Current question: {req.message}"
    )


def _sse(chunk: dict) -> str:
    return f"data: {json.dumps(chunk)}\n\n"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat/stream")
def chat_stream(req: ChatRequest) -> StreamingResponse:
    def gen():
        # Shows as a live status line in the widget while the crew works.
        yield _sse({"action": "Asking the Revenue Copilot…"})
        try:
            resp = _agentcore.invoke_agent_runtime(
                agentRuntimeArn=AGENT_RUNTIME_ARN,
                runtimeSessionId=_runtime_session_id(req.session_id),
                payload=json.dumps({"prompt": _build_prompt(req)}),
            )
            if "text/event-stream" in (resp.get("contentType") or ""):
                # A streaming entrypoint (async-generator) relays chunk by
                # chunk. agents/runtime.py returns one dict today, so this
                # branch only fires if the entrypoint is made streaming later.
                for raw in resp["response"].iter_lines():
                    line = raw.decode() if isinstance(raw, bytes) else raw
                    if not line.startswith("data: "):
                        continue
                    piece = line[len("data: "):]
                    try:
                        piece = json.loads(piece)
                    except json.JSONDecodeError:
                        pass
                    yield _sse({"type": "text", "content": str(piece)})
            else:
                body = json.loads(resp["response"].read())
                if "error" in body:
                    yield _sse({"type": "error", "error": body["error"]})
                else:
                    yield _sse({"type": "text", "content": str(body.get("result", body))})
        except Exception as exc:  # surface AWS errors in the widget, not a dead bubble
            yield _sse({"type": "error", "error": f"{type(exc).__name__}: {exc}"})
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
