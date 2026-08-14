# Multi-stage lightweight Python Dockerfile for Mnemosyne Backend
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies if required for psycopg2/build
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

# Expose port (Render automatically provides $PORT)
EXPOSE 8000

# Run FastAPI & FastMCP SSE server via uvicorn
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
