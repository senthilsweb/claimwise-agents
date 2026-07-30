# Getting Started

At the end you will have run the agents locally, first for free with no
AWS account needed, then for real against a live model.

## Path 1 — zero AWS cost (2 minutes)

This proves the data adapter, every tool, and the trust boundary (agents
can't write) all work, without spending a single model call.

```bash
git clone https://github.com/senthilsweb/claimwise-agents.git
cd claimwise-agents
cp .env.sample .env
```

Edit `.env` and point `DUCKDB_PATH` at a built Claimwise database — see
the [Claimwise repo](https://github.com/senthilsweb/claimwise) if you
don't have one yet (`make setup deps build` there produces
`dbt-pipeline/rcm.duckdb`).

```bash
make setup
make smoke
```

Expected output ends with:

```
31/31 checks passed.
```

## Path 2 — talk to a live agent (needs an AWS account)

1. Get Bedrock model access — open **Bedrock → Model catalog** in the AWS
   console, pick a Claude model, and note its model ID. Some models need
   a cross-region inference profile ID instead of the bare model ID —
   `aws bedrock list-inference-profiles --region <your-region>` shows
   both.
2. Authenticate the CLI: `aws configure` (access key) or `aws configure
   sso`, whichever your account uses.
3. Set in `.env`:
   ```
   AWS_REGION=<your-region>
   AWS_PROFILE=<your-profile>
   BEDROCK_MODEL_ID=<the model id from step 1>
   ```
4. Chat with the full crew:
   ```bash
   make run
   ```
   ```
   Claimwise Supervisor (full crew) — ask a question (Ctrl-D to quit).
   Target: reading the gold layer from DuckDB.
   Tracing: off (no LANGSMITH_*/ARIZE_*/OTEL_* env set).

   > What is our overall denial rate?

   The overall denial rate is 14.62%, from the mtr_executive_summary table.
   ```

## What next

- Every environment variable → [Configuration](configuration.md)
- What each agent answers → [The Agents](the-agents.md)
- Every `make` target → [Commands](commands.md)
