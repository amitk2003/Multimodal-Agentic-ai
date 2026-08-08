FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
# weasyprint requires libpango, libcairo, libgdk-pixbuf and friends
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run with Gunicorn + Uvicorn worker in production
CMD ["sh", "-c", "gunicorn -w ${WORKERS:-4} -k uvicorn.workers.UvicornWorker app.main:socket_app --bind 0.0.0.0:${PORT:-8000}"]
