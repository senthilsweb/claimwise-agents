"""Tools for the Data Steward — pipeline governance, not the warehouse
itself. This agent answers "can I trust these numbers today" by running
the pipeline's own dbt test suite live, tracing a gold table back through
the real dbt DAG, and looking up agreed term definitions — never by
inventing an opinion about data quality.
"""

import json
import os
import re
import subprocess
from pathlib import Path

from strands import tool

from agents import config
from agents.data import release_duckdb_connection
from agents.glossary import GLOSSARY

_SUMMARY_RE = re.compile(r"PASS=(\d+)\s+WARN=(\d+)\s+ERROR=(\d+)\s+SKIP=(\d+)")
_DBT_TARGET_MAP = {"duckdb": "dev", "databricks": "prod"}


@tool
def run_dq_checks() -> dict:
    """Run the claimwise pipeline's real data-quality test suite right now
    (not a cached result) and report whether today's data actually passes:
    counts of passed/warned/errored/skipped tests, and a trustworthy flag
    (True only if zero tests errored).
    """
    repo = config.require(config.CLAIMWISE_DBT_PATH, "CLAIMWISE_DBT_PATH")
    dbt_target = _DBT_TARGET_MAP.get(config.AGENT_TARGET, "dev")
    dbt_bin = str(Path(repo) / ".venv" / "bin" / "dbt")

    if config.AGENT_TARGET == "duckdb":
        # dbt's DuckDB adapter always opens read-write, even for `dbt test`
        # — release our own read-only lock on the same file first, or the
        # subprocess fails with a DuckDB lock-conflict IOException.
        release_duckdb_connection()

    try:
        result = subprocess.run(
            [dbt_bin, "test", "--target", dbt_target],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=120,
            # Never go through the dbt-ol wrapper here — it hangs if the
            # OpenLineage/Marquez endpoint it points at isn't reachable.
            env={**os.environ, "ENABLE_OPENLINEAGE": "false"},
        )
    except subprocess.TimeoutExpired:
        return {"ran": False, "error": "dbt test timed out after 120s"}
    except FileNotFoundError:
        return {"ran": False, "error": f"dbt binary not found at {dbt_bin} — check CLAIMWISE_DBT_PATH"}

    output = result.stdout + result.stderr
    match = _SUMMARY_RE.search(output)
    if not match:
        return {"ran": True, "parsed": False, "raw_tail": output[-1000:]}

    passed, warned, errored, skipped = (int(x) for x in match.groups())
    return {
        "ran": True,
        "parsed": True,
        "target": dbt_target,
        "passed": passed,
        "warned": warned,
        "errored": errored,
        "skipped": skipped,
        "trustworthy": errored == 0,
    }


def _load_manifest() -> dict:
    repo = config.require(config.CLAIMWISE_DBT_PATH, "CLAIMWISE_DBT_PATH")
    manifest_path = Path(repo) / "target" / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"No manifest.json at {manifest_path} — build the claimwise repo first")
    return json.loads(manifest_path.read_text())


def _find_node(manifest: dict, model_name: str) -> tuple[str, dict] | None:
    for node_id, node in manifest.get("nodes", {}).items():
        if node.get("name") == model_name:
            return node_id, node
    return None


@tool
def get_lineage(model_name: str) -> dict:
    """Look up where a table's data actually comes from — its direct
    upstream dependencies in the real dbt DAG (read from the pipeline's
    own manifest, not a guess), e.g. "mtr_claims_funnel" depends on
    "fct_claims".

    Args:
        model_name: A model name from the claimwise dbt project, e.g.
            "mtr_claims_funnel" or "fct_claims".
    """
    manifest = _load_manifest()
    found = _find_node(manifest, model_name)
    if not found:
        return {"found": False, "model_name": model_name}

    node_id, node = found
    dep_ids = node.get("depends_on", {}).get("nodes", [])
    upstream = []
    for dep_id in dep_ids:
        dep_node = manifest.get("nodes", {}).get(dep_id)
        if dep_node:
            upstream.append(dep_node.get("name"))

    return {
        "found": True,
        "model_name": model_name,
        "resource_type": node.get("resource_type"),
        "upstream": upstream,
    }


@tool
def glossary_lookup(term: str) -> dict:
    """Look up the one agreed business definition of a term, e.g. "denial
    rate", "claim", "open AR". Use this instead of guessing what a word
    means from context.

    Args:
        term: The term to define.
    """
    key = term.strip().lower()
    if key in GLOSSARY:
        return {"found": True, "term": key, "definition": GLOSSARY[key]}
    partial = [k for k in GLOSSARY if key in k or k in key]
    if partial:
        return {"found": True, "term": partial[0], "definition": GLOSSARY[partial[0]]}
    return {"found": False, "term": term, "known_terms": sorted(GLOSSARY.keys())}
