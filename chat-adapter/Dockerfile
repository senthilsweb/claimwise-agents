# claimwise-chat-adapter — translates the mcp-chat-client widget's REST/SSE
# contract into SigV4-signed InvokeAgentRuntime calls. AWS credentials come
# from the environment or a mounted ~/.aws (see docker-compose.yml).
FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir \
    "fastapi>=0.115" "uvicorn>=0.30" "boto3>=1.34" "python-dotenv>=1.0"

COPY app.py ./

EXPOSE 8006
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8006"]
