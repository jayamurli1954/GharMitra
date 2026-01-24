FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (essential for asyncpg)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application code
COPY . .

# Start application
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
