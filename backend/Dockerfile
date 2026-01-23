FROM python:3.11-slim

WORKDIR /app

# Verify Python version
RUN python --version

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
# Prefer binary wheels but allow source builds if needed
RUN pip install --upgrade pip setuptools wheel && \
    pip install --prefer-binary -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will set PORT env var)
EXPOSE $PORT

# Start application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}
