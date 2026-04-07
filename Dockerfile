# Railway-specific Dockerfile
# FORCE COMPLETE REBUILD: 2024-01-15 22:00 UTC - NUCLEAR OPTION
# This should force Railway to rebuild from scratch
ARG FORCE_REBUILD=2024-01-15-22-00-00
RUN echo "FORCE_REBUILD=$FORCE_REBUILD"

FROM python:3.9-slim

# Force rebuild with timestamp
ARG BUILD_TIMESTAMP=2024-01-15-22-00-00
RUN echo "Build timestamp: $BUILD_TIMESTAMP"

WORKDIR /app

# Install system dependencies with cache bust
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
RUN echo "Build timestamp: $(date +%s)" > /app/build_timestamp.txt && echo "NUCLEAR REBUILD: $(date)" >> /app/build_timestamp.txt

# Railway expects the app to listen on $PORT
ENV PORT=8080
EXPOSE $PORT

# Start command with NUCLEAR FORCE REBUILD - USING BACKUP FILE
CMD echo "🚀 Starting Nexus CRM app" && python -c "import sys; print('Python version:', sys.version)" && echo "🚀 Serving app_server:app" && uvicorn app_server:app --host 0.0.0.0 --port $PORT