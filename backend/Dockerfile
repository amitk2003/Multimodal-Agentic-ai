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

# Run with uvicorn (production: remove --reload)
CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "8000"]
