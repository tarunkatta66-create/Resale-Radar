# Python 3.11 slim base image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a dedicated non-root user and group
RUN useradd -m -u 1000 appuser

# Copy application files, data, and trained models
COPY app/ ./app/
COPY data/ ./data/
COPY models/ ./models/
COPY static/ ./static/

# Adjust permissions for non-root user
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Container healthcheck using standard Python urllib (no external curl package needed)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request, os; port = os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health')" || exit 1

# Start Uvicorn ASGI server with dynamic port support for Render
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
