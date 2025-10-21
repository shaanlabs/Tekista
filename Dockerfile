FROM python:3.12-slim

# Minimal environment hardening and ensure /app is on PYTHONPATH
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# Copy requirements and install; install build tools only temporarily
COPY requirements.txt .

# install build deps temporarily, install requirements, then cleanup
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Create a non-root user, prepare instance/ and tighten permissions
RUN useradd --create-home appuser \
    && mkdir -p /app/instance \
    && chown -R appuser:appuser /app \
    && chmod -R go-rwx /app \
    && find /app -type d -exec chmod 750 {} + \
    && find /app -type f -exec chmod 640 {} +

USER appuser

EXPOSE 5000

# Default Flask settings (can be overridden via docker-compose or docker run -e)
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Add Ollama defaults (adjust OLLAMA_MODEL to the exact name you have pulled)
ENV OLLAMA_HOST=http://host.docker.internal:11434
# Use requested llama3.2 3B model
ENV OLLAMA_MODEL=llama3.2:3b
ENV OLLAMA_USE_GPU=true

# Add a simple HTTP healthcheck implemented with Python (no curl required)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:5000/health')"]

# Default command (keeps compatibility with existing project)
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]