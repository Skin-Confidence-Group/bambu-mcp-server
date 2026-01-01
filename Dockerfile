# Dockerfile for Bambu MCP Server on Railway
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY pyproject.toml .

# Install the package
RUN pip install -e .

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Health check (using curl instead of requests)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the server - Railway sets $PORT dynamically
CMD python -m uvicorn bambu_mcp.server:app --host 0.0.0.0 --port ${PORT:-8000}
