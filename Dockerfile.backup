# Railway-specific Dockerfile
# Force rebuild: 2024-01-15-EMERGENCY-CACHE-BUST
# Timestamp: 2024-01-15 20:30 UTC
FROM python:3.9-slim

# Add cache busting
ARG CACHE_BUST=2024-01-15-20-30
RUN echo "Cache bust: $CACHE_BUST"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Force rebuild timestamp
RUN echo "Build timestamp: $(date)" > /app/build_timestamp.txt

# Railway expects the app to listen on $PORT
ENV PORT=8080
EXPOSE $PORT

# Start command with cache bust - FORCE REBUILD
CMD echo "Starting app at $(date) - FORCE REBUILD VERSION" && python -c "import sys; print('Python version:', sys.version)" && uvicorn app_server:app --host 0.0.0.0 --port $PORT