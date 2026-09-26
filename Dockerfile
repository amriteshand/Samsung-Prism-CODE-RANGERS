FROM python:3.11-slim

LABEL maintainer="Samsung PRISM Hackathon Team"
LABEL theme="Theme 2: Smart Guided Troubleshooting Engine"
LABEL hackathon="Samsung PRISM GenAI Hackathon 3rd Edition"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

# Install minimal OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application codebase and datasets
COPY data/ ./data/
COPY engine/ ./engine/
COPY api/ ./api/
COPY benchmark/ ./benchmark/
COPY tests/ ./tests/
COPY metrics.md .

# Pre-warm indices and verify unit tests during image build
RUN python -m unittest discover -s tests -p "test_*.py"

EXPOSE 8000

# Health check to ensure sub-300ms ready state
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start container with production uvicorn server
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
