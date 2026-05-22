FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir \
    "mcp[cli]>=1.6.0" \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "pydantic>=2.0.0" \
    "httpx>=0.27.0" \
    "pydantic-settings>=2.0.0" \
    "pyyaml>=6.0"

ENV PYTHONPATH=/app

# For local mode: mount your governance repo at /governance
# For github mode: set GOVERNANCE_REPO_URL and GITHUB_TOKEN

ENV GOVERNANCE_MODE=github
ENV GOVERNANCE_REPO_PATH=/governance
ENV MCP_SERVER_HOST=0.0.0.0
ENV MCP_SERVER_PORT=8080
ENV LOG_LEVEL=INFO

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["python", "-m", "src.main"]
