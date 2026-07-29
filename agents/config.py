"""Environment-driven config. No credentials or paths hardcoded anywhere else."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

AGENT_TARGET = os.getenv("AGENT_TARGET", "duckdb")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "")

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "")

# The claimwise dbt-pipeline repo root — needed only by the Data Steward
# (run_dq_checks runs `dbt test` there; get_lineage reads its manifest.json).
CLAIMWISE_DBT_PATH = os.getenv("CLAIMWISE_DBT_PATH", "")

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")
DATABRICKS_CATALOG = os.getenv("DATABRICKS_CATALOG", "workspace")

# --- Observability (all optional — absence just disables tracing) ---
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").strip().lower() == "true"
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "claimwise-agents")

ARIZE_SPACE_ID = os.getenv("ARIZE_SPACE_ID", "")
ARIZE_API_KEY = os.getenv("ARIZE_API_KEY", "")
ARIZE_PROJECT_NAME = os.getenv("ARIZE_PROJECT_NAME", "claimwise-agents")

# Generic OTLP endpoint — used for the home-lab OpenObserve instance
# (telemetry.nathansweb.com), but works with any OTLP/HTTP collector.
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
OTEL_EXPORTER_OTLP_HEADERS = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")


def require(value: str, name: str) -> str:
    if not value:
        raise RuntimeError(f"{name} is not set — check .env (see .env.sample)")
    return value
